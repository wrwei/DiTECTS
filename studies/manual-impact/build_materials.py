#!/usr/bin/env python3
"""Build the participant materials for the manual change-impact study.

Writes studies/manual-impact/materials/: the eleven ADS model documents a participant searches, with the same
content the counted manual search reads (tools/manual_trace.py, build_segments): no typed links, no identity
space, no completion overlay and no stored identifier references (FMEDA `traces` and `itemElement`, fault-tree
gate wiring, GSN edges). SysML and executable sources are copied unchanged; the FMEDA, fault tree, GSN safety
case and twin are written as plain tables of their visible fields.

  python3 studies/manual-impact/build_materials.py          # writes materials/ and materials/MANIFEST.txt
  python3 studies/manual-impact/build_materials.py --check  # exit 1 if materials/ differs

Standard library only.
"""
import csv, glob, hashlib, io, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "materials")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def documents():
    """{relative output path: text} for the eleven documents."""
    docs = {}
    docs["01-requirements/01-requirements.sysml"] = read("models/sysml/01-requirements.sysml")
    docs["02-design/02-design.sysml"] = read("models/sysml/02-design.sysml")

    f = json.loads(read("models/fmeda/ads-fmeda.json"))
    cols = [c for c in f["columns"] if c != "traces"]
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n")
    w.writerow(["row"] + cols)
    for r in f["rows"]:
        w.writerow(["row %d" % r["rowNumber"]] + ["" if r.get(c) is None else r.get(c) for c in cols])
    docs["03-fmeda/fmeda.csv"] = "# %s (%s): %s\n" % (f.get("modelName", ""), f.get("analysisKind", ""), f.get("description", "")) + buf.getvalue()

    ft = json.loads(read("models/fta/ads-fta.json"))
    lines = ["# %s" % " ".join(str(ft.get(k, "")) for k in ("modelName", "faultTreeName", "description")), "",
             "code | type | name | description"]
    for e in ft["elements"]:
        if e["@type"] == "FaultTree":
            lines.insert(1, "# " + " ".join(str(e.get(k, "")) for k in ("name", "polarity", "purpose", "notation")))
            continue
        lines.append(" | ".join([e["@id"], e["@type"], e.get("name") or "", e.get("description") or ""]))
    docs["04-fault-tree/fault-tree.txt"] = "\n".join(lines) + "\n"

    g = json.loads(read("models/safety-case/gsn-safety-case.json"))
    docs["05-gsn-safety-case/gsn-safety-case.txt"] = "node | type | text\n" + "\n".join(
        " | ".join([x["name"], x["type"], x.get("description") or ""]) for x in g) + "\n"

    for src in ["formal/dafny/ADSController.dfy"]:
        docs["06-dafny/" + os.path.basename(src)] = read(src)
    for p in sorted(glob.glob(os.path.join(ROOT, "formal/isabelle/*.thy"))) + [os.path.join(ROOT, "formal/isabelle/ROOT")]:
        docs["07-isabelle/" + os.path.basename(p)] = read(os.path.relpath(p, ROOT))
    for p in sorted(glob.glob(os.path.join(ROOT, "formal/csp/*.csp"))):
        docs["08-csp/" + os.path.basename(p)] = read(os.path.relpath(p, ROOT))
    for p in sorted(x for x in glob.glob(os.path.join(ROOT, "implementation/java/src/**"), recursive=True) if os.path.isfile(x)):
        rel = os.path.relpath(p, os.path.join(ROOT, "implementation/java"))
        docs["09-java/" + rel] = read(os.path.relpath(p, ROOT))
    docs["10-modelica/ADSChangeover.mo"] = read("simulation/modelica/ADSChangeover.mo")

    ns = json.loads(read("namespace/ads-namespace.json"))
    tw = ["kind | name | mesh or signal"]
    for n in ns["nodes"]:
        if n["concern"] == "digital-twin":
            tw.append(" | ".join([n["kind"], n["label"] or "", n.get("text") or ""]))
    docs["11-digital-twin/digital-twin.txt"] = "\n".join(tw) + "\n"
    return docs


def manifest(docs):
    return "".join("%s  %s\n" % (hashlib.sha256(t.encode("utf-8")).hexdigest(), p) for p, t in sorted(docs.items()))


def main():
    docs = documents()
    man = manifest(docs)
    if "--check" in sys.argv:
        ok = os.path.exists(os.path.join(OUT, "MANIFEST.txt")) and open(os.path.join(OUT, "MANIFEST.txt"), encoding="utf-8").read() == man
        print("materials current" if ok else "materials STALE"); sys.exit(0 if ok else 1)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for p, t in docs.items():
        dst = os.path.join(OUT, p); os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(t)
    with open(os.path.join(OUT, "MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write(man)
    print("wrote %d files in %d documents to %s" % (len(docs), len({p.split('/')[0] for p in docs}), os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
