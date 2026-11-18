# Manual change-impact study: protocol

Fixed before the first session (16 November 2026). Changes after any session has started are recorded in
the *Amendments* section with their date and reason.

## Question

How long does it take an engineer without the digital thread to answer the review question

> What must be reconsidered if the duty bed's capacity changes?

for the ADS models, and how much of the thread's answer does the engineer find?

## Design

* **Participants.** Two to four engineers or researchers with an MBSE background who have not seen the ADS
  case study, the demonstration or this repository. People who have done this task before are not eligible;
  if they take part, report them separately. Record background on the Session sheet.
* **Ethics and consent.** Check your institution's requirements before running sessions; a low-risk
  procedure may still need approval. Obtain written consent covering the recording sheet and its
  deposit under an anonymous participant code.
* **One task per participant.** The change is to `dryerA`, the duty dryer bed in the SysML design model.
* **Materials.** The folder `materials/` (built by `build_materials.py`), opened in a text editor with
  find-in-files (for example VS Code). It contains the eleven model documents with the content the counted
  manual search reads: the two SysML files, the FMEDA, the fault tree, the GSN safety case, the Dafny,
  Isabelle, CSP, Java and Modelica sources, and the digital twin's part and signal names. Typed links, the
  identity space, the completion overlay and stored identifier references are not included.
* **Not allowed.** The repository, the static demonstration, the paper, other people, websites and AI
  assistants. The experimenter does not answer questions about the models.

## Procedure

1. Give the participant `recording-sheet.xlsx` and the materials. Read out the Task and Procedure rows of the
   Instructions sheet. Allow five minutes to open the documents and try find-in-files; this is not timed.
2. Record the start time on the Session sheet. From here every activity counts: reading the models,
   searching and recording.
3. **Round 1:** the participant searches all eleven documents for the dryer bed ('dryerA', 'DRYER A' or
   any other name they see for it) and records every element that the matches show it may relate to.
4. **Round 2 onwards:** the participant searches for each element recorded in the previous round and
   records any new elements. Each search is logged on the Search log sheet and each element on the Elements
   sheet, with the round and clock time.
5. **Stop** when a round records no new element, or at six hours of working time. Record the end time and the
   reason for stopping. Breaks are logged and excluded from working time.
6. The participant confirms on the Session sheet that only the materials folder was used.

## Scoring

`score.py` matches each row of the Elements sheet to one element of the identity space, using the document
and the name as written (case, spaces, hyphens and underscores ignored; twin names qualified with *part* or
*signal*). Executable models count as one element each, Modelica parameters separately.

* Rows the scorer cannot match are listed in the scored report. Two authors adjudicate each one
  independently, entering the agreed identifier in the sheet's last column; disagreements and their
  resolution are recorded in `results/adjudication.md`. Adjudication happens before recall is reported.
* The answer key is the thread's unbounded closure from `dryerA`: 133 elements. Recall is found / 133.

## Pre-specified outcomes

For each participant: working time (minutes), rounds, searches logged, elements found and recall, recall by
thread depth, cumulative elements by round, and whether G2 and S1 were found. Reported alongside, without
pooling into a single estimate: the counted manual search (117 of 133, 88%; an estimated 1.4 to 5.8 hours).

## Data

Completed sheets are saved as `results/<code>.xlsx` with participant codes only (P1, P2, ...). Run
`python3 studies/manual-impact/score.py results/<code>.xlsx` and keep the generated `-scored.json` and
`-scored.md`. Do not edit a sheet after scoring other than in the adjudication column.

## Files

| File | Purpose |
|---|---|
| `build_materials.py` | Builds `materials/` from the deposited models; `--check` verifies it is current |
| `materials/` | The eleven documents given to participants, with `MANIFEST.txt` checksums |
| `recording-sheet.xlsx` | Blank recording sheet: Instructions, Session, Search log, Elements |
| `score.py` | Scores a completed sheet against the 133-element answer key; `--self-test` checks the matcher |
| `../../tests/test_manual_study.py` | Checks the scorer end to end against the counted manual search (117 of 133) |

## Amendments

* **17 November 2026, after sessions P1 and P2.** FMEDA row 11 was reclassified as safety-related (periodic leak
  test, 60% coverage) and the completion link `Sn2-to-FMEA-Valves` gained row 11 as a second target. `materials/`
  is kept as both participants used it, so `materials/03-fmeda/fmeda.csv` still shows row 11 as not safety-related
  and `build_materials.py --check` reports the materials stale against the current models. The answer key is
  unchanged (133 elements from `dryerA`, the same depths), and both sessions score the same.
* **18 November 2026, after sessions P1 and P2.** The unmatched rows of both sessions were adjudicated by one
  author, not by two authors independently as specified under Scoring. The four accepted rows and their reasons
  are in `results/adjudication.md`; the answer key and the scorer are unchanged.
