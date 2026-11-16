"""Check the controller protocols and timed memory interface with real FDR."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FDR = os.environ.get("FDR_PATH") or shutil.which("refines")
if not FDR and sys.platform == "darwin":
    candidate = Path("/Applications/FDR4.app/Contents/MacOS/refines")
    if candidate.is_file():
        FDR = str(candidate)


@unittest.skipUnless(FDR, "FDR is not installed")
class PowerLossPropertyTests(unittest.TestCase):
    def check_protocols(self, initial_bed):
        # FDR resolves includes relative to the entry file, so stage the driver
        # next to the model rather than changing the model's include paths.
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "csp"
            shutil.copytree(ROOT / "formal/csp", work)
            checks = "\n".join((work / "tests" / f).read_text() for f in
                               ["powerloss_response.csp", "bed_alternation.csp"])
            initial = work / "instantiations.csp"
            initial.write_text(initial.read_text().replace(
                "ADS_InitialBed = Dryer_BedA", "ADS_InitialBed = " + initial_bed))
            assertions = (work / "file_robochart_controller_coreassertions.csp").read_text() + checks
            expected = len(re.findall(r"^assert ", assertions, re.M))
            driver = work / "response_checks.csp"
            driver.write_text('include "file_robochart_controller_coreassertions.csp"\n' + checks)
            run = subprocess.run([FDR, "-f", "plain", driver.name], cwd=work,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout[-5000:])
        self.assertEqual(len(re.findall(r"Result:\s*Passed", run.stdout)), expected, run.stdout[-5000:])
        self.assertNotRegex(run.stdout, r"Result:\s*Failed")

    def test_controller_protocols_starting_on_bed_a(self):
        self.check_protocols("Dryer_BedA")

    def test_controller_protocols_starting_on_bed_b(self):
        self.check_protocols("Dryer_BedB")

    def test_timed_controller_has_no_timelock_or_nondeterminism(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "timed"
            shutil.copytree(ROOT / "formal/csp/timed", work)
            entry = work / "file_robochart_controller_coreassertions.csp"
            expected = len(re.findall(r"^assert ", entry.read_text(), re.M))
            self.assertEqual(expected, 30)
            run = subprocess.run([FDR, "-f", "plain", entry.name], cwd=work,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout[-5000:])
        self.assertEqual(len(re.findall(r"Result:\s*Passed", run.stdout)), expected, run.stdout[-5000:])
        self.assertNotRegex(run.stdout, r"Result:\s*Failed")


if __name__ == "__main__":
    unittest.main()
