#!/usr/bin/env python3
"""Estimate the time a manual (name-search) impact analysis would take.

Converts the operations counted by tools/manual_trace.py into time with the
keystroke-level model (KLM; Card, Moran and Newell, Commun. ACM 23(7), 1980)
and typical reading speeds for technical text (200-300 words per minute;
Rayner et al., Psychol. Sci. Public Interest 17(1), 2016).

Two bounds are reported:
  low  - one "find in files" search per term covering all eleven files,
         skilled typist (K = 0.20 s), reading at 300 words per minute;
  high - one search per term per file, average typist (K = 0.28 s),
         reading at 200 words per minute.
Both bounds use the KLM operators P = 1.1 s (point to a match or a file)
and M = 1.35 s (mental preparation: decide what to do next).

Per search:   M + P + (len(term) + 4) * K   (open the file or search pane,
              open find, type the term, confirm, judge the result count)
Per hit:      P + M                          (go to the match, judge it)
Per segment:  words / reading speed          (read each matched segment once)
Per element:  M + len(label) * K             (record the element as affected)

The digital thread's query time is negligible; reviewing its result still
requires reading the returned elements, which is estimated the same way.
Standard library only. Usage: python3 tools/manual_time.py
"""
import importlib.util
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P_OP, M_OP = 1.1, 1.35
BOUNDS = {
    "low": {"K": 0.20, "wpm": 300, "find_in_files": True},
    "high": {"K": 0.28, "wpm": 200, "find_in_files": False},
}
SCENARIOS = ["dryerA", "controller", "REQ-ADS-007"]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def words(text):
    return len(text.split())


def estimate(eng, run, start, bound):
    K, wpm, fif = bound["K"], bound["wpm"], bound["find_in_files"]
    ndocs = len(eng.DOCS)
    terms = run["searched"]
    per_term = sum(M_OP + P_OP + (len(t) + 4) * K for t in terms)
    t_search = per_term if fif else per_term * ndocs
    read = set()
    hits = 0
    for t in terms:
        for s in eng.hits(t):
            hits += 1
            read.add(s["sid"])
    t_hits = hits * (P_OP + M_OP)
    t_read = sum(words(eng.segs[i]["text"]) for i in read) / wpm * 60
    t_record = sum(M_OP + len(eng.node[e]["label"]) * K for e in run["found"])
    total = t_search + t_hits + t_read + t_record
    return {"search_s": round(t_search, 1), "inspect_hits_s": round(t_hits, 1),
            "read_s": round(t_read, 1), "record_s": round(t_record, 1),
            "total_h": round(total / 3600, 2), "hits": hits, "segments_read": len(read),
            "terms": len(terms)}


def thread_review(eng, impact_ids, bound):
    w = sum(words(eng.seg_of[e]["text"]) for e in impact_ids if e in eng.seg_of)
    return round((w / bound["wpm"] * 60 + len(impact_ids) * M_OP) / 3600, 2)


def main():
    mt = load("manual_trace", "tools/manual_trace.py")
    tool = load("ads_impact", "namespace/impact.py")
    ns = json.load(open(os.path.join(ROOT, "namespace/ads-namespace.json")))
    node, adj = tool.index(ns)
    out = {"model": {"P_s": P_OP, "M_s": M_OP, "bounds": BOUNDS,
                     "sources": ["Card, Moran and Newell (1980) Commun. ACM 23(7):396-410",
                                 "Rayner et al. (2016) Psychol. Sci. Public Interest 17(1):4-34"]},
           "scenarios": {}, "all_starts": {}}
    for variant in ("EXACT", "LENIENT"):
        eng = mt.Engine(ns, variant)
        eng.DOCS = mt.DOCUMENTS
        per_start = {b: [] for b in BOUNDS}
        rev = {b: [] for b in BOUNDS}
        for n in ns["nodes"]:
            run = eng.run(n["id"])
            closure = [i for _, i, _ in tool.impact(node, adj, n["id"], None)]
            for b, bound in BOUNDS.items():
                est = estimate(eng, run, n["id"], bound)
                per_start[b].append(est["total_h"])
                rev[b].append(thread_review(eng, closure, bound))
                label = n.get("shortName") or n["label"]
                if label in SCENARIOS and n["concern"] in ("design", "requirements"):
                    out["scenarios"].setdefault(label, {}).setdefault(variant, {})[b] = est
                    out["scenarios"][label].setdefault("thread_review_h", {})[b] = rev[b][-1]
        out["all_starts"][variant] = {
            b: {"median_h": round(statistics.median(per_start[b]), 2),
                "max_h": round(max(per_start[b]), 2)} for b in BOUNDS}
        out["all_starts"]["thread_review"] = {
            b: {"median_h": round(statistics.median(rev[b]), 2)} for b in BOUNDS}
    path = os.path.join(ROOT, "results", "manual_time.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for s, v in out["scenarios"].items():
        print(s, {k: (v[k]["low"]["total_h"], v[k]["high"]["total_h"]) for k in ("EXACT", "LENIENT")},
              "thread review", v["thread_review_h"])
    print("all starts", json.dumps(out["all_starts"]))


if __name__ == "__main__":
    main()
