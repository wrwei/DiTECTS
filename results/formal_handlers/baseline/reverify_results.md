# Re-verification results (2026-11-15T20:25:15+0000)

Condition: `baseline`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.28 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.12 | 11 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 49.08 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 2.42 | 27 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 4.48 | 14 tests, 14 passed, 0 failed, 0 skipped |
