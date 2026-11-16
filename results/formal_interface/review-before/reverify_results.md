# Re-verification results (2026-11-15T18:07:27+0000)

Condition: `mutants`  Repository: `~/ads-experiments/review3-before-src`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| I10 | fault | isabelle | PASS | survived | 38.5 | Startup (InitialToNormalOperation) is also enabled in FailSafe, so FailSafe can be left without backupRestored |
| I11 | fault | isabelle | PASS | survived | 38.54 | Init records only powerLoss in the trace, with no state entry |
| F7 | fault | fdr | PASS | survived | 1.21 | Startup performs raiseAlarm.in (an input on an output channel) before entering NormalOperation |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| fdr | 0/1 | 1 | 0 | 0 | 0/0 |
| isabelle | 0/2 | 2 | 0 | 0 | 0/0 |
| Total | 0/3 | 3 | 0 | 0 | 0/0 |
