# Re-verification results (2026-11-15T08:20:08+0000)

Condition: `all`  Repository: `<repo>`

## Baseline
| Solution | Evidence | Checker | Verdict | s | Detail |
|---|---|---|---|---|---|
| Sn8 | ADS Controller Behaviour | isabelle | PASS | 41.77 | Finished ADSController_Check |

## Seeded mutants
| Mutant | Class | Checker | Verdict | Outcome | s | Description |
|---|---|---|---|---|---|---|
| I1 | fault | isabelle | FAIL | detected | 40.47 | NormalOperationToFailSafe leaves dewpointHigh enabled in FailSafe |
| I2 | fault | isabelle | FAIL | detected | 39.2 | New Dryer value Offline; Init puts no bed on duty |
| I3 | fault | isabelle | FAIL | detected | 47.12 | Init starts with an empty trace, violating inv tr \<noteq> [] |
| I4 | fault | isabelle | FAIL | detected | 32.67 | FailSafeToNormalOperation removed from the machine operations (no exit from FailSafe) |
| IC1 | control | isabelle | PASS | control passed | 37.95 | Edit the introduction text block |

| Checker | Faults detected | Faults survived | Timed out | Not assessed | Controls passed |
|---|---|---|---|---|---|
| isabelle | 4/4 | 0 | 0 | 0 | 1/1 |
| Total | 4/4 | 0 | 0 | 0 | 1/1 |

## Stale evidence: ST1-tCycle
Change: ADSController::changeoverPeriod 7000 s -> 9000 s (SysML design attribute), propagated to ADSChangeover.tCycle through the sim-binding  
Flagged by namespace/impact.py closure (unbounded): Sn10@3, Sn2@3, Sn3@3, Sn7@3, Sn8@3, Sn9@3, Sn1@4, Sn11@7, Sn4@7, Sn5@8, Sn6@8

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn8 | isabelle | False | PASS | Finished ADSController_Check |

## Stale evidence: ST2-initialBed
Change: ADSController.activeDryer default Dryer::BedA -> Dryer::BedB, propagated to the Dafny, Isabelle, CSP and Java artefacts  
Flagged by namespace/impact.py closure (unbounded): Sn10@2, Sn2@2, Sn3@2, Sn7@2, Sn8@2, Sn9@2, Sn1@3, Sn11@6, Sn4@6, Sn5@7, Sn6@7

| Solution | Checker | Artefact changed | Verdict | Detail |
|---|---|---|---|---|
| Sn8 | isabelle | True | PASS | Finished ADSController_Check |

## Impact-traversal latency (namespace/impact.py)
```
{
 "unbounded": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.0585,
  "p95_ms": 0.0912,
  "max_ms": 0.5532,
  "cone_median": 133.0,
  "cone_max": 133
 },
 "depth5": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.0275,
  "p95_ms": 0.045,
  "max_ms": 0.1591,
  "cone_median": 75.0,
  "cone_max": 127
 },
 "index_build_ms": 0.156,
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
