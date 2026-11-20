#!/usr/bin/env python3
"""Score a completed recording sheet of the manual change-impact study against the thread's answer key.

The answer key is the unbounded closure from dryerA in namespace/ads-namespace.json (134 elements, computed
with namespace/impact.py). Each row of the sheet's Elements tab is matched to one identity-space element:
by the document it names and its name, compared with the visible names tools/manual_trace.py uses, ignoring
case, spaces, hyphens and underscores; digital-twin names carry a "part" or "signal" qualifier. Executable models are one element each (any row in 06-dafny to
10-modelica), except Modelica parameters, which match by name. Rows that do not match are listed for
adjudication; an adjudicated Element ID in the last column overrides the match.

  python3 studies/manual-impact/score.py results/P1.xlsx         # writes results/P1-scored.json and .md
  python3 studies/manual-impact/score.py --self-test             # checks the matcher (no files written)

Requires openpyxl for reading .xlsx.
"""
import argparse, collections, datetime, importlib.util, json, os, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
START = "dryerA"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


MT = load(os.path.join(ROOT, "tools", "manual_trace.py"), "manual_trace")
IMP = load(os.path.join(ROOT, "namespace", "impact.py"), "impact")
NS = json.load(open(os.path.join(ROOT, "namespace", "ads-namespace.json"), encoding="utf-8"))
NODE = {n["id"]: n for n in NS["nodes"]}
EXEC_DOC = {"06-dafny": "Dafny Model", "07-isabelle": "Isabelle Model", "08-csp": "FDR Model", "09-java": "Java Model",
            "10-modelica": "ModelicaModel"}


def doc_of(n):
    c, k = n["concern"], n["kind"]
    if c == "requirements": return "01-requirements"
    if c == "design": return "02-design"
    if c == "failure-analysis": return "03-fmeda" if n.get("notation") == "FMEDA" else "04-fault-tree"
    if c == "safety-case": return "05-gsn-safety-case"
    if c == "digital-twin": return "11-digital-twin"
    if k == "ModelicaParameter": return "10-modelica"
    return {v: d for d, v in EXEC_DOC.items()}[k]


def norm(s):
    return MT.lenient_norm(str(s or "").strip())[0]


def answer_key():
    node, adj = IMP.index(IMP.load())
    s = IMP.resolve(node, START)
    depth = {i: d for d, i, _ in IMP.impact(node, adj, s, None)}
    return s, depth


def name_index():
    idx = collections.defaultdict(set)
    for n in NS["nodes"]:
        names = MT.visible_names(n)
        if n["kind"] == "FMEARow":
            names = names + [n["label"].split()[-1]]
        if n["kind"] in ("TwinPart", "TwinBinding"):
            q = "part" if n["kind"] == "TwinPart" else "signal"
            names = names + [nm + " " + q for nm in names if nm]
        for nm in names:
            if nm:
                idx[(doc_of(n), norm(nm))].add(n["id"])
    return idx


IDX = name_index()


def match(doc, text):
    doc = (doc or "").strip()
    if doc in EXEC_DOC:
        if doc == "10-modelica":
            hit = IDX.get((doc, norm(text)), set())
            if len(hit) == 1:
                return next(iter(hit)), "name"
        return next(n["id"] for n in NS["nodes"] if n["kind"] == EXEC_DOC[doc]), "executable model"
    hit = IDX.get((doc, norm(text)), set())
    if len(hit) == 1:
        return next(iter(hit)), "name"
    return None, ("ambiguous" if hit else "no match")


def minutes(t):
    if t in (None, ""): return None
    if isinstance(t, datetime.time): return t.hour * 60 + t.minute
    if isinstance(t, datetime.datetime): return t.hour * 60 + t.minute
    h, m = str(t).strip().split(":")[:2]
    return int(h) * 60 + int(m)


def score(session, searches, elements):
    s, depth = answer_key()
    rows, found, first_round = [], set(), {}
    for r in elements:
        rnd, clock, doc, text = r[0], r[1], r[2], r[3]
        adjud = r[6] if len(r) > 6 else None
        if not (doc or text):
            continue
        eid, how = (str(adjud).strip(), "adjudicated") if adjud else match(doc, text)
        rows.append({"round": rnd, "clock": str(clock or ""), "document": doc, "element": text, "matched": eid,
                     "match": how, "in_answer_key": bool(eid and eid in depth)})
        if eid and eid in depth:
            found.add(eid)
            try: first_round.setdefault(eid, int(rnd))
            except (TypeError, ValueError): first_round.setdefault(eid, None)
    total = len(depth)
    by_depth = collections.Counter(depth[i] for i in found)
    key_by_depth = collections.Counter(depth.values())
    rounds = sorted({r for r in first_round.values() if r is not None})
    per_round = {r: sum(1 for x in first_round.values() if x is not None and x <= r) for r in rounds}
    label = lambda i: NODE[i].get("shortName") or NODE[i]["label"]
    sess = {k: v for k, v in session}
    start, end = minutes(sess.get("Start time (hh:mm)")), minutes(sess.get("End time (hh:mm)"))
    brk = 0
    for k in (1, 2, 3):
        a, b = minutes(sess.get("Break %d start" % k)), minutes(sess.get("Break %d end" % k))
        if a is not None and b is not None: brk += b - a
    working = (end - start - brk) if start is not None and end is not None else None
    return {
        "participant": sess.get("Participant code"),
        "answer_key": {"start": START, "elements": total, "source": "namespace/ads-namespace.json"},
        "found": len(found), "recall": round(len(found) / total, 4),
        "recall_by_depth": {d: "%d/%d" % (by_depth.get(d, 0), key_by_depth[d]) for d in sorted(key_by_depth)},
        "cumulative_by_round": per_round,
        "found_G2": any(label(i) == "G2" for i in found), "found_S1": any(label(i) == "S1" for i in found),
        "rows": len(rows), "unmatched_rows": [r for r in rows if not r["matched"]],
        "outside_answer_key": [r for r in rows if r["matched"] and not r["in_answer_key"]],
        "searches_logged": sum(1 for r in searches if any(c not in (None, "") for c in r[:3])),
        "working_minutes": working, "break_minutes": brk,
        "missed": sorted(label(i) for i in depth if i not in found),
        "matched_rows": rows,
    }


def read_sheet(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    session = [(r[0], r[1]) for r in wb["Session"].iter_rows(values_only=True) if r[0]]
    searches = [r for r in wb["Search log"].iter_rows(min_row=2, values_only=True)]
    elements = [r for r in wb["Elements"].iter_rows(min_row=2, values_only=True)]
    return session, searches, elements


def self_test():
    """Feed the matcher every visible name of every answer-key element; all must resolve to that element."""
    s, depth = answer_key()
    bad = []
    for i in depth:
        n = NODE[i]
        doc = doc_of(n)
        names = MT.visible_names(n) if doc not in EXEC_DOC or n["kind"] == "ModelicaParameter" else ["model file"]
        if n["kind"] in ("TwinPart", "TwinBinding"):  # participants qualify twin names with "part" or "signal"
            names = [nm + (" part" if n["kind"] == "TwinPart" else " signal") for nm in names if nm]
        for nm in names:
            got, how = match(doc, nm)
            if got != i:
                bad.append((n["label"], doc, nm, got, how))
    print("self-test: %d answer-key elements, %d name checks failed" % (len(depth), len(bad)))
    for b in bad[:20]:
        print("  ", b)
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    res = score(*read_sheet(a.sheet))
    stem = os.path.splitext(a.sheet)[0]
    json.dump(res, open(stem + "-scored.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    md = ["# Scored: %s" % (res["participant"] or os.path.basename(a.sheet)), "",
          "* Found %d of %d answer-key elements (%.0f%%); G2 %s, S1 %s." % (res["found"], res["answer_key"]["elements"], 100 * res["recall"],
              "found" if res["found_G2"] else "missed", "found" if res["found_S1"] else "missed"),
          "* Working time %s min (breaks %d min); %d searches logged; %d element rows." % (res["working_minutes"], res["break_minutes"], res["searches_logged"], res["rows"]),
          "* Cumulative found by round: %s" % res["cumulative_by_round"],
          "* Recall by thread depth: %s" % res["recall_by_depth"],
          "* Rows needing adjudication: %d; rows outside the answer key: %d" % (len(res["unmatched_rows"]), len(res["outside_answer_key"])), ""]
    for r in res["unmatched_rows"]:
        md.append("  - round %s, %s: %r (%s)" % (r["round"], r["document"], r["element"], r["match"]))
    md += ["", "Missed: " + ", ".join(res["missed"])]
    open(stem + "-scored.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md[:7]))


if __name__ == "__main__":
    main()
