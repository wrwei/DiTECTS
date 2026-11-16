# Re-verification results (2026-11-15T20:26:16+0000)

Condition: `mutants`  Repository: `<repo>`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| D1 | fault | dafny | FAIL | detected | 1.12 | PowerLoss during Changeover no longer enters FailSafe (controller stays in Changeover) |
| D2 | fault | dafny | FAIL | detected | 0.98 | Changeover takes the duty bed offline (new Dryer value NoBed) before the standby bed is live |
| D3 | fault | dafny | FAIL | detected | 1.0 | FailSafe is left on PowerLoss as well as BackupRestored |
| D4 | fault | dafny | FAIL | detected | 0.99 | requires mode == FailSafe removed from transitionFromFailSafe |
| D5 | fault | dafny | FAIL | detected | 1.0 | step() dispatches Changeover events to the NormalOperation handler |
| D6 | fault | dafny | FAIL | detected | 0.93 | ChangeoverComplete returns to NormalOperation without swapping the duty bed |
| DC1 | control | dafny | PASS | control passed | 0.9 | Add a true postcondition: DewpointHigh in NormalOperation leads to Changeover |
| DC2 | control | dafny | PASS | control passed | 0.92 | Swap the order of the two requires clauses of transitionFromNormalOperation and edit a comment |
| J1 | fault | gradle | FAIL | detected | 3.4 | PowerLoss during Changeover emits EnterFailSafe but the mode stays Changeover |
| J2 | fault | gradle | FAIL | detected | 3.16 | nextDryer(BedA) returns BedA: changeover never swaps the duty bed |
| J3 | fault | gradle | FAIL | detected | 3.39 | FailSafe is also left on DewpointHigh |
| J4 | fault | gradle | FAIL | detected | 3.42 | Duty bed is swapped when changeover starts (DewpointHigh) instead of when it completes |
| JC1 | control | gradle | PASS | control passed | 3.13 | Rename private field dryers -> dryerFunctions throughout ADSController |
| JC2 | control | gradle | PASS | control passed | 3.07 | Final "else if (currentMode == ADSMode.FailSafe)" replaced by plain "else" (enum has exactly three values, field never null) |
| F1 | fault | fdr | FAIL | detected | 0.97 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.87 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.83 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| F4 | fault | fdr | FAIL | detected | 0.78 | nextDryer always returns BedA: changeover never swaps the duty bed |
| FC1 | control | fdr | PASS | control passed | 0.8 | Swap the order of the two NormalOperation transitions ([] is commutative) |
| I1 | fault | isabelle | FAIL | detected | 51.86 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 49.51 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 48.78 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 42.38 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| I5 | fault | isabelle | FAIL | detected | 47.29 | ChangeoverToNormalOperation no longer updates activeDryer (the duty bed never alternates) |
| IC1 | control | isabelle | PASS | control passed | 46.99 | Edit the introduction text block |
| D7 | fault | dafny | FAIL | detected | 1.29 | DewpointHigh no longer starts a changeover |
| D8 | fault | dafny | FAIL | detected | 1.0 | BackupRestored no longer leaves FailSafe |
| D9 | fault | dafny | FAIL | detected | 1.01 | Duty bed changes before ChangeoverComplete |
| I6 | fault | isabelle | FAIL | detected | 40.64 | Remove both power-loss operations from the executable machine while retaining their definitions and the stored trigger set |
| I7 | fault | isabelle | FAIL | detected | 55.79 | NormalOperationToChangeover enters FailSafe (with the FailSafe trigger set) instead of Changeover |
| I8 | fault | isabelle | FAIL | detected | 47.67 | NormalOperationToChangeover swaps the duty bed when changeover starts (bed swaps twice per cycle) |
| I9 | fault | isabelle | FAIL | detected | 47.63 | FailSafeToNormalOperation enters Changeover (with the Changeover trigger set) instead of NormalOperation |
| F5 | fault | fdr | FAIL | detected | 2.17 | FailSafe exit no longer emits restoreNormal |
| F6 | fault | fdr | FAIL | detected | 0.91 | Dewpoint alarm no longer emits raiseAlarm |
| J5 | fault | gradle | FAIL | detected | 3.92 | Dewpoint alarm no longer emits RaiseAlarm |
| I10 | fault | isabelle | FAIL | detected | 53.22 | Startup (InitialToNormalOperation) is also enabled in FailSafe, so FailSafe can be left without backupRestored |
| I11 | fault | isabelle | FAIL | detected | 50.68 | Init records only powerLoss in the trace, with no state entry |
| F7 | fault | fdr | FAIL | detected | 2.25 | Startup performs raiseAlarm.in (an input on an output channel) before entering NormalOperation |
| I12 | fault | isabelle | FAIL | detected | 49.43 | The power-loss channel in NormalOperation runs the changeover operation (handler binding swapped in the executable operation list) |
| F8 | fault | fdr | FAIL | detected | 1.25 | The composed module no longer emits enterFailSafe on entering FailSafe |
| F9 | fault | fdr | FAIL | detected | 0.86 | The composed module writes the current bed instead of the other bed on changeover completion |
| F10 | fault | fdr | FAIL | detected | 0.88 | The controller no longer emits enterFailSafe on entering FailSafe |
| F11 | fault | fdr | FAIL | detected | 0.82 | The controller writes the current bed instead of the other bed on changeover completion |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 9/9 | 0 | 0 | 0 | 2/2 |
| fdr | 11/11 | 0 | 0 | 0 | 1/1 |
| gradle | 5/5 | 0 | 0 | 0 | 2/2 |
| isabelle | 12/12 | 0 | 0 | 0 | 1/1 |
| Total | 37/37 | 0 | 0 | 0 | 6/6 |
