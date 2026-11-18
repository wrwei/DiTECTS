#!/usr/bin/env python3
"""Detect changed model elements between two repository revisions and flag the evidence they affect.

Static evidence (FMEDA rows, fault-tree events, design elements) cannot be re-run, so a change to
it is found by comparison instead. This tool compares every identified element record in the
model files under models/ between two git revisions by content hash, lists the elements that were
added, removed or changed (with the fields that changed), and runs namespace/impact.py from each
changed element over the identity space of the later revision. It reports the Solutions reached,
with their depth and whether any of their evidence has a configured runner.

The platform does the same with a stored baseline that fingerprints each thread element as
sha256(name|updatedAt); this tool fingerprints the deposited element records instead, so it needs
no database.

  python3 tools/change_detect.py --before e52552d^ --after e52552d --out results/change_fmeda_row11
"""
import argparse, collections, hashlib, importlib.util, json, os, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Overlay and derived evidence map are not models; link changes are reported separately.
SKIP = {"models/traceability/completion.json", "models/safety-case/evidence-resolution.json"}
RUNNER_KINDS = {"Dafny Model", "Isabelle Model", "FDR Model", "Java Model", "ModelicaModel"}


def git(*args):
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null")
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, env=env)
    if r.returncode:
        raise SystemExit(r.stderr.strip())
    return r.stdout


def elements(doc):
    """Every identified record in a model document, keyed by its identifier."""
    out = {}

    def walk(o):
        if isinstance(o, dict):
            i = o.get("@id") or o.get("elementId") or o.get("gid")
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


def element_changes(before, after):
    files = [f for f in git("ls-tree", "-r", "--name-only", after, "models/").split()
             if f.endswith(".json") and f not in SKIP]
    out = []
    for f in files:
        ea = elements(json.loads(git("show", f"{after}:{f}")))
        try:
            eb = elements(json.loads(git("show", f"{before}:{f}")))
        except SystemExit:
            eb = {}
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


def link_changes(before, after):
    path = "models/traceability/completion.json"
    la = {l["_id"]: l for l in json.loads(git("show", f"{after}:{path}"))["links"]}
    lb = {l["_id"]: l for l in json.loads(git("show", f"{before}:{path}"))["links"]}
    out = []
    for i in sorted(set(la) | set(lb)):
        a, b = la.get(i), lb.get(i)
        if a and not b:
            out.append({"link": a["name"], "change": "added"})
        elif b and not a:
            out.append({"link": b["name"], "change": "removed"})
        elif sorted(a["targets"]) != sorted(b["targets"]) or a["source"] != b["source"]:
            out.append({"link": a["name"], "change": "endpoints", "targets": {"from": b["targets"], "to": a["targets"]}})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--out", help="write <out>.json and <out>.md")
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("impact", os.path.join(REPO, "namespace", "impact.py"))
    impact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(impact)
    ns = json.loads(git("show", f"{args.after}:namespace/ads-namespace.json"))
    node, adj = impact.index(ns)
    by_uuid = {n.get("uuid"): n["id"] for n in ns["nodes"] if n.get("uuid")}
    label = lambda i: node[i].get("shortName") or node[i]["label"]
    cites = collections.defaultdict(set)
    for e in ns["edges"]:
        if e["kind"] == "traceability" and node[e["source"]]["kind"] == "Solution":
            cites[e["source"]].add(e["target"])

    changes = element_changes(args.before, args.after)
    flagged = []
    for c in changes:
        start = by_uuid.get(c["id"]) or (c["id"] if c["id"] in node else None)
        c["element"] = label(start) if start else None
        if not start or c["change"] == "removed":
            continue
        for d, i, _ in impact.impact(node, adj, start, None):
            if node[i]["kind"] == "Solution":
                runner = sorted(label(t) for t in cites[i] if node[t]["kind"] in RUNNER_KINDS)
                flagged.append({"from": c["element"], "solution": label(i), "depth": d,
                                "direct": start in cites[i], "runnerEvidence": runner})
    flagged.sort(key=lambda f: (f["from"], f["depth"], f["solution"]))
    res = {"before": args.before, "after": args.after,
           "beforeCommit": git("rev-parse", "--short", args.before).strip(),
           "afterCommit": git("rev-parse", "--short", args.after).strip(),
           "elementChanges": changes, "linkChanges": link_changes(args.before, args.after),
           "flaggedSolutions": flagged}

    L = ["# Change detection: %s (%s) to %s (%s)" % (args.before, res["beforeCommit"], args.after, res["afterCommit"]), "",
         "Generated by `python3 tools/change_detect.py --before %s --after %s`." % (args.before, args.after), "",
         "## Changed elements", ""]
    for c in changes:
        L.append("- %s `%s` in `%s`: %s" % (c["element"] or c["id"], c["id"], c["file"], c["change"]))
        for k, v in (c.get("fields") or {}).items():
            L.append("  - `%s`: %s -> %s" % (k, json.dumps(v["from"]), json.dumps(v["to"])))
    L += ["", "## Changed links", ""] + ["- %s: %s" % (l["link"], l["change"]) for l in res["linkChanges"]]
    L += ["", "## Solutions reached", "", "| From | Solution | Depth | Cites the element | Evidence with a runner |", "|---|---|---|---|---|"]
    L += ["| %s | %s | %d | %s | %s |" % (f["from"], f["solution"], f["depth"], "yes" if f["direct"] else "",
                                          ", ".join(f["runnerEvidence"]) or "none") for f in flagged]
    text = "\n".join(L) + "\n"
    if args.out:
        json.dump(res, open(args.out + ".json", "w"), indent=1)
        open(args.out + ".md", "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
