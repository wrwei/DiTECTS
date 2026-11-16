# Re-verification results (2026-11-15T18:11:01+0000)

Condition: `baseline`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.17 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.01 | 11 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 39.54 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 1.26 | 23 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 4.04 | 14 tests, 14 passed, 0 failed, 0 skipped |
