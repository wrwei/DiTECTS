# Re-verification results (2026-11-15T18:11:50+0000)

Condition: `mutants`  Repository: `<repo>`


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
