# Re-verification results (2026-11-15T16:25:03+0000)

Condition: `baseline`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.76 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.09 | 11 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 37.19 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 1.32 | 23 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 3.65 | 14 tests, 14 passed, 0 failed, 0 skipped |
