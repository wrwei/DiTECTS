# Bed-alternation correction (15 November 2026)

## Defects found by review of the formal models
1. CSP (`formal/csp/instantiations.csp`, and the unchecked timed copy): `nextDryer(current) = Dryer_BedA`, so the
   RoboChart action `activeDryer := nextDryer(activeDryer)` never changed bed.
2. Dafny (`formal/dafny/ADSController.dfy`): `ChangeoverComplete` returned to NormalOperation without updating `activeDryer`.
3. Isabelle (`formal/isabelle/ADSController_Beh.thy`): `nextDryer` was declared (`consts`) but unused;
   `ChangeoverToNormalOperation` did not update `activeDryer`. No property stated that power loss is accepted
   in NormalOperation and Changeover.
4. SysML (`models/sysml/02-design.sysml`, `ADSOperation`): no Changeover-to-FailSafe power-loss transition;
   `changeover_complete` had no trigger and no bed-swap effect.
5. Dafny `Valid()` and Isabelle R2 hold by construction for the two-valued bed type; they are retained because
   they reject type extensions (faults D2, I2), and their captions say so.

## Corrections
- Dafny: `function nextDryer`, lemma `NextDryerSwitchesBed`, `activeDryer := nextDryer(activeDryer)` on
  ChangeoverComplete, postconditions on `transitionFromChangeover` and `step`.
- Isabelle: `definition nextDryer` (`[z_defs]`), lemma `nextDryer_switches_bed`, update
  `activeDryer' = nextDryer activeDryer` in `ChangeoverToNormalOperation`, property R3 with seven lemmas, Hoare
  triple `ChangeoverToNormalOperation_alternates`. Template FORK comments removed.
- CSP: `nextDryer` corrected; traces refinement `ADS_AlternationStart [T= ADS_AlternationView` (first write may
  name either bed, each later write the other bed); component-level processes composed with
  `[| {|set_EXT_activeDryer|} |] SKIP` (no external writer of the shared variable, as in the module).
- SysML: `changeover_to_failsafe`, `accept when changeoverComplete do swapDutyBed`, action `swapDutyBed`.
- Mutants: D6, I5, F4 added (each removes the bed swap, mirroring J2): 19 faults, 6 controls.

## Results (one run, `results/formal_alternation/`)
| Item | Before | After |
|---|---|---|
| Sn7 Dafny baseline | 6 verified, 1.11 s | 9 verified, 0 errors, 0.94 s |
| Sn8 Isabelle baseline | pass, 41.77 s | pass, 39.25 s |
| Sn9 FDR baseline | 21/21, 0.88 s | 22 assertions passed, 0 failed, 1.44 s |
| Sn10 Gradle baseline | 14/14, 4.15 s | 14 tests, 14 passed, 0 failed, 0 skipped, 4.01 s |
| Sn2 OpenModelica baseline | pass, 1.26 s | pass, 0.99 s |
| Faults detected | 16/16 | 19/19 |
| Controls passed | 6/6 | 6/6 |
| ST1 / ST2 verdicts | unchanged | unchanged |

First attempt (`results/formal_alternation/attempt1/`): Isabelle R2 preservation for
`ChangeoverToNormalOperation` failed (definition not unfolded); FDR 18/22 (component-level determinism with an
external writer). Both were fixed as above before the reported run.

## Manual-search baseline (SysML text changed)
Recall unchanged (EXACT 79%, LENIENT 88%; 2,035 and 2,255 searches). Reading time 27-43 min (was 27-42);
thread review 0.50-0.73 h, 30-44 min (was 0.49-0.72 h, 29-43 min). Recorded as protocol amendment A3.

## Follow-up contract review (15 November 2026)

The review of commit `dcb1627` found four further faulty variants that still passed: ignoring a dewpoint
alarm, ignoring backup restoration, changing bed before completion, and removing both power-loss
operations from the Isabelle machine. The review outputs and source hashes are retained in
`results/formal_contracts/review-before/`; these faults are now D7--D9 and I6.

- Dafny specifies the complete mode/input table and preserves the bed outside changeover completion.
  The correct source verifies 11 obligations; all three new faulty variants fail postconditions.
- Isabelle separates the event vocabulary from the executable operation list. The machine and its
  input-acceptance proof use that same list. R3 checks the offered inputs; `InputsAgree` connects the
  stored trigger set to them. Two further Hoare triples check the power-loss destination, trace and
  bed preservation. I6 remains a well-formed theory and fails the input-acceptance proof in Docker.
- The CSP alternation protocol uses failures-divergences refinement, retains controller inputs, and
  checks the first swap against the initial bed as well as later swaps. All model memories and the
  protocol share `ADS_InitialBed`; the initial-bed scenario changes that one parameter.
- The timed CSP suite previously failed four determinism and three timelock assertions. Its checked
  interfaces now exclude external bed writers and hide the internal memory writes that are consumed
  without delay. All 30 original assertions are retained and pass. No restart deadline was added.
- Comments in the models distinguish valid selector values and simulated DF from physical availability.

One complete run in `results/formal_contracts/` passes all five baselines, detects all 23 selected faults
and passes all six controls. Both change scenarios keep their previous outcomes: the longer period fails
the DF assertion; changing the initial bed fails seven Java tests with the old expectation.
The prior 19-fault result is in `results/prior_formal_contracts/`. The new total includes faults exposed
by review and is not an independent performance estimate.

The CSP property checks pass 35 assertions for each initial bed. They reject a wrong first write,
a missing completion response, an early write and a write without completion. The missing-write example
offers all other legal inputs, so its failure identifies the absent write. The separate timed suite
passes 30 assertions. Raw outputs and source hashes are in `results/formal_contracts/csp-checks.json`.
All 17 regression tests pass; the old hard-coded expectation of 26 CSP assertions has been removed.

The manual-search procedure is unchanged (amendment A4). Recall, searches and per-round counts are
unchanged: 105/133 with exact matching and 117/133 with lenient matching, using 2,035 and 2,255 searches.
Longer formal definitions increase estimated reading time to 29--46 minutes and thread review to
32--47 minutes; total estimates are 1.1--5.1 and 1.4--5.7 hours respectively. The manual-search figure
uses unchanged counts. The demonstration is refreshed from the revised sources; its own index has
547 elements and reports 86 of 370 phase-placed elements linked (23%). The identity space remains
134 elements and 216 edges.

## Second review: destinations, bed frame and output commands (15 November 2026)

Six candidate faults passed the 23-fault suite (`results/formal_outputs/review-before/`):

| Candidate | Now | Fault | Why it passed |
|---|---|---|---|
| IX1 | I7 | NormalOperationToChangeover enters FailSafe | Isabelle had destination lemmas only for the power-loss operations |
| IX2 | I8 | Bed also swapped at changeover start | Isabelle constrained `activeDryer` only on changeover completion |
| IX3 | I9 | FailSafeToNormalOperation enters Changeover | as IX1 |
| FX1 | F5 | `restoreNormal` removed | both CSP views hid output commands |
| FX2 | F6 | `raiseAlarm` removed | as FX1 |
| JX1 | J5 | `RaiseAlarm` removed | the Java test checked only the last command |

Corrections: Isabelle destination lemmas for InitialToNormalOperation, NormalOperationToChangeover,
ChangeoverToNormalOperation and FailSafeToNormalOperation (destination mode, recorded trace with output
commands, bed); CSP command protocol `ADS_CommandNormal [FD= ADS_CommandView` (23 assertions); Java
`Actuator.history()` and a command-sequence assertion in `dewpointHighStartsChangeover` (still 14 tests).

One run (`results/formal_outputs/`): all five baselines pass (Dafny 11 verified, Isabelle finished, FDR 23/23,
Gradle 14/14, OpenModelica pass), 29/29 faults detected, 6/6 controls pass, both scenarios unchanged; all
17 regression tests pass on the host (`results/formal_outputs/regression-tests.txt`); an 18th, added afterwards
for the recorded I7-I9, F5, F6 and J5 results, needs no checker and passes. The previous combined
result is in `results/prior_formal_outputs/`. These faults were exposed by review; the total is not an
independent estimate.

Manual search (amendment A5): recall and search counts unchanged (105/133 and 117/133; 2,035 and 2,255
searches); the exact-match per-round curve for `dryerA` changes at rounds 2 and 3 (17 to 18, 47 to 48).
Totals 1.13-5.08 h (exact) and 1.38-5.75 h (lenient); reading
30-47 min; thread review 0.55-0.8 h (33-48 min).

The demonstration is refreshed from the revised sources; its index now has 551 elements (four Isabelle
lemmas added) and reports 86 of 374 phase-placed elements linked (23%). The identity space remains 134
elements and 216 edges.

## Third review: offered operations, trace invariant and public channels (15 November 2026)

Three faults passed the 29-fault suite at `d59c19c` (`results/formal_interface/review-before/`):

| Fault | Checker | Why it passed |
|---|---|---|
| I10: startup also enabled in FailSafe | Isabelle | the accepted-input mapping excluded startup, so recovery without `backupRestored` went unnoticed |
| I11: initial trace holds only `powerLoss` | Isabelle | the invariant required only a non-empty trace |
| F7: `raiseAlarm.in` before startup | FDR | the command view hid input-direction events on output channels |

Corrections: lemma `ADSController_offered_by_mode` fixes the operations offered in each mode; the invariant is
`wf_rcstore tr st None` (the invariant proofs add `nth_append`); `ADS_CommandEvents` is the set of all eight
public channels, so both directions stay visible. A first proof attempt left an exhaustiveness goal in the
new lemma and did not unfold list indexing in five invariant proofs; both were fixed before the reported run.

One run (`results/formal_interface/`): all five baselines pass (Dafny 11 verified, Isabelle finished, FDR
23/23, Gradle 14/14, OpenModelica pass), 32/32 faults detected (Isabelle 11/11, FDR 7/7), 6/6 controls pass,
both scenarios unchanged. In the host run, one regression test failed on three subtests (I7-I9) because it
mapped line numbers recorded on the previous theory; the other 17 tests passed. With this run deposited, a host run of
the patched suite passed all 18 tests (`results/formal_interface/regression-tests-patched.txt`).

Manual search (amendment A6): recall, searches and per-round counts unchanged. Totals 1.13-5.09 h
(exact) and 1.39-5.76 h (lenient); reading 30-48 min; thread review 0.56-0.81 h
(34-49 min).

The demonstration is refreshed again; its index has 552 elements (one Isabelle lemma added) and reports
86 of 375 phase-placed elements linked (23%). The identity space remains 134 elements and 216 edges.

## Fourth review: handler targets and per-copy protocols (15 November 2026)

Five faults passed the 32-fault suite at `054a6d9` (`results/formal_handlers/review-before/`):

| Fault | Checker | Why it passed |
|---|---|---|
| I12: power-loss channel in NormalOperation runs the changeover operation | Isabelle | the response lemmas covered the operations, not the operation run for each event |
| F8: composed module no longer emits enterFailSafe | FDR | the command protocol checked only the standalone state machine |
| F9: composed module never swaps the bed | FDR | the bed protocol checked only the standalone state machine |
| F10: controller no longer emits enterFailSafe | FDR | as F8 |
| F11: controller never swaps the bed | FDR | as F9 |

Corrections: function `ADSController_channel_target` and lemma `ADSController_handler_targets` (for every
offered event, every return state has the channel's target mode); the command and bed protocols for
`ADSController_Module` and `ADSController_Ctrl`, each on that copy's public channels and bed write (27
assertions). The handler-lemma proof was chosen by building candidate proof methods in separate scratch
sessions: of the variants whose outcome was seen, T1-T5 failed and T10 proved; T6-T9 were stopped by the
build time limit before finishing. Only T10 is in the deposited theory.

One run (`results/formal_handlers/`): all five baselines pass (Dafny 11 verified, Isabelle finished, FDR
27/27, Gradle 14/14, OpenModelica pass), 37/37 faults detected (Isabelle 12/12, FDR 11/11), 6/6 controls pass,
both scenarios unchanged. F3-F7 edit all three copies and now also fail the module and controller protocols.
In that host run, the recorded-result checks failed on line numbers and counts recorded on the previous
theory and suite; with this run deposited, a host run of the patched suite passed all 18 tests
(`results/formal_handlers/regression-tests-patched.txt`).

Manual search (amendment A7): recall, searches and per-round counts unchanged. Totals 1.16-5.12 h
(exact) and 1.41-5.8 h (lenient); reading 32-50 min; thread review 0.58-0.84 h
(35-50 min).

The demonstration is refreshed again; its index has 554 elements (the Isabelle channel table and handler
lemma added) and reports 86 of 377 phase-placed elements linked (23%). The identity space remains 134
elements and 216 edges.
