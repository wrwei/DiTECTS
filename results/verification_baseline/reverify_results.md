# Re-verification results (2026-11-15T08:21:22+0000)

Condition: `baseline`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.26 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.11 | 6 verified, 0 errors |
| Sn9 | ADS Controller Refinement | fdr | PASS | 0.92 | 20 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 4.15 | 14 tests, 14 passed, 0 failed, 0 skipped |
