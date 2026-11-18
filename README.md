# DiTECTS: ADS case-study models, tools and results

The engineering models of the abstracted Atmosphere Detritiation System (ADS) used in the article
*Digital-thread-centric engineering of safety-critical systems from requirements to digital twin*.
The ADS removes tritiated water vapour from a glovebox atmosphere; two molecular-sieve beds alternate, the
duty bed drying the gas whilst the standby bed is regenerated.

Eleven models cover the system across the nine phases of a V-model lifecycle. A completion overlay records
the typed links added after export, and the digital twin maps a plant mesh to the design.

## Models

| Lifecycle phase | Model | Files | Primary elements |
|---|---|---|---|
| Requirements analysis | SysML requirements | `models/sysml/01-requirements.sysml` | 15 requirements (SysML v2 textual notation), e.g. `REQ-TRIT-014` discharge limit, `REQ-ADS-001` DF >= 1000, `REQ-ADS-005` bed capacity, `REQ-ADS-007` loss-of-power response |
| System design | SysML design | `models/sysml/02-design.sysml` | 10 part definitions, the `ads` composition, the controller state machine (NormalOperation, Changeover, FailSafe), 17 `satisfy` statements |
| System design | Fault tree | `models/fta/ads-fta.json` | Top event `TE-01` (tritium discharge exceeds the authorised limit), AND/OR gates, basic events |
| Sub-system design | FMEDA | `models/fmeda/ads-fmeda.json` | 17 rows, 14 safety-related, with safety mechanisms and diagnostic coverage |
| Module design | RoboChart controller (CSP) | `formal/csp/` | Generated CSP with untimed and timed assertion suites, checked with FDR4 |
| Implementation | Java controller and tests | `implementation/java/` | Controller implementation and 14 JUnit tests (Gradle) |
| Module verification | Dafny proofs | `formal/dafny/ADSController.dfy` | Transition contracts for every mode/input combination, bed selection and alternation |
| Module verification | Isabelle/HOL proofs | `formal/isabelle/` | Controller theory: enabled inputs, operation destinations, recorded commands and bed, deadlock freedom |
| Integration verification | Modelica changeover simulation | `simulation/modelica/ADSChangeover.mo` | Simplified decontamination-factor trajectory with the assertion `DF >= DFtarget` |
| System verification | Digital twin | `models/digital-twin/` | Plant mesh, 10 part mappings to design parts, 4 telemetry signals bound to design attributes |
| Acceptance | GSN safety case | `models/safety-case/gsn-safety-case.json` | 26 nodes; top claim G1 addresses `REQ-TRIT-014`; Solutions Sn7–Sn10 cite the controller evidence |

`models/sysml/omg/` holds the two SysML models in OMG interchange JSON, as exported by the modelling
platform. `models/traceability/completion.json` holds the links and records authored after export to
complete the thread, each with a rationale. All were accepted in engineering review on 17 November 2026;
the completed review sheet is `models/traceability/engineering-review-2026-11-17.xlsx`.

## Checking the executable models

| Model | Checker used in the article | Command |
|---|---|---|
| Dafny | Dafny 4.11.0 | `dafny verify formal/dafny/ADSController.dfy` |
| Isabelle/HOL | Isabelle2023 with the Z_Machines session (CyPhyAssure) | `isabelle build -D formal/isabelle` |
| CSP | FDR 4.2.7 | `refines formal/csp/file_robochart_controller_coreassertions.csp` (and `formal/csp/timed/`, `formal/csp/tests/`) |
| Java | Gradle 9.0.0, JUnit 5.11.4, OpenJDK 21 | `cd implementation/java && gradle test` |
| Modelica | OpenModelica 1.26.9 | `simulate(ADSChangeover)` over the model's experiment annotation |

## Identity space, tools and results

| Path | Contents |
|---|---|
| `namespace/ads-namespace.json` | Element identity space: 134 elements and 217 edges derived from the models and the completion overlay |
| `namespace/impact.py` | Change-impact traversal over the identity space (`python3 namespace/impact.py dryerA --stats`) |
| `tools/coverage.py` | Coverage checks over the identity space (`--export <dir>` checks the export-only thread) |
| `tools/manual_trace.py`, `tools/manual_time.py` | Name-search comparison with the traversal and its time estimate |
| `tools/reverify.py`, `tools/c3/` | Evidence re-verification: baseline, 37 seeded faults and 6 controls, change scenarios, traversal latency |
| `tools/derive_from_export.py`, `tools/sim_bindings.py` | Derivation of the views and identity space from the platform's project export; simulation value bindings |
| `results/` | Recorded outputs of the tools above, with change logs |
| `studies/manual-impact/` | Protocol, participant materials, recording sheet and scorer for a timed manual change-impact study |
| `tests/` | Unit and regression tests (`python3 -m pytest tests`) |

All tools use the Python 3 standard library. `tools/reverify.py` additionally calls the checkers listed above;
`tests/test_csp_powerloss.py` needs a licensed FDR installation. The platform's project export used by
`tools/derive_from_export.py` is not included. The static demonstration of the platform's project viewers is
not included in this repository.

```
python3 namespace/impact.py dryerA --stats            # impact of a change to the duty dryer bed
python3 tools/coverage.py                              # coverage of the completed thread
python3 tools/manual_trace.py                          # rewrites results/manual_vs_thread.{json,md}; deterministic
python3 tools/manual_time.py                           # -> results/manual_time.json
python3 tools/reverify.py links                        # Solution -> evidence -> checker
python3 tools/reverify.py baseline                     # unmodified artefacts
python3 tools/reverify.py mutants                      # tools/c3/mutants.json
python3 tools/reverify.py stale                        # tools/c3/stale.json
python3 tools/reverify.py latency --reps 30
python3 studies/manual-impact/score.py --self-test
```

The protocol section of `results/manual_vs_thread.md` was fixed before the first run and is hashed in
`results/manual_vs_thread.json`; it is left unchanged here. Where it refers to the twin mesh under `demo/` and to
the twin model as not deposited, the mesh is `models/digital-twin/ads-digital-twin-plant.glb` (byte-identical)
and the twin model is `models/digital-twin/ads-digital-twin.json`, which the name-search procedure does not read.

## Detecting changes to static evidence

`tools/change_detect.py --before <rev> --after <rev>` compares every identified element record under
`models/` between two revisions and runs `namespace/impact.py` from each changed element, listing the
Solutions reached and whether any of their evidence can be re-run. `results/change_fmeda_row11.{json,md}`
applies it to the reclassification of FMEDA row 11 (`e52552d^` to `e52552d`).

## Licence

This repository accompanies a manuscript under peer review and is provided under the
[DiTECTS Reviewer Evaluation Licence](LICENSE): editors and referees may download, build, run and inspect it
for the review only. The RoboChart CSP semantic libraries keep their EPL-2.0 licence ([NOTICE](NOTICE)).
