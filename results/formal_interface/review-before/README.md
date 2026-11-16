# Review before the offered-operations, trace-invariant and public-channel checks

Three faults (`candidates.json`, now I10, I11 and F7) were run against the pushed revision `d59c19c`.
All three passed their checker:

| Fault | Checker | Why it passed |
|---|---|---|
| I10: startup also enabled in FailSafe | Isabelle | the accepted-input mapping excluded the startup operation |
| I11: initial trace holds only `powerLoss` | Isabelle | the state invariant required only a non-empty trace |
| F7: `raiseAlarm.in` before startup | FDR | the command view hid input-direction events on output channels |

`reverify_results.*` and `logs/` hold that run.
