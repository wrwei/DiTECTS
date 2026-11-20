#!/usr/bin/env python3
"""Change scenarios for static evidence: detect what changed and flag the evidence it affects.

Static evidence (FMEDA rows, fault-tree events, design elements) cannot be re-run, so a change to
it is found by comparison instead. For each scenario in tools/c3/static.json the tool copies the
deposited models to a temporary directory, applies the scenario's edits there (the repository is
not modified), and compares every identified element record in the model files with the
deposited version by content hash. From each changed element it runs namespace/impact.py over the
deposited impact graph and reports the Solutions reached, their depth, whether they cite the
element, and which of their evidence has a configured runner. It also reports whether any
executable artefact changed, which decides whether re-running a checker could reveal the change.

The platform does the same with a stored baseline that fingerprints each thread element as
sha256(name|updatedAt); this tool fingerprints the deposited element records, so it needs no
database.

  python3 tools/change_detect.py --out results/change_static
"""
import argparse, collections, hashlib, importlib.util, json, os, re, shutil, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = "models"
# Overlay and derived evidence map are not models.
SKIP = {"models/traceability/completion.json", "models/safety-case/evidence-resolution.json"}
EXECUTABLE_DIRS = ("formal", "implementation", "simulation", "models/sysml")
RUNNER_KINDS = {"Dafny Model", "Isabelle Model", "FDR Model", "Java Model", "ModelicaModel"}


def elements(doc):
    """Every identified record in a model document, keyed by its identifier."""
    out = {}

    def walk(o):
        if isinstance(o, dict):
            # "_id" last: the safety-case records carry no other identifier
            i = o.get("@id") or o.get("elementId") or o.get("gid") or o.get("_id")
            if i and len(o) > 2:
                out.setdefault(str(i), o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(doc)
    return out


def digest(rec):
    return hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()


def model_files(root):
    out = []
    for d, _, fs in os.walk(os.path.join(root, MODEL_DIR)):
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
            if f.endswith(".json") and rel not in SKIP:
                out.append(rel)
    return sorted(out)


def element_changes(base_root, new_root):
    out = []
    for f in model_files(new_root):
        ea = elements(json.load(open(os.path.join(new_root, f))))
        eb = elements(json.load(open(os.path.join(base_root, f)))) if os.path.exists(os.path.join(base_root, f)) else {}
        for i in sorted(set(ea) | set(eb)):
            if i not in eb:
                out.append({"file": f, "id": i, "change": "added"})
            elif i not in ea:
                out.append({"file": f, "id": i, "change": "removed"})
            elif digest(ea[i]) != digest(eb[i]):
                keys = sorted(set(ea[i]) | set(eb[i]))
                diff = {k: {"from": eb[i].get(k), "to": ea[i].get(k)} for k in keys if ea[i].get(k) != eb[i].get(k)}
                out.append({"file": f, "id": i, "change": "changed", "fields": diff})
    return out


def apply_edits(root, edits):
    """Same rules as tools/reverify.py: regex pattern, literal replacement, expected match count."""
    touched = set()
    for e in edits:
        p = os.path.join(root, e["file"])
        text = open(p, encoding="utf-8", newline="").read()
        rx = re.compile(e["pattern"])
        n = len(rx.findall(text))
        if e.get("expectCount") and n != e["expectCount"]:
            raise ValueError("pattern in %s matched %dx, expected %d" % (e["file"], n, e["expectCount"]))
        if n == 0:
            raise ValueError("pattern in %s matched nothing" % e["file"])
        open(p, "w", encoding="utf-8", newline="").write(rx.sub(lambda m: e["replace"], text))
        touched.add(e["file"])
    return touched


def run_scenario(sc, node, adj, cites, label, by_uuid, impact):
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(os.path.join(REPO, MODEL_DIR), os.path.join(td, MODEL_DIR))
        touched = apply_edits(td, sc["edits"])
        changes = element_changes(REPO, td)
    executable = sorted(f for f in touched if f.startswith(EXECUTABLE_DIRS))
    flagged = []
    for c in changes:
        start = by_uuid.get(c["id"]) or (c["id"] if c["id"] in node else None)
        c["element"] = label(start) if start else None
        if not start or c["change"] == "removed":
            continue
        for d, i, _ in impact.impact(node, adj, start, None):
            if node[i]["kind"] in ("Solution", "Goal"):
                runner = sorted(label(t) for t in cites[i] if node[t]["kind"] in RUNNER_KINDS)
                flagged.append({"from": c["element"], "element": label(i), "kind": node[i]["kind"], "depth": d,
                                "cites": start in cites[i], "runnerEvidence": runner})
    flagged.sort(key=lambda f: (f["depth"], f["kind"], f["element"]))
    return {"scenario": sc["id"], "change": sc.get("change"), "filesEdited": sorted(touched),
            "executableArtefactsChanged": executable, "elementChanges": changes, "flagged": flagged}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarios", default=os.path.join(REPO, "tools", "c3", "static.json"))
    ap.add_argument("--out", help="write <out>.json and <out>.md")
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("impact", os.path.join(REPO, "namespace", "impact.py"))
    impact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(impact)
    ns = json.load(open(os.path.join(REPO, "namespace", "ads-namespace.json")))
    node, adj = impact.index(ns)
    by_uuid = {n.get("uuid"): n["id"] for n in ns["nodes"] if n.get("uuid")}
    label = lambda i: node[i].get("shortName") or node[i]["label"]
    cites = collections.defaultdict(set)
    for e in ns["edges"]:
        if e["kind"] == "traceability" and node[e["source"]]["kind"] == "Solution":
            cites[e["source"]].add(e["target"])

    results = [run_scenario(sc, node, adj, cites, label, by_uuid, impact) for sc in json.load(open(args.scenarios))]

    L = ["# Static-evidence change scenarios", "",
         "Generated by `python3 tools/change_detect.py`. Each scenario is applied to a temporary copy of the",
         "deposited models and compared with them; the repository is not modified.", ""]
    for r in results:
        L += ["## %s" % r["scenario"], "", r["change"] or "", "", "Changed elements:", ""]
        for c in r["elementChanges"]:
            L.append("- %s `%s` in `%s`: %s" % (c["element"] or c["id"], c["id"], c["file"], c["change"]))
            for k, v in (c.get("fields") or {}).items():
                L.append("  - `%s`: %s -> %s" % (k, json.dumps(v["from"]), json.dumps(v["to"])))
        L += ["", "Executable artefacts changed: %s" % (", ".join(r["executableArtefactsChanged"]) or "none"), "",
              "| Depth | Kind | Element | Cites the changed element | Evidence with a runner |", "|---|---|---|---|---|"]
        L += ["| %d | %s | %s | %s | %s |" % (f["depth"], f["kind"], f["element"], "yes" if f["cites"] else "",
                                              ", ".join(f["runnerEvidence"]) or ("none" if f["kind"] == "Solution" else ""))
              for f in r["flagged"]]
        L.append("")
    text = "\n".join(L)
    if args.out:
        json.dump(results, open(args.out + ".json", "w"), indent=1)
        open(args.out + ".md", "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
