"""Checks of the gate GJ records: LinkML validation, RDF parse and isomorphism, label rules, E19 and optional SHACL.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream E,
for the main agent. Gate GJ (OPEN), status EXCEPTION (process rule 10), NOT RELEASED. Plan: chapter 5.4 of
`crisp-dm/00-cross-cutting/plan-full-conversion.md`.
Change of 13.10.2026 (stream G of wave 4, Claude Opus 5.5): rule A2 of addendum A in check C1 (recorded I95 gaps),
and check C10 as information (decision M5, rule A3).
Change of 13.10.2026 (stream X2 of the last change round before the design freeze, Claude Opus 5.5). An error
raised in check C10 is recorded and does not stop the record.

1 Checks for one record (folder <out>/<doc>/ of `src/m10_writer.py` and `src/m10_rdf.py`)
  C1  LinkML validation (linkml==1.11.1, the validator of linkml-validate with the plugin JsonschemaValidationPlugin,
      closed=True): <doc>.ech.yaml against I95 (class Container), <doc>.provenance.yaml against the profile 0.2.0
      (class ExtractionRecord), <doc>.labels.yaml against the label schema (class LabelRecord), and the atom
      layout of the record against the label schema (class PdfLayout). Option --cli: the command linkml-validate
      (uvx --offline) for the three YAML files.
      Record with recorded I95 gaps (addendum A to the criteria, rule A2; manifest key i95_gaps; functions in
      `src/m10_gaps.py`): the check of <doc>.ech.yaml uses I95 with exactly the recorded gap slots of the affair
      not required (a copy of the schema in memory; no schema file changes). Such a record passes only if its
      absent required slots in I95 are exactly its recorded gaps, I95 without a change refuses it, the relaxed
      check gives 0 errors, and the side file has the NotMappedRecord of each gap. This check is always in
      process (also with --cli). A record without a recorded gap is checked against I95 without a change.
  C2  rdflib parses each RDF file (TriG, RDF/XML, Turtle).
  C3  The union of the TriG graphs is isomorphic with <doc>.gesamt.rdf.xml. <doc>.ech.ttl is isomorphic with
      <doc>.ech.rdf.xml and with the graph <record>/ech-0295 of the TriG file. The blank nodes of these graphs
      form a forest, so a comparison of the canonical triples (each blank node replaced by the SHA-256 of its
      subtree) decides in linear time. For another graph, or with --exact-isomorphism, rdflib.compare.isomorphic
      decides.
  C4  Each named graph of the TriG file is isomorphic with its part, made again from the YAML files, the block
      file and the atom file. The TriG file has the 4 named graphs only.
  C5  Each leaf value of each YAML file is a value or a node IRI of its graph. A float also has its decimal
      forms (5e-08 is the xsd:decimal 0.00000005 of src/m10_rdf.py).
  C6  Each IRI of each graph has a scheme.
  C7  Each label from a rule, an Apertus head or a code step has one probability (xsd:decimal in [0.005, 0.995]),
      a calibration IRI of a prov:Plan node in the label graph, a value status, a page and a character span. Each
      option probability is in [0.005, 0.995]. A label from the export, a constant or a copy has none of these.
  C8  Each Docling block of the atom graph has one block label with the page and the span of the block. The spans
      of the block file give the block texts in the document text of `src/m10_docs.py` (interface 2). The label
      graph has one label D1. The subject of a copy label is a node of the provenance graph.
  C9  E19 for each TextBlock of the instance: `m06_converter.e19_problems` with the atoms and the text changes of
      its TextBlockRecord. The atoms of the TextBlockRecord are the atoms of the blocks whose block labels name
      the instance path of the TextBlock, without the fixed atoms. Information only: the independent wording
      comparison `m06_ech_ausgabe.wortlaut_abgleich`.
  C10 SHACL only if pyshacl is importable (decision JD5: pyshacl==0.40.1). Else the result is "skipped".
      The shapes come from gen-shacl (linkml ShaclGenerator, default options), once for each schema: the wrapper
      for the graph <record>/ech-0295, the profile 0.2.0 for <record>/provenance, the label schema for
      <record>/labels and <record>/atoms. pyshacl validates each of the 4 graphs against its shapes (inference
      none). These graphs are the parts of C4, which are isomorphic with the named graphs of the TriG file; their
      blank-node names come from their content, so each run gives the same text. The result gives, for each
      graph, the validation results grouped by node shape, constraint component, path and severity, with
      examples of the focus node and the value. The shape digest is the SHA-256 of the canonical triples of the
      shapes (gen-shacl gives new blank-node names in each run).
      C10 is information only (decision M5 of the protocol, addendum A rule A3). It does not decide the key
      passed. The key shacl_information_only is true in each result.
      An error raised in C10 (gen-shacl or pyshacl) does not stop the record. The result of C10 is then the status
      "error" with the type of the exception (keys error_type and reason). The key passed does not change.
  Output: <folder>/validation.json and the key "validation" of manifest.json.
  Keys of validation.json: passed (C1 to C9 only; the same value with and without pyshacl), conformance ("i95" or
  "i95_with_recorded_gaps": the rule of check C1; it is a result only with passed true), i95_gaps (the list of
  the manifest), shacl_information_only (true), C1_linkml to C9_e19 and C10_shacl (each with passed or status).
  For a record with gaps, C1_linkml has the key i95_gap_rule with the details of rule A2.

2 Process rule 6
  The checks read the atom file and the Docling file only at the explicit paths daten/iso/<kind>/<doc>.json.

Usage (from the project folder; one command on one line):
  uv run --offline --no-project --python 3.12 --with linkml==1.11.1 python src/m10_validate.py --out <dir>
      [--doc DOC ...] [--cli]
  With C10 (the record of the pyshacl download is daten/gj/shacl/pyshacl_install.json):
  uv run --offline --no-project --python 3.12 --with linkml==1.11.1 --with pyshacl==0.40.1 python
      src/m10_validate.py --out <dir> [--doc DOC ...] [--cli]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from decimal import Decimal
from functools import lru_cache
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_record as gr  # noqa: E402  (E19 signatures; not changed)
import m03_iso_v4 as v4  # noqa: E402  (fixed answers; not changed)
import m06_converter as mc  # noqa: E402  (E19 check; not changed)
import m06_ech_ausgabe as ea  # noqa: E402  (independent wording comparison; not changed)
import m10_docs as docs_text  # noqa: E402  (document text and spans of interface 2, stream B)
import m10_gaps as gp  # noqa: E402  (recorded I95 gaps, addendum A rule A2)
import m10_rdf as rdf  # noqa: E402

ROOT = rdf.ROOT
SCRIPT = "src/m10_validate.py"
I95 = mc.I95
PROFILE = rdf.PROFILE
LABEL_SCHEMA = rdf.LABEL_SCHEMA
WRAPPER = rdf.WRAPPER
UVX_VALIDATE = ["uvx", "--offline", "--from", rdf.LINKML, "linkml-validate"]
PLB = "https://schema.parlpdfech.example/labels/"
PPX = "https://schema.parlpdfech.example/profile/"
PROB_SOURCES = {"rule", "apertus_head", "code_step"}
FIXED_SOURCES = {"export", "constant", "copy"}
P_MIN, P_MAX = 0.005, 0.995
RX_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
if gp.I95.resolve() != Path(I95).resolve():
    raise SystemExit("src/m10_gaps.py and src/m06_converter.py name different I95 files")


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ C1 LinkML validation
@lru_cache(maxsize=None)
def validator(schema: Path):
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin
    with rdf.in_src():
        v = Validator(str(schema), validation_plugins=[JsonschemaValidationPlugin(closed=True)])
        list(v.iter_results({}, "PdfLayout" if schema == LABEL_SCHEMA else
                            "ExtractionRecord" if schema == PROFILE else "Container"))   # compile once in src/
    return v


def linkml_check(schema: Path, cls: str, data: dict, name: str) -> dict:
    with rdf.in_src():
        msgs = [r.message for r in validator(schema).iter_results(data, cls)]
    return {"file": name, "schema": rdf.rel(schema), "class": cls, "valid": not msgs, "errors": len(msgs),
            "messages": [m[:400] for m in msgs[:10]]}


def linkml_cli(schema: Path, cls: str, path: Path) -> dict:
    p = subprocess.run(UVX_VALIDATE + ["-s", str(schema), "-C", cls, str(path)], capture_output=True, text=True,
                       timeout=900)
    errors = [z for z in p.stdout.splitlines() if z.startswith("[ERROR]")]
    ok = p.returncode == 0 and not errors and "No issues found" in p.stdout
    return {"file": rdf.rel(path), "schema": rdf.rel(schema), "class": cls, "valid": ok, "errors": len(errors),
            "messages": [z[:400] for z in errors[:10]] or ([] if ok else p.stderr.strip().splitlines()[-3:]),
            "tool": "linkml-validate (uvx --offline)"}


def gap_check(rule: dict, name: str) -> dict:
    """The C1 entry of <doc>.ech.yaml for a record with recorded gaps (addendum A, rule A2): the result of I95
    with exactly the recorded gap slots not required. The entry is valid only if the whole gap rule passes."""
    x = rule["i95_with_recorded_gaps"]
    errors = x["errors"] if x["errors"] is not None else 1
    return {"file": name, "schema": rdf.rel(I95), "class": "Container", "valid": bool(rule["passed"]),
            "errors": errors if errors or rule["passed"] else len(rule["problems"]),
            "messages": (x["messages"] + [m[:400] for m in rule["problems"]])[:10],
            "i95_slots_not_required": x["slots_not_required"]}


# ------------------------------------------------------------------ C3 and C4 isomorphism
def term_key(t) -> tuple:
    import rdflib
    if isinstance(t, rdflib.Literal):
        return ("L", str(t), str(t.datatype or ""), t.language or "")
    return ("U", str(t))


def bnode_forest(g) -> bool:
    """True if each blank node has at most one incoming triple and the blank nodes have no cycle."""
    import rdflib
    incoming: dict = {}
    for s, _, o in g:
        if isinstance(o, rdflib.BNode):
            incoming[o] = incoming.get(o, 0) + 1
            if incoming[o] > 1 or o == s:
                return False
    seen, stack = set(), set()

    def cyclic(b) -> bool:
        if b in stack:
            return True
        if b in seen:
            return False
        seen.add(b)
        stack.add(b)
        bad = any(cyclic(o) for o in g.objects(b, None) if isinstance(o, rdflib.BNode))
        stack.discard(b)
        return bad
    return not any(cyclic(b) for b in incoming)


def canonical_triples(g):
    """The triples of g with each blank node replaced by the SHA-256 of its sorted subtree (blank-node forests)."""
    import collections
    import rdflib
    memo: dict = {}

    def h(b) -> str:
        if b not in memo:
            parts = sorted(repr((term_key(p), ("B", h(o)) if isinstance(o, rdflib.BNode) else term_key(o)))
                           for p, o in g.predicate_objects(b))
            memo[b] = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
        return memo[b]

    def k(t):
        return ("B", h(t)) if isinstance(t, rdflib.BNode) else term_key(t)
    return collections.Counter((k(s), term_key(p), k(o)) for s, p, o in g)


def same_graph(g1, g2) -> bool:
    """Isomorphism test. For graphs whose blank nodes form a forest (all graphs of these records) the canonical
    triples decide in linear time; for other graphs rdflib.compare.isomorphic decides."""
    from rdflib.compare import isomorphic
    if len(g1) != len(g2):
        return False
    if bnode_forest(g1) and bnode_forest(g2):
        return canonical_triples(g1) == canonical_triples(g2)
    return isomorphic(g1, g2)


# ------------------------------------------------------------------ C5 leaf values
@lru_cache(maxsize=None)
def enum_meanings(schema: Path) -> dict[str, set[str]]:
    """{permissible value: IRIs of its meaning} of all enums of a schema (an enum value with a meaning is an IRI)."""
    sv, _, _ = rdf.bundle(schema)
    out: dict[str, set[str]] = {}
    with rdf.in_src():
        for e in sv.all_enums().values():
            for name, pv in (e.permissible_values or {}).items():
                if pv.meaning:
                    out.setdefault(name, set()).add(sv.expand_curie(pv.meaning))
    return out


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    elif obj is not None:
        yield prefix, obj


def graph_values(g) -> set[str]:
    import rdflib
    out = set()
    for t in g:
        for x in (t[0], t[2]):
            s = str(x)
            out |= {s, s.lower()}
            if isinstance(x, rdflib.URIRef):
                out.add(re.split(r"[/#]", s)[-1])
            elif isinstance(x, rdflib.Literal):
                py = x.toPython()
                out |= {str(py), str(py).lower()}
    return out


def leaf_forms(v, meanings: dict) -> set[str]:
    s = str(v)
    out = {s, s.lower()} | meanings.get(s, set())
    if isinstance(v, bool):
        out.add("true" if v else "false")
    if isinstance(v, float):
        out.add(repr(v))
        out.add(str(Decimal(repr(v))))   # src/m10_rdf.py as_decimals: 5.5e-05 is the decimal 0.000055 in the graph
        out.add(format(Decimal(repr(v)), "f"))   # the xsd:decimal text of rdflib: 5e-08 is 0.00000005 (not 5E-8)
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", v):
        out.add(v[:-1] + "+00:00")
    return out


def leaf_coverage(data: dict, g, schema: Path) -> list[str]:
    vals, meanings = graph_values(g), enum_meanings(schema)
    return [p for p, v in leaves(data) if not leaf_forms(v, meanings) & vals]


# ------------------------------------------------------------------ C7 and C8 label rules
def label_checks(graphs: dict, doc: dict) -> dict:
    import rdflib
    from rdflib.namespace import PROV, RDF, XSD
    P = rdflib.Namespace(PLB)
    X = rdflib.Namespace(PPX)
    gl, ga, gp = graphs["labels"], graphs["atoms"], graphs["provenance"]
    plans = set(gl.subjects(RDF.type, PROV.Plan))
    bad, n_prob, n_fixed, by_kind = [], 0, 0, {}
    block_labels: dict[str, list] = {}
    for la in gl.subjects(RDF.type, P.LabelAssertion):
        name = str(la).rsplit("/", 1)[-1]
        src = {str(o).rsplit("/", 1)[-1] for o in gl.objects(la, P.labelSource)}
        kind = {str(o).rsplit("/", 1)[-1] for o in gl.objects(la, P.labelKind)}
        k = next(iter(kind), "?")
        by_kind[k] = by_kind.get(k, 0) + 1
        probs = list(gl.objects(la, P.probability))
        cals = list(gl.objects(la, P.calibration))
        status = list(gl.objects(la, P.valueStatus))
        opts = [o for op in gl.objects(la, P.optionProbability) for o in gl.objects(op, P.probability)]
        if len(src) != 1:
            bad.append(f"{name}: {len(src)} label sources")
            continue
        s = next(iter(src))
        if s in PROB_SOURCES:
            n_prob += 1
            if len(probs) != 1 or probs[0].datatype != XSD.decimal or not P_MIN <= float(probs[0]) <= P_MAX:
                bad.append(f"{name}: not one probability (xsd:decimal) in [{P_MIN}, {P_MAX}]")
            if len(cals) != 1 or not isinstance(cals[0], rdflib.URIRef) or cals[0] not in plans:
                bad.append(f"{name}: not one calibration IRI of a prov:Plan node of the label graph")
            if len(status) != 1:
                bad.append(f"{name}: not one value status")
            page = list(gl.objects(la, P.page))
            cs, ce = list(gl.objects(la, P.charStart)), list(gl.objects(la, P.charEnd))
            if len(page) != 1 or int(page[0]) < 1:
                bad.append(f"{name}: not one page")
            if len(cs) != 1 or len(ce) != 1 or not 0 <= int(cs[0]) <= int(ce[0]):
                bad.append(f"{name}: not one character span")
            if any(not P_MIN <= float(o) <= P_MAX for o in opts):
                bad.append(f"{name}: an option probability is not in [{P_MIN}, {P_MAX}]")
        elif s in FIXED_SOURCES:
            n_fixed += 1
            if probs or cals or status or opts:
                bad.append(f"{name}: a label from {s} has a probability, a calibration or a value status")
            if s == "copy":
                subj = next(gl.objects(la, RDF.subject), None)
                if subj is None or not any(gp.triples((subj, None, None))):
                    bad.append(f"{name}: the subject of the copy label is not a node of the provenance graph")
        else:
            bad.append(f"{name}: unknown label source {s}")
        if k == "block_slot":
            block_labels.setdefault(str(next(gl.objects(la, RDF.subject))), []).append(la)
    blocks = set(ga.subjects(RDF.type, P.PdfBlock))
    for b in blocks:
        ls = block_labels.get(str(b), [])
        if len(ls) != 1:
            bad.append(f"{str(b).rsplit('/', 1)[-1]}: {len(ls)} block labels")
            continue
        la = ls[0]
        want = (int(next(ga.objects(b, X.pageNumber))), int(next(ga.objects(b, X.charStart))),
                int(next(ga.objects(b, X.charEnd))))
        got = (int(next(gl.objects(la, P.page))), int(next(gl.objects(la, P.charStart))),
               int(next(gl.objects(la, P.charEnd))))
        if want != got:
            bad.append(f"{str(b).rsplit('/', 1)[-1]}: page and span of the block label {got} differ from the block {want}")
    extra = set(block_labels) - {str(b) for b in blocks}
    if extra:
        bad.append(f"{len(extra)} block labels for blocks that are not in the atom graph")
    if by_kind.get("document_text_parts", 0) != 1:
        bad.append(f"{by_kind.get('document_text_parts', 0)} labels D1")
    try:
        docs_text.check_doc(doc)      # the block spans give the block texts in m10_docs.doc_text (interface 2)
    except (ValueError, KeyError, TypeError) as e:
        bad.append(f"interface 2 spans: {e}")
    return {"passed": not bad, "problems": bad[:50], "labels": sum(by_kind.values()), "by_kind": by_kind,
            "pdf_derived_labels": n_prob, "labels_without_probability": n_fixed, "blocks": len(blocks),
            "calibration_nodes": len(plans)}


# ------------------------------------------------------------------ C9 E19
def instance_value(obj, path: str):
    for name, idx in re.findall(r"([A-Za-z_]+)|\[(\d+)\]", path):
        obj = obj[name] if name else obj[int(idx)]
    return obj


def e19_checks(d: str, ech: dict, prov: dict, labels: dict, doc: dict) -> dict:
    atoms = json.loads(rdf.explicit_atoms(d).read_text(encoding="utf-8"))["atome"]
    by_id = {a["id"]: a for a in atoms}
    fixed = v4.fixed_answers(d)
    block_atoms = {b["block"]: b["atoms"] for b in doc["blocks"]}
    by_path: dict[str, list[str]] = {}
    for la in labels["label_assertions"]:
        if la["label_kind"] == "block_slot" and la.get("instance_path"):
            by_path.setdefault(la["instance_path"], []).append(la["label_subject"].rsplit("/", 1)[-1])
    bad, info, n, chars = [], [], 0, 0
    for r in prov["text_block_records"]:
        if r["mapping_status"] != "in_ech_instance":
            continue
        n += 1
        path = r["instance_path"]
        tb = instance_value(ech, path)
        text = tb["text"]
        ids = [e["atom_id"] for u in r["units"] for e in u.get("atom_evidence") or []]
        want = [a for b in by_path.get(path, []) for a in block_atoms[b] if a not in fixed]
        if ids != want:
            bad.append(f"{path}: the atoms of the TextBlockRecord are not the atoms of its labelled blocks")
        if tb.get("text_type") != r.get("ech_text_type"):
            bad.append(f"{path}: text_type differs from ech_text_type of the TextBlockRecord")
        tc = r["text_changes"]
        bad += [f"{path}: {x}" for x in mc.e19_problems(d, by_id, ids, text, tc)]
        chars += len(gr.signature_text(text))
        empty = set(tc.get("empty_atoms") or [])
        w = ea.wortlaut_abgleich(ea.sichtbarer_text(text, "richtext"),
                                 [by_id[a].get("text") or "" for a in ids if a not in empty])
        if not w["ok"]:
            info.append(f"{path}: the independent wording comparison stops at letter {w['abweichung_ab']}")
    return {"passed": not bad, "text_blocks": n, "characters": chars, "problems": bad[:50],
            "independent_comparison_differences": info[:20]}


# ------------------------------------------------------------------ C10 SHACL (optional)
SHACL_SCHEMAS = {"ech-0295": WRAPPER, "provenance": PROFILE, "labels": LABEL_SCHEMA, "atoms": LABEL_SCHEMA}
SHACL_GROUPS, SHACL_EXAMPLES = 30, 5


@lru_cache(maxsize=None)
def shacl_shapes(schema: Path):
    """(shapes graph, facts) of gen-shacl (linkml ShaclGenerator, default options) for one schema, once per process."""
    import rdflib
    from linkml.generators.shaclgen import ShaclGenerator
    from rdflib.namespace import RDF, SH
    with rdf.in_src():
        text = ShaclGenerator(str(schema)).serialize()
    g = rdflib.Graph().parse(data=text, format="turtle")
    keys = sorted(f"{n}\t{k!r}" for k, n in canonical_triples(g).items()) if bnode_forest(g) else [text]
    return g, {"schema": rdf.rel(schema), "schema_sha256": sha256(schema), "triples": len(g),
               "node_shapes": len(set(g.subjects(RDF.type, SH.NodeShape))),
               "digest": hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest(),
               "digest_method": "canonical triples" if bnode_forest(g) else "Turtle text (not stable)"}


def short(x) -> str:
    return re.split(r"[/#]", str(x))[-1] if x is not None else ""


def node_text(g, n) -> str:
    """An IRI, or a blank node with its name and the path from the nearest IRI (for example
    '_:b3f… (<record>/label/B4-slot optionProbability)'). The blank-node names of the part graphs come from their
    content (src/m10_rdf.py stable_bnodes), so the text is the same in each run."""
    import rdflib
    if not isinstance(n, rdflib.BNode):
        return str(n)
    steps, cur = [], n
    for _ in range(20):
        up = next(iter(g.subject_predicates(cur)), None)
        if up is None:
            break
        cur = up[0]
        steps.insert(0, short(up[1]))
        if not isinstance(cur, rdflib.BNode):
            break
    return f"_:{n} ({'<' + str(cur) + '> ' if not isinstance(cur, rdflib.BNode) else ''}{' '.join(steps)})"


def shacl_results(rg, shapes, data) -> list[dict]:
    """The results of a pyshacl report graph, grouped by node shape, constraint component, path and severity (a
    property shape is replaced by the node shape that holds it), each group with its first examples in sorted order."""
    from rdflib.namespace import RDF, SH
    holder = {ps: ns for ns, ps in shapes.subject_objects(SH.property)}
    rows = []
    for r in rg.subjects(RDF.type, SH.ValidationResult):
        src = rg.value(r, SH.sourceShape)
        value = rg.value(r, SH.value)
        rows.append(((str(holder.get(src, src)), short(rg.value(r, SH.sourceConstraintComponent)),
                      str(rg.value(r, SH.resultPath) or ""), short(rg.value(r, SH.resultSeverity))),
                     {"focus_node": node_text(data, rg.value(r, SH.focusNode)),
                      "value": "" if value is None else node_text(data, value)[:300],
                      "message": str(rg.value(r, SH.resultMessage) or "")[:300]}))
    groups: dict = {}
    for key, ex in sorted(rows, key=lambda x: (x[0], x[1]["focus_node"], x[1]["value"], x[1]["message"])):
        g = groups.setdefault(key, {"node_shape": key[0], "component": key[1], "path": key[2], "severity": key[3],
                                    "count": 0, "examples": []})
        g["count"] += 1
        if len(g["examples"]) < SHACL_EXAMPLES:
            g["examples"].append(ex)
    return sorted(groups.values(), key=lambda g: (-g["count"], g["node_shape"], g["component"], g["path"]))


def shacl_checks(graphs: dict) -> dict:
    """C10: each graph of the record against the gen-shacl shapes of its schema (SHACL_SCHEMAS)."""
    try:
        import pyshacl
    except ImportError:
        return {"status": "skipped", "reason": "pyshacl is not importable (the command has no --with pyshacl)"}
    from importlib.metadata import version
    out = {}
    for name, schema in SHACL_SCHEMAS.items():
        shapes, facts = shacl_shapes(schema)
        conforms, rg, _ = pyshacl.validate(graphs[name], shacl_graph=shapes, inference="none", abort_on_first=False,
                                           allow_infos=False, allow_warnings=False, advanced=False)
        groups = shacl_results(rg, shapes, graphs[name])
        out[name] = {"conforms": bool(conforms), "shapes": facts["schema"], "triples": len(graphs[name]),
                     "results": sum(g["count"] for g in groups), "groups": groups[:SHACL_GROUPS]}
    return {"status": "run", "passed": all(x["conforms"] for x in out.values()),
            "tools": {p: version(p) for p in ("pyshacl", "owlrl", "rdflib", "linkml")},
            "method": "gen-shacl shapes (linkml ShaclGenerator, default options); pyshacl.validate of each of the 4 "
                      "graphs of the record (the parts of C4), inference none",
            "shapes": {facts["schema"]: facts for facts in (shacl_shapes(s)[1] for s in dict.fromkeys(SHACL_SCHEMAS.values()))},
            "graphs": out}


# ------------------------------------------------------------------ one record
def validate_record(folder: Path, d: str, cli: bool = False, exact: bool = False) -> dict:
    import rdflib
    from rdflib.compare import isomorphic
    iso = isomorphic if exact else same_graph
    t0 = time.perf_counter()
    folder = Path(folder)
    paths = rdf.record_paths(folder, d)
    man = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    ech, prov, labels = (rdf.load_yaml(paths[k]) for k in ("ech_yaml", "provenance_yaml", "labels_yaml"))
    parts, info = rdf.part_graphs(folder, d)
    gaps, _ = gp.manifest_gaps(man)        # rdf.part_graphs stops for a problem of the manifest keys
    res: dict = {"doc_id": d, "script": {"path": SCRIPT, "sha256": sha256(Path(__file__))}, "tools": rdf.linkml_versions(),
                 "conformance": gp.conformance(gaps), "i95_gaps": gaps}
    # C1 (a record with recorded gaps: addendum A, rule A2; else I95 without a change)
    rule = gp.gap_rule(ech, man, prov.get("not_mapped_records") or []) if gaps else None
    if cli:
        c1 = [gap_check(rule, paths["ech_yaml"].name) if rule else linkml_cli(I95, "Container", paths["ech_yaml"]),
              linkml_cli(PROFILE, "ExtractionRecord", paths["provenance_yaml"]),
              linkml_cli(rdf.LABEL_SCHEMA, "LabelRecord", paths["labels_yaml"])]
    else:
        c1 = [gap_check(rule, paths["ech_yaml"].name) if rule else linkml_check(I95, "Container", ech, paths["ech_yaml"].name),
              linkml_check(PROFILE, "ExtractionRecord", prov, paths["provenance_yaml"].name),
              linkml_check(LABEL_SCHEMA, "LabelRecord", labels, paths["labels_yaml"].name)]
    c1.append(linkml_check(LABEL_SCHEMA, "PdfLayout", info["layout"], "atom layout (in memory)"))
    res["C1_linkml"] = {"passed": all(x["valid"] for x in c1), "results": c1}
    if rule:
        res["C1_linkml"]["i95_gap_rule"] = rule
    # C2
    parsed, c2 = {}, []
    for key, fmt in (("gesamt_trig", "trig"), ("gesamt_rdfxml", "xml"), ("ech_ttl", "turtle"), ("ech_rdfxml", "xml")):
        try:
            parsed[key] = (rdflib.Dataset() if fmt == "trig" else rdflib.Graph()).parse(paths[key], format=fmt)
            c2.append({"file": paths[key].name, "parsed": True, "triples": len(parsed[key])})
        except Exception as e:  # noqa: BLE001  (each parse error is a finding)
            c2.append({"file": paths[key].name, "parsed": False, "error": str(e)[:300]})
    res["C2_parse"] = {"passed": all(x["parsed"] for x in c2), "results": c2}
    if not res["C2_parse"]["passed"]:
        return finish(folder, man, res, t0)
    ds = parsed["gesamt_trig"]
    named = {str(g.identifier): g for g in ds.graphs() if len(g)}
    record = info["record_iri"]
    trig = {name: named.get(f"{record}/{name}") for name in rdf.GRAPHS}
    union = rdflib.Graph()
    for g in named.values():
        for t in g:
            union.add(t)
    # C3
    c3 = {"union_equals_gesamt_rdfxml": iso(union, parsed["gesamt_rdfxml"]),
          "ech_ttl_equals_ech_rdfxml": iso(parsed["ech_ttl"], parsed["ech_rdfxml"]),
          "ech_ttl_equals_trig_graph": trig["ech-0295"] is not None and iso(parsed["ech_ttl"], trig["ech-0295"])}
    res["C3_isomorphism"] = {"passed": all(c3.values()), **c3,
                             "method": "rdflib.compare.isomorphic" if exact else "same_graph (canonical triples of "
                                       "blank-node forests, else rdflib.compare.isomorphic)"}
    # C4
    c4 = {name: trig[name] is not None and iso(trig[name], parts[name]) for name in rdf.GRAPHS}
    c4_extra = sorted(set(named) - {f"{record}/{n}" for n in rdf.GRAPHS})
    res["C4_parts"] = {"passed": all(c4.values()) and not c4_extra, "graphs": c4, "other_graphs": c4_extra,
                       "triples": {n: len(parts[n]) for n in rdf.GRAPHS}}
    # C5
    c5 = {"ech_yaml": leaf_coverage(ech, parts["ech-0295"], WRAPPER),
          "provenance_yaml": leaf_coverage(prov, parts["provenance"], PROFILE),
          "labels_yaml": leaf_coverage(labels, parts["labels"], LABEL_SCHEMA),
          "atom_layout": leaf_coverage(info["layout"], parts["atoms"], LABEL_SCHEMA)}
    res["C5_leaf_values"] = {"passed": not any(c5.values()),
                             "leaves": {"ech_yaml": sum(1 for _ in leaves(ech)), "provenance_yaml": sum(1 for _ in leaves(prov)),
                                        "labels_yaml": sum(1 for _ in leaves(labels)),
                                        "atom_layout": sum(1 for _ in leaves(info["layout"]))},
                             "missing": {k: v[:20] for k, v in c5.items()}}
    # C6
    no_scheme = sorted({str(x) for g in parts.values() for t in g for x in t
                        if isinstance(x, rdflib.URIRef) and not RX_SCHEME.match(str(x))})
    res["C6_iri_scheme"] = {"passed": not no_scheme, "iris_without_scheme": no_scheme[:20]}
    # C7, C8
    doc = json.loads((ROOT / man["inputs"]["docs"]["path"]).read_text(encoding="utf-8"))
    res["C7_C8_labels"] = label_checks(parts, doc)
    # C9
    res["C9_e19"] = e19_checks(d, ech, prov, labels, doc)
    # C10 (the parts: C4 compares them with the named graphs of the TriG file, and their blank-node names are stable).
    # C10 is information only (decision M5; addendum A, rule A3): an error of the SHACL tools does not stop the record.
    try:
        c10 = shacl_checks(parts)
    except Exception as e:  # noqa: BLE001  (each error of gen-shacl or pyshacl; the key passed does not use C10)
        c10 = {"status": "error", "error_type": type(e).__name__, "reason": f"{type(e).__name__}: {str(e)[:200]}"}
    res["C10_shacl"] = c10 | {"information_only": True}
    return finish(folder, man, res, t0)


def finish(folder: Path, man: dict, res: dict, t0: float) -> dict:
    """Writes validation.json and the key validation of the manifest. The key passed uses C1 to C9 only. C10
    (SHACL) is information: it does not decide the validity (decision M5; addendum A to the criteria, rule A3)."""
    keys = [k for k in res if k.startswith("C") and k != "C10_shacl"]
    shacl = res.get("C10_shacl") or {}
    res["passed"] = all(res[k]["passed"] for k in keys)
    res["shacl_information_only"] = True
    res["seconds"] = round(time.perf_counter() - t0, 3)
    p = folder / "validation.json"
    rdf.write_json(p, res)
    man["validation"] = {"passed": res["passed"], "conformance": res["conformance"],
                         "checks": {k: res[k]["passed"] for k in keys},
                         "shacl": shacl.get("status"), "shacl_passed": shacl.get("passed"),
                         "shacl_information_only": True, "file": rdf.rel(p), "sha256": sha256(p)}
    man["seconds"]["validate"] = res["seconds"]
    if "rdf" in man:
        man["seconds"]["rdf"] = man["rdf"]["seconds"]
    rdf.write_json(folder / "manifest.json", man)
    return res


def cmd_validate(args) -> int:
    out = Path(args.out).resolve()
    docs = [str(x) for x in args.doc] if args.doc else sorted(p.name for p in out.iterdir() if (p / "manifest.json").exists())
    ok = 0
    for d in docs:
        r = validate_record(out / d, d, args.cli, args.exact_isomorphism)
        ok += bool(r["passed"])
        checks = ", ".join(f"{k.split('_')[0]} {v.get('passed', v.get('status'))}" for k, v in r.items()
                           if k.startswith("C") and k != "C10_shacl")
        c10 = r.get("C10_shacl") or {}
        print(f"{d}: passed {r['passed']} ({checks}; information only: C10 {c10.get('status')}"
              f"{', conforms ' + str(c10.get('passed')) if c10.get('status') == 'run' else ''}), conformance "
              f"{r['conformance']}, {r['seconds']} s", flush=True)
    print(json.dumps({"documents": len(docs), "passed": ok}, indent=1))
    return 0 if ok == len(docs) else 2


def main() -> None:
    ap = argparse.ArgumentParser(description="checks of the gate GJ records")
    ap.add_argument("--out", required=True, help="folder of the writer (one subfolder for each document)")
    ap.add_argument("--doc", nargs="*")
    ap.add_argument("--cli", action="store_true", help="C1 with the command linkml-validate (uvx --offline)")
    ap.add_argument("--exact-isomorphism", action="store_true", help="C3 and C4 with rdflib.compare.isomorphic only")
    a = ap.parse_args()
    sys.exit(cmd_validate(a))


if __name__ == "__main__":
    main()
