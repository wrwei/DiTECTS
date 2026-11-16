# Change log: SysML-to-Modelica value bindings and the OpenModelica runner (14–15 November 2026)

Every number the article reports that the change moved, old → new, followed by what did not move.
"Old" is the committed thread at `fe2efa8` (128 elements, 206 edges) and the re-verification run of
13 November 2026; "new" is this working tree. Every new value was produced by the repository's own tools.
The tables below copy them from the result files named in each section.

## What changed

* **Design attributes.** Three SysML attributes, with doc comments, carry the simulation's design values:
  `ADSController::changeoverPeriod = 7000` (s) and `MolecularSieveDryer::saturationTimeConstant = 4000` (s) in
  `models/sysml/02-design.sysml`, and `detritiationCapacity::minDecontaminationFactor = 1000` on REQ-ADS-001 in
  `models/sysml/01-requirements.sysml`.
* **Overlay records.** `models/traceability/completion.json` gains a `sysml` section (the three attributes in the
  export's record shapes: attribute usage, feature value, literal) and a `simulation` section (the Modelica
  parameters `tCycle`, `tSat`, `DFtarget` and three Degree 0 bindings). All carry origin `completion`, a rationale,
  a `platformAction` and the status `pending engineering review`.
* **Identity space.** New edge kinds `parameter-of` (parameter → Modelica model) and `sim-binding` (parameter →
  the attribute whose value it takes). `attribute-of` now also covers simulation-bound attributes, and an attribute
  owned by a requirement is joined to that requirement. Both ends of a binding carry `value`. Schema `ads-namespace/5`.
* **Coverage.** New check B1: every simulation binding resolves both ends and joins equal values, in the thread and
  in the SysML and Modelica files. The other 16 checks are unchanged.
* **Re-verification.** New `modelica` runner in `tools/reverify.py`: applies the bindings (SysML text → scratch
  Modelica source), simulates `ADSChangeover` with `omc` in `openmodelica/openmodelica:v1.26.9-minimal`
  (`sha256:18dc2bd10cf7814960437b61981fc26eb23688240479deef761127ef66a2326e`, arm64; OpenModelica 1.26.9) over its
  experiment annotation (0–20000 s, 10 s interval). The verdicts are PASS (no assertion), FAIL (assertion fired, or no
  translation), TIMEOUT, or NOT_ASSESSED (no runtime).
* **Period scenario ST1** is redefined: the change is made to the SysML attribute `changeoverPeriod` (7000 → 9000 s),
  reaches `tCycle` through the binding, and is re-verified by the OpenModelica runner. ST2 (initial bed) is as before.
* **Manual-tracing protocol amendment A1**, made before the re-run (see `manual_vs_thread.md`), gives the new element
  kinds segments and names.
* **Execution note.** The initial Docker, FDR and Gradle results were recorded on 14--15 November 2026 with
  `tools/reverify.py`. A follow-up run on 15 November checked all five baselines and all Isabelle conditions
  after the explicit-state proof update. A subsequent FDR run checked the added power-loss protocol,
  all CSP mutations and both change scenarios. The combined result identifies each source run.
  Host and Python versions are recorded in the result files.

## Identity space (`namespace/ads-namespace.json`)

| Quantity | Old | New |
|---|---:|---:|
| Elements | 128 | 134 |
| Edges | 206 | 216 |
| Elements with a UUID | 109 | 112 |
| Completion-origin elements (new nodes) | 6 | 12 |
| Completion-origin edges | 49 | 59 |
| Non-traceability (structural) edges | 99 | 109 |
| Edges `attribute-of` | 5 | 9 |
| Edges `parameter-of` | 0 | 3 |
| Edges `sim-binding` | 0 | 3 |
| Elements, concern `design` | 17 | 19 |
| Elements, concern `requirements` | 15 | 16 |
| Elements, concern `executable-evidence` | 5 | 8 |

Unchanged edge kinds: `traceability` 107, `fta-input` 24, `gsn-SupportedBy` 21, `fmeda-item` 17, `fta-fmeda` 14,
`fta-output` 10, `gsn-InContextOf` 4, `twin-binding` 4. Unchanged concerns: failure-analysis 51, safety-case 26,
digital-twin 14.

## Impact traversal (`namespace/impact.py`), cumulative closure size by depth

| Start | Old (d1, d2, … unbounded) | New |
|---|---|---|
| dryerA | 7, 20, 48, 67, 89, 107, 118, 126 → 127 | 8, 22, 51, 72, 95, 113, 124, 132 → 133 |
| G1 | 9, 21, 46, 95, 120 → 127 (from d6) | 9, 21, 47, 97, 126 → 133 (from d6) |
| controller | 11, 23, 45, 61, 77, 96, 116, 124, 126 → 127 | 12, 27, 51, 68, 87, 106, 123, 130, 132 → 133 |
| REQ-ADS-007 | 6, 19, 34, 62, 86, 106, 122, 126 → 127 | 6, 19, 34, 64, 91, 112, 128, 132 → 133 |
| ADS Changeover Transient_Modelica | 2, 17, 34, 61, 79, 101, 116, 124, 126 → 127 | 5, 23, 41, 72, 95, 114, 124, 130, 132 → 133 |
| changeoverPeriod (new ST1 start) | — | 2, 13, 27, 51, 68, 87, 106, 123, 130, 132 → 133 |

Maximum depth is unchanged for every start above (dryerA 9, G1 6, controller 10, REQ-ADS-007 9, Modelica 10).
The impact app's self-check expectations moved with the namespace: dryerA depth 1/2/4/5/unbounded
8/22/72/95/133 (was 7/20/67/89/127), elements 134 (128), edges 216 (206).

## Coverage (`tools/coverage.py`)

| Quantity | Old | New |
|---|---:|---:|
| Checks | 16 | 17 (B1 added) |
| Completed thread: gaps | 0 | 0 |
| Completed thread: C1 elements checked | 128 | 134 |
| Completed thread: B1 bindings checked | — | 3 (all pass) |
| Exported thread (`--no-completion --drop-kinds attribute-of,fta-fmeda`): gaps | 87 | 87 |
| Exported thread: B1 | — | 0 bindings (holds vacuously) |

The exported thread is unchanged at 117 elements, 134 edges (151 without `--drop-kinds`; 45 gaps), 53 trace links
(60 pairs), 7 components.

## Latency (`reverify.py latency --reps 30`, `results/latency_completed_thread.*`)

| Quantity | Old | New |
|---|---:|---:|
| Starts × reps (n) | 128 × 30 (3840) | 134 × 30 (4020) |
| Unbounded: median / p95 / max (ms) | 0.052 / 0.0568 / 0.1828 | 0.054 / 0.0604 / 1.0715 |
| Unbounded: cone median / max | 127 / 127 | 133 / 133 |
| Depth ≤ 5: median / p95 / max (ms) | 0.0233 / 0.0365 / 0.0519 | 0.0245 / 0.0375 / 0.0813 |
| Depth ≤ 5: cone median / max | 71 / 121 | 75 / 127 |
| Index build (ms) | 0.081 | 0.083 |

Same host (macOS arm64, 10 CPUs, Python 3.9.6). The new unbounded maximum (1.07 ms) is a single outlier among 4020
traversals; the median and p95 moved by 0.002–0.004 ms.

## Manual tracing (`tools/manual_trace.py`, `results/manual_vs_thread.*`)

| Quantity | Old | New |
|---|---:|---:|
| Elements with a segment | 128 of 128 | 134 of 134 |
| Lexicon size | 94 | 101 |
| dryerA, EXACT: recall_∞ | 0.748 | 0.7594 |
| dryerA, EXACT: elements found at fixpoint | 95 | 101 |
| dryerA, EXACT: rounds / terms / searches / segment hits / segments read | 8 / 172 / 1892 / 304 / 117 | 8 / 179 / 1969 / 325 / 123 |
| dryerA, EXACT: round-k recall k = 1, 2, 3 | 0.4286, 0.4, 0.6042 | 0.375, 0.3636, 0.5882 |
| dryerA, LENIENT: recall_∞ | 0.874 | 0.8797 |
| dryerA, LENIENT: elements found at fixpoint | 111 | 117 |
| dryerA, LENIENT: rounds / terms / searches / segment hits / segments read | 4 / 198 / 2178 / 558 / 143 | 4 / 205 / 2255 / 598 / 149 |
| dryerA, LENIENT: round-k recall k = 1, 2, 3 | 0.4286, 0.95, 0.9167 | 0.375, 0.9545, 0.9216 |
| All starts (n) | 128 | 134 |
| All starts, EXACT: median recall_∞ (max) | 0.748 (0.7559) | 0.7594 (0.7669) |
| All starts, EXACT: median terms / searches | 172 / 1892 | 179 / 1969 |
| All starts, EXACT: median round-k recall k = 2, 3 | 0.3205, 0.4226 | 0.3117, 0.4317 |
| All starts, LENIENT: median recall_∞ (max) | 0.874 (0.8819) | 0.8797 (0.8872) |
| All starts, LENIENT: median terms / searches | 198 / 2178 | 205 / 2255 |
| All starts, LENIENT: median round-k recall k = 2, 3 | 0.5917, 0.8165 | 0.6169, 0.8394 |
| All starts, LENIENT+DIAGRAM: median recall_∞ / searches | 0.937 / 2343 | 0.9398 / 2420 |

The dryerA miss classes are unchanged in count (EXACT: cascade 6, structural 10, typed-link+structural 3,
name-variant 8, typed-link-only 4, mention-not-extracted 1; LENIENT: typed-link-only 3, structural 10,
typed-link+structural 1, cascade 1, mention-not-extracted 1). The median rounds (EXACT 9, LENIENT 5) and the
median round-1 recall (0) over all starts are unchanged. The doc comments of the bound attributes name their
Modelica parameter, so name search can follow a binding through that text.

## Manual time estimate (`tools/manual_time.py`, `results/manual_time.json`), hours, low–high bound

| Quantity | Old | New |
|---|---:|---:|
| dryerA (also controller, REQ-ADS-007), EXACT | 0.99–4.64 | 1.03–4.83 |
| dryerA (also controller, REQ-ADS-007), LENIENT | 1.25–5.45 | 1.31–5.65 |
| Thread review of the closure | 0.48–0.69 | 0.49–0.72 |
| All starts, EXACT: median (max high) | 0.99–4.64 (4.66) | 1.03–4.83 (4.85) |
| All starts, LENIENT: median (max high) | 1.25–5.45 (5.49) | 1.31–5.65 (5.70) |

## Re-verification (`tools/reverify.py`, `results/reverify_bound_thread.*`)

| Quantity | Old | New |
|---|---:|---:|
| Runners | 4 (Dafny, Isabelle, FDR4, Gradle) | 5 (+ OpenModelica) |
| Solution → evidence pairs | 49 | 49 |
| … of which with a runner | 4 (Sn7–Sn10) | 5 (Sn2, Sn7–Sn10) |
| Baseline | 4/4 PASS | 5/5 PASS |
| Baseline Sn2 (Modelica) | no checker (evidence record) | PASS: bound tCycle = 7000, tSat = 4000, DFtarget = 1000; assertion not fired; min DF 1390.2 at t = 7000 s (left limit at the swap) |
| Mutants: faults detected | 14/16 (I4 TIMEOUT at 1800.62 s; F3 survived) | 16/16 after the explicit-state proof and CSP protocol updates |
| Mutants: controls passed | 6/6 | 6/6 |

**Mutant I4 (Isabelle): classification corrected on 15 November 2026.** In this run the PolyML process was
killed (exit 137) after 1748.66 s, inside the 6 GB container memory limit and before the 1800 s budget.
The original dispatcher classified it as FAIL and counted it as detected. The corrected dispatcher records
a killed checker as NOT_ASSESSED, even when its output also reports a failed or unfinished session.
The deposited result was reclassified from its recorded output; its exit code, elapsed time and original
log are unchanged. No checker was re-run for this correction. At that stage, the totals were 14/16 faults
detected, one survived and one not assessed, with all six controls passing. The 13 November I4 run remains
TIMEOUT because it reached the 1800 s budget. The other 21 mutant outcomes were unchanged.

**Subsequent Docker re-run on 15 November 2026.** The final deadlock-freedom proof step was changed from
`by (metis St.exhaust_disc)` to `by (case_tac st; auto)`, keeping the model definitions unchanged.
The unmodified theory passed in 41.77 s; I1--I4 all failed their checks, IC1 passed, and both change
scenarios passed the Isabelle check. I4 produced `Failed to finish proof` in 32.67 s rather than a killed
process. At that stage, 15/16 faults were detected, one survived and 6/6 controls passed.
`results/isabelle_cases/` contains the complete fresh results and logs. The earlier I4 record is retained
under `sources.proofUpdate.previousI4` in the combined result. Its saved exit code does not establish why
that historical process was killed.

**CSP power-loss response added on 15 November 2026.** The original FDR assertions checked only generic
behaviour and missed F3. One failures-divergences protocol refinement now requires the fail-safe entry
action after an accepted power-loss input, before another controller input. External shutdown and memory
writes are blocked for this operational protocol; the other finite actions are hidden. The generated
controller definitions are unchanged. The original passes all 21 assertions; F1--F3 fail and FC1 passes.
Both change scenarios pass FDR. Additional checks confirm power loss is reachable in both operating
states and after recovery, and reject a controller that stops without its response. Final totals are
16/16 selected faults detected and 6/6 controls passed. Full output is in `results/fdr_powerloss/`;
the earlier F3 result is retained under `sources.cspResponseUpdate.previousF3` in the combined JSON.
These are targeted improvements after the initial run, not an independent fault-detection estimate.

### Change scenarios: flagged Solutions (impact closure) and verdicts

| | Old | New |
|---|---|---|
| ST1 change | `tCycle` 7000 → 9000 s in the Modelica source | SysML `changeoverPeriod` 7000 → 9000 s, propagated to `tCycle` by the binding |
| ST1 start element | Modelica model record | `changeoverPeriod` attribute |
| ST1 Solution depths | Sn2@1; Sn1, Sn3, Sn7, Sn8, Sn9, Sn10@3; Sn4@5; Sn5, Sn6, Sn11@7 | Sn2, Sn3, Sn7, Sn8, Sn9, Sn10@3; Sn1@4; Sn4, Sn11@7; Sn5, Sn6@8 |
| ST1 Sn2 verdict | not assessed (no checker); equation-evaluated min DF 845.3 at the 8990 s sample | **FAIL**: assertion fired at t = 8320 s ("Detritiation continuity violated: plant DF fell below the authorised target during changeover"); diagnostic run (assertion as warning): min DF 843.2 at t = 9000 s (left limit before the swap) over 0–20000 s |
| ST1 Sn7–Sn10 | PASS (artefacts unchanged) | PASS (artefacts unchanged) |
| ST2 Solution depths | Sn2, Sn3, Sn7–Sn10@2; Sn1@3; Sn4, Sn11@6; Sn5, Sn6@7 | unchanged |
| ST2 verdicts | Sn7, Sn8, Sn9 PASS; Sn10 FAIL (7 of 14 tests) | Sn7, Sn8, Sn9 PASS; Sn10 FAIL (7 of 14 tests); Sn2 PASS (unchanged values; min DF 1390.2) |

The analytical check agrees: with tCycle = 9000 s the DF falls below 1000 once the bed age exceeds
tSat·ln(DFfresh/DFtarget) = 4000·ln 8 ≈ 8318 s; OpenModelica reported the violation at 8320 s. Its minimum,
8000·exp(−9000/4000) ≈ 843.2, occurs just before the swap at 9000 s.

## Demonstration cross-check (`demo/`, not modified)

The deposited demo carries 192 of the old 206 edges (all but the 14 `fta-fmeda`). Against the new
thread it lacks the 6 new elements (`changeoverPeriod`, `saturationTimeConstant`, `minDecontaminationFactor`,
`tCycle`, `tSat`, `DFtarget`) and 10 edges (4 `attribute-of`, 3 `parameter-of`, 3 `sim-binding`). A regenerated demo
would need 134 elements and 202 of 216 edges for the same "all but `fta-fmeda`" result, over 938 closures
(134 starts × 7 depths) instead of 896. In the demo's data model, the three attributes must be in its SysML models.
The Modelica model's indexed symbols already include its parameter declarations (component declarations). The bindings need a record that joins an
attribute's qualified name to a Modelica parameter, from which `attribute-of`, `parameter-of` and `sim-binding`
follow, as twin bindings yield `attribute-of` today. Left unchanged, the demo graph reproduces 349 of the 896
closures of the new thread (without `fta-fmeda`) over the 128 shared starts. dryerA in the demo stays
7/20/48/66/88/107/127, against 8/22/51/71/94/113/133 for the new thread without `fta-fmeda`.

## Not changed

* Typed cross-concern links 87 (53 exported, 34 completion), endpoint pairs 107, concern pairs 8; the `traceability`
  edges are byte-identical.
* dryerA → G1 shortest path: four hops via dryerCapacityMargin, G2, S1; G1 first reached at depth 4;
  REQ-TRIT-014, REQ-ADS-002 and REQ-ADS-005 first reached from dryerA at depths 5, 3 and 1.
* FMEDA (17 rows), fault tree (35 elements, 10 minimal cut sets), GSN safety case (26 elements),
  `models/fta/ads-fta.json`, `models/safety-case/*.json`, OMG interchange files.
* Exported-thread coverage (87 gaps; 45 without dropping structural kinds) and the 16 original checks' definitions.
* The mutant edits (16 faults, 6 controls); no Modelica mutants were added. The baseline verdicts of Dafny,
  Isabelle, FDR4 and Gradle (PASS), and the Dafny and Java mutant outcomes.
* ST2: its start, flagged depths, edits and the Dafny/Isabelle/FDR/Gradle verdicts.
* Host and the existing runners: Python 3.9.6, macOS arm64, 10 CPUs; Dafny 4.11.0; Isabelle via
  `isabelle-runtime:22.04`. Recorded now as FDR 4.2.7 and Gradle 9.0.0 (the 13 November record kept only banner
  lines for these two). One version did move: Java 21.0.9 → 21.0.10 (a patch update on the host).
* The 128 previous elements and 206 previous edges are unchanged and in the same order; the new records are additions.
