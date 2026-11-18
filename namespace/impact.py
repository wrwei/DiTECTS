#!/usr/bin/env python3
"""Impact analysis over the ADS thread.

Reads ads-namespace.json: every ADS model element that participates in a
cross-concern relationship, in one namespace, with the edges between them.
Impact analysis is then a breadth-first traversal -- no tooling required.

  ./impact.py dryerA                 # closure, grouped by depth
  ./impact.py dryerA --depth 2       # bounded
  ./impact.py dryerA --to G1         # shortest path, hop by hop
  ./impact.py --list requirements    # what is in the namespace
  ./impact.py --stats                # counts, by concern and edge kind
"""
import json, argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def load(path=None):
    with open(path or os.path.join(HERE, "ads-namespace.json")) as f:
        return json.load(f)

def index(ns):
    node = {n["id"]: n for n in ns["nodes"]}
    adj = collections.defaultdict(list)
    for e in ns["edges"]:
        adj[e["source"]].append((e["target"], e["kind"], e.get("name")))
        adj[e["target"]].append((e["source"], e["kind"], e.get("name")))
    return node, adj

def resolve(node, query):
    """Accept an id, a label, or a short name.

    Requirements are labelled by their declaredName (dischargeLimit) but cited
    in the article by their short name (REQ-TRIT-014), so both must resolve or
    a reader cannot reproduce the published traversals.
    """
    if query in node:
        return query
    for key in ("label", "shortName"):
        exact = [i for i, n in node.items() if n.get(key) == query]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise SystemExit("ambiguous: %r matches %d elements" % (query, len(exact)))
    lowered = query.lower()
    for key in ("label", "shortName"):
        loose = [i for i, n in node.items() if (n.get(key) or "").lower() == lowered]
        if len(loose) == 1:
            return loose[0]
        if len(loose) > 1:
            raise SystemExit("ambiguous: %r matches %d elements" % (query, len(loose)))
    raise SystemExit("no element with id, label or short name %r" % query)

def show(n):
    name = n.get("label") or n["id"]
    if n.get("shortName"):
        name = "%s (%s)" % (name, n["shortName"])
    return "%-38s %-20s %s" % (name, n["concern"], (n.get("text") or "")[:46])

def impact(node, adj, start, max_depth=None):
    """Breadth-first closure. Returns [(depth, id, via_kind), ...]."""
    seen, frontier, out, depth = {start}, [start], [], 0
    while frontier and (max_depth is None or depth < max_depth):
        depth += 1
        nxt = []
        for u in frontier:
            for v, kind, _ in sorted(adj[u]):
                if v not in seen:
                    seen.add(v); nxt.append(v); out.append((depth, v, kind))
        frontier = nxt
    return out

def path(node, adj, start, target):
    prev = {start: None}
    q = collections.deque([start])
    while q:
        u = q.popleft()
        if u == target:
            break
        for v, kind, name in adj[u]:
            if v not in prev:
                prev[v] = (u, kind, name); q.append(v)
    if target not in prev:
        return None
    out, cur = [], target
    while prev[cur]:
        u, kind, name = prev[cur]
        out.append((cur, kind, name)); cur = u
    return list(reversed(out))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("element", nargs="?", help="id or label to start from")
    ap.add_argument("--depth", type=int, help="bound the traversal")
    ap.add_argument("--to", help="shortest path to this element")
    ap.add_argument("--list", metavar="CONCERN", help="list elements in a concern")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--namespace", help="path to ads-namespace.json")
    a = ap.parse_args()
    ns = load(a.namespace)
    node, adj = index(ns)

    if a.stats:
        print("%d elements, %d edges, one identity space\n" % (len(ns["nodes"]), len(ns["edges"])))
        print("by concern:")
        for c, k in collections.Counter(n["concern"] for n in ns["nodes"]).most_common():
            print("  %-18s %3d" % (c, k))
        print("\nby edge kind:")
        for c, k in collections.Counter(e["kind"] for e in ns["edges"]).most_common():
            print("  %-18s %3d" % (c, k))
        return

    if a.list:
        for n in sorted(ns["nodes"], key=lambda x: str(x.get("label"))):
            if n["concern"] == a.list:
                print(" ", show(n))
        return

    if not a.element:
        ap.error("give an element, or --list / --stats")
    start = resolve(node, a.element)

    if a.to:
        target = resolve(node, a.to)
        p = path(node, adj, start, target)
        if not p:
            print("%s does not reach %s" % (node[start].get("label"), node[target].get("label"))); return
        print("%s" % node[start].get("label"))
        for i, (v, kind, name) in enumerate(p, 1):
            print("  %d. -[%s%s]-> %s" % (i, kind, "/" + name if name else "", node[v].get("label") or v))
        return

    hits = impact(node, adj, start, a.depth)
    print("impact of changing %s (%s)\n" % (node[start].get("label"), node[start]["concern"]))
    for d in sorted({h[0] for h in hits}):
        at = [h for h in hits if h[0] == d]
        print("depth %d  (%d)" % (d, len(at)))
        for _, v, kind in sorted(at, key=lambda h: str(node[h[1]].get("label"))):
            print("    %-14s %s" % (kind, show(node[v])))
    print("\n%d elements across %d concerns" %
          (len(hits), len({node[v]["concern"] for _, v, _ in hits})))

if __name__ == "__main__":
    main()
