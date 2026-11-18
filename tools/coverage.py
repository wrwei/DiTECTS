#!/usr/bin/env python3
"""Coverage of the ADS thread: does it connect everything a safety argument needs?

Standard library only. Reads namespace/ads-namespace.json (or, with --export, derives the namespace
in memory from a project export, optionally without the completion overlay), the SysML OMG JSON
(requirements and satisfy relationships) and the FMEDA JSON (safety-related rows).

Checks
  R1  every requirement is satisfied by a design element, or recorded out of scope by an Assumption
  R2  every requirement is argued by a Goal (or an Assumption)
  R3  every SysML satisfy relationship in the design model is a trace link in the thread
  S1  every Goal is developed (SupportedBy) and every Solution cites evidence
  F1  every safety-related FMEDA row is cited by a Solution
  F2  every fault-tree basic event is cited by a Solution and joined to its FMEDA row
  F3  every safety-related FMEDA row has a fault-tree event
  F4  every FMEDA row has a typed link to the design part it analyses (the part its itemElement names)
  F5  every requirement identifier cited in failure-analysis text (FMEDA row fields, fault-tree element
      names and descriptions) is backed by a typed link from the citing element to that requirement;
      the fault tree's own description is attributed to its top event
  C1  the impact graph is one connected component
  C2  every telemetry binding reaches the safety case
  E1  the design part each executable artefact models links to it directly
  E2  every design element (or simulation model) a Solution's text names is backed by an evidential
      link from that Solution to it; the terms and the elements they denote are in SOLUTION_TERMS
  B1  every simulation binding (sim-binding edge or binds link) resolves both ends -- a Modelica parameter owned by a Modelica
      model (parameter-of) and a SysML attribute -- and joins equal values: in the thread (the two nodes'
      `value`) and in the repository files (the SysML text and the Modelica source)

  python3 tools/coverage.py                                   # the committed thread
  python3 tools/coverage.py --export <dir> --no-completion    # the export-only thread
  python3 tools/coverage.py --export <dir> --no-completion --drop-kinds attribute-of,fta-fmeda
                                                              # ... as derived before the structural edges
  python3 tools/coverage.py --export <dir> --completion <file>  # another completion overlay
  python3 tools/coverage.py --json out.json
"""
import argparse, collections, json, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "namespace")); sys.path.insert(0, HERE)
import impact as I  # noqa: E402
import sim_bindings as SB  # noqa: E402

# E2: terms in a Solution's text and the elements they denote (labels in the identity space). Only terms that
# name or unambiguously denote an element are listed. Deliberately absent: "controller" (the subject of G8's claim,
# not evidence for it; its verification artefacts link to it directly), "one live bed" / "dryer alternation" /
# "backup" in Sn7, Sn8 and Sn10 (properties of the controller's logic, not of the beds or the UPS).
SOLUTION_TERMS = [
    (r"dual-bed", ["dryerA", "dryerB"]),                       # the two molecular-sieve beds
    (r"changeover", ["changeoverValves"]),                     # satisfy changeoverContinuity by changeoverValves
    (r"\bUPS\b", ["backupSupply"]),                            # part def UPSBackupSupply
    (r"\bDF design", ["ads"]),                                 # DF of the ADS train; satisfy detritiationCapacity by ads
    (r"recombiner", ["recombiner"]),
    (r"stack[- ]monitor", ["stackMonitor"]),
    (r"calibration", ["dewpointMonitor"]),                     # the only design element with a calibration attribute
    (r"regeneration[- ]path", ["dryerARegenReturn", "interfaceEdge"]),  # dryerA/dryerB regenOut -> condenser.regenReturn
    (r"blower", ["blower"]),
    (r"FMU transient", ["ADS Changeover Transient_Modelica"]),  # the Modelica changeover transient (simulation evidence)
]

def omg(path):
    d = json.load(open(path, encoding="utf-8"))
    return [e.get("payload", e) for e in (d["elements"] if isinstance(d, dict) and "elements" in d else d)]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--namespace", default=os.path.join(REPO, "namespace", "ads-namespace.json"))
    ap.add_argument("--export", help="derive the namespace in memory from this project export")
    ap.add_argument("--no-completion", action="store_true", help="with --export: without the completion overlay")
    ap.add_argument("--completion", default=os.path.join(REPO, "models", "traceability", "completion.json"),
                    help="with --export: the completion overlay to apply (default: the committed one)")
    ap.add_argument("--drop-kinds", default="", help="comma-separated edge kinds to ignore, e.g. attribute-of,fta-fmeda")
    ap.add_argument("--json", help="write the results here")
    a = ap.parse_args()
    if a.export:
        import derive_from_export as D
        x = D.Export(a.export)
        if not a.no_completion and os.path.exists(a.completion):
            x.apply_completion(json.load(open(a.completion, encoding="utf-8")))
        ns = json.loads(json.dumps(D.derive_namespace(x)))
        fta = json.loads(json.dumps(D.derive_fta(x)))
    else:
        ns = I.load(a.namespace)
        fta = json.load(open(os.path.join(REPO, "models", "fta", "ads-fta.json"), encoding="utf-8"))
    drop = set(filter(None, a.drop_kinds.split(",")))
    if drop:
        ns["edges"] = [e for e in ns["edges"] if e["kind"] not in drop]
    node, adj = I.index(ns)
    out_, in_ = collections.defaultdict(list), collections.defaultdict(list)
    for e in ns["edges"]:
        out_[e["source"]].append(e); in_[e["target"]].append(e)
    lab = lambda i: node[i].get("shortName") or node[i]["label"]
    kind = lambda k: [n for n in ns["nodes"] if n["kind"] == k]
    trace = lambda e: e["kind"] == "traceability"

    req = omg(os.path.join(REPO, "models", "sysml", "omg", "01-requirements.omg.json"))
    des = omg(os.path.join(REPO, "models", "sysml", "omg", "02-design.omg.json"))
    allE = {e["@id"]: e for e in req + des}
    reqs = [e for e in req if e["@type"] == "RequirementUsage"]
    by_uuid = {n.get("uuid"): n for n in ns["nodes"] if n.get("uuid")}
    res = collections.OrderedDict()

    r1, r2 = [], []
    for r in reqs:
        n = by_uuid.get(r["@id"]); name = r.get("declaredShortName") or r["declaredName"]
        src = [node[e["source"]] for e in in_[n["id"]] if trace(e)] if n else []
        if not any(s["concern"] == "design" or s["kind"] == "Assumption" for s in src): r1.append(name)
        if not any(s["kind"] in ("Goal", "Assumption") for s in src): r2.append(name)
    res["R1 requirements without design element or scope record"] = (r1, len(reqs))
    res["R2 requirements argued by no Goal or Assumption"] = (r2, len(reqs))

    def ref(v): return v.get("@id") if isinstance(v, dict) else v
    model_sat = {(allE.get(ref(s.get("satisfyingFeature")), {}).get("declaredName"),
                  allE.get(ref(s.get("satisfiedRequirement")), {}).get("declaredShortName"))
                 for s in des if s["@type"] == "SatisfyRequirementUsage"}
    # satisfy statements added to the SysML text by the completion overlay (not yet in the platform's OMG export)
    if not (a.export and a.no_completion) and os.path.exists(a.completion):
        model_sat |= {(s["satisfyingFeature"], s["satisfiedRequirement"])
                      for s in json.load(open(a.completion, encoding="utf-8")).get("sysml", {}).get("satisfy", [])}
    thread_sat = {(node[e["source"]]["label"], node[e["target"]].get("shortName")) for e in ns["edges"]
                  if trace(e) and node[e["source"]]["concern"] == "design" and node[e["target"]]["concern"] == "requirements"}
    res["R3 SysML satisfy relationships missing from the thread"] = (sorted("%s->%s" % p for p in model_sat - thread_sat), len(model_sat))
    res["R3b thread satisfactions with no SysML satisfy (add to the model)"] = (sorted("%s->%s" % p for p in thread_sat - model_sat), len(thread_sat))

    res["S1 Goals not developed"] = ([g["label"] for g in kind("Goal") if not any(e["kind"] == "gsn-SupportedBy" for e in out_[g["id"]])], len(kind("Goal")))
    res["S1b Solutions citing no evidence"] = ([s["label"] for s in kind("Solution") if not any(trace(e) for e in out_[s["id"]])], len(kind("Solution")))

    fm = json.load(open(os.path.join(REPO, "models", "fmeda", "ads-fmeda.json"), encoding="utf-8"))["rows"]
    rows = {n["label"]: n for n in kind("FMEARow")}
    cited = lambda i: any(trace(e) and node[e["source"]]["kind"] == "Solution" for e in in_[i])
    safety = [r for r in fm if r.get("safetyRelated")]
    rowid = lambda r: rows["FMEDA row %d" % r["rowNumber"]]["id"]
    res["F1 safety-related FMEDA rows cited by no Solution"] = (["row %d" % r["rowNumber"] for r in safety if not cited(rowid(r))], len(safety))
    be = kind("FTABasicEvent")
    res["F2 basic events cited by no Solution"] = ([lab(b["id"]) for b in be if not cited(b["id"])], len(be))
    res["F2b basic events not joined to their FMEDA row"] = ([lab(b["id"]) for b in be if not any(e["kind"] == "fta-fmeda" for e in out_[b["id"]])], len(be))
    res["F3 safety-related FMEDA rows with no fault-tree event"] = (["row %d" % r["rowNumber"] for r in safety if not any(e["kind"] == "fta-fmeda" for e in in_[rowid(r)])], len(safety))

    # F4: a typed link from the row must land on the design element its itemElement names.
    f4 = []
    for r in fm:
        n = rows.get("FMEDA row %d" % r["rowNumber"])
        want = (r.get("itemElement") or {}).get("@id")
        hit = n and [e for e in out_[n["id"]] if e["kind"] == "traceability" and node[e["target"]]["concern"] == "design"
                     and node[e["target"]].get("uuid") == want]
        if not hit:
            f4.append("row %d" % r["rowNumber"])
    res["F4 FMEDA rows with no typed link to their design part"] = (f4, len(fm))

    # F5: every requirement identifier in failure-analysis text is a typed link from the citing element.
    REQ_ID = re.compile(r"\bREQ-[A-Z]+-\d+\b")
    def strings(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for k, w in v.items():
                if k != "traces":
                    yield from strings(w)
        elif isinstance(v, list):
            for w in v:
                yield from strings(w)
    req_node = {n["shortName"]: n["id"] for n in ns["nodes"] if n["concern"] == "requirements" and n.get("shortName")}
    by_code = {n["uuid"]: n for n in ns["nodes"] if n.get("notation") == "FTA"}
    citations = []  # (citing node id, citing label, requirement short name)
    for r in fm:
        n = rows.get("FMEDA row %d" % r["rowNumber"])
        for q in sorted({m for t in strings(r) for m in REQ_ID.findall(t)}):
            citations.append((n and n["id"], "FMEDA row %d" % r["rowNumber"], q))
    top = next((e.get("topEvent", {}).get("@id") for e in fta["elements"] if e["@type"] == "FaultTree"), None)
    fta_text = collections.defaultdict(set)
    for e in fta["elements"]:
        code = top if e["@type"] == "FaultTree" else e["@id"]
        fta_text[code] |= {m for t in strings({k: v for k, v in e.items() if k not in ("inputs", "outputEvent", "topEvent")})
                           for m in REQ_ID.findall(t)}
    fta_text[top] |= set(REQ_ID.findall(fta.get("description") or ""))
    for code in sorted(fta_text):
        for q in sorted(fta_text[code]):
            citations.append((by_code.get(code, {}).get("id"), code, q))
    f5 = ["%s cites %s" % (lbl, q) for nid, lbl, q in citations
          if not (nid and q in req_node and any(trace(e) and e["target"] == req_node[q] for e in out_[nid]))]
    res["F5 requirement IDs in failure-analysis text with no typed link"] = (f5, len(citations))

    seen, comps = set(), []
    for s in node:
        if s not in seen:
            c = {s} | {v for _, v, _ in I.impact(node, adj, s)}; seen |= c; comps.append(sorted(lab(i) for i in c))
    comps.sort(key=len, reverse=True)
    res["C1 elements outside the main component"] = ([y for c in comps[1:] for y in c], len(node))
    tb = kind("TwinBinding")
    res["C2 telemetry bindings that reach no Solution"] = ([b["label"] for b in tb if not any(node[v]["kind"] == "Solution" for _, v, _ in I.impact(node, adj, b["id"]))], len(tb))
    ev = [n for n in ns["nodes"] if n["kind"] in ("Dafny Model", "Isabelle Model", "FDR Model", "Java Model")]
    res["E1 executable artefacts with no direct design link"] = ([n["label"] for n in ev if not any(trace(e) and node[e["source"]]["concern"] == "design" for e in in_[n["id"]])], len(ev))

    by_label = collections.defaultdict(list)
    for n in ns["nodes"]:
        by_label[n["label"]].append(n["id"])
    e2, e2n = [], 0
    for sn in kind("Solution"):
        for pat, labels in SOLUTION_TERMS:
            if re.search(pat, sn.get("text") or "", re.I):
                for t in labels:
                    e2n += 1
                    ids = by_label.get(t, [])
                    if len(ids) != 1 or not any(trace(e) and e["target"] == ids[0] for e in out_[sn["id"]]):
                        e2.append("%s -> %s" % (sn["label"], t))
    res["E2 elements named in Solution text with no evidential link"] = (e2, e2n)

    # B1: Degree 0 simulation bindings join equal values, in the thread and in the files.
    mo_text = {}
    mdir = os.path.join(REPO, "simulation", "modelica")
    for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        if fn.endswith(".mo"):
            t = open(os.path.join(mdir, fn), encoding="utf-8").read()
            m = re.search(r"^\s*model\s+(\w+)", t, re.M)
            if m:
                mo_text[m.group(1)] = t
    same = lambda u, v: u is not None and v is not None and abs(float(u) - float(v)) <= 1e-9 * max(1.0, abs(float(u)))
    b1, sb = [], SB.bindings(ns)
    for b in sb:
        p, at, mdl = b["parameter"], b["attribute"], b["model"]
        name = "%s <- %s" % (p and p["label"], at and at["label"])
        if not p or p.get("kind") != "ModelicaParameter" or not mdl or mdl.get("kind") != "ModelicaModel":
            b1.append(name + " (parameter end unresolved)"); continue
        if not at or at.get("kind") != "SAttributeUsage" or not at.get("qualifiedName"):
            b1.append(name + " (attribute end unresolved)"); continue
        if not same(p.get("value"), at.get("value")):
            b1.append("%s (thread values differ: %s vs %s)" % (name, p.get("value"), at.get("value"))); continue
        sv, _ = SB.sysml_value(REPO, at["qualifiedName"])
        decl = SB.modelica_parameter(mo_text.get(p["qualifiedName"].split(".")[0], ""), p["label"])
        if not same(sv, at.get("value")) or not decl or not same(decl[0], p.get("value")):
            b1.append("%s (files differ from the thread: SysML %s, Modelica %s)" % (name, sv, decl and decl[0]))
    res["B1 simulation bindings unresolved or joining unequal values"] = (b1, len(sb))

    summary = {"nodes": len(ns["nodes"]), "edges": len(ns["edges"]),
               "traceLinks": len({e["name"] for e in ns["edges"] if trace(e)}), "traceEdges": sum(1 for e in ns["edges"] if trace(e)),
               "components": len(comps)}
    print("thread: %(nodes)d elements, %(edges)d edges, %(traceLinks)d trace links (%(traceEdges)d endpoint pairs), %(components)d component(s)" % summary)
    gaps = 0
    for k, (bad, total) in res.items():
        informational = k.startswith("R3b")
        gaps += 0 if informational else len(bad)
        print("%s %-68s %s" % ("  " if not bad else ("i " if informational else "x "), k, ("%d/%d: %s" % (len(bad), total, ", ".join(bad))) if bad else "none (of %d)" % total))
    print("gaps: %d" % gaps)
    if a.json:
        json.dump({"summary": summary, "gaps": gaps, "checks": {k: {"failing": b, "of": t} for k, (b, t) in res.items()}}, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
