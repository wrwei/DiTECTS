#!/usr/bin/env python3
"""Fault examples for the thread itself: what the checks report when a link, a binding, a piece of
evidence or the model structure is wrong.

The change scenarios (tools/reverify.py, tools/change_detect.py) start from a correct thread and
change a model. These examples do the opposite: each one damages the thread or lets it fall out
of step with the models, and records which check, if any, reports the damage. Every example in
tools/c3/thread-faults.json is applied to a temporary copy of the repository; the repository is
not modified. Four checks then run on the copy:

  resolution  every endpoint of every edge is an element of the thread
              (the precondition of tools/coverage.py and tools/derive_from_export.py)
  coverage    the 17 rules of tools/coverage.py; skipped when resolution fails
  comparison  element records in the model files that differ from the deposited ones
              (tools/change_detect.py), with the Goals and Solutions reached from each
  freshness   evidence files whose content no longer matches the hash stored with their recorded
              verdict (results/reverify_bound_thread.json), with the Solutions that cite them

An example is "reported" when at least one check reports something, and "not reported" otherwise.
Each example states the outcome it expects; a run fails when an outcome differs. An example's
optional "note" records an observation made outside this tool and how it was obtained.

Edits (in an example's "edits" list)
  {"op": "remove-edge",   "edge": SEL}
  {"op": "retarget-edge", "edge": SEL, "end": "source"|"target", "to": ELEMENT | {"missingId": "..."}}
  {"op": "remove-node",   "node": ELEMENT}
  {"op": "reidentify-node", "node": ELEMENT, "id": "...", "uuid": "..."}
  {"op": "copy-node",     "node": ELEMENT, "id": "...", "uuid": "...", "label": "...", "text": "..."}
  {"op": "rename-node",   "node": ELEMENT, "label": "..."}
  {"op": "replace-text",  "file": "...", "pattern": REGEX, "replace": LITERAL, "expectCount": N}
SEL selects exactly one edge by any of "name", "kind", "source", "target". ELEMENT is an element's
short name or label, or "Kind:label" where the label alone is ambiguous.

  python3 tools/thread_faults.py --out results/thread_faults
"""
import argparse, collections, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMESPACE = "namespace/ads-namespace.json"
RECORD = "results/reverify_bound_thread.json"
STAGED = ("models", "namespace", "tools", "simulation", "formal", "implementation")
# Evidence directory -> kind of the executable model the thread registers for it.
EVIDENCE_KIND = {"formal/dafny/": "Dafny Model", "formal/isabelle/": "Isabelle Model", "formal/csp/": "FDR Model",
                 "implementation/java/": "Java Model", "simulation/modelica/": "ModelicaModel"}


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def name_of(n):
    return n.get("shortName") or n["label"]


class Thread:
    """The identity-space file of one copy, with the selectors the edits use."""

    def __init__(self, root):
        self.path = os.path.join(root, NAMESPACE)
        self.d = json.load(open(self.path, encoding="utf-8"))

    def save(self):
        json.dump(self.d, open(self.path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    def node(self, sel):
        kind, _, label = sel.rpartition(":")
        hits = [n for n in self.d["nodes"] if name_of(n) == label and (not kind or n["kind"] == kind)]
        if len(hits) != 1:
            raise ValueError("element %r selects %d elements" % (sel, len(hits)))
        return hits[0]

    def edge(self, sel):
        want = {k: (self.node(v)["id"] if k in ("source", "target") else v) for k, v in sel.items()}
        hits = [e for e in self.d["edges"] if all(e.get(k) == v for k, v in want.items())]
        if len(hits) != 1:
            raise ValueError("edge %r selects %d edges" % (sel, len(hits)))
        return hits[0]


def apply(root, edits, change_detect):
    th = Thread(root)
    for e in edits:
        op = e["op"]
        if op == "remove-edge":
            th.d["edges"].remove(th.edge(e["edge"]))
        elif op == "retarget-edge":
            to = e["to"]
            th.edge(e["edge"])[e["end"]] = to["missingId"] if isinstance(to, dict) else th.node(to)["id"]
        elif op == "remove-node":
            th.d["nodes"].remove(th.node(e["node"]))
        elif op == "reidentify-node":
            th.node(e["node"]).update(id=e["id"], uuid=e["uuid"])
        elif op == "copy-node":
            new = dict(th.node(e["node"]))
            new.pop("shortName", None)
            new.update(id=e["id"], uuid=e["uuid"], label=e["label"], text=e["text"])
            th.d["nodes"].append(new)
        elif op == "rename-node":
            th.node(e["node"])["label"] = e["label"]
        elif op == "replace-text":
            th.save()
            change_detect.apply_edits(root, [e])
            th = Thread(root)
        else:
            raise ValueError("unknown edit %r" % op)
    th.save()


def resolution(root):
    d = json.load(open(os.path.join(root, NAMESPACE), encoding="utf-8"))
    ids = {n["id"]: n for n in d["nodes"]}
    nm = lambda i: name_of(ids[i]) if i in ids else "?"
    return ["%s: %s -> %s" % (e.get("name") or e["kind"], nm(e["source"]), nm(e["target"]))
            for e in d["edges"] if e["source"] not in ids or e["target"] not in ids]


def coverage(root):
    out = os.path.join(root, "coverage.json")
    r = subprocess.run([sys.executable, os.path.join("tools", "coverage.py"), "--json", out], cwd=root, capture_output=True, text=True)
    if not os.path.exists(out):
        raise RuntimeError("coverage.py did not finish: " + (r.stderr.strip().splitlines() or ["?"])[-1])
    c = json.load(open(out))
    return {k.split(" ", 1)[0]: {"rule": k.split(" ", 1)[1], "failing": v["failing"]} for k, v in c["checks"].items() if v["failing"]}


def comparison(root, change_detect, impact, base):
    """Changed element records and, from each, the Goals and Solutions reached in the deposited graph."""
    node, adj = impact.index(base)
    by_uuid = {n["uuid"]: n["id"] for n in base["nodes"] if n.get("uuid")}
    out = []
    for c in change_detect.element_changes(REPO, root):
        start = by_uuid.get(c["id"]) or (c["id"] if c["id"] in node else None)
        reached = sorted(((d, node[i]["kind"], name_of(node[i])) for d, i, _ in impact.impact(node, adj, start, None)
                          if node[i]["kind"] in ("Goal", "Solution")), key=lambda x: (x[0], x[2])) if start else []
        out.append({"element": name_of(node[start]) if start else "record %s (not an element of the thread)" % c["id"][:8], "file": c["file"], "change": c["change"],
                    "fields": sorted(c.get("fields") or {}),
                    "goalsReached": sum(1 for r in reached if r[1] == "Goal"),
                    "solutionsReached": sum(1 for r in reached if r[1] == "Solution"),
                    "nearest": ["%s (depth %d)" % (r[2], r[0]) for r in reached[:4]]})
    return out


def freshness(root, base):
    """Evidence files that differ from the hash stored with their recorded verdict."""
    rec = json.load(open(os.path.join(REPO, RECORD), encoding="utf-8"))
    node = {n["id"]: n for n in base["nodes"]}
    citing = collections.defaultdict(set)
    for e in base["edges"]:
        if e["kind"] == "traceability" and node[e["source"]]["kind"] == "Solution":
            citing[node[e["target"]]["kind"]].add(name_of(node[e["source"]]))
    verdict = {b["solution"]: b["verdict"] for b in rec["baseline"]}
    out = []
    for rel, h in sorted(rec["sources"]["artefactSHA256"].items()):
        kind = next((k for p, k in EVIDENCE_KIND.items() if rel.startswith(p)), None)
        if not kind:
            continue
        cur = hashlib.sha256(open(os.path.join(root, rel), "rb").read()).hexdigest() if os.path.exists(os.path.join(root, rel)) else None
        if cur != h:
            out.append({"file": rel, "state": "missing" if cur is None else "differs from the recorded hash",
                        "solutions": ["%s (recorded %s)" % (s, verdict.get(s, "no verdict")) for s in sorted(citing[kind])]})
    return out


def run_example(ex, change_detect, impact, base):
    with tempfile.TemporaryDirectory() as td:
        for d in STAGED:
            shutil.copytree(os.path.join(REPO, d), os.path.join(td, d), ignore=shutil.ignore_patterns("__pycache__", "build", ".gradle"))
        apply(td, ex["edits"], change_detect)
        res = {"resolution": resolution(td)}
        res["coverage"] = coverage(td) if not res["resolution"] else None
        res["comparison"] = comparison(td, change_detect, impact, base)
        res["freshness"] = freshness(td, base)
    reporting = [k for k in ("resolution", "coverage", "comparison", "freshness") if res[k]]
    out = {"id": ex["id"], "group": ex["group"], "fault": ex["fault"], "expect": ex["expect"],
           "outcome": "reported" if reporting else "not reported", "reportedBy": reporting}
    if ex.get("note"):
        out["note"] = ex["note"]   # an observation made outside this tool, with how it was obtained
    out.update(res)
    out["asExpected"] = out["outcome"] == ex["expect"]["outcome"] and reporting == ex["expect"].get("by", [])
    return out


def summarise(r):
    bits = []
    if r["resolution"]:
        bits.append("resolution: %d unresolved endpoints (%s)" % (len(r["resolution"]), "; ".join(r["resolution"])))
    for k, v in (r["coverage"] or {}).items():
        bits.append("coverage %s: %s" % (k, "; ".join(v["failing"])))
    if r["coverage"] is None:
        bits.append("coverage: not run")
    for c in r["comparison"]:
        bits.append("comparison: %s %s%s; reaches %d Goals and %d Solutions, nearest %s" % (
            c["element"], c["change"], " (%s)" % ", ".join(c["fields"]) if c["fields"] else "",
            c["goalsReached"], c["solutionsReached"], ", ".join(c["nearest"]) or "none"))
    for f in r["freshness"]:
        bits.append("freshness: %s %s; cited by %s" % (f["file"], f["state"], ", ".join(f["solutions"])))
    bits = bits or ["no check reports anything"]
    if r.get("note"):
        bits.append("note: " + r["note"])
    return bits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--examples", default=os.path.join(REPO, "tools", "c3", "thread-faults.json"))
    ap.add_argument("--out", help="write <out>.json and <out>.md")
    args = ap.parse_args()
    change_detect = load("change_detect", "tools/change_detect.py")
    impact = load("impact", "namespace/impact.py")
    base = json.load(open(os.path.join(REPO, NAMESPACE), encoding="utf-8"))

    with tempfile.TemporaryDirectory() as td:   # the unmodified copy must be clean, or nothing below means anything
        for d in STAGED:
            shutil.copytree(os.path.join(REPO, d), os.path.join(td, d), ignore=shutil.ignore_patterns("__pycache__", "build", ".gradle"))
        clean = {"resolution": resolution(td), "coverage": coverage(td), "comparison": comparison(td, change_detect, impact, base), "freshness": freshness(td, base)}
    if any(clean.values()):
        raise SystemExit("the unmodified copy is not clean: %s" % json.dumps(clean)[:600])

    results = [run_example(ex, change_detect, impact, base) for ex in json.load(open(args.examples, encoding="utf-8"))]
    L = ["# Fault examples for the thread", "",
         "Generated by `python3 tools/thread_faults.py`. Each example is applied to a temporary copy of the",
         "repository; the repository is not modified. On the unmodified copy all four checks report nothing.", ""]
    for g in dict.fromkeys(r["group"] for r in results):
        L += ["## %s" % g, "", "| Example | Fault | Outcome | What the checks report |", "|---|---|---|---|"]
        L += ["| %s | %s | %s | %s |" % (r["id"], r["fault"], r["outcome"], "<br>".join(summarise(r)).replace("|", "\\|"))
              for r in results if r["group"] == g]
        L.append("")
    n = collections.Counter(r["outcome"] for r in results)
    L += ["%d examples: %d reported, %d not reported." % (len(results), n["reported"], n["not reported"]), ""]
    text = "\n".join(L)
    if args.out:
        json.dump(results, open(args.out + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        open(args.out + ".md", "w", encoding="utf-8").write(text)
    print(text)
    bad = [r["id"] for r in results if not r["asExpected"]]
    if bad:
        raise SystemExit("outcome differs from the expected one in: %s" % ", ".join(bad))


if __name__ == "__main__":
    main()
