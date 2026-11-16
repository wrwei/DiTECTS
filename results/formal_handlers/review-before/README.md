# Review before the handler-target lemma and the module and controller protocols

Five faults (`candidates.json`, now I12 and F8-F11) were run against the pushed revision `054a6d9`.
All five passed their checker:

| Fault | Checker | Why it passed |
|---|---|---|
| I12: power-loss channel in NormalOperation runs the changeover operation | Isabelle | the response lemmas covered the operations, not the operation the machine runs for each event |
| F8: composed module no longer emits enterFailSafe | FDR | the command protocol checked only the standalone state machine |
| F9: composed module never swaps the bed | FDR | the bed protocol checked only the standalone state machine |
| F10: controller no longer emits enterFailSafe | FDR | as F8 |
| F11: controller never swaps the bed | FDR | as F9 |

`reverify_results.*` and `logs/` hold that run.
