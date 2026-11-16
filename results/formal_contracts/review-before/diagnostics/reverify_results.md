# Re-verification results (2026-11-15T14:37:27+0000)

Condition: `mutants`  Repository: `<repo>`


## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| REVIEW_D_NO_START | fault | dafny | PASS | survived | 0.92 | DewpointHigh no longer starts a changeover |
| REVIEW_D_NO_RECOVERY | fault | dafny | PASS | survived | 0.96 | BackupRestored no longer leaves FailSafe |
| REVIEW_D_EARLY_SWAP | fault | dafny | PASS | survived | 0.95 | Duty bed changes before ChangeoverComplete |
| REVIEW_I_NO_POWERLOSS | fault | isabelle | PASS | survived | 30.8 | Remove both power-loss operations from the executable machine; keep R1/R3 and the unused operation lemmas |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| dafny | 0/3 | 3 | 0 | 0 | 0/0 |
| isabelle | 0/1 | 1 | 0 | 0 | 0/0 |
| Total | 0/4 | 4 | 0 | 0 | 0/0 |
