# Re-verification results (2026-11-17T15:23:05+0000)

Condition: `latency`  Repository: `/Users/ranwei/Git/DiTECTS`


## Impact-traversal latency (namespace/impact.py)
```
{
 "unbounded": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.0553,
  "p95_ms": 0.0638,
  "max_ms": 0.1735,
  "cone_median": 133.0,
  "cone_max": 133
 },
 "depth5": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.0255,
  "p95_ms": 0.0386,
  "max_ms": 0.057,
  "cone_median": 75.0,
  "cone_max": 127
 },
 "index_build_ms": 0.086,
 "graph": {
  "nodes": 134,
  "edges": 217
 },
 "host": {
  "python": "3.9.6",
  "platform": "macOS-26.5.2-arm64-arm-64bit",
  "machine": "arm64",
  "cpus": 10
 }
}
```
