# Re-verification results (2026-11-15T18:11:01+0000)

Condition: `baseline + mutants + stale (one run on all five targets after the offered-operations, trace-invariant and public-channel checks)`  Repository: `.`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn2 | ADS Changeover Transient_Modelica | modelica | PASS | 1.17 | bound tCycle=7000, tSat=4000, DFtarget=1000; simulation completed, assertion not fired; min DF 1390.2 at t = 7000 s over 0-20000 s |
| Sn7 | ADS Controller Proof - Dafny | dafny | PASS | 1.01 | 11 verified, 0 errors |
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 39.54 | Finished ADSController_Check |
| Sn9 | ADS Controller Refinement | fdr | PASS | 1.26 | 23 assertions passed, 0 failed |
| Sn10 | ADS Controller Implementation | gradle | PASS | 4.04 | 14 tests, 14 passed, 0 failed, 0 skipped |

## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| D1 | fault | dafny | FAIL | detected | 1.04 | PowerLoss during Changeover no longer enters FailSafe (controller stays in Changeover) |
| D2 | fault | dafny | FAIL | detected | 0.99 | Changeover takes the duty bed offline (new Dryer value NoBed) before the standby bed is live |
| D3 | fault | dafny | FAIL | detected | 0.96 | FailSafe is left on PowerLoss as well as BackupRestored |
| D4 | fault | dafny | FAIL | detected | 0.93 | requires mode == FailSafe removed from transitionFromFailSafe |
| D5 | fault | dafny | FAIL | detected | 0.96 | step() dispatches Changeover events to the NormalOperation handler |
| D6 | fault | dafny | FAIL | detected | 0.93 | ChangeoverComplete returns to NormalOperation without swapping the duty bed |
| DC1 | control | dafny | PASS | control passed | 0.97 | Add a true postcondition: DewpointHigh in NormalOperation leads to Changeover |
| DC2 | control | dafny | PASS | control passed | 0.91 | Swap the order of the two requires clauses of transitionFromNormalOperation and edit a comment |
| J1 | fault | gradle | FAIL | detected | 3.45 | PowerLoss during Changeover emits EnterFailSafe but the mode stays Changeover |
| J2 | fault | gradle | FAIL | detected | 3.21 | nextDryer(BedA) returns BedA: changeover never swaps the duty bed |
| J3 | fault | gradle | FAIL | detected | 3.28 | FailSafe is also left on DewpointHigh |
| J4 | fault | gradle | FAIL | detected | 3.28 | Duty bed is swapped when changeover starts (DewpointHigh) instead of when it completes |
| JC1 | control | gradle | PASS | control passed | 3.29 | Rename private field dryers -> dryerFunctions throughout ADSController |
| JC2 | control | gradle | PASS | control passed | 3.18 | Final "else if (currentMode == ADSMode.FailSafe)" replaced by plain "else" (enum has exactly three values, field never null) |
| F1 | fault | fdr | FAIL | detected | 0.92 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.72 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.72 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| F4 | fault | fdr | FAIL | detected | 0.71 | nextDryer always returns BedA: changeover never swaps the duty bed |
| FC1 | control | fdr | PASS | control passed | 0.77 | Swap the order of the two NormalOperation transitions ([] is commutative) |
| I1 | fault | isabelle | FAIL | detected | 38.17 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 36.98 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 37.68 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 37.89 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| I5 | fault | isabelle | FAIL | detected | 36.91 | ChangeoverToNormalOperation no longer updates activeDryer (the duty bed never alternates) |
| IC1 | control | isabelle | PASS | control passed | 37.51 | Edit the introduction text block |
| D7 | fault | dafny | FAIL | detected | 1.16 | DewpointHigh no longer starts a changeover |
| D8 | fault | dafny | FAIL | detected | 0.96 | BackupRestored no longer leaves FailSafe |
| D9 | fault | dafny | FAIL | detected | 0.96 | Duty bed changes before ChangeoverComplete |
| I6 | fault | isabelle | FAIL | detected | 36.87 | Remove both power-loss operations from the executable machine while retaining their definitions and the stored trigger set |
| I7 | fault | isabelle | FAIL | detected | 37.69 | NormalOperationToChangeover enters FailSafe (with the FailSafe trigger set) instead of Changeover |
| I8 | fault | isabelle | FAIL | detected | 37.23 | NormalOperationToChangeover swaps the duty bed when changeover starts (bed swaps twice per cycle) |
| I9 | fault | isabelle | FAIL | detected | 37.39 | FailSafeToNormalOperation enters Changeover (with the Changeover trigger set) instead of NormalOperation |
| F5 | fault | fdr | FAIL | detected | 1.35 | FailSafe exit no longer emits restoreNormal |
| F6 | fault | fdr | FAIL | detected | 0.81 | Dewpoint alarm no longer emits raiseAlarm |
| J5 | fault | gradle | FAIL | detected | 3.61 | Dewpoint alarm no longer emits RaiseAlarm |
| I10 | fault | isabelle | FAIL | detected | 38.13 | Startup (InitialToNormalOperation) is also enabled in FailSafe, so FailSafe can be left without backupRestored |
| I11 | fault | isabelle | FAIL | detected | 37.66 | Init records only powerLoss in the trace, with no state entry |
| F7 | fault | fdr | FAIL | detected | 1.21 | Startup performs raiseAlarm.in (an input on an output channel) before entering NormalOperation |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 9/9 | 0 | 0 | 0 | 2/2 |
| fdr | 7/7 | 0 | 0 | 0 | 1/1 |
| gradle | 5/5 | 0 | 0 | 0 | 2/2 |
| isabelle | 11/11 | 0 | 0 | 0 | 1/1 |
| Total | 32/32 | 0 | 0 | 0 | 6/6 |

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
