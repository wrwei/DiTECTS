# Re-verification results (2026-11-15T16:04:59+0000)

Condition: `mutants`  Repository: `<repo>`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| IX1 | fault | isabelle | PASS | survived | 50.13 | NormalOperationToChangeover enters FailSafe (with the FailSafe trigger set) instead of Changeover |
| IX2 | fault | isabelle | PASS | survived | 46.51 | NormalOperationToChangeover swaps the duty bed when changeover starts (bed swaps twice per cycle) |
| IX3 | fault | isabelle | PASS | survived | 40.93 | FailSafeToNormalOperation enters Changeover (with the Changeover trigger set) instead of NormalOperation |
| FX1 | fault | fdr | PASS | survived | 1.39 | FailSafe exit no longer emits restoreNormal |
| FX2 | fault | fdr | PASS | survived | 0.81 | Dewpoint alarm no longer emits raiseAlarm |
| JX1 | fault | gradle | PASS | survived | 4.09 | Dewpoint alarm no longer emits RaiseAlarm |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| fdr | 0/2 | 2 | 0 | 0 | 0/0 |
| gradle | 0/1 | 1 | 0 | 0 | 0/0 |
| isabelle | 0/3 | 3 | 0 | 0 | 0/0 |
| Total | 0/6 | 6 | 0 | 0 | 0/0 |
