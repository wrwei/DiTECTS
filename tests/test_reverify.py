"""Regression checks for checker interruption and fault-detection counts.

Run with python3 -m unittest discover -s tests -v.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import re
import shutil
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import reverify


KILLED_OUTPUT = '''Running ADSController_Check ...
/tmp/isabelle/bash_script: line 1: 184 Killed "$POLYML_EXE" -q
ADSController_Check FAILED
Unfinished session(s): ADSController_Check
'''


class CheckerInterruptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        out = Path(self.temp.name)
        (out / "logs").mkdir()
        self.args = SimpleNamespace(out=str(out), keep_work=False, isabelle_docker=None,
                                    isabelle="isabelle", timeout_isabelle=1800, only={"Sn8"})
        ns = json.loads((ROOT / "namespace/ads-namespace.json").read_text())
        self.link = next(l for l in reverify.evidence_links(ns) if l["solution"] == "Sn8")

    def dispatch(self, status, output, timed_out=False):
        result = {"exit": status, "output": output, "timedOut": timed_out, "seconds": 1.0}
        with patch.object(reverify, "run_proc", return_value=result):
            return reverify.dispatch(self.args, self.link, "regression")

    def test_killed_isabelle_process_is_unassessed_even_with_failed_session_output(self):
        result = self.dispatch(137, KILLED_OUTPUT)
        self.assertEqual(result["verdict"], "NOT_ASSESSED")
        self.assertIn("Killed", result["detail"])
        log = (Path(self.args.out) / result["log"]).read_text()
        self.assertIn(KILLED_OUTPUT, log)
        self.assertIn("# exit: 137", log)

    def test_killed_child_is_unassessed_when_wrapper_exits_one(self):
        self.assertEqual(self.dispatch(1, KILLED_OUTPUT)["verdict"], "NOT_ASSESSED")

    def test_signal_exit_is_unassessed_without_output(self):
        for status in (-signal.SIGKILL, 137, -signal.SIGTERM, 143):
            with self.subTest(status=status):
                self.assertEqual(self.dispatch(status, "")["verdict"], "NOT_ASSESSED")

    def test_timeout_stays_timeout_when_it_kills_the_checker(self):
        self.assertEqual(self.dispatch(137, KILLED_OUTPUT, timed_out=True)["verdict"], "TIMEOUT")

    def test_memory_failure_with_a_failed_session_is_unassessed(self):
        output = "java.lang.OutOfMemoryError: Java heap space\nUnfinished session(s): ADSController_Check"
        self.assertEqual(self.dispatch(1, output)["verdict"], "NOT_ASSESSED")

    def test_genuine_proof_failure_stays_a_fault(self):
        output = "*** Failed to finish proof (line 169)\nUnfinished session(s): ADSController_Check"
        self.assertEqual(self.dispatch(1, output)["verdict"], "FAIL")

    def test_completed_proof_passes_despite_an_unrelated_theorem_name(self):
        output = "Checking theorem Killed\nFinished ADSController_Check (0:00:01 elapsed time)"
        self.assertEqual(self.dispatch(0, output)["verdict"], "PASS")

    def test_killed_mutant_is_not_counted_as_detected(self):
        mutants = Path(self.args.out) / "mutants.json"
        mutants.write_text(json.dumps([{"id": "I4", "solution": "Sn8", "class": "fault", "edits": []}]))
        self.args.mutants = str(mutants)
        res = {"mutants": []}
        process = {"exit": 137, "output": KILLED_OUTPUT, "timedOut": False, "seconds": 1.0}
        with patch.object(reverify, "run_proc", return_value=process), contextlib.redirect_stdout(io.StringIO()):
            reverify.run_mutants(self.args, [self.link], res)
        self.assertEqual(res["mutants"][0]["outcome"], "not assessed")


class RecordedResultsTests(unittest.TestCase):
    def test_report_counts_unassessed_fault_separately(self):
        # Historical result before the bed-alternation correction (16 faults).
        result = json.loads((ROOT / "results/prior_formal_alternation/reverify_bound_thread.json").read_text())
        result = copy.deepcopy(result)
        history = {"I4": result["sources"]["proofUpdate"]["previousI4"],
                   "F3": result["sources"]["cspResponseUpdate"]["previousF3"]}
        result["mutants"] = [history.get(m["mutant"], m) for m in result["mutants"]]
        report = reverify.markdown(result)
        self.assertIn("| isabelle | 3/4 | 0 | 0 | 1 | 1/1 |", report)
        self.assertIn("| Total | 14/16 | 1 | 0 | 1 | 6/6 |", report)

    def test_current_docker_run_detects_i4_by_a_proof_failure(self):
        result = json.loads((ROOT / "results/reverify_bound_thread.json").read_text())
        i4 = next(m for m in result["mutants"] if m["mutant"] == "I4")
        self.assertEqual(i4["exit"], 1)
        self.assertEqual(i4["verdict"], "FAIL")
        self.assertEqual(i4["outcome"], "detected")
        self.assertIn("Failed to finish proof", i4["detail"])
        self.assertTrue((ROOT / "results" / i4["log"]).is_file())
        report = reverify.markdown(result)
        self.assertIn("| isabelle | 12/12 | 0 | 0 | 0 | 1/1 |", report)
        self.assertIn("| fdr | 11/11 | 0 | 0 | 0 | 1/1 |", report)
        self.assertIn("| Total | 37/37 | 0 | 0 | 0 | 6/6 |", report)

    def test_power_loss_protocol_detects_the_previously_surviving_fault(self):
        result = json.loads((ROOT / "results/reverify_bound_thread.json").read_text())
        f3 = next(m for m in result["mutants"] if m["mutant"] == "F3")
        self.assertEqual(f3["verdict"], "FAIL")
        self.assertEqual(f3["outcome"], "detected")
        self.assertEqual(f3["detail"], "20 assertions passed, 7 failed")
        log = (ROOT / "results" / f3["log"]).read_text()
        for text in ["ADS_ResponseNormal [FD= ADS_ResponseView", "Counterexample", "ADSController::dewpointHigh.in", "ADSController::powerLoss.in"]:
            self.assertIn(text, log)

    def test_alternation_check_detects_a_bed_selection_stub(self):
        result = json.loads((ROOT / "results/reverify_bound_thread.json").read_text())
        f4 = next(m for m in result["mutants"] if m["mutant"] == "F4")
        self.assertEqual(f4["verdict"], "FAIL")
        self.assertEqual(f4["outcome"], "detected")
        self.assertEqual(f4["detail"], "24 assertions passed, 3 failed")
        log = (ROOT / "results" / f4["log"]).read_text()
        for text in ["ADS_AlternationStart(ADS_InitialBed) [FD= ADS_AlternationView", "Counterexample", "set_activeDryer"]:
            self.assertIn(text, log)
        baseline = {b["solution"]: b for b in result["baseline"]}
        self.assertEqual(baseline["Sn9"]["detail"], "27 assertions passed, 0 failed")

    def test_removing_power_loss_operations_fails_a_proof_in_a_well_formed_theory(self):
        result = json.loads((ROOT / "results/reverify_bound_thread.json").read_text())
        fault = next(m for m in result["mutants"] if m["mutant"] == "I6")
        self.assertEqual(fault["verdict"], "FAIL")
        self.assertEqual(fault["outcome"], "detected")
        self.assertIn("Failed to finish proof", fault["detail"])
        log = (ROOT / "results" / fault["log"]).read_text()
        self.assertIn("NormalOperation", log)
        self.assertIn("Changeover", log)
        self.assertNotIn("Undefined constant", log)
        self.assertNotIn("Unknown constant", log)

    def test_destination_and_command_checks_detect_the_review_faults(self):
        result = json.loads((ROOT / "results/reverify_bound_thread.json").read_text())
        faults = {m["mutant"]: m for m in result["mutants"]}
        specs = {m["id"]: m for m in json.loads((ROOT / "tools/c3/mutants.json").read_text())}

        def failing_lemmas(mid):
            # Proof failures name lines of the mutated theory; rebuild it to find each failing lemma.
            log = (ROOT / "results" / faults[mid]["log"]).read_text()
            numbers = {int(n) for n in re.findall(r"line (\d+) of", log)}
            with tempfile.TemporaryDirectory() as temporary:
                shutil.copytree(ROOT / "formal/isabelle", temporary, dirs_exist_ok=True)
                reverify.apply_edits(temporary, specs[mid]["edits"])
                lines = (Path(temporary) / "ADSController_Beh.thy").read_text().splitlines()
            return {next(l for l in reversed(lines[:n]) if l.startswith("lemma")) for n in numbers}

        expected = {"I7": "NormalOperationToChangeover_destination", "I8": "NormalOperationToChangeover_destination",
                    "I9": "FailSafeToNormalOperation_destination", "I10": "ADSController_offered_by_mode",
                    "I11": "Init_inv", "I12": "ADSController_handler_targets"}
        for mid, lemma in expected.items():
            with self.subTest(mutant=mid):
                self.assertEqual(faults[mid]["outcome"], "detected")
                self.assertTrue(any(lemma in l for l in failing_lemmas(mid)), failing_lemmas(mid))
        for mid in ["F5", "F6", "F7"]:
            with self.subTest(mutant=mid):
                # Each fault edits all three copies, so the module and controller protocols fail too.
                self.assertEqual(faults[mid]["detail"], "24 assertions passed, 3 failed")
                self.assertIn("ADS_CommandNormal [FD= ADS_CommandView",
                              (ROOT / "results" / faults[mid]["log"]).read_text())
        j5 = (ROOT / "results" / faults["J5"]["log"]).read_text()
        self.assertIn("DewpointHigh requests changeover and commands StartChangeover FAILED", j5)
        expected_copy = {"F8": "ADS_ModuleCommandNormal [FD= ADS_ModuleCommandView",
                         "F9": "ADS_ModuleAlternationStart(ADS_InitialBed) [FD= ADS_ModuleAlternationView",
                         "F10": "ADS_CtrlCommandNormal [FD= ADS_CtrlCommandView",
                         "F11": "ADS_CtrlAlternationStart(ADS_InitialBed) [FD= ADS_CtrlAlternationView"}
        for mid, text in expected_copy.items():
            with self.subTest(mutant=mid):
                # A fault in one copy of the state machine fails exactly that copy's protocol.
                self.assertEqual(faults[mid]["detail"], "26 assertions passed, 1 failed")
                log = " ".join((ROOT / "results" / faults[mid]["log"]).read_text().split())
                self.assertIn(" ".join(text.split()), log)  # FDR wraps long assertion names
        for review in ["formal_outputs", "formal_interface", "formal_handlers"]:
            before = json.loads((ROOT / "results" / review / "review-before/reverify_results.json").read_text())
            self.assertEqual({m["outcome"] for m in before["mutants"]}, {"survived"})

if __name__ == "__main__":
    unittest.main()
