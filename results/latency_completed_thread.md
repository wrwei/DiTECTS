# Re-verification results (2026-11-14T19:31:10+0000)

Condition: `latency`  Repository: `.`


## Impact-traversal latency (namespace/impact.py)
```
{
 "unbounded": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.054,
  "p95_ms": 0.0604,
  "max_ms": 1.0715,
  "cone_median": 133.0,
  "cone_max": 133
 },
 "depth5": {
  "n": 4020,
  "starts": 134,
  "reps": 30,
  "median_ms": 0.0245,
  "p95_ms": 0.0375,
  "max_ms": 0.0813,
  "cone_median": 75.0,
  "cone_max": 127
 },
 "index_build_ms": 0.083,
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
