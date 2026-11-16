#!/usr/bin/env python3
"""Build impact-app.html by embedding the namespace in the app template.

The app is a single self-contained HTML file so a reviewer can open it from
disk with no web server, no build step, no dependencies and no network. That
requires the graph to be embedded rather than fetched: a browser opening a
file:// page blocks XHR and fetch against a sibling file.

Embedding means the app carries a copy of the data, so this script is the only
way it should ever be produced -- edit impact-app.template.html, then run:

    ./build_app.py            # regenerate impact-app.html
    ./build_app.py --check    # verify the committed app matches the namespace

--check exits non-zero if they have diverged, which is the guard against the
app silently reporting stale figures after the namespace is regenerated.
"""
import json, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
NAMESPACE = os.path.join(HERE, "ads-namespace.json")
TEMPLATE = os.path.join(HERE, "impact-app.template.html")
OUTPUT = os.path.join(HERE, "impact-app.html")
MARKER = "__NAMESPACE_JSON__"


def render():
    with open(NAMESPACE) as f:
        ns = json.load(f)
    with open(TEMPLATE) as f:
        template = f.read()

    if template.count(MARKER) != 1:
        raise SystemExit(
            f"template must contain {MARKER} exactly once, "
            f"found {template.count(MARKER)}"
        )

    # Compact, deterministic, and safe to sit inside a <script> element: an
    # embedded "</script>" in any string field would otherwise close the block
    # early, so escape the only sequence that can do that.
    payload = json.dumps(ns, separators=(",", ":"), sort_keys=True)
    payload = payload.replace("</", "<\\/")
    return template.replace(MARKER, payload), ns


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify the committed app is current; do not write")
    args = ap.parse_args()

    html, ns = render()

    if args.check:
        if not os.path.exists(OUTPUT):
            print("impact-app.html is missing; run ./build_app.py")
            return 1
        with open(OUTPUT) as f:
            current = f.read()
        if current != html:
            print("impact-app.html is stale -- the namespace or template has "
                  "changed since it was built. Run ./build_app.py")
            return 1
        print("impact-app.html is current (%d elements, %d edges)"
              % (len(ns["nodes"]), len(ns["edges"])))
        return 0

    with open(OUTPUT, "w") as f:
        f.write(html)
    print("wrote %s (%d bytes) -- %d elements, %d edges, %d with element UUIDs"
          % (os.path.basename(OUTPUT), len(html), len(ns["nodes"]),
             len(ns["edges"]), sum(1 for n in ns["nodes"] if n.get("uuid"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
