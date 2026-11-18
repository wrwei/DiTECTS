#!/usr/bin/env python3
"""Review-time re-verification over the ADS impact graph (standard library only).

Follows every safety-case Solution's evidence links in namespace/ads-namespace.json, resolves a
checker from the target element's kind, runs it on a scratch copy of the artefacts in this
repository, and records a current verdict. No authoring platform is involved.

  kind            artefacts                checker
  Dafny Model     formal/dafny             dafny verify *.dfy
  Isabelle Model  formal/isabelle          isabelle build -D <dir>      (host, or --isabelle-docker)
  FDR Model       formal/csp               refines <*_coreassertions.csp>
  Java Model      implementation/java      gradle test --offline --no-daemon
  ModelicaModel   simulation/modelica      omc <script>.mos in an OpenModelica container (--modelica-docker)
                  (+ models/sysml)         simulate(ADSChangeover) over its experiment annotation
  (FMEDA rows, fault-tree events, design elements: evidence records, no checker configured)

Simulation bindings. Before the modelica runner simulates, it applies every Degree 0 value binding
(namespace edges ModelicaParameter -> SAttributeUsage: typed links with relation binds, or sim-binding edges;
see tools/sim_bindings.py) whose
parameter belongs to the target model: the parameter's value is read from the bound attribute in the
scratch copy of the SysML text and written into the scratch copy of the Modelica source. A design change
made to the SysML attribute therefore reaches the simulation through the binding. The modelica verdict
is PASS when the simulation completes without the DF assertion firing, FAIL when the assertion fires (its
message and time are recorded) or the model does not translate, TIMEOUT, or NOT_ASSESSED when no
container runtime or image is available. After a FAIL caused by the assertion, a diagnostic run on a
second copy, with that assertion lowered to AssertionLevel.warning, reports the minimum DF over the whole
experiment horizon; it does not change the verdict.

Conditions
  baseline   unmodified artefacts
  mutants    seeded faults and semantics-preserving controls (tools/c3/mutants.json)
  stale      a design change: impact closure over the namespace (namespace/impact.py) flags the
             Solutions it reaches; their executable evidence is re-run with the change applied
             (tools/c3/stale.json)
  latency    wall-clock cost of the impact traversal from every element
  dry-run    check that every mutant / stale edit applies with its expected match count

Examples
  python3 tools/reverify.py baseline
  python3 tools/reverify.py all --isabelle-docker isabelle-runtime:22.04 --out ~/ads-experiments/reverify
  python3 tools/reverify.py mutants --only Sn7,Sn10
  python3 tools/reverify.py latency --reps 30

Verdicts: PASS, FAIL, TIMEOUT (checker exceeded its time budget; evidence NOT re-established),
NOT_ASSESSED (checker unavailable, killed or stopped by a resource/environment failure;
no artefact verdict was established).
"""
import argparse, csv, json, os, platform, re, shutil, signal, statistics, subprocess, sys, tempfile, time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "namespace"))
import impact as ns_impact  # noqa: E402  (the repository's own traversal)
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import sim_bindings as SB  # noqa: E402  (Degree 0 SysML-to-Modelica value bindings)

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

RUNNERS = {
    "Dafny Model":    {"runner": "dafny",    "dir": "formal/dafny",        "timeout": 120},
    "Isabelle Model": {"runner": "isabelle", "dir": "formal/isabelle",     "timeout": 1800},
    "FDR Model":      {"runner": "fdr",      "dir": "formal/csp",          "timeout": 600},
    "Java Model":     {"runner": "gradle",   "dir": "implementation/java", "timeout": 900},
    # The modelica runner's scratch copy keeps repository paths (edits name them, e.g.
    # models/sysml/02-design.sysml), because bound values are read from the SysML text.
    "ModelicaModel":  {"runner": "modelica", "dir": "simulation/modelica", "with": ["models/sysml"], "timeout": 600},
}

def stage(spec, wd):
    """Scratch copy of a runner's artefacts: its directory, or (with "with") a repository-shaped tree."""
    if spec.get("with"):
        for d in [spec["dir"]] + spec["with"]:
            shutil.copytree(os.path.join(REPO, d), os.path.join(wd, d))
    else:
        shutil.copytree(os.path.join(REPO, spec["dir"]), wd)


# ------------------------------------------------------------------ evidence links
def evidence_links(ns):
    node = {n["id"]: n for n in ns["nodes"]}
    links = []
    for e in ns["edges"]:
        s, t = node.get(e["source"]), node.get(e["target"])
        if e["kind"] != "traceability" or not s or s.get("kind") != "Solution" or not t:
            continue
        spec = RUNNERS.get(t.get("kind"))
        links.append({"solution": s["label"], "solutionId": s["id"], "link": e.get("name"),
                      "target": t.get("label") or t["id"], "targetId": t["id"], "targetKind": t.get("kind"),
                      "runner": spec["runner"] if spec else None})
    return sorted(links, key=lambda l: (int(re.sub(r"\D", "", l["solution"]) or 0), l["link"] or ""))


# ------------------------------------------------------------------ edits (JS replace semantics)
def _js_repl(template):
    def f(m):
        return re.sub(r"\$(\d|\$|&)", lambda t: "$" if t.group(1) == "$" else
                      (m.group(0) if t.group(1) == "&" else (m.group(int(t.group(1))) or "")), template)
    return f

def apply_edits(workdir, edits):
    changed = False
    for e in edits:
        p = os.path.join(workdir, e["file"])
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
        rx = re.compile(e["pattern"])
        n = len(rx.findall(text))
        if e.get("expectCount") and n != e["expectCount"]:
            raise ValueError("pattern in %s matched %dx, expected %d" % (e["file"], n, e["expectCount"]))
        if n == 0:
            raise ValueError("pattern in %s matched nothing" % e["file"])
        new = rx.sub(_js_repl(e["replace"]), text)
        changed |= new != text
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
    return changed


# ------------------------------------------------------------------ process control
def run_proc(cmd, cwd, timeout, env=None, on_timeout=None):
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    timed_out = False
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if on_timeout:
            on_timeout()
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, _ = p.communicate()
    return {"exit": p.returncode, "output": out.decode("utf-8", "replace"), "timedOut": timed_out,
            "seconds": round(time.monotonic() - t0, 2)}


# ------------------------------------------------------------------ checkers and verdict rules
def check_dafny(args, wd, link=None):
    files = sorted(f for f in os.listdir(wd) if f.endswith(".dfy"))
    cmd = [args.dafny, "verify"] + ["./" + f for f in files]
    r = run_proc(cmd, wd, args.timeout_dafny)
    m = re.search(r"(\d+) verified, (\d+) errors?", r["output"])
    ok = r["exit"] == 0 and m is not None and int(m.group(2)) == 0
    err = re.search(r"^.*(errors? detected|Error:).*$", r["output"], re.M)
    detail = "%s verified, %s errors" % (m.group(1), m.group(2)) if m else (err.group(0).strip()[:160] if err else "no Dafny summary line")
    return cmd, r, ok, detail, bool(m or err)

def isabelle_session(wd):
    with open(os.path.join(wd, "ROOT")) as fh:
        m = re.search(r'session\s+"?([\w.-]+)"?', fh.read())
    return m.group(1) if m else None

def check_isabelle(args, wd, link=None):
    session = isabelle_session(wd)
    if args.isabelle_docker:
        name = "reverify-isa-%d-%d" % (os.getpid(), int(time.time() * 1000) % 100000)
        root = os.path.realpath(args.out)
        cmd = ["docker", "run", "--rm", "--init", "--name", name, "--platform", "linux/amd64",
               "--memory", args.isabelle_memory, "-v", "%s:/opt/isabelle:ro" % args.isabelle_home,
               "-v", "%s:%s" % (root, root), "-w", wd, args.isabelle_docker,
               "timeout", "-k", "30", str(args.timeout_isabelle + 60),
               "/opt/isabelle/bin/isabelle", "build", "-D", wd]
        kill = lambda: subprocess.run(["docker", "kill", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        cmd, kill = [args.isabelle, "build", "-D", wd], None
    r = run_proc(cmd, wd, args.timeout_isabelle, on_timeout=kill)
    out = r["output"]
    bad = re.search(r"\*\*\*|\bFAILED\b|Unfinished session|Bad session|Unknown session", out)
    finished = session and re.search(r"Finished %s\b" % re.escape(session), out)
    ok = r["exit"] == 0 and bool(finished) and not bad
    if ok:
        detail = "Finished %s" % session
    else:
        first = PROCESS_FAILURE.search(out) or re.search(r"^\*\*\*.*$", out, re.M) or bad
        detail = (first.group(0) if first else "no 'Finished %s'" % session)[:160]
    return cmd, r, ok, detail, bool(finished or bad)

def fdr_entry(wd):
    top = sorted(f for f in os.listdir(wd) if f.endswith(".csp"))
    core = [f for f in top if f.endswith("_coreassertions.csp")]
    return (core or top)[0]

def check_fdr(args, wd, link=None):
    cmd = [args.fdr, "./" + fdr_entry(wd)]
    env = dict(os.environ, TERM="dumb", NO_COLOR="1")
    r = run_proc(cmd, wd, args.timeout_fdr, env=env)
    clean = ANSI.sub("", r["output"])           # refines colours its results even without a TTY
    r["output"] = clean
    passed = len(re.findall(r"Result:\s*Passed", clean))
    failed = len(re.findall(r"Result:\s*Failed", clean))
    ok = r["exit"] == 0 and passed > 0 and failed == 0   # refines exits 0 even when assertions fail
    parsed = passed + failed > 0 or bool(re.search(r"error", clean, re.I) and not re.search(r"licen[cs]e", clean, re.I))
    return cmd, r, ok, "%d assertions passed, %d failed" % (passed, failed), parsed

def check_gradle(args, wd, link=None):
    cmd = [args.gradle, "test", "--offline", "--no-daemon", "--console=plain"]
    r = run_proc(cmd, wd, args.timeout_gradle)
    tests = fails = skipped = 0
    rep = os.path.join(wd, "build", "test-results", "test")
    if os.path.isdir(rep):
        for f in os.listdir(rep):
            if f.endswith(".xml"):
                ts = ET.parse(os.path.join(rep, f)).getroot()
                tests += int(ts.get("tests", 0)); skipped += int(ts.get("skipped", 0))
                fails += int(ts.get("failures", 0)) + int(ts.get("errors", 0))
    ok = r["exit"] == 0 and tests > 0 and fails == 0
    detail = "%d tests, %d passed, %d failed, %d skipped" % (tests, tests - fails - skipped, fails, skipped)
    if tests == 0 and re.search(r"Compilation failed|compileJava FAILED|compileTestJava FAILED", r["output"]):
        detail = "compilation failed"
    return cmd, r, ok, detail, tests > 0 or detail == "compilation failed"

MODELICA_ASSERT = re.compile(r'assertion has been violated at time\s+([-+0-9.eE]+)(.*?)-->\s*\\?"(.*?)\\?"\s*$', re.S | re.M)

def modelica_class(text):
    m = re.search(r"^\s*model\s+(\w+)", text, re.M)
    return m.group(1) if m else None

def apply_sim_bindings(args, wd, link):
    """Set each bound parameter of the target model from its SysML attribute (scratch copies only)."""
    applied = []
    mdir = os.path.join(wd, RUNNERS["ModelicaModel"]["dir"])
    files = {modelica_class(open(os.path.join(mdir, f), encoding="utf-8").read()): os.path.join(mdir, f)
             for f in sorted(os.listdir(mdir)) if f.endswith(".mo")}
    for b in SB.bindings(args.ns):
        p, a, m = b["parameter"], b["attribute"], b["model"]
        if not p or not a or not m or m["id"] != link["targetId"]:
            continue
        value, src = SB.sysml_value(wd, a["qualifiedName"])
        cls, name = p["qualifiedName"].split(".", 1)
        if value is None or cls not in files:
            raise ValueError("binding %s <- %s could not be resolved in the scratch copy" % (p["qualifiedName"], a["qualifiedName"]))
        with open(files[cls], encoding="utf-8", newline="") as fh:
            text = fh.read()
        before = SB.modelica_parameter(text, name)[0]
        new, n = SB.set_modelica_parameter(text, name, value)
        if n != 1:
            raise ValueError("parameter %s declared %d times" % (p["qualifiedName"], n))
        with open(files[cls], "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        applied.append({"parameter": p["qualifiedName"], "attribute": a["qualifiedName"], "from": src,
                        "value": value, "previous": before, "changed": value != before})
    return applied, files

def modelica_run(args, wd, cls, tag):
    """omc in the container: load the model, simulate it over its experiment annotation, CSV result."""
    mdir = os.path.join(wd, RUNNERS["ModelicaModel"]["dir"])
    script = os.path.join(mdir, "reverify_%s.mos" % tag)
    with open(script, "w") as fh:
        fh.write('loadFile("%s.mo"); getErrorString();\n' % cls)
        # omc prints the SimulationResult record (resultFile, messages); the verdict is parsed from it.
        fh.write('simulate(%s, outputFormat="csv", fileNamePrefix="%s_%s"); getErrorString();\n' % (cls, cls, tag))
    name = "reverify-omc-%d-%d" % (os.getpid(), int(time.time() * 1000) % 100000)
    root = os.path.realpath(wd)
    cmd = ["docker", "run", "--rm", "--init", "--pull", "never", "--name", name]
    if args.modelica_platform:
        cmd += ["--platform", args.modelica_platform]
    cmd += ["-e", "HOME=/tmp", "-v", "%s:%s" % (root, root), "-w", os.path.join(root, RUNNERS["ModelicaModel"]["dir"]),
            args.modelica_docker, "timeout", "-k", "30", str(args.timeout_modelica + 30), "omc", os.path.basename(script)]
    kill = lambda: subprocess.run(["docker", "kill", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = run_proc(cmd, wd, args.timeout_modelica, on_timeout=kill)
    csvp = os.path.join(mdir, "%s_%s_res.csv" % (cls, tag))
    series = []
    if os.path.exists(csvp):
        with open(csvp, newline="") as fh:
            rows = list(csv.reader(fh))
        if rows:
            hdr = [h.strip('"') for h in rows[0]]
            if "time" in hdr and "DF" in hdr:
                it, idf = hdr.index("time"), hdr.index("DF")
                series = [(float(x[it]), float(x[idf])) for x in rows[1:] if len(x) > max(it, idf)]
    return cmd, r, series

def check_modelica(args, wd, link=None):
    if not args.modelica_docker:
        return (["(no --modelica-docker image)"], {"exit": None, "output": "no OpenModelica runtime configured", "timedOut": False, "seconds": 0},
                False, "no OpenModelica runtime configured", False, {})
    applied, files = apply_sim_bindings(args, wd, link)
    classes = sorted(c for c in files if c)
    cls = classes[0] if len(classes) == 1 else (applied[0]["parameter"].split(".")[0] if applied else classes[0])
    cmd, r, series = modelica_run(args, wd, cls, "verdict")
    out = r["output"]
    extra = {"bindingsApplied": applied}
    asserted = MODELICA_ASSERT.search(out)
    finished = re.search(r"The simulation finished successfully", out)
    translated = re.search(r"record SimulationResult", out) or finished or asserted
    if series:
        t_min, df_min = min(series, key=lambda x: x[1])
        extra["simulated"] = {"samples": len(series), "tEnd": series[-1][0], "minDF": round(df_min, 4), "minDFAt": t_min}
    if asserted:
        extra["assertion"] = {"time": float(asserted.group(1)), "message": asserted.group(3)}
        ok = False
        detail = "assertion fired at t = %.1f s: %s" % (float(asserted.group(1)), asserted.group(3))
        if args.modelica_diagnose:
            dwd = wd + "__diagnostic"
            if os.path.exists(dwd):
                shutil.rmtree(dwd)
            shutil.copytree(wd, dwd)
            mo = os.path.join(dwd, os.path.relpath(files[cls], wd))
            text = open(mo, encoding="utf-8").read()
            text2, n = re.subn(r'(assert\(DF\s*>=\s*DFtarget,\s*"[^"]*")\)', r"\1, AssertionLevel.warning)", text)
            open(mo, "w", encoding="utf-8").write(text2)
            _, rd, ds = modelica_run(args, dwd, cls, "diagnostic")
            if n == 1 and ds:
                t_min, df_min = min(ds, key=lambda x: x[1])
                extra["diagnostic"] = {"assertionLevel": "warning", "samples": len(ds), "tEnd": ds[-1][0],
                                       "minDF": round(df_min, 4), "minDFAt": t_min,
                                       "note": "second scratch copy with the DF assertion lowered to a warning; not a verdict"}
                detail += "; diagnostic run (assertion as warning): min DF %.1f at t = %.0f s over 0-%.0f s" % (df_min, t_min, ds[-1][0])
            with open(os.path.join(args.out, "logs", "%s__diagnostic.log" % os.path.basename(wd)), "w") as fh:
                fh.write(rd["output"])
            if not args.keep_work:
                shutil.rmtree(dwd, ignore_errors=True)
    elif finished and translated:
        ok = True
        detail = "simulation completed, assertion not fired"
        if series:
            detail += "; min DF %.1f at t = %.0f s over 0-%.0f s" % (extra["simulated"]["minDF"], extra["simulated"]["minDFAt"], series[-1][0])
    else:
        ok = False
        err = re.search(r"^.*(Error|error):.*$", out, re.M)
        detail = ("translation or simulation failed: " + err.group(0).strip()[:140]) if err else "no simulation result"
    vals = ", ".join("%s=%g" % (a["parameter"].split(".")[-1], a["value"]) for a in applied)
    detail = ("bound %s; " % vals if vals else "") + detail
    parsed = bool(asserted or finished or re.search(r"record SimulationResult|Error:", out))
    return cmd, r, ok, detail, parsed, extra

CHECKERS = {"dafny": check_dafny, "isabelle": check_isabelle, "fdr": check_fdr, "gradle": check_gradle,
            "modelica": check_modelica}

ENV_FAILURE = re.compile(r"A valid license is required|Cannot connect to the Docker daemon|"
                         r"permission denied while trying to connect to the docker|"
                         r"Unable to find image|No such image|pull access denied|"
                         r"Could not (start|create) .*daemon|Operation not permitted", re.I)

PROCESS_FAILURE = re.compile(
    r"^\s*(?:\*\*\*\s*)?Killed(?:\s|$)|"
    r"^.*:\s*line\s+\d+:\s*\d+\s+Killed(?:\s|$)|"
    r"\bout of memory\b|\bcannot allocate memory\b|\bstd::bad_alloc\b|"
    r"\bjava\.lang\.OutOfMemoryError\b|\bheap space exhausted\b",
    re.I | re.M)

def classify_verdict(result, ok, parsed):
    """Separate checker interruption from a verdict on the checked artefact."""
    if result["timedOut"]:
        return "TIMEOUT"
    status = result["exit"]
    if status is None:
        return "NOT_ASSESSED"
    # subprocess uses negative signal numbers; a shell/container uses 128 + signal.
    stopped = status < 0 or status in (128 + signal.SIGKILL, 128 + signal.SIGTERM,
                                       128 + signal.SIGINT, 128 + signal.SIGABRT,
                                       128 + signal.SIGSEGV)
    if stopped or (not ok and PROCESS_FAILURE.search(result["output"])):
        return "NOT_ASSESSED"
    if ok:
        return "PASS"
    if not parsed and ENV_FAILURE.search(result["output"]):
        return "NOT_ASSESSED"
    return "FAIL"

def dispatch(args, link, tag, edits=None):
    spec = RUNNERS[link["targetKind"]]
    wd = os.path.join(args.out, "work", "%s__%s" % (tag, link["solution"]))
    if os.path.exists(wd):
        shutil.rmtree(wd)
    stage(spec, wd)
    changed = apply_edits(wd, edits) if edits else False
    extra = {}
    try:
        out = CHECKERS[spec["runner"]](args, wd, link)
        cmd, r, ok, detail, parsed = out[:5]
        extra = out[5] if len(out) > 5 else {}
    except FileNotFoundError as e:
        cmd, r, ok, detail, parsed = [str(e.filename)], {"exit": None, "output": str(e), "timedOut": False, "seconds": 0}, False, "checker not found", False
    except ValueError as e:      # a simulation binding could not be applied: the thread and the files disagree
        cmd, r, ok, detail, parsed = ["(bindings)"], {"exit": 1, "output": str(e), "timedOut": False, "seconds": 0}, False, str(e), True
    verdict = classify_verdict(r, ok, parsed)
    log = os.path.join(args.out, "logs", "%s__%s__%s.log" % (tag, link["solution"], spec["runner"]))
    with open(log, "w") as fh:
        fh.write("# %s %s -> %s via %s\n# command: %s\n# exit: %s  timedOut: %s  seconds: %s\n\n%s\n" % (
            tag, link["solution"], link["target"], spec["runner"], " ".join(cmd), r["exit"], r["timedOut"], r["seconds"], r["output"]))
    if os.path.exists(wd) and not args.keep_work:
        shutil.rmtree(wd, ignore_errors=True)
    res = {"tag": tag, "solution": link["solution"], "link": link["link"], "target": link["target"],
           "runner": spec["runner"], "command": " ".join(cmd), "exit": r["exit"], "verdict": verdict,
           "detail": detail, "seconds": r["seconds"], "artefactChanged": changed, "log": os.path.relpath(log, args.out)}
    res.update(extra)
    return res


# ------------------------------------------------------------------ conditions
def executable(links, only):
    ex = [l for l in links if l["runner"]]
    return [l for l in ex if not only or l["solution"] in only]

def run_baseline(args, links, res):
    for l in executable(links, args.only):
        r = dispatch(args, l, "baseline")
        res["baseline"].append(r); say("[baseline] %-5s %-8s %-12s (%6.2fs) %s" % (r["solution"], r["runner"], r["verdict"], r["seconds"], r["detail"]))

def run_mutants(args, links, res):
    by_sol = {l["solution"]: l for l in executable(links, args.only)}
    with open(args.mutants) as fh:
        mutants = json.load(fh)
    for m in mutants:
        l = by_sol.get(m["solution"])
        if not l:
            continue
        try:
            r = dispatch(args, l, "mutant-" + m["id"], m["edits"])
        except ValueError as e:
            r = {"tag": "mutant-" + m["id"], "solution": m["solution"], "runner": l["runner"], "verdict": "MUTANT_INVALID", "detail": str(e), "seconds": 0}
        r.update({"mutant": m["id"], "class": m["class"], "operator": m.get("operator"), "description": m.get("description")})
        v = r["verdict"]
        if v in ("NOT_ASSESSED", "MUTANT_INVALID"):
            r["outcome"] = "not assessed"
        elif m["class"] == "fault":
            r["outcome"] = {"FAIL": "detected", "PASS": "survived", "TIMEOUT": "timed out (not re-established)"}[v]
        else:
            r["outcome"] = {"PASS": "control passed", "FAIL": "false alarm", "TIMEOUT": "control timed out"}[v]
        res["mutants"].append(r); say("[mutant %-4s] %-7s %-8s %-12s => %-30s (%6.2fs) %s" % (m["id"], m["class"], r["runner"], v, r["outcome"], r["seconds"], r["detail"]))

def run_stale(args, ns, links, res):
    node, adj = ns_impact.index(ns)
    for sc in json.load(open(args.stale)):
        depth_of = {}
        for start in sc["traceEndpoints"]:
            depth_of[start] = 0
            for d, v, _ in ns_impact.impact(node, adj, start, args.stale_depth):
                depth_of[v] = min(d, depth_of.get(v, d))
        flagged = sorted({(node[i]["label"], d) for i, d in depth_of.items() if node.get(i, {}).get("kind") == "Solution"},
                         key=lambda x: (x[1], x[0]))
        entry = {"scenario": sc["id"], "change": sc.get("change"), "startNodes": sc["traceEndpoints"],
                 "traversal": "namespace/impact.py closure" + (" depth<=%d" % args.stale_depth if args.stale_depth else " (unbounded)"),
                 "flaggedSolutions": [{"solution": s, "depth": d} for s, d in flagged], "redispatch": []}
        fl = {s for s, _ in flagged}
        for l in executable(links, args.only):
            if l["solution"] not in fl:
                continue
            r = dispatch(args, l, "stale-" + sc["id"], sc.get("artefactEdits", {}).get(l["solution"]))
            entry["redispatch"].append(r)
            say("[stale %s] %-5s depth %d changed=%-5s %-8s (%6.2fs) %s" % (sc["id"], l["solution"], depth_of[l["solutionId"]], r["artefactChanged"], r["verdict"], r["seconds"], r["detail"]))
        res["stale"].append(entry)

def run_latency(args, ns, res):
    t0 = time.perf_counter(); node, adj = ns_impact.index(ns); t_index = (time.perf_counter() - t0) * 1e3
    starts = sorted(node)
    out = {}
    for depth in (None, 5):
        ms, cones = [], []
        for rep in range(args.reps):
            for s in starts:
                t = time.perf_counter(); c = ns_impact.impact(node, adj, s, depth); ms.append((time.perf_counter() - t) * 1e3)
                if rep == 0:
                    cones.append(len(c))
        ms.sort()
        out["unbounded" if depth is None else "depth%d" % depth] = {
            "n": len(ms), "starts": len(starts), "reps": args.reps,
            "median_ms": round(statistics.median(ms), 4), "p95_ms": round(ms[int(round(0.95 * (len(ms) - 1)))], 4),
            "max_ms": round(ms[-1], 4), "cone_median": statistics.median(cones), "cone_max": max(cones)}
    out["index_build_ms"] = round(t_index, 3)
    out["graph"] = {"nodes": len(ns["nodes"]), "edges": len(ns["edges"])}
    out["host"] = {"python": platform.python_version(), "platform": platform.platform(),
                   "machine": platform.machine(), "cpus": os.cpu_count()}
    res["latency"] = out
    say(json.dumps(out, indent=1))

def dry_run(args, links):
    problems, n = [], 0
    specs = {l["solution"]: RUNNERS[l["targetKind"]] for l in links if l["runner"]}
    sets = [("mutant " + m["id"], m["solution"], m["edits"]) for m in json.load(open(args.mutants))]
    sets += [("stale %s/%s" % (s["id"], sol), sol, e) for s in json.load(open(args.stale)) for sol, e in s.get("artefactEdits", {}).items()]
    for name, sol, edits in sets:
        with tempfile.TemporaryDirectory() as td:
            wd = os.path.join(td, "w"); stage(specs[sol], wd)
            try:
                if not apply_edits(wd, edits):
                    problems.append("%s: edit made no change" % name)
            except ValueError as e:
                problems.append("%s: %s" % (name, e))
        n += 1
    say("dry-run: %d edit sets checked, %d problems" % (n, len(problems)))
    for p in problems:
        say("  " + p)
    return problems


# ------------------------------------------------------------------ versions, report
def versions(args):
    def first(cmd, want=r"\d+\.\d+"):
        """First output line that carries a version number (gradle prints a banner, refines a header)."""
        try:
            r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
            lines = [ANSI.sub("", x).strip() for x in (r.stdout + r.stderr).splitlines() if x.strip()]
            hit = [x for x in lines if re.search(want, x)]
            return (hit or lines or [None])[0] and (hit or lines)[0][:120]
        except Exception as e:  # noqa: BLE001
            return "unavailable (%s)" % type(e).__name__
    v = {"python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine(),
         "cpus": os.cpu_count(), "dafny": first([args.dafny, "--version"]), "gradle": first([args.gradle, "--version"], r"^Gradle \d"),
         "java": first([os.path.join(os.environ["JAVA_HOME"], "bin", "java") if os.environ.get("JAVA_HOME") else "java", "-version"])}
    v["fdr"] = first([args.fdr, "--version"]) if os.path.exists(args.fdr) or shutil.which(args.fdr) else "unavailable"
    v["isabelle"] = ("docker image %s" % args.isabelle_docker) if args.isabelle_docker else first([args.isabelle, "version"])
    v["openmodelica"] = openmodelica_version(args)
    return v

def openmodelica_version(args):
    """Image tag, content digest and omc --version of the OpenModelica container, or why it is unavailable."""
    if not args.modelica_docker:
        return {"available": False, "reason": "no --modelica-docker image configured"}
    info = {"image": args.modelica_docker}
    try:
        r = subprocess.run(["docker", "image", "inspect", "--format", "{{json .RepoDigests}} {{.Id}} {{.Architecture}}", args.modelica_docker],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            info.update(available=False, reason=(r.stderr or r.stdout).strip()[:200]); return info
        digests, image_id, arch = r.stdout.strip().rsplit(" ", 2)
        info.update(repoDigests=json.loads(digests), imageId=image_id, architecture=arch)
        cmd = ["docker", "run", "--rm", "--pull", "never"] + (["--platform", args.modelica_platform] if args.modelica_platform else []) + [args.modelica_docker, "omc", "--version"]
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
        info.update(available=r.returncode == 0, omc=(r.stdout or r.stderr).strip().splitlines()[-1][:120] if (r.stdout or r.stderr).strip() else None)
    except Exception as e:  # noqa: BLE001
        info.update(available=False, reason="%s: %s" % (type(e).__name__, e))
    return info

def markdown(res):
    L = ["# Re-verification results (%s)" % res["generatedAt"], "", "Condition: `%s`  Repository: `%s`" % (res["condition"], res["repo"]), ""]
    if res["baseline"]:
        L += ["## Baseline", "| Solution | Evidence | Checker | Verdict | s | Detail |", "|---|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s | %s |" % (r["solution"], r["target"], r["runner"], r["verdict"], r["seconds"], r["detail"]) for r in res["baseline"]]
    if res["mutants"]:
        L += ["", "## Seeded mutants", "| Mutant | Class | Checker | Verdict | Outcome | s | Description |", "|---|---|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s | %s | %s |" % (r["mutant"], r["class"], r["runner"], r["verdict"], r["outcome"], r["seconds"], r.get("description", "")) for r in res["mutants"]]
        L += ["", "| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |", "|---|---|---|---|---|---|"]
        for ck in sorted({r["runner"] for r in res["mutants"]}) + ["Total"]:
            rs = res["mutants"] if ck == "Total" else [r for r in res["mutants"] if r["runner"] == ck]
            f = [r for r in rs if r["class"] == "fault"]; c = [r for r in rs if r["class"] == "control"]
            L.append("| %s | %d/%d | %d | %d | %d | %d/%d |" % (ck, sum(r["outcome"] == "detected" for r in f), len(f),
                     sum(r["outcome"] == "survived" for r in f), sum(r["verdict"] == "TIMEOUT" for r in f),
                     sum(r["outcome"] == "not assessed" for r in f),
                     sum(r["outcome"] == "control passed" for r in c), len(c)))
    for sc in res["stale"]:
        L += ["", "## Stale evidence: %s" % sc["scenario"], "Change: %s  " % sc["change"],
              "Flagged by %s: %s" % (sc["traversal"], ", ".join("%s@%d" % (f["solution"], f["depth"]) for f in sc["flaggedSolutions"])), "",
              "| Solution | Checker | Artefact changed | Verdict | Detail |", "|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s |" % (r["solution"], r["runner"], r["artefactChanged"], r["verdict"], r["detail"]) for r in sc["redispatch"]]
    if res.get("latency"):
        L += ["", "## Impact-traversal latency (namespace/impact.py)", "```", json.dumps(res["latency"], indent=1), "```"]
    return "\n".join(L) + "\n"

def say(s):
    print(s, flush=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=["baseline", "mutants", "stale", "all", "latency", "dry-run", "links"])
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "reverify-out"))
    ap.add_argument("--namespace", default=os.path.join(REPO, "namespace", "ads-namespace.json"))
    ap.add_argument("--mutants", default=os.path.join(HERE, "c3", "mutants.json"))
    ap.add_argument("--stale", default=os.path.join(HERE, "c3", "stale.json"))
    ap.add_argument("--only", type=lambda s: set(s.split(",")), help="restrict to Solutions, e.g. Sn8,Sn9")
    ap.add_argument("--stale-depth", type=int, default=None, help="bound the stale-evidence closure")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--dafny", default=os.environ.get("DAFNY_PATH", "dafny"))
    ap.add_argument("--fdr", default=os.environ.get("FDR_PATH", "/Applications/FDR4.app/Contents/MacOS/refines" if sys.platform == "darwin" else "refines"))
    ap.add_argument("--gradle", default=os.environ.get("GRADLE_PATH", "gradle"))
    ap.add_argument("--isabelle", default=os.environ.get("ISABELLE_PATH", "isabelle"))
    ap.add_argument("--isabelle-docker", metavar="IMAGE", help="run Isabelle in this amd64 image with --isabelle-home mounted")
    ap.add_argument("--isabelle-home", default=os.path.expanduser("~/Isabelle2023-CyPhyAssure"))
    ap.add_argument("--isabelle-memory", default="6g")
    ap.add_argument("--modelica-docker", metavar="IMAGE", default=os.environ.get("MODELICA_DOCKER"),
                    help="OpenModelica image for the modelica runner, e.g. openmodelica/openmodelica:v1.26.1-minimal")
    ap.add_argument("--modelica-platform", default=os.environ.get("MODELICA_PLATFORM", ""),
                    help="docker --platform for the OpenModelica image (e.g. linux/amd64 on an arm64 host)")
    ap.add_argument("--no-modelica-diagnose", dest="modelica_diagnose", action="store_false",
                    help="skip the diagnostic minimum-DF run after an assertion failure")
    for t, d in (("dafny", 120), ("isabelle", 1800), ("fdr", 600), ("gradle", 900), ("modelica", 600)):
        ap.add_argument("--timeout-" + t, type=int, default=d)
    ap.add_argument("--keep-work", action="store_true", help="keep the scratch artefact copies")
    args = ap.parse_args()
    args.out = os.path.abspath(os.path.expanduser(args.out))
    ns = ns_impact.load(args.namespace)
    args.ns = ns
    links = evidence_links(ns)
    if args.condition == "links":
        for l in links:
            say("%-5s %-26s -> %-40s %s" % (l["solution"], l["link"], l["target"], l["runner"] or "(record, no checker)"))
        return
    if args.condition == "dry-run":
        sys.exit(1 if dry_run(args, links) else 0)
    os.makedirs(os.path.join(args.out, "logs"), exist_ok=True)
    res = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "condition": args.condition, "repo": REPO,
           "namespace": os.path.relpath(args.namespace, REPO), "evidenceLinks": links, "baseline": [], "mutants": [], "stale": []}
    if args.condition != "latency":
        res["toolVersions"] = versions(args)
    if args.condition in ("baseline", "all"):
        run_baseline(args, links, res)
    if args.condition in ("mutants", "all"):
        run_mutants(args, links, res)
    if args.condition in ("stale", "all"):
        run_stale(args, ns, links, res)
    if args.condition in ("latency", "all"):
        run_latency(args, ns, res)
    with open(os.path.join(args.out, "reverify_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    with open(os.path.join(args.out, "reverify_results.md"), "w") as fh:
        fh.write(markdown(res))
    say("wrote %s" % os.path.join(args.out, "reverify_results.{json,md}"))

if __name__ == "__main__":
    main()
