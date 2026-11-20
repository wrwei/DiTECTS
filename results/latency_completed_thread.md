# Re-verification results (2026-11-20T07:36:12+0000)

Condition: `latency`  Repository: `/Users/ranwei/Git/DiTECTS`


## Impact-traversal latency (namespace/impact.py)
```
{
 "unbounded": {
  "n": 4050,
  "starts": 135,
  "reps": 30,
  "median_ms": 0.0552,
  "p95_ms": 0.0617,
  "max_ms": 0.0938,
  "cone_median": 134,
  "cone_max": 134
 },
 "depth5": {
  "n": 4050,
  "starts": 135,
  "reps": 30,
  "median_ms": 0.0254,
  "p95_ms": 0.039,
  "max_ms": 0.0595,
  "cone_median": 76,
  "cone_max": 128
 },
 "index_build_ms": 0.086,
 "graph": {
  "nodes": 135,
  "edges": 218
 },
 "host": {
  "python": "3.9.6",
  "platform": "macOS-26.5.2-arm64-arm-64bit",
  "machine": "arm64",
  "cpus": 10
 }
}
```
