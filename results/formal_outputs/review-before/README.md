# Review before the destination, bed-frame and command checks

Six candidate faults (`candidates.json`) were run against the formal models and Java implementation recorded in
`results/prior_formal_outputs/reverify_bound_thread.json` (`sources.artefactSHA256`). All six passed their checker:

| Candidate | Now | Checker | Fault |
|---|---|---|---|
| IX1 | I7 | Isabelle | NormalOperationToChangeover enters FailSafe |
| IX2 | I8 | Isabelle | Bed swapped when changeover starts as well as when it completes |
| IX3 | I9 | Isabelle | FailSafeToNormalOperation enters Changeover |
| FX1 | F5 | FDR | restoreNormal output removed |
| FX2 | F6 | FDR | raiseAlarm output removed |
| JX1 | J5 | Gradle | RaiseAlarm output removed |

`reverify_results.*` and `logs/` hold that run.
