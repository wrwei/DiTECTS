# Re-verification results (2026-11-15T20:37:38+0000)

Condition: `stale`  Repository: `<repo>`


## Stale evidence: ST1-tCycle
Change: ADSController::changeoverPeriod 7000 s -> 9000 s (SysML design attribute), propagated to ADSChangeover.tCycle through the sim-binding  
Flagged by namespace/impact.py closure (unbounded): Sn10@3, Sn2@3, Sn3@3, Sn7@3, Sn8@3, Sn9@3, Sn1@4, Sn11@7, Sn4@7, Sn5@8, Sn6@8

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | True | FAIL | bound tCycle=9000, tSat=4000, DFtarget=1000; assertion fired at t = 8320.0 s: Detritiation continuity violated: plant DF fell below the authorised target during changeover; diagnostic run (assertion as warning): min DF 843.2 at t = 9000 s over 0-20000 s |
| Sn7 | dafny | False | PASS | 11 verified, 0 errors |
| Sn8 | isabelle | False | PASS | Finished ADSController_Check |
| Sn9 | fdr | False | PASS | 27 assertions passed, 0 failed |
| Sn10 | gradle | False | PASS | 14 tests, 14 passed, 0 failed, 0 skipped |

## Stale evidence: ST2-initialBed
Change: ADSController.activeDryer default Dryer::BedA -> Dryer::BedB, propagated to the Dafny, Isabelle, CSP and Java artefacts  
Flagged by namespace/impact.py closure (unbounded): Sn10@2, Sn2@2, Sn3@2, Sn7@2, Sn8@2, Sn9@2, Sn1@3, Sn11@6, Sn4@6, Sn5@7, Sn6@7

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | False | PASS | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | dafny | True | PASS | 11 verified, 0 errors |
| Sn8 | isabelle | True | PASS | Finished ADSController_Check |
| Sn9 | fdr | True | PASS | 27 assertions passed, 0 failed |
| Sn10 | gradle | True | FAIL | 14 tests, 7 passed, 7 failed, 0 skipped |
