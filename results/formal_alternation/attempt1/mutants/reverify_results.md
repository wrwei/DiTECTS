# Re-verification results (2026-11-15T13:47:34+0000)

Condition: `mutants`  Repository: `<repo>`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| D1 | fault | dafny | FAIL | detected | 0.94 | PowerLoss during Changeover no longer enters FailSafe (controller stays in Changeover) |
| D2 | fault | dafny | FAIL | detected | 0.89 | Changeover takes the duty bed offline (new Dryer value NoBed) before the standby bed is live |
| D3 | fault | dafny | FAIL | detected | 0.9 | FailSafe is left on PowerLoss as well as BackupRestored |
| D4 | fault | dafny | FAIL | detected | 0.85 | requires mode == FailSafe removed from transitionFromFailSafe |
| D5 | fault | dafny | FAIL | detected | 0.89 | step() dispatches Changeover events to the NormalOperation handler |
| D6 | fault | dafny | FAIL | detected | 0.93 | ChangeoverComplete returns to NormalOperation without swapping the duty bed |
| DC1 | control | dafny | PASS | control passed | 0.88 | Add a true postcondition: DewpointHigh in NormalOperation leads to Changeover |
| DC2 | control | dafny | PASS | control passed | 0.81 | Swap the order of the two requires clauses of transitionFromNormalOperation and edit a comment |
| J1 | fault | gradle | FAIL | detected | 3.22 | PowerLoss during Changeover emits EnterFailSafe but the mode stays Changeover |
| J2 | fault | gradle | FAIL | detected | 3.1 | nextDryer(BedA) returns BedA: changeover never swaps the duty bed |
| J3 | fault | gradle | FAIL | detected | 3.19 | FailSafe is also left on DewpointHigh |
| J4 | fault | gradle | FAIL | detected | 3.11 | Duty bed is swapped when changeover starts (DewpointHigh) instead of when it completes |
| JC1 | control | gradle | PASS | control passed | 3.08 | Rename private field dryers -> dryerFunctions throughout ADSController |
| JC2 | control | gradle | PASS | control passed | 3.09 | Final "else if (currentMode == ADSMode.FailSafe)" replaced by plain "else" (enum has exactly three values, field never null) |
| F1 | fault | fdr | FAIL | detected | 0.93 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.71 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.75 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| F4 | fault | fdr | FAIL | detected | 0.72 | nextDryer always returns BedA: changeover never swaps the duty bed |
| FC1 | control | fdr | FAIL | false alarm | 0.74 | Swap the order of the two NormalOperation transitions ([] is commutative) |
| I1 | fault | isabelle | FAIL | detected | 36.42 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 36.77 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 35.48 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 32.32 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| I5 | fault | isabelle | FAIL | detected | 36.34 | ChangeoverToNormalOperation no longer updates activeDryer (the duty bed never alternates) |
| IC1 | control | isabelle | FAIL | false alarm | 36.58 | Edit the introduction text block |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 6/6 | 0 | 0 | 0 | 2/2 |
| fdr | 4/4 | 0 | 0 | 0 | 0/1 |
| gradle | 4/4 | 0 | 0 | 0 | 2/2 |
| isabelle | 5/5 | 0 | 0 | 0 | 0/1 |
| Total | 19/19 | 0 | 0 | 0 | 4/6 |
