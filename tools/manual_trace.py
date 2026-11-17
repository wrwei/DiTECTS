#!/usr/bin/env python3
"""Simulated manual (name-based) change-impact tracing vs. the digital thread.

Implements the protocol fixed in results/manual_vs_thread.md ("Protocol" section):
an engineer without typed links or a shared identity space opens the ADS model files,
searches them for the changed element's names, reads every hit, adds the names the hit
cites to a worklist and repeats to a fixpoint. Text hits are mapped to element ids of
namespace/ads-namespace.json so the result can be compared with namespace/impact.py.

  python3 tools/manual_trace.py            # writes results/manual_vs_thread.{json,md}

Standard library only; Python >= 3.9. This is a simulation, not a human study.
"""
import collections
import glob
import hashlib
import importlib.util
import json
import os
import re
import statistics
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(ROOT, "results", "manual_vs_thread.json")
OUT_MD = os.path.join(ROOT, "results", "manual_vs_thread.md")
MARKER = "<!-- RESULTS -->"

# Changes made to the implementation after the first run (bug fixes only). Kept verbatim
# in the outputs; empty means the first run is the reported run.
DEVIATIONS = [
    "Before the first comparative run, a segmentation dry-run showed that the SysML lexicon regex also "
    "matched prose inside doc comments ('interface carrying TritiatedAir' put the word 'carrying' in the "
    "lexicon). The lexicon is now built from parsed declaration headers only, as P4 specifies. No result "
    "had been computed when this was fixed.",
    "Also before the first complete run, the results-marker split was changed to use only the stand-alone "
    "marker line, because the introduction mentions the marker text. This is an I/O fix with no effect on any number.",
    "After the first complete run, the reporting was extended without changing the protocol or any "
    "computed number: the lenient term(s) that produce each EXACT name-variant miss, the "
    "fixpoint-size distribution, the list of starts with a fixpoint below 20, the share of first findings "
    "whose hop is a thread edge, and a summarised list of per-scenario text-only hits. Per-start JSON "
    "records were compacted (missed element ids and counts instead of full lists, 9.7 MB -> 1.4 MB); the full "
    "lists are kept for the four named scenarios.",
    "Protocol amendment A1 (2026-11-14, before the re-run on the thread with SysML-to-Modelica value "
    "bindings; no result on the extended thread had been computed). The identity space gained three SysML "
    "attributes and three Modelica parameters, for which P3/P4 had no rule. A1 extends P3 and P4 the way "
    "they already treat SysML attribute usages: an attribute usage declared in a requirement usage is an "
    "element segment, as one declared in a part definition is; each Modelica parameter declaration "
    "(`parameter Real <name> = ...;`) of an identity-space parameter is an element segment and is cut out "
    "of the Modelica model's segment; a Modelica parameter's visible name is its declared name; every "
    "parameter name declared in the Modelica file joins the lexicon; parameter-of and sim-binding are "
    "structural edge kinds in the P9 audit. Nothing else changed.",
]

# ----------------------------------------------------------------------------- protocol
DOCUMENTS = [
    ("sysml-requirements", "models/sysml/01-requirements.sysml"),
    ("sysml-design", "models/sysml/02-design.sysml"),
    ("fmeda", "models/fmeda/ads-fmeda.json"),
    ("fta", "models/fta/ads-fta.json"),
    ("gsn", "models/safety-case/gsn-safety-case.json"),
    ("dafny", "formal/dafny/ADSController.dfy"),
    ("isabelle", "formal/isabelle/*.thy + formal/isabelle/ROOT"),
    ("csp", "formal/csp/*.csp (excluding defs/ and timed/)"),
    ("java", "implementation/java/src/**"),
    ("modelica", "simulation/modelica/ADSChangeover.mo"),
    ("twin", "twin elements' labels / mesh names / binding labels (namespace/ads-namespace.json)"),
]
EXCLUDED_INPUTS = [
    "models/traceability/completion.json",
    "models/safety-case/evidence-resolution.json",
    "namespace/* (except the visible labels of the 14 digital-twin elements, see P2)",
    "FMEDA rows' and FTA elements' `traces` arrays (stored typed-link records)",
    "FMEDA `itemElement`, FTA gate `inputs`/`outputEvent`, FaultTree `topEvent` (structured id references)",
    "internal ids / UUIDs (`@id` other than an FTA element's own code, `_id`)",
]
EXEC_NAMES = {  # P4: registered model name, notation name, primary unit name
    "Java Model": ["ADS Controller Implementation", "Java", "ADSController"],
    "Dafny Model": ["ADS Controller Proof - Dafny", "Dafny", "ADSController"],
    "Isabelle Model": ["ADS Controller Behaviour", "Isabelle", "ADSController_Beh"],
    "FDR Model": ["ADS Controller Refinement", "CSP", "FDR", "file_robochart_controller"],
    "ModelicaModel": ["ADS Changeover Transient_Modelica", "Modelica", "ADSChangeover"],
}
EXEC_DOC = {"Java Model": "java", "Dafny Model": "dafny", "Isabelle Model": "isabelle",
            "FDR Model": "csp", "ModelicaModel": "modelica"}
STOPWORDS = set("""the and for with from into not any all both either top row rows model part port
item state event data type value test true false none null def doc attribute requirement
package interface system""".split())
RE_REQ = re.compile(r"REQ-([A-Z]+)-(\d{3})((?:\s*/\s*\d{3})*)")
RE_GSN = re.compile(r"\b(?:G|S|Sn|C|A)\d{1,2}\b")
RE_FTA = re.compile(r"\b(?:TE|IE|BE|G)-\d{2}\b")
RE_ROW = re.compile(r"\brows?\s+(\d+(?:\s*/\s*\d+)*)")
ID_PATTERNS = [re.compile(r"^REQ-[A-Z]+-\d{3}$"), re.compile(r"^(?:G|S|Sn|C|A)\d{1,2}$"),
               re.compile(r"^(?:TE|IE|BE|G)-\d{2}$"), re.compile(r"^(?:FMEDA )?row \d+$")]
VARIANTS = ["EXACT", "LENIENT", "LENIENT+DIAGRAM"]
PRIMARY = ["EXACT", "LENIENT"]
SCENARIOS = [
    ("dryerA", "dryerA", "design part usage"),
    ("controller", "controller", "design part usage; change to the initial bed (activeDryer = BedA)"),
    ("modelica", "ADS Changeover Transient_Modelica", "Modelica model; change to the bed-swap period tCycle"),
    ("REQ-ADS-007", "REQ-ADS-007", "requirement lossOfPowerResponse"),
]
STRUCTURAL = {"attribute-of", "fta-input", "fta-output", "gsn-SupportedBy", "gsn-InContextOf",
              "twin-binding", "fmeda-item", "fta-fmeda", "parameter-of", "sim-binding"}  # A1: last two
RE_MO_PARAM = re.compile(r"\bparameter\s+Real\s+(\w+)\s*=[^;]*;")  # A1: Modelica parameter declarations
MISS_CLASSES = ["no-segment", "name-variant", "mention-not-extracted", "typed-link-only",
                "structural", "typed-link+structural", "cascade"]
DEPTHS = [1, 2, 3, 4, 5, 6]


def keep(term):
    t = term.strip()
    if not t:
        return False
    if any(p.match(t) for p in ID_PATTERNS):
        return True
    if len(t) < 3:
        return False
    return t.lower() not in STOPWORDS


# ----------------------------------------------------------------------------- matchers
def _word(c):
    return c.isalnum() or c == "_"


def exact_match(term, text):
    pre = r"(?<![A-Za-z0-9_])" if _word(term[0]) else ""
    post = r"(?![A-Za-z0-9_])" if _word(term[-1]) else ""
    return re.search(pre + re.escape(term) + post, text) is not None


def lenient_norm(text):
    """Lower-case, drop whitespace/hyphens/underscores; return (normalised, token boundaries)."""
    out, bounds, prev, sep = [], {0}, None, False
    n = len(text)
    for i, c in enumerate(text):
        if c.isspace() or c in "-_":
            sep = True
            continue
        pos = len(out)
        if prev is not None:
            nxt = text[i + 1] if i + 1 < n else ""
            if sep or not c.isalnum() or not prev.isalnum():
                bounds.add(pos)
            elif prev.islower() and c.isupper():
                bounds.add(pos)
            elif prev.isupper() and c.isupper() and nxt.islower():
                bounds.add(pos)
            elif prev.isalpha() != c.isalpha():
                bounds.add(pos)
        out.append(c.lower())
        prev, sep = c, False
    s = "".join(out)
    bounds.add(len(s))
    return s, bounds


_NORM_CACHE = {}


def lenient_match(term, text):
    nt = _NORM_CACHE.get(term)
    if nt is None:
        nt = _NORM_CACHE[term] = lenient_norm(term)[0]
    if not nt:
        return False
    key = ("T", text)
    nb = _NORM_CACHE.get(key)
    if nb is None:
        nb = _NORM_CACHE[key] = lenient_norm(text)
    s, bounds = nb
    p = s.find(nt)
    while p >= 0:
        if p in bounds and p + len(nt) in bounds:
            return True
        p = s.find(nt, p + 1)
    return False


def matcher(variant):
    return exact_match if variant == "EXACT" else lenient_match


# ----------------------------------------------------------------------------- thread side
def load_impact():
    spec = importlib.util.spec_from_file_location("impact", os.path.join(ROOT, "namespace", "impact.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------- SysML parsing
def _skip_ws(t, i, end):
    while i < end and t[i].isspace():
        i += 1
    return i


def parse_sysml(t, i=0, end=None):
    """Statements at one nesting level: dicts with start, end, header, children."""
    end = len(t) if end is None else end
    out = []
    while True:
        i = _skip_ws(t, i, end)
        if i >= end or t[i] == "}":
            return out, i
        if re.match(r"doc\s*/\*", t[i:i + 64]):
            j = t.index("*/", i) + 2
            out.append({"start": i, "end": j, "header": "doc", "children": []})
            i = j
            continue
        j = i
        while j < end:
            if t.startswith("/*", j):
                j = t.index("*/", j) + 2
                continue
            c = t[j]
            if c == "'":
                j = t.index("'", j + 1) + 1
                continue
            if c == ";":
                out.append({"start": i, "end": j + 1, "header": " ".join(t[i:j].split()), "children": []})
                i = j + 1
                break
            if c == "{":
                kids, k = parse_sysml(t, j + 1, end)
                out.append({"start": i, "end": k + 1, "header": " ".join(t[i:j].split()), "children": kids})
                i = k + 1
                break
            j += 1
        else:
            raise SystemExit("SysML parse error near offset %d" % i)


def sysml_segments(doc, text, sysml_ids):
    """Element segments for identity-space usages; every other top-level statement is context."""
    segs = []

    def classify(st, parent_kind):
        h = st["header"]
        m = re.match(r"requirement <'([^']+)'> (\w+)", h)
        if m:
            return ("SRequirementUsage", m.group(2), m.group(1))
        m = re.match(r"part (?!def\b)(\w+)", h)
        if m:
            return ("SPartUsage", m.group(1), None)
        m = re.match(r"interface (?!def\b)(\w+)", h)
        if m:
            return ("SInterfaceUsage", m.group(1), None)
        m = re.match(r"attribute (\w+)", h)
        if m and parent_kind in ("part def", "requirement"):  # A1: also attributes of requirement usages
            return ("SAttributeUsage", m.group(1), None)
        return None

    def kind_of(h):
        m = re.match(r"(part def|state def|requirement def|item def|port def|interface def|enum def|package|requirement)\b", h)
        return m.group(1) if m else None

    def walk(st, owner, parent_kind):
        c = classify(st, parent_kind)
        eid = sysml_ids.get((c[0], c[1])) if c else None
        if eid:
            seg = {"doc": doc, "eid": eid, "span": (st["start"], st["end"]), "holes": [],
                   "sysml": {"kind": c[0], "name": c[1], "short": c[2]}}
            segs.append(seg)
            if owner is not None:
                owner["holes"].append((st["start"], st["end"]))
            nxt = seg
        elif owner is None:
            seg = {"doc": doc, "eid": None, "span": (st["start"], st["end"]), "holes": []}
            segs.append(seg)
            nxt = seg
        else:
            nxt = owner
        for ch in st["children"]:
            walk(ch, nxt, kind_of(st["header"]))

    top, _ = parse_sysml(text)
    for st in top:
        if st["header"].startswith("package"):
            for ch in st["children"]:
                walk(ch, None, "package")
        else:
            walk(st, None, None)
    for s in segs:
        a, b = s["span"]
        parts, cur = [], a
        for h0, h1 in sorted(s.pop("holes")):
            parts.append(text[cur:h0])
            cur = h1
        parts.append(text[cur:b])
        s["text"] = " ".join(parts)
        s.pop("span")
    return segs


def sysml_lexicon(text):
    """Declared usage names, read from parsed statement headers (never from doc comments)."""
    names = set()

    def walk(st):
        h = st["header"]
        m = re.match(r"requirement <'([^']+)'> (\w+)", h)
        if m:
            names.update(m.groups())
        m = re.match(r"(?:part|interface|attribute) (?!def\b)(\w+)", h)
        if m:
            names.add(m.group(1))
        for ch in st["children"]:
            walk(ch)

    for st in parse_sysml(text)[0]:
        walk(st)
    return names


# ----------------------------------------------------------------------------- documents
def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def build_segments(ns, variant):
    node = {n["id"]: n for n in ns["nodes"]}
    by_uuid = {n["uuid"]: n["id"] for n in ns["nodes"] if n.get("uuid")}
    sysml_ids = {}
    for n in ns["nodes"]:
        if n["concern"] in ("requirements", "design"):
            key = (n["kind"], n["label"])
            if key in sysml_ids:
                raise SystemExit("ambiguous SysML element %r" % (key,))
            sysml_ids[key] = n["id"]
    segs, lexicon, checks = [], set(), {}

    # SysML
    for doc, rel in (("sysml-requirements", "models/sysml/01-requirements.sysml"),
                     ("sysml-design", "models/sysml/02-design.sysml")):
        t = read(rel)
        segs += sysml_segments(doc, t, sysml_ids)
        lexicon |= sysml_lexicon(t)

    # FMEDA
    f = json.loads(read("models/fmeda/ads-fmeda.json"))
    vis_cols = [c for c in f["columns"] if c != "traces"]
    segs.append({"doc": "fmeda", "eid": None,
                 "text": " ".join(str(f.get(k, "")) for k in ("modelName", "analysisKind", "description"))})
    for r in f["rows"]:
        cells = ["row %d" % r["rowNumber"]] + [str(r[c]) for c in vis_cols if c in r and r[c] is not None]
        segs.append({"doc": "fmeda", "eid": by_uuid.get(r["@id"]), "text": " | ".join(cells)})

    # FTA
    ft = json.loads(read("models/fta/ads-fta.json"))
    segs.append({"doc": "fta", "eid": None,
                 "text": " ".join(str(ft.get(k, "")) for k in ("modelName", "faultTreeName", "description"))})
    for e in ft["elements"]:
        if e["@type"] == "FaultTree":
            segs.append({"doc": "fta", "eid": None,
                         "text": " ".join(str(e.get(k, "")) for k in ("name", "polarity", "purpose", "notation"))})
            continue
        parts = [e["@id"], e["@type"], e.get("name") or "", e.get("description") or ""]
        if variant == "LENIENT+DIAGRAM" and "Gate" in e["@type"]:
            for ref in ([e["outputEvent"]] if e.get("outputEvent") else []) + list(e.get("inputs", [])):
                parts += [ref.get("@id", ""), ref.get("name", "")]
        segs.append({"doc": "fta", "eid": by_uuid.get(e["@id"]), "text": " | ".join(parts)})

    # GSN
    for g in json.loads(read("models/safety-case/gsn-safety-case.json")):
        segs.append({"doc": "gsn", "eid": g["_id"] if g["_id"] in node else None,
                     "text": " | ".join([g["name"], g["type"], g.get("description") or ""])})

    # Executable models: one element per model, whole file set
    files = {
        "dafny": ["formal/dafny/ADSController.dfy"],
        "isabelle": sorted(glob.glob(os.path.join(ROOT, "formal/isabelle/*.thy"))) + [os.path.join(ROOT, "formal/isabelle/ROOT")],
        "csp": sorted(glob.glob(os.path.join(ROOT, "formal/csp/*.csp"))),
        "java": sorted(p for p in glob.glob(os.path.join(ROOT, "implementation/java/src/**"), recursive=True) if os.path.isfile(p)),
        "modelica": ["simulation/modelica/ADSChangeover.mo"],
    }
    files = {k: [os.path.relpath(os.path.join(ROOT, p), ROOT) for p in v] for k, v in files.items()}
    checks["executable_files"] = files
    exec_ids = {n["kind"]: n["id"] for n in ns["nodes"] if n["concern"] == "executable-evidence"}
    params = {n["label"]: n["id"] for n in ns["nodes"] if n["kind"] == "ModelicaParameter"}
    for kind, doc in EXEC_DOC.items():
        text = "\n".join(read(p) for p in files[doc])
        if doc == "modelica":
            # A1: each identity-space parameter declaration is its own element segment, cut out of the model's.
            parts, cur = [], 0
            for m in RE_MO_PARAM.finditer(text):
                lexicon.add(m.group(1))
                if m.group(1) in params:
                    segs.append({"doc": doc, "eid": params[m.group(1)], "text": m.group(0)})
                    parts.append(text[cur:m.start()])
                    cur = m.end()
            text = " ".join(parts + [text[cur:]])
        segs.append({"doc": doc, "eid": exec_ids[kind], "text": text})

    # Twin (built from the twin elements' visible labels; see P2)
    for n in ns["nodes"]:
        if n["concern"] == "digital-twin":
            segs.append({"doc": "twin", "eid": n["id"], "text": " | ".join([n["kind"], n["label"] or "", n.get("text") or ""])})
            lexicon.add(n["label"])
            if n["kind"] == "TwinPart" and n.get("text"):
                lexicon.add(n["text"])
    glb = (glob.glob(os.path.join(ROOT, "models/digital-twin/*.glb"))
           or glob.glob(os.path.join(ROOT, "demo/demo-assets/twin-display/*.glb")))
    if glb:
        b = open(glb[0], "rb").read()
        L = struct.unpack("<I", b[12:16])[0]
        gnodes = {x.get("name") for x in json.loads(b[20:20 + L]).get("nodes", [])}
        meshes = [n["text"] for n in ns["nodes"] if n["kind"] == "TwinPart"]
        checks["twin_mesh_names_in_glb"] = {"glb": os.path.relpath(glb[0], ROOT),
                                            "mesh_names": len(meshes),
                                            "found_in_glb": sum(m in gnodes for m in meshes)}
    for names in EXEC_NAMES.values():
        lexicon.update(names)

    for i, s in enumerate(segs):
        s["sid"] = i
    lexicon = sorted(x for x in lexicon if x and keep(x))
    return segs, lexicon, checks


def visible_names(n):
    k = n["kind"]
    if n["concern"] in ("requirements", "design"):
        return [n["label"]] + ([n["shortName"]] if n.get("shortName") else [])
    if k == "FMEARow":
        return [n["label"], n["label"].replace("FMEDA ", "")]
    if n.get("notation") == "FTA":
        return [n["label"], n["text"]]
    if n["concern"] == "safety-case":
        return [n["label"]]
    if k == "TwinPart":
        return [n["label"], n["text"]]
    if k == "TwinBinding":
        return [n["label"]]
    if k == "ModelicaParameter":  # A1
        return [n["label"]]
    if n["concern"] == "executable-evidence":
        return list(EXEC_NAMES[k])
    raise SystemExit("no name rule for %s" % k)


def cited(text, lexicon, match):
    out = set()
    for m in RE_REQ.finditer(text):
        out.add("REQ-%s-%s" % (m.group(1), m.group(2)))
        for x in re.findall(r"\d{3}", m.group(3) or ""):
            out.add("REQ-%s-%s" % (m.group(1), x))
    out.update(RE_GSN.findall(text))
    out.update(RE_FTA.findall(text))
    for m in RE_ROW.finditer(text):
        for x in re.findall(r"\d+", m.group(1)):
            out.add("row %d" % int(x))
    for name in lexicon:
        if match(name, text):
            out.add(name)
    return out


# ----------------------------------------------------------------------------- engine
class Engine:
    def __init__(self, ns, variant):
        self.ns, self.variant = ns, variant
        self.node = {n["id"]: n for n in ns["nodes"]}
        self.segs, self.lexicon, self.checks = build_segments(ns, variant)
        self.match = matcher(variant)
        self.seg_of = {}
        for s in self.segs:
            if s["eid"]:
                if s["eid"] in self.seg_of:
                    raise SystemExit("element %s has two segments" % s["eid"])
                self.seg_of[s["eid"]] = s
        self._hits = {}
        self.seg_terms = {}
        for s in self.segs:
            names = set(visible_names(self.node[s["eid"]])) if s["eid"] else set()
            self.seg_terms[s["sid"]] = names | cited(s["text"], self.lexicon, self.match)

    def hits(self, term):
        h = self._hits.get(term)
        if h is None:
            h = self._hits[term] = [s for s in self.segs if self.match(term, s["text"])]
        return h

    def run(self, start):
        n0 = self.node[start]
        terms = sorted({t for t in visible_names(n0) if keep(t)})
        origin = {t: ("element", start) for t in terms}  # term -> (kind, element id or via-term)
        searched, found, read_segs = set(), {}, set()
        rounds, seg_hits, per_round = 0, 0, []
        while terms:
            rounds += 1
            cand = {}
            new_found = []
            for t in terms:
                searched.add(t)
                for s in self.hits(t):
                    seg_hits += 1
                    read_segs.add(s["sid"])
                    e = s["eid"]
                    if e and e != start and e not in found:
                        found[e] = {"round": rounds, "term": t, "doc": s["doc"]}
                        new_found.append(e)
                    for c in sorted(self.seg_terms[s["sid"]]):
                        if c not in cand:
                            cand[c] = ("element", e) if e else ("context", t)
            nxt = sorted(c for c in cand if keep(c) and c not in searched)
            for c in nxt:
                origin[c] = cand[c]
            per_round.append({"round": rounds, "terms": terms, "new_found": sorted(new_found),
                              "cum_found": len(found)})
            terms = nxt

        def origin_element(t, depth=0):
            kind, ref = origin[t]
            if kind == "element" or depth > 50:
                return ref
            return origin_element(ref, depth + 1)

        for e, rec in found.items():
            rec["source"] = origin_element(rec["term"])
        return {"found": found, "rounds": rounds, "searched": sorted(searched),
                "searches": len(searched) * len(DOCUMENTS), "seg_hits": seg_hits,
                "segments_read": len(read_segs), "per_round": per_round}


# ----------------------------------------------------------------------------- analysis
def q(xs):
    xs = sorted(xs)
    if len(xs) == 1:
        return {"median": xs[0], "q1": xs[0], "q3": xs[0], "min": xs[0], "max": xs[0], "n": 1}
    q1, med, q3 = statistics.quantiles(xs, n=4, method="inclusive")
    return {"median": round(med, 4), "q1": round(q1, 4), "q3": round(q3, 4),
            "min": round(xs[0], 4), "max": round(xs[-1], 4), "mean": round(statistics.mean(xs), 4), "n": len(xs)}


def ratio(a, b):
    return round(a / b, 4) if b else None


def compare(eng, tool, adj_set, adj, node, start, depth_of, res, lenient_eng=None):
    found = res["found"]
    M = set(found)
    T_inf = set(depth_of)
    T = {k: {e for e, d in depth_of.items() if d <= k} for k in DEPTHS}
    Mk = {k: {e for e, r in found.items() if r["round"] <= k} for k in DEPTHS}
    out = {
        "thread": {"per_depth_cum": {k: len(T[k]) for k in DEPTHS}, "unbounded": len(T_inf),
                   "max_depth": max(depth_of.values()) if depth_of else 0, "queries": 1},
        "manual": {"per_round_cum": {r["round"]: r["cum_found"] for r in res["per_round"]},
                   "fixpoint": len(M)},
        "recall_unbounded": ratio(len(M & T_inf), len(T_inf)),
        "recall_round_k_vs_depth_k": {k: ratio(len(Mk[k] & T[k]), len(T[k])) for k in (1, 2, 3)},
        "recall_fixpoint_vs_depth_k": {k: ratio(len(M & T[k]), len(T[k])) for k in (1, 2, 3)},
        "beyond_depth_hits_round_k": {k: len(Mk[k] - T[k]) for k in (1, 2, 3)},
        "manual_only": sorted(M - T_inf),
        "effort": {"rounds": res["rounds"], "terms": len(res["searched"]), "searches": res["searches"],
                   "segment_hits": res["seg_hits"], "segments_read": res["segments_read"]},
    }
    # text-only hits: first-finding hop is not a thread edge
    text_only = []
    for e, r in sorted(found.items()):
        src = r["source"]
        if (src, e) not in adj_set:
            text_only.append({"element": e, "label": node[e].get("shortName") or node[e]["label"],
                              "round": r["round"], "term": r["term"],
                              "source": node[src].get("shortName") or node[src]["label"],
                              "thread_depth": depth_of.get(e)})
    out["text_only_hits"] = text_only
    out["first_finding_via_thread_edge"] = ratio(len(found) - len(text_only), len(found))
    # audit of misses
    reached = M | {start}
    searched = res["searched"]
    misses = []
    for v in sorted(T_inf - M):
        seg = eng.seg_of.get(v)
        nbrs = [(u, k) for u, k, _ in adj[v] if u in reached]
        sub = None
        if seg is None:
            cls = "no-segment"
        elif eng.variant == "EXACT" and any(lenient_match(t, seg["text"]) for t in searched):
            cls = "name-variant"
            sub = "lenient term: " + ", ".join(t for t in searched if lenient_match(t, seg["text"]))
        else:
            cls = None
            for u, _ in nbrs:
                useg = eng.seg_of.get(u)
                if not useg:
                    continue
                for nm in visible_names(node[v]):
                    if nm and lenient_match(nm, useg["text"]):
                        cls = "mention-not-extracted"
                        if not keep(nm):
                            sub = "stop-listed"
                        elif eng.variant == "EXACT" and not exact_match(nm, useg["text"]):
                            sub = "variant spelling"
                        else:
                            sub = "not in lexicon / extraction rules"
                        break
                if cls:
                    break
            if cls is None:
                kinds = {k for _, k in nbrs}
                if not nbrs:
                    cls = "cascade"
                elif kinds <= {"traceability"}:
                    cls = "typed-link-only"
                elif kinds <= STRUCTURAL:
                    cls = "structural"
                    sub = "+".join(sorted(kinds))
                else:
                    cls = "typed-link+structural"
                    sub = "+".join(sorted(kinds))
        misses.append({"element": v, "label": node[v].get("shortName") or node[v]["label"],
                       "concern": node[v]["concern"], "class": cls, "detail": sub,
                       "thread_depth": depth_of[v],
                       "found_neighbours": sorted({node[u].get("shortName") or node[u]["label"] for u, _ in nbrs})})
    out["misses"] = misses
    out["miss_classes"] = dict(collections.Counter(m["class"] for m in misses))
    return out


def main():
    tool = load_impact()
    ns = tool.load()
    node, adj = tool.index(ns)
    adj_set = {(u, v) for u in adj for v, _, _ in adj[u]}
    assert len(ns["nodes"]) == 134 and len(ns["edges"]) == 216, "namespace size changed"  # 128/206 before A1

    # thread side + the dryerA check the article relies on
    depth = {}
    for s in node:
        depth[s] = {e: d for d, e, _ in tool.impact(node, adj, s, None)}
    dA = tool.resolve(node, "dryerA")
    dryerA_totals = [sum(1 for d in depth[dA].values() if d <= k) for k in DEPTHS] + [len(depth[dA])]
    assert dryerA_totals == [8, 22, 51, 72, 95, 113, 133], dryerA_totals  # [7, 20, 48, 67, 89, 107, 127] before A1
    connected = all(len(depth[s]) == len(node) - 1 for s in node)

    engines = {v: Engine(ns, v) for v in VARIANTS}
    e0 = engines["EXACT"]
    seg_cov = sorted(e0.seg_of)
    unsegmented = [{"element": i, "label": node[i]["label"], "reason": "no segment produced by P3"}
                   for i in sorted(node) if i not in e0.seg_of]
    seg_by_doc = collections.Counter(s["doc"] for s in e0.segs if s["eid"])
    ctx_by_doc = collections.Counter(s["doc"] for s in e0.segs if not s["eid"])

    # mapping check: SysML segments vs. the OMG export (elementId -> declaredName)
    omg_ok = []
    for rel in ("models/sysml/omg/01-requirements.omg.json", "models/sysml/omg/02-design.omg.json"):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            els = {e.get("@id"): e for e in json.load(open(p, encoding="utf-8")).get("elements", [])}
            for s in e0.segs:
                if s.get("sysml") and node[s["eid"]].get("uuid") in els:
                    omg_ok.append(els[node[s["eid"]]["uuid"]].get("declaredName") == s["sysml"]["name"])

    per_start = {}
    for v, eng in engines.items():
        for s in sorted(node):
            res = eng.run(s)
            c = compare(eng, tool, adj_set, adj, node, s, depth[s], res)
            c["per_round_detail"] = [{"round": r["round"], "n_terms": len(r["terms"]),
                                      "new_found": len(r["new_found"]), "cum_found": r["cum_found"]}
                                     for r in res["per_round"]]
            per_start.setdefault(s, {"label": node[s].get("shortName") or node[s]["label"],
                                     "concern": node[s]["concern"], "kind": node[s]["kind"]})[v] = c

    # scenarios (full detail)
    scenarios = []
    for key, q_, desc in SCENARIOS:
        s = tool.resolve(node, q_)
        sc = {"scenario": key, "start": s, "start_label": node[s]["label"], "description": desc,
              "thread": per_start[s]["EXACT"]["thread"]}
        for v in VARIANTS:
            res = engines[v].run(s)
            c = per_start[s][v]
            sc[v] = {
                "manual_per_round_cum": c["manual"]["per_round_cum"],
                "manual_fixpoint": c["manual"]["fixpoint"],
                "rounds_detail": [{"round": r["round"], "terms": r["terms"],
                                   "new_found": [node[e].get("shortName") or node[e]["label"] for e in r["new_found"]]}
                                  for r in res["per_round"]],
                "recall_unbounded": c["recall_unbounded"],
                "recall_round_k_vs_depth_k": c["recall_round_k_vs_depth_k"],
                "recall_fixpoint_vs_depth_k": c["recall_fixpoint_vs_depth_k"],
                "beyond_depth_hits_round_k": c["beyond_depth_hits_round_k"],
                "manual_only": c["manual_only"], "effort": c["effort"],
                "misses": c["misses"], "miss_classes": c["miss_classes"],
                "text_only_hits": c["text_only_hits"],
            }
        scenarios.append(sc)

    # aggregates over all starts
    agg = {}
    for v in VARIANTS:
        rows = [per_start[s][v] for s in sorted(node)]
        a = {
            "recall_unbounded": q([r["recall_unbounded"] for r in rows]),
            "recall_round_k_vs_depth_k": {k: q([r["recall_round_k_vs_depth_k"][k] for r in rows]) for k in (1, 2, 3)},
            "recall_fixpoint_vs_depth_k": {k: q([r["recall_fixpoint_vs_depth_k"][k] for r in rows]) for k in (1, 2, 3)},
            "manual_fixpoint_size": q([r["manual"]["fixpoint"] for r in rows]),
            "effort": {k: q([r["effort"][k] for r in rows]) for k in ("rounds", "terms", "searches", "segment_hits", "segments_read")},
            "starts_with_zero_found": sum(1 for r in rows if r["manual"]["fixpoint"] == 0),
            "fixpoint_size_distribution": dict(sorted(collections.Counter(r["manual"]["fixpoint"] for r in rows).items())),
            "starts_with_fixpoint_below_20": sorted(
                ("%s [%s] (%d)" % (per_start[s]["label"], per_start[s]["concern"], per_start[s][v]["manual"]["fixpoint"]) for s in sorted(node)
                 if per_start[s][v]["manual"]["fixpoint"] < 20)),
            "first_finding_via_thread_edge": q([r["first_finding_via_thread_edge"] for r in rows
                                                if r["first_finding_via_thread_edge"] is not None]),
            "starts_with_full_recall": sum(1 for r in rows if r["recall_unbounded"] == 1.0),
            "manual_only_total": sum(len(r["manual_only"]) for r in rows),
            "miss_classes_total": dict(sorted(collections.Counter(
                m["class"] for r in rows for m in r["misses"]).items())),
            "miss_detail_total": dict(sorted(collections.Counter(
                "%s:%s" % (m["class"], m["detail"]) for r in rows for m in r["misses"] if m["detail"]).items())),
            "text_only_hits_total": sum(len(r["text_only_hits"]) for r in rows),
            "text_only_hits_by_term": dict(collections.Counter(
                h["term"] for r in rows for h in r["text_only_hits"]).most_common(15)),
            "beyond_depth_hits_round_k_total": {k: sum(r["beyond_depth_hits_round_k"][k] for r in rows) for k in (1, 2, 3)},
            "by_start_concern": {},
        }
        for cn in sorted({node[s]["concern"] for s in node}):
            rr = [per_start[s][v] for s in sorted(node) if node[s]["concern"] == cn]
            a["by_start_concern"][cn] = {"n": len(rr),
                                         "recall_unbounded": q([r["recall_unbounded"] for r in rr]),
                                         "searches": q([r["effort"]["searches"] for r in rr])}
        # elements no start can find manually
        ever = collections.Counter()
        for s in node:
            for e in node:
                if e != s and not any(m["element"] == e for m in per_start[s][v]["misses"]):
                    ever[e] += 1
        never = [e for e in sorted(node) if ever[e] == 0]
        a["elements_never_found_from_any_start"] = [
            {"element": e, "label": node[e].get("shortName") or node[e]["label"], "concern": node[e]["concern"]}
            for e in never]
        a["found_from_n_starts"] = q([ever[e] for e in node])
        agg[v] = a

    # per-start records keep counts; full miss / hit lists are kept for the named scenarios only
    compact = {}
    for s_, rec in per_start.items():
        c_ = {k: rec[k] for k in ("label", "concern", "kind")}
        for v in VARIANTS:
            r = dict(rec[v])
            r["missed"] = sorted(m["element"] for m in r.pop("misses"))
            r["text_only_hits"] = len(r["text_only_hits"])
            r.pop("thread")
            c_[v] = r
        c_["thread"] = rec["EXACT"]["thread"]
        compact[s_] = c_

    with open(OUT_MD, encoding="utf-8") as f:
        md = f.read()
    if ("\n" + MARKER) not in md:
        raise SystemExit("results/manual_vs_thread.md lacks the Protocol section / marker")
    head = md.rpartition("\n" + MARKER)[0] + "\n"
    proto = head[head.index("## Protocol"):]
    proto_sha = hashlib.sha256(proto.encode("utf-8")).hexdigest()

    out = {
        "schema": "manual-vs-thread/1",
        "note": "Simulation of name-based manual tracing over the model files; not a human study.",
        "protocol": {
            "sha256_of_protocol_section": proto_sha,
            "documents": [{"id": d, "path": p} for d, p in DOCUMENTS],
            "excluded_inputs": EXCLUDED_INPUTS,
            "executable_model_names": EXEC_NAMES,
            "stopwords": sorted(STOPWORDS), "min_term_length": 3,
            "identifier_patterns": [p.pattern for p in ID_PATTERNS],
            "variants": {"EXACT": "case-sensitive substring, word boundary at identifier ends",
                         "LENIENT": "case-insensitive; whitespace, '-' and '_' ignored; matches start/end on token boundaries (separator, punctuation, camelCase, letter/digit)",
                         "LENIENT+DIAGRAM": "pre-registered sensitivity: LENIENT plus FTA gate inputs/outputEvent visible in the gate segment"},
            "primary_variants": PRIMARY,
            "quantiles": "statistics.quantiles(n=4, method='inclusive')",
        },
        "deviations": DEVIATIONS,
        "checks": {"dryerA_thread_cum_depth1_6_and_unbounded": dryerA_totals,
                   "thread_connected": connected,
                   "sysml_segments_match_omg_declaredName": "%d/%d" % (sum(omg_ok), len(omg_ok)),
                   **e0.checks},
        "segmentation": {
            "elements_with_segment": len(seg_cov), "of": len(node),
            "unsegmented": unsegmented,
            "element_segments_by_document": dict(sorted(seg_by_doc.items())),
            "context_segments_by_document": dict(sorted(ctx_by_doc.items())),
            "lexicon_size": len(e0.lexicon),
            "caveat": "the 14 digital-twin segments are built from the twin elements' visible labels in namespace/ads-namespace.json (the twin model file is not parsed); mesh names cross-checked against the GLB node names",
        },
        "scenarios": scenarios,
        "aggregate_all": agg,
        "per_start": compact,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=False, default=str)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(head + MARKER + "\n" + render_md(out, node))
    print("wrote %s and %s" % (os.path.relpath(OUT_JSON, ROOT), os.path.relpath(OUT_MD, ROOT)))
    for v in PRIMARY:
        a = agg[v]
        print("%-8s recall_inf median %.3f IQR [%.3f, %.3f]; searches median %s" % (
            v, a["recall_unbounded"]["median"], a["recall_unbounded"]["q1"], a["recall_unbounded"]["q3"],
            a["effort"]["searches"]["median"]))


# ----------------------------------------------------------------------------- report
def fmt_q(d, pct=False):
    if pct:
        return "%.0f%% [%.0f–%.0f%%]" % (100 * d["median"], 100 * d["q1"], 100 * d["q3"])
    return "%g [%g–%g]" % (d["median"], d["q1"], d["q3"])


def render_md(o, node):
    L = []
    ck = o["checks"]
    L.append("\n## Results\n")
    L.append("Generated by `python3 tools/manual_trace.py`. Protocol section sha256 `%s`." % o["protocol"]["sha256_of_protocol_section"][:16])
    L.append("")
    L.append("**Checks.**")
    L.append("")
    L.append("- dryerA thread totals at depth 1–6 and unbounded: %s." % "/".join(map(str, ck["dryerA_thread_cum_depth1_6_and_unbounded"])))
    L.append("- Thread connected (every start reaches all %d others): %s." % (len(node) - 1, ck["thread_connected"]))
    L.append("- SysML segment names agree with the OMG export's declaredName: %s." % ck["sysml_segments_match_omg_declaredName"])
    if "twin_mesh_names_in_glb" in ck:
        g = ck["twin_mesh_names_in_glb"]
        L.append("- Twin mesh names present as GLB node names: %d/%d." % (g["found_in_glb"], g["mesh_names"]))
    sg = o["segmentation"]
    L.append("\n### Segmentation\n")
    L.append("%d of %d identity-space elements have a searchable segment. Element segments by document: %s. Context segments: %s. Lexicon: %d names." % (
        sg["elements_with_segment"], sg["of"],
        ", ".join("%s %d" % kv for kv in sg["element_segments_by_document"].items()),
        ", ".join("%s %d" % kv for kv in sg["context_segments_by_document"].items()), sg["lexicon_size"]))
    if sg["unsegmented"]:
        L.append("")
        L.append("Unsegmented: " + "; ".join("%s (%s)" % (u["label"], u["reason"]) for u in sg["unsegmented"]))
    L.append("")
    L.append("Caveat: " + sg["caveat"] + ".")

    L.append("\n### Named scenarios\n")
    L.append("Columns k1–k3 give cumulative counts at thread depth k or manual round k. 'fix' is the manual fixpoint.")
    L.append("Thread queries: 1 per start. Searches = distinct terms × 11 documents.\n")
    L.append("| Scenario | Side | k1 | k2 | k3 | k4 | k5 | k6 | ∞ / fix | recall ∞ | recall k1/k2/k3 (round k vs depth k) | fixpoint vs depth k1/k2/k3 | rounds | terms | searches |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for sc in o["scenarios"]:
        th = sc["thread"]
        L.append("| %s | thread | %s | %d | — | — | — | 1 query |" % (
            sc["scenario"], " | ".join(str(th["per_depth_cum"][k]) for k in DEPTHS), th["unbounded"]))
        for v in VARIANTS:
            m = sc[v]
            pr = m["manual_per_round_cum"]
            last = max(pr) if pr else 0
            cells = [str(pr.get(k, pr[last] if pr else 0)) for k in DEPTHS]
            L.append("| %s | %s | %s | %d | %.0f%% | %s | %s | %d | %d | %d |" % (
                sc["scenario"], v, " | ".join(cells), m["manual_fixpoint"], 100 * m["recall_unbounded"],
                " / ".join("%.0f%%" % (100 * m["recall_round_k_vs_depth_k"][k]) for k in (1, 2, 3)),
                " / ".join("%.0f%%" % (100 * m["recall_fixpoint_vs_depth_k"][k]) for k in (1, 2, 3)),
                m["effort"]["rounds"], m["effort"]["terms"], m["effort"]["searches"]))
    L.append("")
    L.append("Columns k1–k6 for a manual row repeat the fixpoint once the fixpoint is reached.")

    L.append("\n### All %d start elements (median [Q1–Q3])\n" % len(node))
    L.append("| Variant | recall ∞ | round-k vs depth-k recall, k=1 / 2 / 3 | fixpoint vs depth-k, k=1 / 2 / 3 | found at fixpoint | rounds | terms | searches | segments read | starts with 0 found | starts with recall 100% |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for v in VARIANTS:
        a = o["aggregate_all"][v]
        L.append("| %s%s | %s | %s | %s | %s | %s | %s | %s | %s | %d | %d |" % (
            v, " (sensitivity)" if v not in PRIMARY else "",
            fmt_q(a["recall_unbounded"], True),
            " / ".join(fmt_q(a["recall_round_k_vs_depth_k"][k], True) for k in (1, 2, 3)),
            " / ".join(fmt_q(a["recall_fixpoint_vs_depth_k"][k], True) for k in (1, 2, 3)),
            fmt_q(a["manual_fixpoint_size"]), fmt_q(a["effort"]["rounds"]), fmt_q(a["effort"]["terms"]),
            fmt_q(a["effort"]["searches"]), fmt_q(a["effort"]["segments_read"]),
            a["starts_with_zero_found"], a["starts_with_full_recall"]))
    L.append("")
    L.append("Thread side, for comparison: 1 query per start, and the unbounded closure is %d for every start." % (len(node) - 1))
    L.append("")
    for v in PRIMARY:
        a = o["aggregate_all"][v]
        L.append("%s fixpoint sizes (size: number of starts): %s. Starts whose fixpoint is below 20: %s." % (
            v, ", ".join("%s: %d" % kv for kv in a["fixpoint_size_distribution"].items()),
            ", ".join(a["starts_with_fixpoint_below_20"])))
        L.append("")
    L.append("")
    L.append("Elements found manually but not reached by the thread, summed over %d starts: " % len(node) + ", ".join(
        "%s %d" % (v, o["aggregate_all"][v]["manual_only_total"]) for v in VARIANTS) + ".")
    L.append("\nRecall ∞ by concern of the start element (median [Q1–Q3]):\n")
    L.append("| Start concern | n | EXACT | LENIENT |")
    L.append("|---|---|---|---|")
    for cn, d in o["aggregate_all"]["EXACT"]["by_start_concern"].items():
        dl = o["aggregate_all"]["LENIENT"]["by_start_concern"][cn]
        L.append("| %s | %d | %s | %s |" % (cn, d["n"], fmt_q(d["recall_unbounded"], True), fmt_q(dl["recall_unbounded"], True)))

    L.append("\n## Audit\n")
    L.append("### Miss classes, summed over all %d starts (element misses)\n" % len(node))
    L.append("| Class | " + " | ".join(VARIANTS) + " |")
    L.append("|---|" + "---|" * len(VARIANTS))
    for c in MISS_CLASSES:
        L.append("| %s | %s |" % (c, " | ".join(str(o["aggregate_all"][v]["miss_classes_total"].get(c, 0)) for v in VARIANTS)))
    L.append("")
    for v in PRIMARY:
        d = o["aggregate_all"][v]["miss_detail_total"]
        if d:
            L.append("%s detail: %s." % (v, "; ".join("%s %d" % kv for kv in d.items())))
            L.append("")
    for v in PRIMARY:
        nv = o["aggregate_all"][v]["elements_never_found_from_any_start"]
        L.append("%s: %d element(s) are found from no start at all: %s." % (
            v, len(nv), ", ".join(x["label"] for x in nv) or "none"))
        L.append("")
    for sc in o["scenarios"]:
        if sc["scenario"] not in ("dryerA", "controller"):
            continue
        L.append("### Misses for %s\n" % sc["scenario"])
        for v in PRIMARY:
            m = sc[v]
            L.append("**%s.** %d missed of %d. By class: %s.\n" % (v, len(m["misses"]), sc["thread"]["unbounded"],
                     ", ".join("%s %d" % kv for kv in sorted(m["miss_classes"].items())) or "none"))
            by = collections.defaultdict(list)
            for x in m["misses"]:
                by[(x["class"], x["detail"])].append("%s (d%d)" % (x["label"], x["thread_depth"]))
            for (c, dtl), labs in sorted(by.items(), key=lambda kv: (MISS_CLASSES.index(kv[0][0]), str(kv[0][1]))):
                L.append("- %s%s: %s" % (c, " [%s]" % dtl if dtl else "", ", ".join(labs)))
            L.append("")
    L.append("### Text-only hits\n")
    L.append("These are elements whose first-finding hop is not a thread edge: the term came from an element that is not adjacent in the thread, or reached the element through a context segment. Because the thread is connected, every such element is still inside T_∞.\n")
    for v in PRIMARY:
        a = o["aggregate_all"][v]
        L.append("- %s: %d text-only first findings over %d starts. Most frequent terms: %s. Beyond-depth hits (M_k \\ T_k) summed for k=1/2/3: %s." % (
            v, a["text_only_hits_total"], len(node),
            ", ".join("`%s` %d" % kv for kv in a["text_only_hits_by_term"].items()) or "none",
            " / ".join(str(a["beyond_depth_hits_round_k_total"][k]) for k in (1, 2, 3))))
    for v in PRIMARY:
        a = o["aggregate_all"][v]
        L.append("- %s: the share of found elements whose first-finding hop is a thread edge has median %s." % (
            v, fmt_q(a["first_finding_via_thread_edge"], True)))
    for sc in o["scenarios"]:
        for v in PRIMARY:
            t = sc[v]["text_only_hits"]
            if t:
                beyond = sum(1 for h in t if h["thread_depth"] > h["round"])
                L.append("- %s, %s: %d of %d found elements were first reached through a non-thread hop, %d of them in an earlier round than their thread depth. Examples: %s. The full list is in the JSON." % (
                    sc["scenario"], v, len(t), sc[v]["manual_fixpoint"], beyond, "; ".join(
                        "%s via `%s` from %s (round %d, thread depth %s)" % (h["label"], h["term"], h["source"], h["round"], h["thread_depth"]) for h in t[:5])))
    L.append("\n## Deviations\n")
    L.append("\n".join("- " + d for d in o["deviations"]) if o["deviations"] else "None. The first run is the reported run.")
    L.append("\n## Limitations\n")
    for x in LIMITATIONS:
        L.append("- " + x)
    L.append("")
    return "\n".join(L)


LIMITATIONS = [
    "This is a simulation of name-based search, not a human study. A real engineer also reads diagrams, uses domain knowledge and asks colleagues. Equally, a real engineer may stop early or skip hits. Neither is modelled.",
    "The procedure is generous to manual tracing in one respect: every hit is read and every cited name is followed to a fixpoint, with no fatigue and no budget. Effort is counted rather than limited.",
    "The procedure is strict in another respect. Relationships carried only by diagram structure (GSN argument edges, FTA gate wiring) or by typed links are invisible to text search. The GSN edges are absent from the deposited GSN file. LENIENT+DIAGRAM bounds the FTA part of this effect.",
    "The twin document is reconstructed from the twin elements' labels in namespace/ads-namespace.json, because the procedure reads names, not the twin model file. Mesh names were cross-checked against the GLB.",
    "Manual round k and thread depth k are different units: one round can follow several textual hops, and one thread hop may need several rounds. The fixpoint-vs-depth-k recall is reported alongside for this reason.",
    "Recall is measured against the thread's own closure, which includes links authored to complete the thread (origin 'completion', accepted in engineering review). The comparison therefore shows what text search recovers of this thread, not of an independent ground truth.",
    "The thread is connected (every unbounded closure is 133 elements). Recall against T_∞ therefore measures coverage of the whole model set, and 'false hits' can only be judged per hop or per depth.",
    "The stop list, the lexicon and the names of the executable models are fixed choices. Other reasonable choices would move the numbers. They were fixed before the first run and not tuned.",
]

if __name__ == "__main__":
    sys.exit(main())
