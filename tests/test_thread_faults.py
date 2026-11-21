"""The fault examples for the thread produce the outcomes they state."""
import json, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_fault_examples_match_expected_outcomes(tmp_path):
    out = str(tmp_path / "thread_faults")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "thread_faults.py"), "--out", out], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    results = json.load(open(out + ".json"))
    assert all(x["asExpected"] for x in results)
    assert sorted(x["id"] for x in results if x["outcome"] == "not reported") == []
    assert results == json.load(open(os.path.join(REPO, "results", "thread_faults.json")))


def test_coverage_stops_on_an_unresolved_edge_end(tmp_path):
    ns = json.load(open(os.path.join(REPO, "namespace", "ads-namespace.json")))
    next(e for e in ns["edges"] if e.get("name") == "Sn7-to-Dafny")["target"] = "0" * 24
    p = str(tmp_path / "ns.json")
    json.dump(ns, open(p, "w"))
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "coverage.py"), "--namespace", p], capture_output=True, text=True)
    assert r.returncode == 2 and "unresolved endpoints: 1" in r.stdout and "Sn7-to-Dafny" in r.stdout
