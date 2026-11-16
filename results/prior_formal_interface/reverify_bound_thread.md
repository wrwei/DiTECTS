# Re-verification results (2026-11-15T16:25:03+0000)

Condition: `baseline + mutants + stale (one run on all five targets after the destination, bed-frame and command checks)`  Repository: `.`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.76 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.09 | 11 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 37.19 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 1.32 | 23 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 3.65 | 14 tests, 14 passed, 0 failed, 0 skipped |

## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| D1 | fault | dafny | FAIL | detected | 1.12 | PowerLoss during Changeover no longer enters FailSafe (controller stays in Changeover) |
| D2 | fault | dafny | FAIL | detected | 0.96 | Changeover takes the duty bed offline (new Dryer value NoBed) before the standby bed is live |
| D3 | fault | dafny | FAIL | detected | 0.91 | FailSafe is left on PowerLoss as well as BackupRestored |
| D4 | fault | dafny | FAIL | detected | 0.99 | requires mode == FailSafe removed from transitionFromFailSafe |
| D5 | fault | dafny | FAIL | detected | 0.98 | step() dispatches Changeover events to the NormalOperation handler |
| D6 | fault | dafny | FAIL | detected | 0.96 | ChangeoverComplete returns to NormalOperation without swapping the duty bed |
| DC1 | control | dafny | PASS | control passed | 0.96 | Add a true postcondition: DewpointHigh in NormalOperation leads to Changeover |
| DC2 | control | dafny | PASS | control passed | 0.98 | Swap the order of the two requires clauses of transitionFromNormalOperation and edit a comment |
| J1 | fault | gradle | FAIL | detected | 4.73 | PowerLoss during Changeover emits EnterFailSafe but the mode stays Changeover |
| J2 | fault | gradle | FAIL | detected | 3.58 | nextDryer(BedA) returns BedA: changeover never swaps the duty bed |
| J3 | fault | gradle | FAIL | detected | 3.29 | FailSafe is also left on DewpointHigh |
| J4 | fault | gradle | FAIL | detected | 3.32 | Duty bed is swapped when changeover starts (DewpointHigh) instead of when it completes |
| JC1 | control | gradle | PASS | control passed | 3.33 | Rename private field dryers -> dryerFunctions throughout ADSController |
| JC2 | control | gradle | PASS | control passed | 3.22 | Final "else if (currentMode == ADSMode.FailSafe)" replaced by plain "else" (enum has exactly three values, field never null) |
| F1 | fault | fdr | FAIL | detected | 1.04 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.75 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.75 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| F4 | fault | fdr | FAIL | detected | 0.72 | nextDryer always returns BedA: changeover never swaps the duty bed |
| FC1 | control | fdr | PASS | control passed | 0.78 | Swap the order of the two NormalOperation transitions ([] is commutative) |
| I1 | fault | isabelle | FAIL | detected | 44.82 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 43.23 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 42.4 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 39.62 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| I5 | fault | isabelle | FAIL | detected | 41.45 | ChangeoverToNormalOperation no longer updates activeDryer (the duty bed never alternates) |
| IC1 | control | isabelle | PASS | control passed | 43.59 | Edit the introduction text block |
| D7 | fault | dafny | FAIL | detected | 1.23 | DewpointHigh no longer starts a changeover |
| D8 | fault | dafny | FAIL | detected | 1.0 | BackupRestored no longer leaves FailSafe |
| D9 | fault | dafny | FAIL | detected | 0.97 | Duty bed changes before ChangeoverComplete |
| I6 | fault | isabelle | FAIL | detected | 37.06 | Remove both power-loss operations from the executable machine while retaining their definitions and the stored trigger set |
| I7 | fault | isabelle | FAIL | detected | 39.99 | NormalOperationToChangeover enters FailSafe (with the FailSafe trigger set) instead of Changeover |
| I8 | fault | isabelle | FAIL | detected | 38.7 | NormalOperationToChangeover swaps the duty bed when changeover starts (bed swaps twice per cycle) |
| I9 | fault | isabelle | FAIL | detected | 38.73 | FailSafeToNormalOperation enters Changeover (with the Changeover trigger set) instead of NormalOperation |
| F5 | fault | fdr | FAIL | detected | 2.28 | FailSafe exit no longer emits restoreNormal |
| F6 | fault | fdr | FAIL | detected | 0.81 | Dewpoint alarm no longer emits raiseAlarm |
| J5 | fault | gradle | FAIL | detected | 5.67 | Dewpoint alarm no longer emits RaiseAlarm |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 9/9 | 0 | 0 | 0 | 2/2 |
| fdr | 6/6 | 0 | 0 | 0 | 1/1 |
| gradle | 5/5 | 0 | 0 | 0 | 2/2 |
| isabelle | 9/9 | 0 | 0 | 0 | 1/1 |
| Total | 29/29 | 0 | 0 | 0 | 6/6 |

## Stale evidence: ST1-tCycle
Change: ADSController::changeoverPeriod 7000 s -> 9000 s (SysML design attribute), propagated to ADSChangeover.tCycle through the sim-binding  
Flagged by namespace/impact.py closure (unbounded): Sn10@3, Sn2@3, Sn3@3, Sn7@3, Sn8@3, Sn9@3, Sn1@4, Sn11@7, Sn4@7, Sn5@8, Sn6@8

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | True | FAIL | bound tCycle=9000, tSat=4000, DFtarget=1000; assertion fired at t = 8320.0 s: Detritiation continuity violated: plant DF fell below the authorised target during changeover; diagnostic run (assertion as warning): min DF 843.2 at t = 9000 s over 0-20000 s |
| Sn7 | dafny | False | PASS | 11 verified, 0 errors |
| Sn8 | isabelle | False | PASS | Finished ADSController_Check |
| Sn9 | fdr | False | PASS | 23 assertions passed, 0 failed |
| Sn10 | gradle | False | PASS | 14 tests, 14 passed, 0 failed, 0 skipped |

## Stale evidence: ST2-initialBed
Change: ADSController.activeDryer default Dryer::BedA -> Dryer::BedB, propagated to the Dafny, Isabelle, CSP and Java artefacts  
Flagged by namespace/impact.py closure (unbounded): Sn10@2, Sn2@2, Sn3@2, Sn7@2, Sn8@2, Sn9@2, Sn1@3, Sn11@6, Sn4@6, Sn5@7, Sn6@7

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn2 | modelica | False | PASS | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | dafny | True | PASS | 11 verified, 0 errors |
| Sn8 | isabelle | True | PASS | Finished ADSController_Check |
| Sn9 | fdr | True | PASS | 23 assertions passed, 0 failed |
| Sn10 | gradle | True | FAIL | 14 tests, 7 passed, 7 failed, 0 skipped |
