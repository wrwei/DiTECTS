"""End-to-end check of studies/manual-impact/score.py.

Builds a temporary recording sheet (never deposited) from the counted manual search's found set for dryerA
(results/manual_vs_thread.json, relaxed matching) and checks that the scorer recovers the same 118 of 134.
"""
import json, os, sys, tempfile, unittest, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


class ManualStudyScorerTests(unittest.TestCase):
    def test_self_test(self):
        sc = load(os.path.join(ROOT, "studies", "manual-impact", "score.py"), "score")
        self.assertEqual(sc.self_test(), 0)

    def test_counted_search_scores_118_of_134(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl not installed")
        sc = load(os.path.join(ROOT, "studies", "manual-impact", "score.py"), "score")
        mv = json.load(open(os.path.join(ROOT, "results", "manual_vs_thread.json"), encoding="utf-8"))
        L = next(x for x in mv["scenarios"] if x["scenario"] == "dryerA")["LENIENT"]
        missed = {m["element"] for m in L["misses"]}
        _, depth = sc.answer_key()
        found = [i for i in depth if i not in missed]
        wb = openpyxl.load_workbook(os.path.join(ROOT, "studies", "manual-impact", "recording-sheet.xlsx"))
        s = wb["Session"]
        values = {"Participant code": "TEST", "Start time (hh:mm)": "09:00", "End time (hh:mm)": "13:30",
                  "Break 1 start": "11:00", "Break 1 end": "11:15"}
        for r in range(1, s.max_row + 1):
            if s.cell(row=r, column=1).value in values:
                s.cell(row=r, column=2).value = values[s.cell(row=r, column=1).value]
        e = wb["Elements"]
        seen_exec = set()
        for i in found:
            n = sc.NODE[i]; doc = sc.doc_of(n)
            if doc in sc.EXEC_DOC and n["kind"] != "ModelicaParameter":
                name = doc + " model"
            else:
                name = sc.MT.visible_names(n)[0]
                if n["kind"] in ("TwinPart", "TwinBinding"):
                    name += " part" if n["kind"] == "TwinPart" else " signal"
            e.append([1, "09:10", doc, name, "dryerA", None, None])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "TEST.xlsx"); wb.save(p)
            res = sc.score(*sc.read_sheet(p))
        self.assertEqual(res["found"], 118)
        self.assertEqual(res["answer_key"]["elements"], 134)
        self.assertEqual(res["unmatched_rows"], [])
        self.assertFalse(res["found_G2"]); self.assertFalse(res["found_S1"])
        self.assertEqual(res["working_minutes"], 255)


if __name__ == "__main__":
    unittest.main()
