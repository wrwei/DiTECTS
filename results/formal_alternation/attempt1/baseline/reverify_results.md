# Re-verification results (2026-11-15T13:46:39+0000)

Condition: `baseline`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.34 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 0.97 | 9 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | FAIL | 44.35 | *** Failed to apply initial proof method (line 210 of "~/ads-experiments/reverify-formalfix/baseline/work/baseline__Sn8/ADSController_Beh.thy"): |
| Sn9 | ADS Controller Refinement | fdr | FAIL | 1.26 | 18 assertions passed, 4 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 3.7 | 14 tests, 14 passed, 0 failed, 0 skipped |
