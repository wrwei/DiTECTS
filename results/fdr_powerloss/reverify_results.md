# Re-verification results (2026-11-15T08:38:34+0000)

Condition: `all`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn9 | ADS Controller Refinement | fdr | PASS | 0.88 | 21 assertions passed, 0 failed |

## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| F1 | fault | fdr | FAIL | detected | 0.76 | Second powerLoss transition from NormalOperation targeting Changeover (nondeterministic response to power loss) |
| F2 | fault | fdr | FAIL | detected | 0.75 | backupRestored transition out of FailSafe deleted (FailSafe becomes a sink) |
| F3 | fault | fdr | FAIL | detected | 0.73 | powerLoss in Changeover leads to NormalOperation instead of FailSafe |
| FC1 | control | fdr | PASS | control passed | 0.74 | Swap the order of the two NormalOperation transitions ([] is commutative) |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| fdr | 3/3 | 0 | 0 | 0 | 1/1 |
| Total | 3/3 | 0 | 0 | 0 | 1/1 |

## Stale evidence: ST1-tCycle
Change: ADSController::changeoverPeriod 7000 s -> 9000 s (SysML design attribute), propagated to ADSChangeover.tCycle through the sim-binding  
Flagged by namespace/impact.py closure (unbounded): Sn10@3, Sn2@3, Sn3@3, Sn7@3, Sn8@3, Sn9@3, Sn1@4, Sn11@7, Sn4@7, Sn5@8, Sn6@8

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn9 | fdr | False | PASS | 21 assertions passed, 0 failed |

## Stale evidence: ST2-initialBed
Change: ADSController.activeDryer default Dryer::BedA -> Dryer::BedB, propagated to the Dafny, Isabelle, CSP and Java artefacts  
Flagged by namespace/impact.py closure (unbounded): Sn10@2, Sn2@2, Sn3@2, Sn7@2, Sn8@2, Sn9@2, Sn1@3, Sn11@6, Sn4@6, Sn5@7, Sn6@7

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn9 | fdr | True | PASS | 21 assertions passed, 0 failed |

## Impact-traversal latency (namespace/impact.py)
```
{
 "unbounded": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.054,
  "p95_ms": 0.0638,
  "max_ms": 0.5937,
  "cone_median": 133.0,
  "cone_max": 133
 },
 "depth5": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.025,
  "p95_ms": 0.0381,
  "max_ms": 0.1438,
  "cone_median": 75.0,
  "cone_max": 127
 },
 "index_build_ms": 0.096,
 "graph": {
  "nodes": 134,
  "edges": 216
 },
 "host": {
  "python": "3.9.6",
  "platform": "macOS-26.5.2-arm64-arm-64bit",
  "machine": "arm64",
  "cpus": 10
 }
}
```
