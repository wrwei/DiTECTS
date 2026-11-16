# Re-verification results (2026-11-15T18:54:46+0000)

Condition: `mutants`  Repository: `~/ads-experiments/review4-before-src`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| I12 | fault | isabelle | PASS | survived | 43.62 | The power-loss channel in NormalOperation runs the changeover operation (handler binding swapped in the executable operation list) |
| F8 | fault | fdr | PASS | survived | 1.3 | The composed module no longer emits enterFailSafe on entering FailSafe |
| F9 | fault | fdr | PASS | survived | 0.87 | The composed module writes the current bed instead of the other bed on changeover completion |
| F10 | fault | fdr | PASS | survived | 0.91 | The controller no longer emits enterFailSafe on entering FailSafe |
| F11 | fault | fdr | PASS | survived | 0.99 | The controller writes the current bed instead of the other bed on changeover completion |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| fdr | 0/4 | 4 | 0 | 0 | 0/0 |
| isabelle | 0/1 | 1 | 0 | 0 | 0/0 |
| Total | 0/5 | 5 | 0 | 0 | 0/0 |
