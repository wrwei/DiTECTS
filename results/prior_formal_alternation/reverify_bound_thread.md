# Re-verification results (2026-11-15T08:42:17+00:00)

Condition: `baseline + mutants + stale (composed; explicit state cases and CSP power-loss protocol)`  Repository: `.`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.26 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.11 | 6 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 41.77 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 0.88 | 21 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 4.15 | 14 tests, 14 passed, 0 failed, 0 skipped |

## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| D1 | fault | dafny | FAIL | detected | 1.1 | PowerLoss during Changeover no longer enters FailSafe (controller stays in Changeover) |
| D2 | fault | dafny | FAIL | detected | 1.05 | Changeover takes the duty bed offline (new Dryer value NoBed) before the standby bed is live |
| D3 | fault | dafny | FAIL | detected | 1.0 | FailSafe is left on PowerLoss as well as BackupRestored |
| D4 | fault | dafny | FAIL | detected | 0.9 | requires mode == FailSafe removed from transitionFromFailSafe |
| D5 | fault | dafny | FAIL | detected | 0.86 | step() dispatches Changeover events to the NormalOperation handler |
| DC1 | control | dafny | PASS | control passed | 0.88 | Add a true postcondition: DewpointHigh in NormalOperation leads to Changeover |
| DC2 | control | dafny | PASS | control passed | 0.91 | Swap the order of the two requires clauses of transitionFromNormalOperation and edit a comment |
| J1 | fault | gradle | FAIL | detected | 3.54 | PowerLoss during Changeover emits EnterFailSafe but the mode stays Changeover |
| J2 | fault | gradle | FAIL | detected | 3.21 | nextDryer(BedA) returns BedA: changeover never swaps the duty bed |
| J3 | fault | gradle | FAIL | detected | 3.3 | FailSafe is also left on DewpointHigh |
| J4 | fault | gradle | FAIL | detected | 3.21 | Duty bed is swapped when changeover starts (DewpointHigh) instead of when it completes |
| JC1 | control | gradle | PASS | control passed | 3.39 | Rename private field dryers -> dryerFunctions throughout ADSController |
| JC2 | control | gradle | PASS | control passed | 3.15 | Final "else if (currentMode == ADSMode.FailSafe)" replaced by plain "else" (enum has exactly three values, field never null) |
| F1 | fault | fdr | FAIL | detected | 0.76 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.75 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.73 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| FC1 | control | fdr | PASS | control passed | 0.74 | Swap the order of the two NormalOperation transitions ([] is commutative) |
| I1 | fault | isabelle | FAIL | detected | 40.47 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 39.2 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 47.12 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 32.67 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| IC1 | control | isabelle | PASS | control passed | 37.95 | Edit the introduction text block |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 5/5 | 0 | 0 | 0 | 2/2 |
| fdr | 3/3 | 0 | 0 | 0 | 1/1 |
| gradle | 4/4 | 0 | 0 | 0 | 2/2 |
| isabelle | 4/4 | 0 | 0 | 0 | 1/1 |
| Total | 16/16 | 0 | 0 | 0 | 6/6 |

## Stale evidence: ST1-tCycle
Change: ADSController::changeoverPeriod 7000 s -> 9000 s (SysML design attribute), propagated to ADSChangeover.tCycle through the sim-binding  
Flagged by namespace/impact.py closure (unbounded): Sn10@3, Sn2@3, Sn3@3, Sn7@3, Sn8@3, Sn9@3, Sn1@4, Sn11@7, Sn4@7, Sn5@8, Sn6@8

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | True | FAIL | bound tCycle=9000, tSat=4000, DFtarget=1000; assertion fired at t = 8320.0 s: Detritiation continuity violated: plant DF fell below the authorised target during changeover; diagnostic run (assertion as warning): min DF 843.2 at t = 9000 s over 0-20000 s |
| Sn7 | dafny | False | PASS | 6 verified, 0 errors |
| Sn8 | isabelle | False | PASS | Finished ADSController_Check |
| Sn9 | fdr | False | PASS | 21 assertions passed, 0 failed |
| Sn10 | gradle | False | PASS | 14 tests, 14 passed, 0 failed, 0 skipped |

## Stale evidence: ST2-initialBed
Change: ADSController.activeDryer default Dryer::BedA -> Dryer::BedB, propagated to the Dafny, Isabelle, CSP and Java artefacts  
Flagged by namespace/impact.py closure (unbounded): Sn10@2, Sn2@2, Sn3@2, Sn7@2, Sn8@2, Sn9@2, Sn1@3, Sn11@6, Sn4@6, Sn5@7, Sn6@7

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | False | PASS | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | dafny | True | PASS | 6 verified, 0 errors |
| Sn8 | isabelle | True | PASS | Finished ADSController_Check |
| Sn9 | fdr | True | PASS | 21 assertions passed, 0 failed |
| Sn10 | gradle | True | FAIL | 14 tests, 7 passed, 7 failed, 0 skipped |
