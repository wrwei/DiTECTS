# Manual (name-based) change-impact tracing vs. the digital thread

This is a **simulation** of name-based manual tracing over the ADS model files. It is not a human
study. It asks one question. If an engineer has the model files but no typed links and no shared
identity space, and searches text for names, which of the elements that the thread's impact
analysis (`namespace/impact.py`) reaches would they find? How many searches would it take?

Reproduce from the repository root with `python3 tools/manual_trace.py` (Python ≥ 3.9, standard
library only). The tool rewrites everything in this file below the `<!-- RESULTS -->` marker and
leaves the Protocol section unchanged.

## Protocol

This section was fixed before the tool was first run and was not changed after seeing results.
Changes made after the first run (bug fixes only) are listed under "Deviations" in the results.

### P1. Ground truth (thread side)

`namespace/ads-namespace.json` (128 elements, 206 edges) is loaded through `namespace/impact.py`
(`index`, `resolve`, `impact`). It is an undirected breadth-first traversal. For a start element
s, `T_k(s)` is the set of elements at depth ≤ k (k = 1..6) and `T_∞(s)` is the unbounded
closure. The start itself is excluded. The thread side costs one query per start.

### P2. Documents (what the engineer may read)

There are eleven documents:

1. `models/sysml/01-requirements.sysml`
2. `models/sysml/02-design.sysml`
3. `models/fmeda/ads-fmeda.json`
4. `models/fta/ads-fta.json`
5. `models/safety-case/gsn-safety-case.json`
6. `formal/dafny/ADSController.dfy`
7. `formal/isabelle/*.thy` + `formal/isabelle/ROOT`
8. `formal/csp/*.csp` (top level only, excluding `formal/csp/defs/` and `formal/csp/timed/`)
9. `implementation/java/src/**` (main and test)
10. `simulation/modelica/ADSChangeover.mo`
11. the digital twin

**Excluded as inputs:**

- `models/traceability/completion.json`
- `models/safety-case/evidence-resolution.json`
- `namespace/*` (except as the source of the twin document, see below)
- every stored typed-link record inside an allowed file: the `traces` arrays of FMEDA rows and FTA
  elements
- every structured object reference by id: FMEDA `itemElement`, FTA gate `inputs` and
  `outputEvent`, FaultTree `topEvent`
- internal ids and UUIDs (`@id` values other than an FTA element's own code, `_id`)

Fields that are the model's own content and visible in its editor are allowed. Examples are
FMEDA columns such as `itemLabel`, `effect`, `currentControls` and `safetyMechanism`; FTA `name`
and `description`; GSN `name` and `description`; and SysML text, including `satisfy` statements,
which are part of the SysML source.

**Twin document.** The twin model (`digitaltwin-model.json` in the project export) is not
deposited in this repository. The repository holds only the twin mesh,
`demo/demo-assets/twin-display/*.glb`, whose node names are the mesh part names. The twin
document is therefore built from the visible fields of the 14 digital-twin elements in
`namespace/ads-namespace.json`:

- each TwinPart contributes its `label` (e.g. `DRYER A`) and its mesh name (`text`, e.g.
  `dryerA`);
- each TwinBinding contributes its signal `label` (e.g. `bedSaturation`) and unit.

The tool checks that every mesh name exists as a node name in the GLB. The binding's target
SysML element and the part's mapped SysML element are typed links and are not used.

### P3. Segmentation (text → element id)

Each document is cut into segments. An **element segment** maps to exactly one identity-space
element. The other segments are **context segments**: text an engineer reads that is not itself
an identity-space element.

- **SysML** (both files), parsed by braces and statements:
  - Element segments are requirement usages (`requirement <'REQ-…'> name …{…}`), part usages
    (`part name : Def …`), interface usages (`interface name …;`) and attribute usages declared
    in part definitions (`attribute name : …`).
  - A segment holds the element's declaration and body, minus the text of nested element
    segments, which belong to the innermost element.
  - Every other top-level statement or block is a context segment of its own: package doc,
    `requirement def`, `item def`, `part def` / `port def` / `interface def` bodies (minus their
    attribute element lines), `enum def`, each `satisfy … by …;` statement, and `state def`.
- **FMEDA:** one element segment per row, holding the row header `row N` plus every visible
  column cell, excluding `traces` and `itemElement`. Model-level fields form one context
  segment.
- **FTA:** one element segment per event or gate, holding its code (`BE-07`), `name` and
  `description`. Gate `inputs` and `outputEvent` are excluded in the primary variants (see P6).
  The `FaultTree` record and the model-level fields form context segments.
- **GSN:** one element segment per node, holding `name` (the GSN id) and `description`. The
  deposited GSN file holds nodes only. The argument edges (SupportedBy, InContextOf) are not in
  any allowed document.
- **Executable models** (Dafny, Isabelle, CSP/FDR, Java, Modelica): each is one element whose
  segment is the concatenated text of its whole file set.
- **Twin:** one element segment per twin part and per twin binding (P2).

Elements with no segment are listed with a reason. The tool reports segmentation coverage out of
128.

### P4. Names and terms

**Visible names of an element** (the names it is known by):

- requirement: declared name and short name (`dryerCapacityMargin`, `REQ-ADS-005`);
- design usage: declared name;
- FMEDA row: `FMEDA row N` and `row N`;
- FTA element: code and name (`BE-07`, `Dryer A sieve breakthrough`);
- GSN node: its id (`Sn1`);
- twin part: label and mesh name;
- twin binding: label;
- executable model: a fixed name set made of its registered model name, its notation name and
  its primary unit name:
  - Java: `ADS Controller Implementation`, `Java`, `ADSController`
  - Dafny: `ADS Controller Proof - Dafny`, `Dafny`, `ADSController`
  - Isabelle: `ADS Controller Behaviour`, `Isabelle`, `ADSController_Beh`
  - CSP/FDR: `ADS Controller Refinement`, `CSP`, `FDR`, `file_robochart_controller`
  - Modelica: `ADS Changeover Transient_Modelica`, `Modelica`, `ADSChangeover`

**Names cited in a segment's text** (what the engineer picks up by reading a hit):

- requirement ids `REQ-XXX-NNN`, with slash shorthand expanded (`REQ-ADS-002/006/007` → three
  ids);
- GSN ids `\b(G|S|Sn|C|A)\d{1,2}\b`;
- FTA codes `\b(TE|IE|BE|G)-\d{2}\b`;
- FMEDA row references `rows? N(/M)*` → `row N`, `row M`;
- lexicon names occurring in the text, matched with the variant's matcher. The lexicon is every
  declared requirement, part, interface and attribute usage name in the two SysML files, every
  requirement short name, every twin part label, mesh name and binding label, and every
  executable-model name.

**Stop list** (fixed). A term is dropped if either condition holds:

1. it is shorter than 3 characters, unless it matches one of the identifier patterns above;
2. its lower-cased form is in this list: the, and, for, with, from, into, not, any, all, both,
   either, top, row, rows, model, part, port, item, state, event, data, type, value, test, true,
   false, none, null, def, doc, attribute, requirement, package, interface, system.

### P5. Procedure (worklist fixpoint)

1. Round 0 term set = the start element's visible names, after the stop list.
2. Round k (k ≥ 1): search every document for every term first issued in round k. Every element
   segment whose text matches a term is **found**. The element's manual hop is k, the first
   round in which it was found. The start is never counted as found.
3. Every segment hit in round k, whether element or context and including the start's own
   segment, contributes its visible names (for element segments) plus the names cited in its
   text to a candidate set. The candidate set minus every term already searched, after the stop
   list, is the term set for round k+1.
4. Stop when a round produces no new term (fixpoint).

### Matching variants

- **EXACT:** a case-sensitive substring match of the term as written. Where the term begins or
  ends with a letter, digit or underscore, that end must not be adjacent to a letter, digit or
  underscore in the text. For example, `dryerA` does not match `dryerARegenReturn`, and
  `controller` does not match `file_robochart_controller`.
- **LENIENT:** both strings are lower-cased and their spaces, hyphens and underscores are
  removed. A match must begin and end on a token boundary of the original text. A token boundary
  is any of the following: string start or end, a removed separator, a non-alphanumeric
  character, a lower→upper (camelCase) transition, an UPPER→Upper-lower transition (`ADSC|ontroller`),
  or a letter↔digit transition. So `DRYER A` matches `dryerA`, `Dryer A` and `DryerA`; `ads`
  matches `ADS`; `ads` does not match `loads`; `row 1` does not match `row 17`.

### P6. Pre-registered secondary sensitivity variant

**LENIENT+DIAGRAM** is LENIENT, except that each FTA gate segment also contains the codes and
names of its `inputs` and `outputEvent`. This models an engineer reading the drawn fault tree
rather than searching it. GSN argument edges cannot be added this way because they are not in
the deposited GSN file. This variant is reported in the JSON and in one summary row. It is not a
headline result.

### P7. Effort

Effort is counted per start and variant:

- rounds executed until the fixpoint;
- distinct terms searched;
- searches issued = terms × 11 documents;
- segment hits, counted as (term, segment) pairs;
- distinct segments read, element and context.

The thread side is 1 query.

### P8. Comparisons

- **Named scenarios:**
  - `dryerA` (design part);
  - `controller` (design part; change to the initial bed);
  - `ADS Changeover Transient_Modelica` (Modelica model; change to the bed-swap period `tCycle`);
  - `REQ-ADS-007`.
- **All 128 starts.**
- **Measures**, with M_k = elements found by round k and M_fix = elements found at the fixpoint:
  - recall_∞ = |M_fix ∩ T_∞| / |T_∞|;
  - round-k recall = |M_k ∩ T_k| / |T_k| for k = 1, 2, 3;
  - fixpoint-vs-depth-k recall = |M_fix ∩ T_k| / |T_k|;
  - manual-only elements = M_fix \ T_∞;
  - beyond-depth hits = M_k \ T_k.
- **Aggregation:** median and IQR (Q1, Q3; `statistics.quantiles`, method "inclusive") over the
  128 starts.

### P9. Audit

Each element in T_∞ \ M_fix is classified as exactly one of the following:

1. **no-segment:** the element has no searchable segment.
2. **name-variant** (EXACT only): some term issued in the run matches the element's segment
   under LENIENT but not under EXACT.
3. **mention-not-extracted:** the element's visible name occurs (LENIENT) in the text of a found
   thread neighbour, but the P4 extraction rules or the stop list did not turn it into a term.
4. **typed-link-only:** every thread edge to a found neighbour is a `traceability` link with no
   textual mention.
5. **structural:\<kind\>:** every thread edge to a found neighbour is a structural edge not
   visible as text (`attribute-of`, `fta-input`, `fta-output`, `gsn-SupportedBy`,
   `gsn-InContextOf`, `twin-binding`, `fmeda-item`, `fta-fmeda`).
6. **typed-link+structural:** a mixture of classes 4 and 5.
7. **cascade:** no thread neighbour of the element was found.

Classes are tested in the order listed and the first that applies is used.

**Text-only hits** are found elements whose first-finding hop is not a thread edge: the source
segment's element and the found element are not adjacent in the thread, or the source was a
context segment. They are listed with the term that produced them.

### Amendment A1 (14 November 2026): SysML-to-Modelica value bindings

Made before the re-run on the extended thread; no result on that thread had been computed. The thread
gained three SysML attributes (`changeoverPeriod`, `saturationTimeConstant`, `minDecontaminationFactor`) and
the three Modelica parameters they set (`tCycle`, `tSat`, `DFtarget`), with `parameter-of` and `sim-binding`
edges, so the identity space now has 134 elements and 216 edges (P1's 128 and 206 are the sizes when the
protocol was fixed). P3 and P4 had no rule for the new kinds. A1 extends them in the way they already treat
SysML attribute usages:

- P3, SysML: an attribute usage declared in a requirement usage is an element segment, as one declared in a
  part definition is.
- P3, Modelica: each `parameter Real <name> = …;` declaration of an identity-space parameter is an element
  segment of its own and is cut out of the Modelica model's segment, which keeps the rest of the file.
- P4: a Modelica parameter's visible name is its declared name; every parameter name declared in the
  Modelica file joins the lexicon.
- P9: `parameter-of` and `sim-binding` are structural edge kinds.

The doc comments of the three SysML attributes name the bound Modelica parameter, so name search can follow
a binding through that text. Nothing else changed.

### Amendment A2 (15 November 2026): model text, no procedural change

Made before the re-run. The design model gained four `satisfy` statements for satisfaction links that the
completion overlay had already added to the thread (`blower`, `dryerA` and `dryerB` to `REQ-ADS-001`,
`REQ-ADS-005` and `REQ-ADS-006`), and the names of the authoring tool and of the organisation that provided the
abstracted design were removed from model comments and from this protocol's wording. The searched documents
therefore changed; the procedure, matching rules, lexicon rules and stop list did not.

### Amendment A3 (15 November 2026): model text, no procedural change

Recorded with the re-run. A review of the formal models corrected bed alternation: the design model's
`ADSOperation` state machine gained a Changeover-to-FailSafe power-loss transition, a `changeoverComplete`
trigger and a `swapDutyBed` action with a doc comment, and the Dafny, Isabelle and CSP sources gained
alternation definitions, properties and comments. The searched documents therefore changed; the procedure,
matching rules, lexicon rules and stop list did not. Recall and search counts are unchanged; segment hits and
the reading-time estimate rose slightly.

### Amendment A4 (15 November 2026): contract review, no procedural change

Recorded with this re-run. Dafny gained complete mode/input and bed-preservation contracts. Isabelle now
derives accepted inputs from its executable operation list. CSP gained a response protocol that checks
the first bed swap and a shared initial-bed parameter. Java and Modelica comments distinguish the
controller and simulation assumptions from physical availability. These edits changed the searched
text; the procedure, matching rules, lexicon rules and stop list did not change. Recall and search counts
are unchanged, while the longer formal definitions increase the reading-time estimate.

### Amendment A5 (15 November 2026): destination and command checks, no procedural change

Recorded with this re-run. Isabelle gained destination lemmas for four operations, CSP gained a command
protocol over the four inputs and four output commands, and the Java actuator records its command history.
These edits changed the searched text; the procedure, matching rules, lexicon rules and stop list did not.

### Amendment A6 (15 November 2026): offered operations, trace invariant and public channels, no procedural change

Recorded with this re-run. Isabelle gained a lemma fixing the operations offered in each mode and a trace
invariant; the CSP command view keeps all public channels visible. These edits changed the searched text; the
procedure, matching rules, lexicon rules and stop list did not.

### Amendment A7 (15 November 2026): handler targets and per-copy protocols, no procedural change

Recorded with this re-run. Isabelle gained a channel-target table and a lemma relating each offered event to the
state it reaches; the CSP suite gained the command and bed protocols for the composed module and the controller.
These edits changed the searched text; the procedure, matching rules, lexicon rules and stop list did not.

### Amendment A8 (16 November 2026): FMEDA analysed items and value bindings as typed links, no procedural change

Recorded with this re-run. The completion overlay gained 17 typed links from FMEDA rows to the design parts their
analysed-item fields name, and 3 typed links recording the Degree 0 value bindings between Modelica parameters and
SysML attributes. Each replaces the `fmeda-item` or `sim-binding` edge between the same two elements, so the graph's
edges are unchanged. The overlay is an excluded input and the `itemElement` field was already excluded, so the
searched text did not change; the procedure, matching rules, lexicon rules and stop list did not either.

<!-- RESULTS -->

## Results

Generated by `python3 tools/manual_trace.py`. Protocol section sha256 `00a0e3fe59584049`.

**Checks.**

- dryerA thread totals at depth 1–6 and unbounded: 8/22/51/72/95/113/133.
- Thread connected (every start reaches all 133 others): True.
- SysML segment names agree with the OMG export's declaredName: 32/32.
- Twin mesh names present as GLB node names: 10/10.

### Segmentation

134 of 134 identity-space elements have a searchable segment. Element segments by document: csp 1, dafny 1, fmeda 17, fta 34, gsn 26, isabelle 1, java 1, modelica 4, sysml-design 19, sysml-requirements 16, twin 14. Context segments: fmeda 1, fta 2, sysml-design 35, sysml-requirements 2. Lexicon: 101 names.

Caveat: the 14 digital-twin segments are built from the twin elements' visible labels in namespace/ads-namespace.json (the twin model file is not parsed); mesh names cross-checked against the GLB node names.

### Named scenarios

Columns k1–k3 give cumulative counts at thread depth k or manual round k. 'fix' is the manual fixpoint.
Thread queries: 1 per start. Searches = distinct terms × 11 documents.

| Scenario | Side | k1 | k2 | k3 | k4 | k5 | k6 | ∞ / fix | recall ∞ | recall k1/k2/k3 (round k vs depth k) | fixpoint vs depth k1/k2/k3 | rounds | terms | searches |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dryerA | thread | 8 | 22 | 51 | 72 | 95 | 113 | 133 | — | — | — | 1 query |
| dryerA | EXACT | 3 | 18 | 48 | 87 | 98 | 104 | 105 | 79% | 38% / 36% / 67% | 100% / 91% / 90% | 8 | 185 | 2035 |
| dryerA | LENIENT | 8 | 94 | 117 | 117 | 117 | 117 | 117 | 88% | 38% / 95% / 92% | 100% / 95% / 92% | 4 | 205 | 2255 |
| dryerA | LENIENT+DIAGRAM | 10 | 98 | 125 | 125 | 125 | 125 | 125 | 94% | 38% / 95% / 96% | 100% / 95% / 96% | 4 | 220 | 2420 |
| controller | thread | 12 | 27 | 51 | 68 | 87 | 106 | 133 | — | — | — | 1 query |
| controller | EXACT | 14 | 47 | 84 | 100 | 101 | 104 | 105 | 79% | 75% / 89% / 88% | 100% / 96% / 94% | 8 | 185 | 2035 |
| controller | LENIENT | 15 | 78 | 116 | 117 | 117 | 117 | 117 | 88% | 75% / 89% / 94% | 100% / 96% / 94% | 5 | 205 | 2255 |
| controller | LENIENT+DIAGRAM | 15 | 81 | 124 | 125 | 125 | 125 | 125 | 94% | 75% / 89% / 94% | 100% / 96% / 94% | 5 | 220 | 2420 |
| modelica | thread | 5 | 23 | 41 | 72 | 95 | 114 | 133 | — | — | — | 1 query |
| modelica | EXACT | 3 | 27 | 52 | 86 | 100 | 101 | 105 | 79% | 0% / 74% / 78% | 100% / 100% / 90% | 9 | 185 | 2035 |
| modelica | LENIENT | 3 | 67 | 116 | 117 | 117 | 117 | 117 | 88% | 0% / 96% / 90% | 100% / 100% / 90% | 5 | 205 | 2255 |
| modelica | LENIENT+DIAGRAM | 3 | 69 | 124 | 125 | 125 | 125 | 125 | 94% | 0% / 96% / 95% | 100% / 100% / 95% | 5 | 220 | 2420 |
| REQ-ADS-007 | thread | 6 | 19 | 34 | 64 | 91 | 112 | 133 | — | — | — | 1 query |
| REQ-ADS-007 | EXACT | 7 | 36 | 77 | 97 | 101 | 104 | 105 | 79% | 50% / 79% / 74% | 83% / 84% / 85% | 8 | 185 | 2035 |
| REQ-ADS-007 | LENIENT | 7 | 73 | 116 | 117 | 117 | 117 | 117 | 88% | 50% / 79% / 85% | 83% / 84% / 85% | 5 | 205 | 2255 |
| REQ-ADS-007 | LENIENT+DIAGRAM | 7 | 76 | 124 | 125 | 125 | 125 | 125 | 94% | 50% / 84% / 88% | 83% / 84% / 88% | 5 | 220 | 2420 |

Columns k1–k6 for a manual row repeat the fixpoint once the fixpoint is reached.

### All 134 start elements (median [Q1–Q3])

| Variant | recall ∞ | round-k vs depth-k recall, k=1 / 2 / 3 | fixpoint vs depth-k, k=1 / 2 / 3 | found at fixpoint | rounds | terms | searches | segments read | starts with 0 found | starts with recall 100% |
|---|---|---|---|---|---|---|---|---|---|---|
| EXACT | 79% [79–79%] | 0% [0–50%] / 33% [10–62%] / 46% [18–67%] | 100% [67–100%] / 84% [65–94%] / 80% [68–89%] | 105 [105–105] | 9 [8–10] | 185 [185–185] | 2035 [2035–2035] | 131 [131–131] | 21 | 0 |
| LENIENT | 88% [88–88%] | 0% [0–57%] / 65% [36–88%] / 84% [67–92%] | 100% [67–100%] / 91% [80–100%] / 88% [79–94%] | 117 [117–117] | 5 [5–5] | 205 [205–205] | 2255 [2255–2255] | 153 [153–153] | 14 | 0 |
| LENIENT+DIAGRAM (sensitivity) | 94% [94–94%] | 33% [0–67%] / 86% [56–100%] / 94% [87–96%] | 100% [100–100%] / 100% [90–100%] / 94% [88–96%] | 125 [125–125] | 5 [5–5] | 220 [220–220] | 2420 [2420–2420] | 161 [161–161] | 7 | 0 |

Thread side, for comparison: 1 query per start, and the unbounded closure is 133 for every start.

EXACT fixpoint sizes (size: number of starts): 0: 21, 1: 2, 2: 3, 105: 105, 106: 3. Starts whose fixpoint is below 20: A1 [safety-case] (0), A2 [safety-case] (2), C1 [safety-case] (0), C2 [safety-case] (0), G-00 [failure-analysis] (0), G-01 [failure-analysis] (0), G-02 [failure-analysis] (0), G-03 [failure-analysis] (0), G-05 [failure-analysis] (0), G-09 [failure-analysis] (0), G2 [safety-case] (0), G4 [safety-case] (0), IE-01 [failure-analysis] (0), IE-02 [failure-analysis] (0), IE-03 [failure-analysis] (0), IE-04 [failure-analysis] (0), IE-06 [failure-analysis] (0), REQ-TRIT-007 [requirements] (2), REQ-TRIT-021 [requirements] (2), S1 [safety-case] (0), S2 [safety-case] (0), Sn9 [safety-case] (0), dryerARegenReturn [design] (0), interfaceEdge [design] (0), releaseRate [design] (1), releaseRate [digital-twin] (1).

LENIENT fixpoint sizes (size: number of starts): 0: 14, 117: 118, 118: 2. Starts whose fixpoint is below 20: A1 [safety-case] (0), C2 [safety-case] (0), G-00 [failure-analysis] (0), G-02 [failure-analysis] (0), G-03 [failure-analysis] (0), G-05 [failure-analysis] (0), G-09 [failure-analysis] (0), G2 [safety-case] (0), G4 [safety-case] (0), IE-01 [failure-analysis] (0), IE-06 [failure-analysis] (0), S1 [safety-case] (0), S2 [safety-case] (0), interfaceEdge [design] (0).


Elements found manually but not reached by the thread, summed over 134 starts: EXACT 0, LENIENT 0, LENIENT+DIAGRAM 0.

Recall ∞ by concern of the start element (median [Q1–Q3]):

| Start concern | n | EXACT | LENIENT |
|---|---|---|---|
| design | 19 | 79% [79–79%] | 88% [88–88%] |
| digital-twin | 14 | 79% [79–79%] | 88% [88–88%] |
| executable-evidence | 8 | 79% [79–79%] | 88% [88–88%] |
| failure-analysis | 51 | 79% [79–79%] | 88% [88–88%] |
| requirements | 16 | 79% [79–79%] | 88% [88–88%] |
| safety-case | 26 | 79% [0–79%] | 88% [88–88%] |

## Audit

### Miss classes, summed over all 134 starts (element misses)

| Class | EXACT | LENIENT | LENIENT+DIAGRAM |
|---|---|---|---|
| no-segment | 0 | 0 | 0 |
| name-variant | 864 | 0 | 0 |
| mention-not-extracted | 108 | 120 | 0 |
| typed-link-only | 329 | 363 | 384 |
| structural | 1132 | 1236 | 522 |
| typed-link+structural | 109 | 121 | 128 |
| cascade | 3929 | 1940 | 912 |

EXACT detail: mention-not-extracted:stop-listed 108; name-variant:lenient term: BLOWER, blower 107; name-variant:lenient term: CHANGEOVER 216; name-variant:lenient term: CSP 1; name-variant:lenient term: DRYER A, dryerA 108; name-variant:lenient term: Loss of drying 1; name-variant:lenient term: ads 324; name-variant:lenient term: stackMonitor, stackMonitorIndependence 107; structural:attribute-of 110; structural:fta-input 236; structural:fta-input+fta-output 216; structural:fta-output 119; structural:gsn-InContextOf 222; structural:gsn-SupportedBy 229; typed-link+structural:gsn-SupportedBy+traceability 109.

LENIENT detail: mention-not-extracted:stop-listed 120; structural:fta-input 134; structural:fta-input+fta-output 361; structural:fta-output 247; structural:gsn-InContextOf 242; structural:gsn-SupportedBy 252; typed-link+structural:gsn-SupportedBy+traceability 121.

EXACT: 23 element(s) are found from no start at all: dryerARegenReturn, interfaceEdge, C1, C2, A1, S1, S2, G2, G4, Sn3, Sn5, IE-01, IE-02, IE-03, IE-04, IE-06, G-00, G-01, G-02, G-03, G-05, Sn11, G-09.

LENIENT: 16 element(s) are found from no start at all: interfaceEdge, C2, A1, S1, S2, G2, G4, Sn3, IE-01, IE-03, IE-06, G-00, G-02, G-03, G-05, G-09.

### Misses for dryerA

**EXACT.** 28 missed of 133. By class: cascade 5, mention-not-extracted 1, name-variant 8, structural 10, typed-link+structural 1, typed-link-only 3.

- name-variant [lenient term: BLOWER, blower]: Sn11 (d7)
- name-variant [lenient term: CHANGEOVER]: IE-04 (d2), G-01 (d7)
- name-variant [lenient term: DRYER A, dryerA]: dryerARegenReturn (d6)
- name-variant [lenient term: ads]: C1 (d5), IE-02 (d6), A2 (d5)
- name-variant [lenient term: stackMonitor, stackMonitorIndependence]: Sn5 (d5)
- mention-not-extracted [stop-listed]: G-00 (d6)
- typed-link-only: interfaceEdge (d6), G4 (d4), Sn3 (d4)
- structural [attribute-of]: releaseRate (d7)
- structural [fta-input]: G-02 (d5), G-03 (d3)
- structural [fta-input+fta-output]: G-05 (d7), G-09 (d3)
- structural [fta-output]: IE-06 (d6)
- structural [gsn-InContextOf]: C2 (d5), A1 (d5)
- structural [gsn-SupportedBy]: S1 (d3), S2 (d5)
- typed-link+structural [gsn-SupportedBy+traceability]: G2 (d2)
- cascade: releaseRate (d8), REQ-TRIT-007 (d6), REQ-TRIT-021 (d6), IE-01 (d7), IE-03 (d4)

**LENIENT.** 16 missed of 133. By class: cascade 1, mention-not-extracted 1, structural 10, typed-link+structural 1, typed-link-only 3.

- mention-not-extracted [stop-listed]: G-00 (d6)
- typed-link-only: interfaceEdge (d6), G4 (d4), Sn3 (d4)
- structural [fta-input]: G-03 (d3)
- structural [fta-input+fta-output]: G-02 (d5), G-05 (d7), G-09 (d3)
- structural [fta-output]: IE-01 (d7), IE-06 (d6)
- structural [gsn-InContextOf]: C2 (d5), A1 (d5)
- structural [gsn-SupportedBy]: S1 (d3), S2 (d5)
- typed-link+structural [gsn-SupportedBy+traceability]: G2 (d2)
- cascade: IE-03 (d4)

### Misses for controller

**EXACT.** 28 missed of 133. By class: cascade 5, mention-not-extracted 1, name-variant 8, structural 10, typed-link+structural 1, typed-link-only 3.

- name-variant [lenient term: BLOWER, blower]: Sn11 (d6)
- name-variant [lenient term: CHANGEOVER]: IE-04 (d4), G-01 (d6)
- name-variant [lenient term: DRYER A, dryerA]: dryerARegenReturn (d8)
- name-variant [lenient term: ads]: C1 (d5), IE-02 (d5), A2 (d5)
- name-variant [lenient term: stackMonitor, stackMonitorIndependence]: Sn5 (d7)
- mention-not-extracted [stop-listed]: G-00 (d6)
- typed-link-only: interfaceEdge (d8), G4 (d3), Sn3 (d2)
- structural [attribute-of]: releaseRate (d9)
- structural [fta-input]: G-02 (d4), G-03 (d4)
- structural [fta-input+fta-output]: G-05 (d6), G-09 (d5)
- structural [fta-output]: IE-06 (d5)
- structural [gsn-InContextOf]: C2 (d5), A1 (d5)
- structural [gsn-SupportedBy]: S1 (d3), S2 (d5)
- typed-link+structural [gsn-SupportedBy+traceability]: G2 (d4)
- cascade: releaseRate (d10), REQ-TRIT-007 (d6), REQ-TRIT-021 (d6), IE-01 (d7), IE-03 (d5)

**LENIENT.** 16 missed of 133. By class: cascade 1, mention-not-extracted 1, structural 10, typed-link+structural 1, typed-link-only 3.

- mention-not-extracted [stop-listed]: G-00 (d6)
- typed-link-only: interfaceEdge (d8), G4 (d3), Sn3 (d2)
- structural [fta-input]: G-03 (d4)
- structural [fta-input+fta-output]: G-02 (d4), G-05 (d6), G-09 (d5)
- structural [fta-output]: IE-01 (d7), IE-06 (d5)
- structural [gsn-InContextOf]: C2 (d5), A1 (d5)
- structural [gsn-SupportedBy]: S1 (d3), S2 (d5)
- typed-link+structural [gsn-SupportedBy+traceability]: G2 (d4)
- cascade: IE-03 (d5)

### Text-only hits

These are elements whose first-finding hop is not a thread edge: the term came from an element that is not adjacent in the thread, or reached the element through a context segment. Because the thread is connected, every such element is still inside T_∞.

- EXACT: 7430 text-only first findings over 134 starts. Most frequent terms: `dewpoint` 829, `controller` 697, `recombiner` 636, `condenser` 531, `blower` 528, `REQ-ADS-007` 381, `REQ-ADS-002` 304, `REQ-ADS-001` 296, `ADSChangeover` 235, `dryerB` 234, `activeDryer` 220, `dryerA` 219, `dewpointMonitor` 215, `changeoverValves` 214, `bedSaturation` 212. Beyond-depth hits (M_k \ T_k) summed for k=1/2/3: 104 / 908 / 2428.
- LENIENT: 12504 text-only first findings over 134 starts. Most frequent terms: `CHANGEOVER` 2712, `ads` 2558, `RECOMBINER` 853, `BLOWER` 818, `DEWPOINT` 802, `CONDENSER` 670, `CONTROLLER` 637, `DRYER A` 635, `BACKUP` 557, `DRYER B` 470, `stackMonitor` 470, `bedSaturation` 337, `activeDryer` 243, `releaseRate` 235, `REQ-ADS-001` 122. Beyond-depth hits (M_k \ T_k) summed for k=1/2/3: 257 / 4367 / 9437.
- EXACT: the share of found elements whose first-finding hop is a thread edge has median 35% [33–36%].
- LENIENT: the share of found elements whose first-finding hop is a thread edge has median 11% [9–12%].
- dryerA, EXACT: 69 of 105 found elements were first reached through a non-thread hop, 36 of them in an earlier round than their thread depth. Examples: dewpoint via `dewpoint` from FMEDA row 7 (round 2, thread depth 6); saturationTimeConstant via `ADSChangeover` from ADS Changeover Transient_Modelica (round 4, thread depth 1); activeDryer via `activeDryer` from FMEDA row 7 (round 3, thread depth 4); bedSaturation via `bedSaturation` from FMEDA row 7 (round 3, thread depth 2); IE-09 via `condenser` from ads (round 4, thread depth 4). The full list is in the JSON.
- dryerA, LENIENT: 104 of 117 found elements were first reached through a non-thread hop, 83 of them in an earlier round than their thread depth. Examples: tSat via `bedSaturation` from FMEDA row 7 (round 2, thread depth 2); releaseRate via `releaseRate` from ads (round 3, thread depth 8); BE-05 via `CHANGEOVER` from FMEDA row 7 (round 2, thread depth 2); dewpoint via `DEWPOINT` from FMEDA row 7 (round 2, thread depth 6); saturationTimeConstant via `CHANGEOVER` from FMEDA row 7 (round 2, thread depth 1). The full list is in the JSON.
- controller, EXACT: 59 of 105 found elements were first reached through a non-thread hop, 46 of them in an earlier round than their thread depth. Examples: dewpoint via `dewpoint` from ADS Controller Implementation (round 2, thread depth 8); saturationTimeConstant via `ADSChangeover` from changeoverPeriod (round 2, thread depth 3); activeDryer via `activeDryer` from ADS Controller Implementation (round 2, thread depth 2); bedSaturation via `bedSaturation` from ADS Controller Implementation (round 3, thread depth 4); IE-09 via `condenser` from ads (round 3, thread depth 6). The full list is in the JSON.
- controller, LENIENT: 95 of 117 found elements were first reached through a non-thread hop, 84 of them in an earlier round than their thread depth. Examples: releaseRate via `releaseRate` from controller (round 3, thread depth 10); BE-05 via `CHANGEOVER` from controller (round 2, thread depth 4); dewpoint via `DEWPOINT` from ADS Controller Implementation (round 2, thread depth 8); saturationTimeConstant via `ADSChangeover` from changeoverPeriod (round 2, thread depth 3); activeDryer via `activeDryer` from controller (round 2, thread depth 2). The full list is in the JSON.
- modelica, EXACT: 69 of 105 found elements were first reached through a non-thread hop, 44 of them in an earlier round than their thread depth. Examples: dewpoint via `dewpoint` from ADS Controller Implementation (round 3, thread depth 8); saturationTimeConstant via `ADSChangeover` from ADS Changeover Transient_Modelica (round 1, thread depth 2); activeDryer via `activeDryer` from ADS Controller Implementation (round 3, thread depth 3); bedSaturation via `bedSaturation` from ADS Controller Implementation (round 4, thread depth 5); IE-09 via `condenser` from ads (round 4, thread depth 6). The full list is in the JSON.
- modelica, LENIENT: 107 of 117 found elements were first reached through a non-thread hop, 86 of them in an earlier round than their thread depth. Examples: releaseRate via `releaseRate` from minDecontaminationFactor (round 3, thread depth 10); BE-05 via `CHANGEOVER` from minDecontaminationFactor (round 2, thread depth 4); dewpoint via `DEWPOINT` from ADS Controller Implementation (round 3, thread depth 8); saturationTimeConstant via `ADSChangeover` from ADS Changeover Transient_Modelica (round 1, thread depth 2); activeDryer via `activeDryer` from ADS Controller Implementation (round 3, thread depth 3). The full list is in the JSON.
- REQ-ADS-007, EXACT: 66 of 105 found elements were first reached through a non-thread hop, 52 of them in an earlier round than their thread depth. Examples: dewpoint via `dewpoint` from ADS Controller Implementation (round 2, thread depth 7); saturationTimeConstant via `ADSChangeover` from ADS Changeover Transient_Modelica (round 3, thread depth 4); activeDryer via `activeDryer` from ADS Controller Implementation (round 2, thread depth 5); bedSaturation via `bedSaturation` from ADS Controller Implementation (round 3, thread depth 5); IE-09 via `condenser` from ads (round 3, thread depth 7). The full list is in the JSON.
- REQ-ADS-007, LENIENT: 100 of 117 found elements were first reached through a non-thread hop, 89 of them in an earlier round than their thread depth. Examples: releaseRate via `releaseRate` from REQ-ADS-007 (round 3, thread depth 9); BE-05 via `CHANGEOVER` from ADS Controller Implementation (round 2, thread depth 5); dewpoint via `DEWPOINT` from ADS Controller Implementation (round 2, thread depth 7); saturationTimeConstant via `CHANGEOVER` from ADS Controller Implementation (round 2, thread depth 4); activeDryer via `activeDryer` from ADS Controller Implementation (round 2, thread depth 5). The full list is in the JSON.

## Deviations

- Before the first comparative run, a segmentation dry-run showed that the SysML lexicon regex also matched prose inside doc comments ('interface carrying TritiatedAir' put the word 'carrying' in the lexicon). The lexicon is now built from parsed declaration headers only, as P4 specifies. No result had been computed when this was fixed.
- Also before the first complete run, the results-marker split was changed to use only the stand-alone marker line, because the introduction mentions the marker text. This is an I/O fix with no effect on any number.
- After the first complete run, the reporting was extended without changing the protocol or any computed number: the lenient term(s) that produce each EXACT name-variant miss, the fixpoint-size distribution, the list of starts with a fixpoint below 20, the share of first findings whose hop is a thread edge, and a summarised list of per-scenario text-only hits. Per-start JSON records were compacted (missed element ids and counts instead of full lists, 9.7 MB -> 1.4 MB); the full lists are kept for the four named scenarios.
- Protocol amendment A1 (2026-11-14, before the re-run on the thread with SysML-to-Modelica value bindings; no result on the extended thread had been computed). The identity space gained three SysML attributes and three Modelica parameters, for which P3/P4 had no rule. A1 extends P3 and P4 the way they already treat SysML attribute usages: an attribute usage declared in a requirement usage is an element segment, as one declared in a part definition is; each Modelica parameter declaration (`parameter Real <name> = ...;`) of an identity-space parameter is an element segment and is cut out of the Modelica model's segment; a Modelica parameter's visible name is its declared name; every parameter name declared in the Modelica file joins the lexicon; parameter-of and sim-binding are structural edge kinds in the P9 audit. Nothing else changed.

## Limitations

- This is a simulation of name-based search, not a human study. A real engineer also reads diagrams, uses domain knowledge and asks colleagues. Equally, a real engineer may stop early or skip hits. Neither is modelled.
- The procedure is generous to manual tracing in one respect: every hit is read and every cited name is followed to a fixpoint, with no fatigue and no budget. Effort is counted rather than limited.
- The procedure is strict in another respect. Relationships carried only by diagram structure (GSN argument edges, FTA gate wiring) or by typed links are invisible to text search. The GSN edges are absent from the deposited GSN file. LENIENT+DIAGRAM bounds the FTA part of this effect.
- The twin document is reconstructed from the twin elements' labels in namespace/ads-namespace.json, because the procedure reads names, not the twin model file. Mesh names were cross-checked against the GLB.
- Manual round k and thread depth k are different units: one round can follow several textual hops, and one thread hop may need several rounds. The fixpoint-vs-depth-k recall is reported alongside for this reason.
- Recall is measured against the thread's own closure, which includes links authored to complete the thread (origin 'completion', pending engineering review). The comparison therefore shows what text search recovers of this thread, not of an independent ground truth.
- The thread is connected (every unbounded closure is 133 elements). Recall against T_∞ therefore measures coverage of the whole model set, and 'false hits' can only be judged per hop or per depth.
- The stop list, the lexicon and the names of the executable models are fixed choices. Other reasonable choices would move the numbers. They were fixed before the first run and not tuned.
