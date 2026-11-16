# DiTECTS: ADS case-study models

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
| Sub-system design | FMEDA | `models/fmeda/ads-fmeda.json` | 17 rows, 13 safety-related, with safety mechanisms and diagnostic coverage |
| Module design | RoboChart controller (CSP) | `formal/csp/` | Generated CSP with untimed and timed assertion suites, checked with FDR4 |
| Implementation | Java controller and tests | `implementation/java/` | Controller implementation and 14 JUnit tests (Gradle) |
| Module verification | Dafny proofs | `formal/dafny/ADSController.dfy` | Transition contracts for every mode/input combination, bed selection and alternation |
| Module verification | Isabelle/HOL proofs | `formal/isabelle/` | Controller theory: enabled inputs, operation destinations, recorded commands and bed, deadlock freedom |
| Integration verification | Modelica changeover simulation | `simulation/modelica/ADSChangeover.mo` | Simplified decontamination-factor trajectory with the assertion `DF >= DFtarget` |
| System verification | Digital twin | `models/digital-twin/` | Plant mesh, 10 part mappings to design parts, 4 telemetry signals bound to design attributes |
| Acceptance | GSN safety case | `models/safety-case/gsn-safety-case.json` | 26 nodes; top claim G1 addresses `REQ-TRIT-014`; Solutions Sn7–Sn10 cite the controller evidence |

`models/sysml/omg/` holds the two SysML models in OMG interchange JSON, as exported by the modelling
platform. `models/traceability/completion.json` holds the links and records authored after export to
complete the thread, each with a rationale and the status *pending engineering review*.

## Checking the executable models

| Model | Checker used in the article | Command |
|---|---|---|
| Dafny | Dafny 4.11.0 | `dafny verify formal/dafny/ADSController.dfy` |
| Isabelle/HOL | Isabelle2023 with the Z_Machines session (CyPhyAssure) | `isabelle build -D formal/isabelle` |
| CSP | FDR 4.2.7 | `refines formal/csp/file_robochart_controller_coreassertions.csp` (and `formal/csp/timed/`, `formal/csp/tests/`) |
| Java | Gradle 9.0.0, JUnit 5.11.4, OpenJDK 21 | `cd implementation/java && gradle test` |
| Modelica | OpenModelica 1.26.9 | `simulate(ADSChangeover)` over the model's experiment annotation |

The element identity space derived from these models, the impact, coverage and re-verification tools, the
measured results and the static demonstration are in the case-study repository
[wrwei/digital-thread-ads-case-study](https://github.com/wrwei/digital-thread-ads-case-study).

## Licence

This repository accompanies a manuscript under peer review and is provided under the
[DiTECTS Reviewer Evaluation Licence](LICENSE): editors and referees may download, build, run and inspect it
for the review only. The RoboChart CSP semantic libraries keep their EPL-2.0 licence ([NOTICE](NOTICE)).
