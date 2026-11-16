#!/usr/bin/env python3
"""Degree 0 simulation bindings: a SysML attribute and a Modelica parameter that must hold equal values.

Standard library only. Shared by tools/derive_from_export.py (parameter values from the export's Modelica
source), tools/coverage.py (check B1: bound values agree in the thread and in the repository files) and
tools/reverify.py (the modelica runner, which sets every bound parameter from its SysML attribute before it
simulates, so a design change reaches the simulation through the binding).

A binding is the namespace edge  ModelicaParameter -[sim-binding]-> SAttributeUsage, or the typed link that
records it (kind traceability, relation binds), which replaces that edge.  Values flow from the
attribute (the design) to the parameter (the simulation). Degree 0 means equality of values; no unit or
dimension conversion is applied, and the unit is recorded on the parameter node.

  python3 tools/sim_bindings.py            # list the bindings and the values in the repository files
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SYSML_DIR = os.path.join("models", "sysml")
NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
OWNER_KEYWORDS = r"(?:part def|item def|attribute def|requirement def|requirement|part|item)"


def _blank_comments(text):
    """Comments replaced by spaces (offsets kept), so braces inside doc text cannot confuse matching."""
    return re.sub(r"/\*.*?\*/|//[^\n]*", lambda m: " " * len(m.group(0)), text, flags=re.S)


def _body(text, owner):
    """(start, end) of the brace body of the declaration named `owner`, or None."""
    clean = _blank_comments(text)
    rx = re.compile(r"\b%s\s+(?:<'[^']*'>\s+)?'?%s'?(?=[\s:{])[^{;]*\{" % (OWNER_KEYWORDS, re.escape(owner)))
    m = rx.search(clean)
    if not m:
        return None
    depth, i = 1, m.end()
    while i < len(clean) and depth:
        depth += {"{": 1, "}": -1}.get(clean[i], 0)
        i += 1
    return m.end(), i - 1


def split_qualified(qn):
    parts = [p.strip("'") for p in qn.split("::")]
    return parts[-2], parts[-1]


def sysml_attribute_value(text, owner, attribute):
    """Literal value of `attribute owner::attribute ... = <number>` in SysML v2 text, or None."""
    span = _body(text, owner)
    if not span:
        return None
    body = _blank_comments(text)[span[0]:span[1]]
    m = re.search(r"\battribute\s+'?%s'?\s*(?::[^=;{]*)?=\s*(%s)" % (re.escape(attribute), NUMBER), body)
    return float(m.group(1)) if m else None


def sysml_value(root, qualified_name):
    """Look the attribute up in every .sysml file under root/models/sysml; (value, file) or (None, None)."""
    owner, attr = split_qualified(qualified_name)
    d = os.path.join(root, SYSML_DIR)
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".sysml"):
            v = sysml_attribute_value(open(os.path.join(d, f), encoding="utf-8").read(), owner, attr)
            if v is not None:
                return v, os.path.join(SYSML_DIR, f)
    return None, None


def _param_rx(name):
    return re.compile(r"(\bparameter\s+Real\s+%s\s*=\s*)(%s)" % (re.escape(name), NUMBER))


def modelica_parameter(text, name):
    """(value, description, unit) of `parameter Real <name> = <number> "<description> [unit]"`, or None."""
    m = re.search(r"\bparameter\s+Real\s+%s\s*=\s*(%s)\s*(?:\"([^\"]*)\")?" % (re.escape(name), NUMBER), text)
    if not m:
        return None
    desc = m.group(2)
    unit = re.search(r"\[([^\]]*)\]\s*$", desc or "")
    return float(m.group(1)), desc, (unit.group(1) if unit else None)


def set_modelica_parameter(text, name, value):
    """Rewrite the parameter's binding equation; returns (new text, number of declarations rewritten)."""
    lit = repr(float(value))
    return _param_rx(name).subn(lambda m: m.group(1) + lit, text)


def bindings(ns):
    """Every binding edge (sim-binding, or a typed link with relation binds), resolved: parameter node,
    attribute node, owning Modelica model node."""
    node = {n["id"]: n for n in ns["nodes"]}
    owner = {e["source"]: e["target"] for e in ns["edges"] if e["kind"] == "parameter-of"}
    out = []
    for e in ns["edges"]:
        if e["kind"] == "sim-binding" or (e["kind"] == "traceability" and e.get("relation") == "binds"):
            out.append({"parameter": node.get(e["source"]), "attribute": node.get(e["target"]),
                        "model": node.get(owner.get(e["source"])), "edge": e})
    return out


def main():
    ns = json.load(open(os.path.join(REPO, "namespace", "ads-namespace.json"), encoding="utf-8"))
    mo = open(os.path.join(REPO, "simulation", "modelica", "ADSChangeover.mo"), encoding="utf-8").read()
    for b in bindings(ns):
        p, a = b["parameter"], b["attribute"]
        sv, f = sysml_value(REPO, a["qualifiedName"])
        mv = modelica_parameter(mo, p["label"])
        print("%-10s <- %-62s thread %s = %s | files: %s = %s (%s), .mo = %s" % (
            p["label"], a["qualifiedName"], p.get("value"), a.get("value"), a["label"], sv, f, mv and mv[0]))


if __name__ == "__main__":
    sys.exit(main())
