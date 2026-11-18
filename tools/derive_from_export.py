#!/usr/bin/env python3
"""Derive the repository's structured views from the modelling tool's project export.

The deposited project export is the source of truth. This script regenerates,
from it, every file in this repository that is a re-shaping of that export
rather than an export in its own right:

  models/fta/ads-fta.json                  fault tree as structured JSON
  models/safety-case/gsn-safety-case.json  GSN argument: identity, type, label, claim
  models/safety-case/evidence-resolution.json  one evidence link, resolved record by record
  namespace/ads-namespace.json             the thread: identity-space elements and their edges

Completion overlay. models/traceability/completion.json holds traceability and analysis content
authored outside the platform to complete the thread (missing trace links, including links from FMEDA
rows and fault-tree events to the requirements their text cites, from FMEDA rows to the design parts
they analyse, from Modelica parameters to the SysML attributes they are bound to, and from Solutions
to the design elements their text names, safety-case Assumption A2 and Solution
Sn11, fault-tree events BE-05/BE-08 under a new gate G-09, three SysML attributes that carry the simulation's
design values, the Modelica parameters they set and the Degree 0 value bindings between them). Its records have the
export's own shapes and carry "origin": "completion"; they are applied to the export before any view is
derived, so every output stays consistent. --no-completion derives the export-only views.

The SysML interchange files (models/sysml/omg/) and the FMEDA JSON
(models/fmeda/) are produced by the platform's own OMG and FMEA JSON export
services and are not regenerated here.

Standard library only. Identities, labels and text are copied verbatim; the
only computed values are the 1-based FMEDA row numbers, which follow rowOrder
exactly as the platform's exports number them.

    ./tools/derive_from_export.py --export <export-dir>            # write
    ./tools/derive_from_export.py --export <export-dir> --check    # compare only
    ./tools/derive_from_export.py --export <export-dir> --report   # FTA checks
    ./tools/derive_from_export.py --export <export-dir> --no-completion --check
"""
import argparse, collections, glob, json, os, re, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_bindings as SB  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OID = lambda s: isinstance(s, str) and len(s) == 24 and all(c in "0123456789abcdef" for c in s)

NOTATION = {"Dafny Model": "Dafny", "Isabelle Model": "Isabelle/HOL", "FDR Model": "CSP/FDR",
            "Java Model": "Java", "ModelicaModel": "Modelica"}
GSN_ARGUMENT = ("Goal", "Strategy", "Solution", "Context", "Assumption", "Justification")


class Export:
    def __init__(self, d):
        self.dir = d
        rd = lambda f: json.load(open(os.path.join(d, f), encoding="utf-8"))
        one = lambda pat: [rd(os.path.basename(p)) for p in sorted(glob.glob(os.path.join(d, pat)))]
        many = lambda pat: [x for lst in one(pat) for x in lst]
        self.models = rd("models.json")
        self.links = rd("traceability.json")
        self.sysml = many("sysml-*-elements.json")
        self.sacm = many("gsn-*-elements.json")
        self.gsn_models = one("gsn-*-model.json")
        self.gsn_nodes = many("gsn-*-nodes.json")
        self.gsn_edges = many("gsn-*-edges.json")
        self.fmea_models = one("fmea-*-model.json")
        self.fmea_rows = many("fmea-*-rows.json")
        self.fta_models = one("fta-*-model.json")
        self.fta = many("fta-*-elements.json")
        self.modelica = one("modelica-*-model.json")
        self.twin = rd("digitaltwin-model.json")
        self.S = {e["_id"]: e for e in self.sysml}
        self.G = {e["_id"]: e for e in self.sacm}
        self.F = {e["_id"]: e for e in self.fta}
        self.R = {r["_id"]: r for r in self.fmea_rows}
        self.M = {m["_id"]: m for m in self.models}
        self.MO = {m["_id"]: m for m in self.modelica}
        self.TP = {p["dtPartId"]: p for p in self.twin.get("partMappings", [])}
        self.TB = {b["bindingId"]: b for b in self.twin.get("dataBindings", [])}
        self.MP = {}          # Modelica parameters declared as elements (completion overlay)
        self.sim_bindings = []  # Degree 0 SysML attribute -> Modelica parameter value bindings

    def apply_completion(self, c):
        """Overlay authored records (models/traceability/completion.json) on the export."""
        self.links += c.get("links", [])
        g = c.get("gsn", {})
        self.sacm += g.get("elements", [])
        self.gsn_nodes += g.get("nodes", [])
        self.gsn_edges += g.get("edges", [])
        self.G.update({e["_id"]: e for e in g.get("elements", [])})
        self.gsn_models[0]["modelElements"] = list(self.gsn_models[0]["modelElements"]) + [
            e["_id"] for e in g.get("elements", []) if e["__t"] in GSN_ARGUMENT]
        f = c.get("fta", {})
        self.fta += f.get("elements", [])
        self.F.update({e["_id"]: e for e in f.get("elements", [])})
        self.fta_models[0]["modelElements"] = list(self.fta_models[0]["modelElements"]) + [
            e["_id"] for e in f.get("elements", [])]
        code = {e.get("elementId"): e for e in self.fta}
        for pt in f.get("patches", []):
            el = code[pt["elementId"]]
            vals = list(el[pt["field"]])
            if pt["replace"]["from"] not in vals:
                raise SystemExit("patch %s: %s not in %s" % (pt["elementId"], pt["replace"]["from"], pt["field"]))
            el[pt["field"]] = [pt["replace"]["to"] if v == pt["replace"]["from"] else v for v in vals]
            el["origin"] = "completion (patched)"
        s = c.get("sysml", {})
        self.sysml += s.get("elements", [])
        self.S.update({e["_id"]: e for e in s.get("elements", [])})
        sim = c.get("simulation", {})
        self.MP.update({p["_id"]: p for p in sim.get("parameters", [])})
        self.sim_bindings += sim.get("bindings", [])

    def sysml_value(self, oid):
        """Literal value of a SysML feature, through its owned FeatureValue (as the export stores it)."""
        for r in self.S[oid].get("ownedRelationship") or []:
            fv = self.S.get(r)
            if fv and fv["__t"] == "SFeatureValue":
                lit = self.S.get(fv.get("value"))
                return lit.get("value") if lit else None
        return None

    def qualified_name(self, oid):
        """Owning-namespace chain of names (the export leaves qualifiedName null)."""
        names, cur = [], self.S.get(oid)
        while cur is not None:
            n = cur.get("declaredName")
            if n:
                names.append(n if n.replace("_", "a").isalnum() else "'%s'" % n)
            cur = self.S.get(cur.get("owningNamespace"))
        return "::".join(reversed(names))

    # GSN text lives behind LangString / Description -> MultiLangString -> LangString.
    def gsn_text(self, ref):
        e = self.G.get(ref)
        if e is None:
            return None
        t = e["__t"]
        if t in ("LangString", "ExpressionLangString"):
            return e.get("content")
        if t == "Description":
            return self.gsn_text(e.get("content"))
        if t == "MultiLangString":
            parts = [self.gsn_text(v) for v in e.get("value", [])]
            return "".join(p for p in parts if p) or None
        return None

    def row_numbers(self):
        out = {}
        for fm in self.fmea_models:
            rows = sorted((r for r in self.fmea_rows if r["fmeaModel"] == fm["_id"]),
                          key=lambda r: r.get("rowOrder") or 0)
            for i, r in enumerate(rows, 1):
                out[r["_id"]] = i
        return out


# --------------------------------------------------------------------------- nodes
def node_for(x, oid, rownum):
    if oid in x.S:
        e = x.S[oid]
        owner = x.S.get(e.get("owningNamespace")) or {}
        concern = "requirements" if "SRequirementUsage" in (e["__t"], owner.get("__t")) else "design"
        n = {"id": oid, "uuid": e.get("elementId"), "concern": concern, "kind": e["__t"],
             "label": e.get("declaredName"), "text": None}
        if e.get("declaredShortName"):
            n["shortName"] = e["declaredShortName"]
        if oid in {b["sysmlElement"] for b in x.sim_bindings}:
            # A simulation-bound attribute carries its value, and the name the runner finds it by in the text.
            n["qualifiedName"] = x.qualified_name(oid)
            n["value"] = x.sysml_value(oid)
        return n
    if oid in x.MP:
        p = x.MP[oid]
        m = x.MO[p["modelicaModel"]]
        decl = SB.modelica_parameter(m["source"], p["name"])
        if decl is None:
            raise SystemExit("parameter %s not declared in %s" % (p["name"], m["name"]))
        value, desc, unit = decl
        return {"id": oid, "uuid": None, "concern": "executable-evidence", "kind": "ModelicaParameter",
                "label": p["name"], "text": desc, "notation": "Modelica",
                "qualifiedName": "%s.%s" % (modelica_class(m["source"]), p["name"]), "value": value, "unit": unit}
    if oid in x.G:
        e = x.G[oid]
        return {"id": oid, "uuid": e.get("gid"), "concern": "safety-case", "kind": e["__t"],
                "label": x.gsn_text(e.get("name")), "text": x.gsn_text(e.get("description"))}
    if oid in x.R:
        r = x.R[oid]
        return {"id": oid, "uuid": r.get("elementId"), "concern": "failure-analysis", "kind": "FMEARow",
                "label": "FMEDA row %d" % rownum[oid], "text": r.get("failureMode"), "notation": "FMEDA"}
    if oid in x.F:
        e = x.F[oid]
        return {"id": oid, "uuid": e.get("elementId"), "concern": "failure-analysis", "kind": e["__t"],
                "label": e.get("elementId"), "text": e.get("name"), "notation": "FTA"}
    if oid in x.M:
        m = x.M[oid]
        return {"id": oid, "uuid": None, "concern": "executable-evidence", "kind": m["type"],
                "label": m["name"], "text": None, "notation": NOTATION[m["type"]]}
    if oid in x.MO:
        m = x.MO[oid]
        return {"id": oid, "uuid": None, "concern": "executable-evidence", "kind": "ModelicaModel",
                "label": m["name"], "text": None, "notation": "Modelica"}
    if oid in x.TP:
        p = x.TP[oid]
        return {"id": oid, "uuid": None, "concern": "digital-twin", "kind": "TwinPart",
                "label": p.get("label"), "text": p.get("meshName")}
    if oid in x.TB:
        b = x.TB[oid]
        return {"id": oid, "uuid": None, "concern": "digital-twin", "kind": "TwinBinding",
                "label": b.get("label"), "text": b.get("unit")}
    return None


def modelica_class(source):
    m = re.search(r"^\s*model\s+(\w+)", source, re.M)
    return m.group(1) if m else None


def derive_namespace(x, previous=None):
    rownum = x.row_numbers()
    edges = []
    # 1. Typed cross-concern links: one edge per (source, target) endpoint pair.
    for l in x.links:
        for t in l["targets"]:
            edge = {"source": l["source"], "target": t, "kind": "traceability", "name": l["name"]}
            if l.get("origin"):
                edge["origin"] = l["origin"]
            if l.get("relation"):
                edge["relation"] = l["relation"]
            edges.append(edge)
    # 2. FMEDA row -> the design part it analyses, read from the row's itemElement field. Where a typed
    # link already records that relationship (the completion overlay's FMEDA-row-to-design links), the
    # typed link is the edge and no field-derived edge is added.
    typed = {(l["source"], t) for l in x.links for t in l["targets"]}
    for r in sorted(x.fmea_rows, key=lambda r: (r["fmeaModel"], r.get("rowOrder") or 0)):
        if r.get("itemElement") and (r["_id"], r["itemElement"]) not in typed:
            edges.append({"source": r["_id"], "target": r["itemElement"], "kind": "fmeda-item"})
    # 3. GSN argument structure, as drawn (graph edge -> node.object).
    # An edge names its ends by the node's nodeId, which is the drawn element's id.
    obj = {n["nodeId"]: n["object"] for n in x.gsn_nodes}
    for e in x.gsn_edges:
        kind = "gsn-" + e["edgeType"].split(":", 1)[1].replace("-edge", "")
        edge = {"source": obj[e["sourceNodeId"]], "target": obj[e["targetNodeId"]], "kind": kind}
        if e.get("origin"):
            edge["origin"] = e["origin"]
        edges.append(edge)
    # 4. Telemetry binding -> design attribute.
    for b in x.twin.get("dataBindings", []):
        edges.append({"source": b["bindingId"], "target": b["sysmlElement"], "kind": "twin-binding"})
    # 5. Fault-tree logic: each gate to its output event and to each input.
    for g in (e for e in x.fta if "outputEvent" in e):
        edges.append({"source": g["_id"], "target": g["outputEvent"], "kind": "fta-output"})
        for i in g.get("inputs", []):
            edges.append({"source": g["_id"], "target": i, "kind": "fta-input"})
    # 6. Bound attribute -> the part usages its owning part definition types (SysML ownership and
    #    typing, both in the export), so telemetry reaches the part it measures. An attribute owned by a
    #    usage (a requirement) is joined to that usage. Telemetry-bound attributes first, then
    #    simulation-bound ones.
    bound = [b["sysmlElement"] for b in x.twin.get("dataBindings", [])]
    bound += [b["sysmlElement"] for b in x.sim_bindings if b["sysmlElement"] not in bound]
    for aid in bound:
        a = x.S.get(aid)
        owner = a and a.get("owningNamespace")
        if (x.S.get(owner) or {}).get("__t", "").endswith("Usage"):
            edge = {"source": a["_id"], "target": owner, "kind": "attribute-of"}
            if a.get("origin"):
                edge["origin"] = a["origin"]
            edges.append(edge)
            continue
        for p in sorted((e for e in x.sysml if e["__t"] == "SPartUsage" and owner in (e.get("partDefinition") or [])),
                        key=lambda e: e["_id"]):
            edge = {"source": a["_id"], "target": p["_id"], "kind": "attribute-of"}
            if a.get("origin"):
                edge["origin"] = a["origin"]
            edges.append(edge)
    # 7. Fault-tree basic event -> the FMEDA row it models, as each event's description states
    #    ("FMEA row N."), with N the 1-based row number the platform exports use.
    by_num = {(r["fmeaModel"], n): rid for rid, n in rownum.items() for r in [x.R[rid]]}
    for e in x.fta:
        desc = e.get("description") or ""
        if e["__t"] == "FTABasicEvent" and desc.startswith("FMEA row "):
            n = int(desc[len("FMEA row "):].split(".", 1)[0])
            hits = [rid for (fm, k), rid in by_num.items() if k == n]
            if len(hits) == 1:
                edges.append({"source": e["_id"], "target": hits[0], "kind": "fta-fmeda"})
    # 8. Modelica parameter -> the Modelica model that declares it.
    for pid, p in x.MP.items():
        edges.append({"source": pid, "target": p["modelicaModel"], "kind": "parameter-of", "origin": p.get("origin")})
    # 9. Degree 0 value binding: Modelica parameter -> the SysML attribute whose value it takes. Where a typed
    # link (relation binds) already records the binding, the typed link is the edge and no sim-binding edge is added.
    for b in x.sim_bindings:
        if (b["modelicaParameter"], b["sysmlElement"]) in typed:
            continue
        edges.append({"source": b["modelicaParameter"], "target": b["sysmlElement"], "kind": "sim-binding",
                      "name": b["label"], "origin": b.get("origin")})

    ids = {e["source"] for e in edges} | {e["target"] for e in edges}
    # Every drawn argument and fault-tree element, and every FMEDA row and twin
    # part, is in the space even if no edge touches it (none is isolated in ADS).
    ids |= {e["_id"] for e in x.sacm if e["__t"] in GSN_ARGUMENT and e.get("graphNode")}
    ids |= {e["_id"] for e in x.fta if e.get("graphNode")}
    ids |= set(x.R) | set(x.TP) | set(x.TB)
    nodes, unresolved = [], []
    for oid in sorted(ids):
        n = node_for(x, oid, rownum)
        src = x.G.get(oid) or x.F.get(oid) or x.S.get(oid) or x.MP.get(oid)
        if n and src and src.get("origin"):
            n["origin"] = src["origin"]
        (nodes.append(n) if n else unresolved.append(oid))
    if unresolved:
        raise SystemExit("unresolved endpoints: %s" % unresolved)

    ns = collections.OrderedDict()
    base = previous or {}
    ns["schema"] = "ads-namespace/5"
    ns["description"] = base.get("description") or ("Every ADS model element that participates in a "
                                                     "cross-concern relationship, in one identity space.")
    ns["provenance"] = (
        "Derived from the modelling tool's project export by tools/derive_from_export.py; identities "
        "and text verbatim. Element UUIDs follow the same per-kind rule as the platform's traceability "
        "resolver: SysML elements, FMEDA rows and fault-tree elements carry elementId, safety-case "
        "elements carry gid. Executable evidence models, and digital-twin mappings, have no UUID of "
        "their own and carry null. A traceability link with several targets contributes one edge per "
        "target, each carrying the link's name. Two edge kinds are read from the export's structure rather "
        "than its trace links: attribute-of (a telemetry-bound attribute to the part usages its owning "
        "definition types) and fta-fmeda (a basic event to the FMEDA row its description names). Edges "
        "and elements with origin 'completion' come from models/traceability/completion.json, authored to "
        "complete the thread and accepted in engineering review on 17 November 2026. A link from a failure-analysis element to a "
        "requirement carries a relation: challenges (the failure or event violates the requirement) or realises "
        "(the safety mechanism or control it names implements the requirement). A link from an FMEDA row to a "
        "design part carries the relation analyses and records the part the row's itemElement field names; "
        "where such a link exists, no field-derived fmeda-item edge is added. A link from a Modelica parameter to a "
        "SysML attribute carries the relation binds and records a Degree 0 value binding; where such a link exists, "
        "it is the binding's edge and no sim-binding edge is added. Three SysML attributes "
        "(changeoverPeriod, saturationTimeConstant, minDecontaminationFactor) and the Modelica parameters they set "
        "(tCycle, tSat, DFtarget) come from the completion overlay: parameter-of joins a parameter to the Modelica model "
        "that declares it, and sim-binding is a Degree 0 value binding from a parameter to the attribute whose value it "
        "takes. Both ends of a binding carry `value` (the SysML literal; the parameter's value as declared in the "
        "exported Modelica source), which must be equal; a bound attribute also carries its `qualifiedName`.")
    ns["identity"] = (
        "`id` is the endpoint identifier the traceability links use. `uuid` is the element's own stable "
        "identifier, matching @id in the SysML, FMEDA, fault-tree and safety-case JSON exports, so a "
        "thread edge can be joined to the model that describes what it points at. Fault-tree elements "
        "are identified by their event and gate codes (TE-01, BE-12, G-04), which are their elementId.")
    ns["nodes"] = nodes
    ns["edges"] = edges
    ns["concerns"] = (
        "Concern names group elements the way the article's link breakdown does, so the two count the "
        "same concern pairs. The five executable evidence models share one concern, "
        "`executable-evidence`, with the specific notation on each node's `notation` field. Failure "
        "analysis is likewise one concern, `failure-analysis`, holding the FMEDA rows (`notation` "
        "FMEDA) and the fault-tree events and gates (`notation` FTA).")
    return ns


# --------------------------------------------------------------------------- fault tree
FTA_DROP = {"_id", "__v", "__t", "ftaModel", "graphNode", "createdAt", "updatedAt", "elementId", "isPublic"}


def derive_fta(x):
    out = []
    for fm in x.fta_models:
        wrapper = next(m for m in x.models if m.get("model") == fm["_id"])
        els = [x.F[i] for i in fm["modelElements"] if i in x.F]
        ref = lambda oid: {"@id": x.F[oid]["elementId"], "name": x.F[oid]["name"]}
        traces = collections.defaultdict(list)
        for l in x.links:
            for t in l["targets"]:
                if t in x.F:
                    src = x.G.get(l["source"])
                    traces[t].append({"name": l["name"], "endpoint": {
                        "type": src["__t"] if src else None,
                        "name": x.gsn_text(src.get("name")) if src else None}})
        rows = []
        for e in els:
            r = collections.OrderedDict()
            r["@id"] = e["elementId"]
            r["@type"] = e["__t"][3:] if e["__t"].startswith("FTA") else e["__t"]
            for k, v in e.items():
                if k in FTA_DROP or v is None or v == []:
                    continue
                if k in ("topEvent", "outputEvent"):
                    r[k] = ref(v)
                elif k == "inputs":
                    r[k] = [ref(i) for i in v]
                elif k == "quantification":
                    r[k] = {qk: qv for qk, qv in v.items() if qv is not None}
                else:
                    r[k] = v
            if traces.get(e["_id"]):
                r["traces"] = traces[e["_id"]]
            rows.append(r)
        doc = collections.OrderedDict()
        doc["modelName"] = wrapper["name"]
        doc["faultTreeName"] = fm["name"]
        doc["description"] = re.sub(r"\s*\(docs/[^)]*\)", "", fm.get("description") or "")  # drop internal source paths
        doc["elementCount"] = len(rows)
        doc["countsByType"] = dict(collections.Counter(r["@type"] for r in rows))
        doc["elements"] = rows
        out.append(doc)
    if len(out) != 1:
        raise SystemExit("expected one fault tree, found %d" % len(out))
    return out[0]


def minimal_cut_sets(x):
    """MOCUS over the gate structure, for the report only."""
    code = {e["_id"]: e["elementId"] for e in x.fta}
    gate_of = {g["outputEvent"]: g for g in x.fta if "outputEvent" in g}
    top = next(e for e in x.fta if e["__t"] == "FTAFaultTree")["topEvent"]

    def expand(ev):
        if ev not in gate_of:
            return [frozenset([code[ev]])]
        g = gate_of[ev]
        subs = [expand(i) for i in g["inputs"]]
        if g["__t"] == "FTAOrGate":
            return [c for s in subs for c in s]
        acc = [frozenset()]
        for s in subs:
            acc = [a | c for a in acc for c in s]
        return acc
    cs = set(expand(top))
    return sorted((c for c in cs if not any(o < c for o in cs)), key=lambda c: (len(c), sorted(c)))


# --------------------------------------------------------------------------- safety case
def derive_gsn(x):
    gm = x.gsn_models[0]
    order = [x.G[i] for i in gm["modelElements"] if i in x.G and x.G[i]["__t"] in GSN_ARGUMENT]
    lines = ["["]
    for i, e in enumerate(order):
        head = '  { "_id": %s, "type": %s, "name": %s,' % tuple(
            json.dumps(v, ensure_ascii=False) for v in (e["_id"], e["__t"], x.gsn_text(e["name"])))
        if e.get("origin"):
            head += ' "origin": %s,' % json.dumps(e["origin"])
        tail = '    "description": %s }%s' % (json.dumps(x.gsn_text(e["description"]), ensure_ascii=False),
                                             "," if i < len(order) - 1 else "")
        lines += [head, tail]
    lines.append("]")
    return "\n".join(lines) + "\n"


def derive_evidence_resolution(x, link_name="Sn7-to-Dafny"):
    l = next(l for l in x.links if l["name"] == link_name)
    sol = x.G[l["source"]]
    chain = [{k: sol[k] for k in ("_id", "__t", "name", "description", "graphNode")}]
    ls = x.G[sol["name"]]
    chain.append({k: ls[k] for k in ("_id", "__t", "lang", "content")})
    d = x.G[sol["description"]]
    chain.append({k: d[k] for k in ("_id", "__t", "content")})
    mls = x.G[d["content"]]
    chain.append({k: mls[k] for k in ("_id", "__t", "value")})
    for v in mls["value"]:
        el = x.G[v]
        chain.append({k: el[k] for k in ("_id", "__t", "content")})
    models = [{k: x.M[t][k] for k in ("_id", "name", "type", "model", "editor")} for t in l["targets"]]
    doc = collections.OrderedDict()
    doc["gsn-safety-case.elements"] = chain
    doc["traceability.links"] = [{k: l[k] for k in ("_id", "name", "source", "targets", "projectID")}]
    doc["models"] = models
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", required=True, help="project export directory of the modelling tool")
    ap.add_argument("--check", action="store_true", help="compare with the committed files; write nothing")
    ap.add_argument("--report", action="store_true", help="print fault-tree cut sets and rate checks")
    ap.add_argument("--completion", default=os.path.join(ROOT, "models", "traceability", "completion.json"),
                    help="completion overlay applied before deriving (default: the committed one)")
    ap.add_argument("--no-completion", action="store_true", help="derive the export-only views")
    a = ap.parse_args()
    x = Export(a.export)
    if not a.no_completion and os.path.exists(a.completion):
        x.apply_completion(json.load(open(a.completion, encoding="utf-8")))

    prev_path = os.path.join(ROOT, "namespace", "ads-namespace.json")
    prev = json.load(open(prev_path, encoding="utf-8")) if os.path.exists(prev_path) else None
    outputs = {
        "models/fta/ads-fta.json": json.dumps(derive_fta(x), indent=1, ensure_ascii=False),
        "models/safety-case/gsn-safety-case.json": derive_gsn(x),
        "models/safety-case/evidence-resolution.json": derive_evidence_resolution(x),
        "namespace/ads-namespace.json": json.dumps(derive_namespace(x, prev), indent=1),
    }

    if a.report:
        mcs = minimal_cut_sets(x)
        print("minimal cut sets: %d" % len(mcs))
        for c in mcs:
            print("  order %d  %s" % (len(c), " . ".join(sorted(c))))
        freq = collections.Counter(b for c in mcs for b in c)
        print("basic events by cut-set count:", ", ".join("%s %d" % kv for kv in freq.most_common()))
        rows = {x.row_numbers()[r["_id"]]: r for r in x.fmea_rows}
        print("basic-event rate vs cited FMEDA row (FIT x mode ratio x 1e-9 per hour):")
        for e in x.fta:
            if e["__t"] != "FTABasicEvent":
                continue
            q = e.get("quantification") or {}
            desc = e.get("description") or ""
            n = int(desc.split("FMEA row ", 1)[1].split(".", 1)[0]) if "FMEA row " in desc else None
            r = rows.get(n)
            expect = r["failureRate"] * r["failureModeRatio"] * 1e-9 if r and r.get("failureRate") is not None else None
            got = q.get("operatingFailureRate")
            ok = (expect is not None and got is not None and abs(expect - got) <= 1e-12 * max(1, abs(expect)))
            print("  %-6s row %-3s %-10s rate=%-9s expected=%-9s %s" % (
                e["elementId"], n, q.get("kind"), got, None if expect is None else float("%.6g" % expect),
                "agrees" if ok else ("not rate-quantified" if got is None else "DIFFERS")))
        return 0

    stale = 0
    for rel, text in outputs.items():
        p = os.path.join(ROOT, rel)
        cur = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if a.check:
            same = cur == text
            stale += not same
            print("%-48s %s" % (rel, "current" if same else ("missing" if cur is None else "STALE")))
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            print("wrote %s (%d bytes)" % (rel, len(text.encode("utf-8"))))
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
