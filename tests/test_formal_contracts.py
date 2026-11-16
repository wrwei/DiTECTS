"""Check the concrete faulty transitions exposed by the model review."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import reverify

DAFNY = shutil.which("dafny")


@unittest.skipUnless(DAFNY, "Dafny is not installed")
class CompleteTransitionContractTests(unittest.TestCase):
    def test_alarm_recovery_and_early_swap_faults_are_rejected(self):
        mutations = json.loads((ROOT / "tools/c3/mutants.json").read_text())
        faults = [m for m in mutations if m["id"] in {"D7", "D8", "D9"}]
        self.assertEqual({m["id"] for m in faults}, {"D7", "D8", "D9"})
        for mutation in faults:
            with self.subTest(mutation=mutation["id"]), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary) / "dafny"
                shutil.copytree(ROOT / "formal/dafny", work)
                self.assertTrue(reverify.apply_edits(str(work), mutation["edits"]))
                run = subprocess.run([DAFNY, "verify", "ADSController.dfy"], cwd=work,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, timeout=120)
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertIn("postcondition could not be proved", run.stdout)


if __name__ == "__main__":
    unittest.main()
