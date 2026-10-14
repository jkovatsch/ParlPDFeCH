"""RDF step of the gate GJ converter: the files of one record as Turtle, RDF/XML and TriG with 4 named graphs.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream E,
for the main agent. Gate GJ (OPEN), status EXCEPTION (process rule 10), NOT RELEASED. Plan: chapters 5.2 item 8,
5.3 and 5.6 of `crisp-dm/00-cross-cutting/plan-full-conversion.md`.
Change of 13.10.2026 (stream G of wave 4, Claude Opus 5.5): chapter 2 item 7, the recorded I95 gaps of addendum A.

1 Task
  Input: the folder of one record that `src/m10_writer.py` wrote (`<doc>.ech.yaml`, `<doc>.provenance.yaml`,
  `<doc>.labels.yaml`, `manifest.json`), the block file that the manifest names (interface 2, normally
  `daten/gj/docs/<doc>.json`) and the atom file `daten/iso/atome/<doc>.json` (explicit path, no fallback of
  `m03_iso_paths`). Both must have the SHA-256 of the manifest.
  Output in the same folder:
    <doc>.gesamt.trig     TriG with 4 named graphs: <record>/ech-0295, <record>/provenance, <record>/atoms,
                          <record>/labels
    <doc>.gesamt.rdf.xml  RDF/XML of the union of the 4 graphs (RDF/XML has no named graphs)
    <doc>.ech.ttl         the eCH-0295 graph only (Turtle)
    <doc>.ech.rdf.xml     the eCH-0295 graph only (RDF/XML)
  The manifest gets the SHA-256 and the triple count of each file.

2 Conversion
  1. In process, with the pinned LinkML (linkml==1.11.1 from the uv cache, offline) and rdflib: the same
     route as `linkml-convert -t ttl` (PythonGenerator, yaml loader, rdflib dumper).
  2. The eCH graph uses the wrapper `src/m03_ech_export_schema.yaml` (it declares mcm). The provenance graph uses
     the profile `src/m06_ech_profil.yaml` 0.2.0. The label graph and the atom graph use the label schema
     `src/m10_label_schema.yaml` (classes LabelRecord and PdfLayout).
  3. The working folder of each conversion is src/, because the generators find an import relative to the
     working folder.
  4. A value of a slot with the range decimal goes into the graph as the decimal of its YAML text
     (for example 0.912), not as the binary expansion of a float.
  5. Each blank node gets a name from its content (parent node, predicate, subtree). The TriG file is the Turtle
     text of each named graph in a fixed order. So equal input gives equal TriG and Turtle text. The RDF/XML text
     of rdflib can change its order from one run to the next (the content stays the same, check C3 of
     src/m10_validate.py). A new RDF run removes the validation result from the manifest.
  6. The base IRI is a parameter (default https://data.parlpdfech.example/). It must be the base IRI that the
     writer used (manifest.json): the writer mints the IRIs of the YAML files.
  7. Recorded I95 gaps (addendum A to the criteria, rule A1; `src/m10_gaps.py`). The manifest key i95_gaps names
     the required slots of the affair for which the export gives no value (affair_type, affair_number). For such
     a record, the Python classes of the eCH graph come from a copy of the resolved schema in memory. In the copy,
     only the recorded gap slots of the class Affair are not required (gap_bundle). No schema file changes. The
     schema view of the RDF dumper does not change. The eCH graph has no triple for a gap slot. A record with no
     recorded gap uses the route of item 1 without a change. Each other absent required slot stops the step.

Usage (from the project folder; one command on one line):
  uv run --offline --no-project --python 3.12 --with linkml==1.11.1 python src/m10_rdf.py convert --out <dir>
      [--doc DOC ...] [--base IRI]
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import time
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_gaps as gp  # noqa: E402  (recorded I95 gaps, addendum A rule A1)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WRAPPER = SRC / "m03_ech_export_schema.yaml"
PROFILE = SRC / "m06_ech_profil.yaml"
LABEL_SCHEMA = SRC / "m10_label_schema.yaml"
ATOMS_DIR = ROOT / "daten/iso/atome"
DEFAULT_BASE = "https://data.parlpdfech.example/"
LINKML = "linkml==1.11.1"
SCRIPT = "src/m10_rdf.py"
GRAPHS = ("ech-0295", "provenance", "atoms", "labels")
PREFIXES = {"aff": "https://ch.paf.link/schema/affairs/", "mcm": "https://ld.ech.ch/schema/0292/meta-common/",
            "ppx": "https://schema.parlpdfech.example/profile/", "plb": "https://schema.parlpdfech.example/labels/",
            "prov": "http://www.w3.org/ns/prov#", "dcterms": "http://purl.org/dc/terms/", "schema": "http://schema.org/",
            "oa": "http://www.w3.org/ns/oa#", "skos": "http://www.w3.org/2004/02/skos/core#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "xsd": "http://www.w3.org/2001/XMLSchema#"}


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def check_base(base: str) -> str:
    if not re.fullmatch(r"https?://[^\s<>\"{}|\\^`]+/", base or ""):
        raise SystemExit(f"base IRI {base!r}: it must start with http:// or https:// and end with /")
    return base


@contextlib.contextmanager
def in_src():
    """The LinkML generators find an import relative to the working folder (plan chapter 5.6 item 2)."""
    old = os.getcwd()
    os.chdir(SRC)
    try:
        yield
    finally:
        os.chdir(old)


# ------------------------------------------------------------------ LinkML (in process)
@lru_cache(maxsize=None)
def bundle(schema: Path):
    """(SchemaView, Python module of the schema, names of the slots with the range decimal), once per process."""
    from linkml.generators.pythongen import PythonGenerator
    from linkml_runtime import SchemaView
    with in_src():
        sv = SchemaView(str(schema))
        module = PythonGenerator(str(schema)).compile_module()
        decimals = frozenset(s.name for s in sv.all_slots().values() if s.range == "decimal")
        sv.all_classes()     # resolve the imports now, inside the working folder src/
    return sv, module, decimals


@lru_cache(maxsize=None)
def gap_bundle(schema: Path, gaps: tuple[str, ...]):
    """bundle(schema) for a record with recorded gaps (addendum A, rule A1). The Python module comes from a copy of
    the resolved schema in memory, in which only the slots `gaps` of the class Affair are not required. The schema
    view and the decimal slots are the objects of bundle(schema). A module with another change stops the step."""
    from linkml.generators.pythongen import PythonGenerator
    from linkml_runtime.utils.compile_python import compile_python
    sv, _, decimals = bundle(schema)
    with in_src():
        strict_text = PythonGenerator(str(schema)).serialize()
        gen = PythonGenerator(str(schema))
        gp.relax_required(gen.schema, gaps)          # the resolved schema of this generator object only
        text = gen.serialize()
    bad = gp.module_change_problems(strict_text, text, gaps)
    if bad:
        raise SystemExit(f"{rel(schema)} with the gap slots {list(gaps)} not required: {bad[:5]}")
    return sv, compile_python(text), decimals


def as_decimals(x, names: frozenset, key: str | None = None):
    """Each float of a slot with the range decimal becomes the decimal of its shortest text form."""
    if isinstance(x, dict):
        return {k: as_decimals(v, names, k) for k, v in x.items()}
    if isinstance(x, list):
        return [as_decimals(v, names, key) for v in x]
    if key in names and isinstance(x, float):
        return Decimal(repr(x))
    return x


def to_graph(schema: Path, cls: str, data: dict, gaps: tuple[str, ...] = ()):
    """The RDF graph of one LinkML instance (the route of linkml-convert -t ttl). `gaps` are the recorded gap slots
    of the affair (addendum A): the Python classes then come from gap_bundle. Without a gap the route is bundle."""
    from linkml_runtime.dumpers import rdflib_dumper
    from linkml_runtime.loaders import yaml_loader
    sv, module, decimals = gap_bundle(schema, gaps) if gaps else bundle(schema)
    with in_src():
        obj = yaml_loader.load_any(source=as_decimals(data, decimals), target_class=module.__dict__[cls])
        g = rdflib_dumper.as_rdf_graph(obj, schemaview=sv)
    bind(g)
    return stable_bnodes(g)


@lru_cache(maxsize=None)
def slot_iris(schema: Path) -> dict[str, str]:
    """{slot name: full IRI of the slot} of a schema and its imports (for the predicates of the label graph)."""
    sv, _, _ = bundle(schema)
    out = {}
    with in_src():
        for name in sv.all_slots():
            try:
                out[name] = sv.get_uri(name, expand=True)
            except (AttributeError, KeyError, ValueError):
                continue
    return out


def stable_bnodes(g):
    """A copy of g whose blank nodes have names from their content: the SHA-256 of the parent node, the predicate
    and the sorted subtree (blank-node forests only; else g itself). Equal input gives equal TriG, Turtle and
    RDF/XML text, apart from the run time values."""
    import rdflib
    inc: dict = {}
    for _, _, o in g:
        if isinstance(o, rdflib.BNode):
            inc[o] = inc.get(o, 0) + 1
    if any(n > 1 for n in inc.values()):
        return g
    memo: dict = {}

    def key(t) -> str:
        if isinstance(t, rdflib.Literal):
            return repr(("L", str(t), str(t.datatype or ""), t.language or ""))
        return repr(("U", str(t)))

    def h(b, depth: int = 0) -> str:
        if depth > 50:
            raise RecursionError("blank-node cycle")
        if b not in memo:
            parts = sorted(repr((key(p_), h(o, depth + 1) if isinstance(o, rdflib.BNode) else key(o)))
                           for p_, o in g.predicate_objects(b))
            memo[b] = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
        return memo[b]

    try:
        for b in inc:
            h(b)
    except RecursionError:
        return g
    name: dict = {}

    def assign(parent: str, children: list) -> None:
        seen: dict = {}
        for p_, o in sorted(children, key=lambda x: (str(x[0]), memo[x[1]])):
            k = (str(p_), memo[o])
            seen[k] = seen.get(k, 0) + 1
            name[o] = "b" + hashlib.sha256(f"{parent}|{k[0]}|{k[1]}|{seen[k]}".encode("utf-8")).hexdigest()[:32]
            assign(name[o], [(p2, o2) for p2, o2 in g.predicate_objects(o) if isinstance(o2, rdflib.BNode)])

    roots: dict = {}
    for s_, p_, o in g:
        if isinstance(o, rdflib.BNode) and not isinstance(s_, rdflib.BNode):
            roots.setdefault(str(s_), []).append((p_, o))
    for s_ in sorted(roots):
        assign(s_, roots[s_])
    if len(name) != len(inc):
        return g
    out = rdflib.Graph()
    for s_, p_, o in g:
        out.add((rdflib.BNode(name[s_]) if s_ in name else s_, p_, rdflib.BNode(name[o]) if o in name else o))
    bind(out)
    return out


def trig_text(graphs: dict, record_iri: str) -> str | None:
    """TriG text of the named graphs in the fixed order of GRAPHS, each graph as the Turtle text of rdflib (that
    text does not depend on the hash seed of the process). None if two graphs bind one prefix to two IRIs."""
    prefixes: dict[str, str] = {}
    bodies = []
    for name in GRAPHS:
        body = []
        for line in graphs[name].serialize(format="turtle").splitlines():
            m = re.match(r"@prefix ([A-Za-z][\w.-]*|): <([^>]*)> \.$", line)
            if m:
                if prefixes.setdefault(m.group(1), m.group(2)) != m.group(2):
                    return None
            elif line.startswith("@"):
                return None
            else:
                body.append(line)
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        # no indentation: a long literal of the Turtle text can span lines
        bodies.append(f"<{record_iri}/{name}> {{\n" + "\n".join(body) + "\n}\n")
    head = "".join(f"@prefix {k}: <{v}> .\n" for k, v in sorted(prefixes.items()))
    return head + "\n" + "\n".join(bodies)


def bind(g) -> None:
    for k, v in PREFIXES.items():
        g.bind(k, v, override=True, replace=True)


def linkml_versions() -> dict[str, str]:
    from importlib.metadata import version
    return {p: version(p) for p in ("linkml", "linkml-runtime", "rdflib")}


# ------------------------------------------------------------------ atom graph
def explicit_atoms(d: str) -> Path:
    p = ATOMS_DIR / f"{d}.json"
    if not p.exists():
        raise SystemExit(f"{d}: no atom file at the explicit path {rel(p)} (no fallback of m03_iso_paths)")
    return p


def layout_record(doc: dict, atoms_file: dict, record_iri: str, source_iri: str) -> dict:
    """The PdfLayout instance of the label schema: each Docling block of the block file (interface 2) with its
    atoms in reading order. The atoms come from the atom file; the block file gives the order and the ranges."""
    by_id = {a["id"]: a for a in atoms_file["atome"]}
    blocks = []
    for n, b in enumerate(doc["blocks"], 1):
        atoms = []
        for aid in b["atoms"]:
            a = by_id[aid]
            x = {"global_uri": f"{record_iri}/atom/{aid}", "atom_id": aid, "page_number": a["seite"]}
            box = a.get("zeilenrahmen") or a.get("rahmen")
            if box:
                x["bbox"] = {"bbox_left": box[0], "bbox_top": box[1], "bbox_right": box[2], "bbox_bottom": box[3]}
            x |= {"char_start": a["zeichen"][0], "char_end": a["zeichen"][1],
                  "from_ocr": any("OCR" in h for h in (a.get("hinweise") or [])), "docling_label": a.get("label") or ""}
            if a.get("text"):
                x["atom_text"] = a["text"]
            if a.get("zeilenrahmen_quelle"):
                x["line_box_source"] = a["zeilenrahmen_quelle"]
            atoms.append(x)
        blocks.append({"global_uri": f"{record_iri}/block/{b['block']}", "block_id": b["block"], "block_position": n,
                       "page_number": b["page"], "docling_label": b.get("docling_label") or "",
                       "char_start": b["char_start"], "char_end": b["char_end"], "block_atoms": atoms})
    return {"global_uri": f"{record_iri}/layout", "describes_record": record_iri, "source_document": source_iri,
            "atom_version": f"{atoms_file.get('version', '')} {atoms_file.get('erzeugt_utc', '')}".strip(),
            "layout_blocks": blocks}


# ------------------------------------------------------------------ one record
def load_yaml(p: Path) -> dict:
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def record_paths(folder: Path, d: str) -> dict[str, Path]:
    return {"ech_yaml": folder / f"{d}.ech.yaml", "provenance_yaml": folder / f"{d}.provenance.yaml",
            "labels_yaml": folder / f"{d}.labels.yaml", "gesamt_trig": folder / f"{d}.gesamt.trig",
            "gesamt_rdfxml": folder / f"{d}.gesamt.rdf.xml", "ech_ttl": folder / f"{d}.ech.ttl",
            "ech_rdfxml": folder / f"{d}.ech.rdf.xml", "manifest": folder / "manifest.json"}


def part_graphs(folder: Path, d: str) -> tuple[dict, dict]:
    """The 4 graphs of the record from its YAML files, the block file of the manifest and the atom file."""
    paths = record_paths(folder, d)
    man = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    labels = load_yaml(paths["labels_yaml"])
    record_iri = man["record_iri"]
    if labels["describes_record"] != record_iri:
        raise SystemExit(f"{d}: the label file describes {labels['describes_record']}, the manifest {record_iri}")
    doc_path = Path(man["inputs"]["docs"]["path"])
    doc_path = doc_path if doc_path.is_absolute() else ROOT / doc_path
    if sha256(doc_path) != man["inputs"]["docs"]["sha256"]:
        raise SystemExit(f"{d}: the block file differs from the file that the writer read")
    atoms_p = explicit_atoms(d)
    if sha256(atoms_p) != man["inputs"]["atoms"]["sha256"]:
        raise SystemExit(f"{d}: the atom file differs from the file that the writer read")
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    layout = layout_record(doc, json.loads(atoms_p.read_text(encoding="utf-8")), record_iri, labels["source_document"])
    ech = load_yaml(paths["ech_yaml"])
    gaps = recorded_gap_slots(d, man, ech)
    graphs = {"ech-0295": to_graph(WRAPPER, "Container", ech, gaps),
              "provenance": to_graph(PROFILE, "ExtractionRecord", load_yaml(paths["provenance_yaml"])),
              "atoms": to_graph(LABEL_SCHEMA, "PdfLayout", layout),
              "labels": to_graph(LABEL_SCHEMA, "LabelRecord", labels)}
    check_gap_graph(d, graphs["ech-0295"], gaps)
    return graphs, {"manifest": man, "layout": layout, "record_iri": record_iri, "i95_gaps": list(gaps)}


def recorded_gap_slots(d: str, man: dict, ech: dict) -> tuple[str, ...]:
    """The recorded gap slots of the manifest (addendum A, rule A1). A problem of the manifest keys stops the step.
    A gap slot with a value in the instance stops the step too. No recorded gap gives the empty tuple."""
    try:
        gaps = gp.gap_slots(man)
    except ValueError as e:
        raise SystemExit(f"{d}: {e}") from None
    bad = gp.instance_gap_problems(ech, gaps) if gaps else []
    if bad:
        raise SystemExit(f"{d}: {'; '.join(bad)}")
    return gaps


def check_gap_graph(d: str, g, gaps: tuple[str, ...]) -> None:
    """The eCH graph of a record with recorded gaps has no triple with the predicate of a gap slot."""
    import rdflib
    iris = slot_iris(WRAPPER) if gaps else {}
    for slot in gaps:
        if slot not in iris or any(g.triples((None, rdflib.URIRef(iris[slot]), None))):
            raise SystemExit(f"{d}: the eCH graph has a triple for the gap slot {slot}, or the slot has no IRI")


def convert_record(folder: Path, d: str, base: str | None = None) -> dict:
    """Writes the 4 RDF files of one record and adds them to its manifest."""
    import rdflib
    t0 = time.perf_counter()
    folder = Path(folder)
    paths = record_paths(folder, d)
    graphs, info = part_graphs(folder, d)
    man, record_iri = info["manifest"], info["record_iri"]
    if base is not None and check_base(base) != man["base_iri"]:
        raise SystemExit(f"{d}: base IRI {base} differs from the base IRI of the writer {man['base_iri']}")
    ds = rdflib.Dataset()
    bind(ds)
    union = rdflib.Graph()
    bind(union)
    for name in GRAPHS:
        ng = ds.graph(rdflib.URIRef(f"{record_iri}/{name}"))
        for t in graphs[name]:
            ng.add(t)
            union.add(t)
    text = trig_text(graphs, record_iri)
    if text is None:
        ds.serialize(paths["gesamt_trig"], format="trig")
    else:
        paths["gesamt_trig"].write_text(text, encoding="utf-8")
    union.serialize(paths["gesamt_rdfxml"], format="pretty-xml")
    graphs["ech-0295"].serialize(paths["ech_ttl"], format="turtle")
    graphs["ech-0295"].serialize(paths["ech_rdfxml"], format="pretty-xml")
    out = {k: {"path": rel(paths[k]), "sha256": sha256(paths[k]), "bytes": paths[k].stat().st_size}
           for k in ("gesamt_trig", "gesamt_rdfxml", "ech_ttl", "ech_rdfxml")}
    result = {"script": {"path": SCRIPT, "sha256": sha256(Path(__file__))}, "tools": linkml_versions(),
              "schemas": {rel(s): sha256(s) for s in (WRAPPER, PROFILE, LABEL_SCHEMA)},
              "i95_gap_slots_not_required": info["i95_gaps"],
              "named_graphs": {name: f"{record_iri}/{name}" for name in GRAPHS},
              "triples": {name: len(graphs[name]) for name in GRAPHS} | {"union": len(union)},
              "files": out, "seconds": round(time.perf_counter() - t0, 3)}
    man["rdf"] = result
    man["outputs"] |= out
    man.pop("validation", None)            # new RDF files: an earlier validation result does not apply
    man["seconds"].pop("validate", None)
    write_json(paths["manifest"], man)
    return result


def cmd_convert(args) -> int:
    out = Path(args.out).resolve()
    docs = [str(x) for x in args.doc] if args.doc else sorted(p.name for p in out.iterdir() if (p / "manifest.json").exists())
    rows = {}
    for d in docs:
        r = convert_record(out / d, d, args.base)
        rows[d] = {"triples": r["triples"], "seconds": r["seconds"]}
        print(f"{d}: {r['triples']['union']} triples ({', '.join(f'{k} {v}' for k, v in r['triples'].items() if k != 'union')}), "
              f"{r['seconds']} s", flush=True)
    print(json.dumps({"documents": len(rows)}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="RDF files of the gate GJ records (TriG with 4 named graphs, RDF/XML, Turtle)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("convert")
    p.add_argument("--out", required=True, help="folder of the writer (one subfolder for each document)")
    p.add_argument("--doc", nargs="*")
    p.add_argument("--base", default=None, help=f"base IRI; must be the base IRI of the writer (default: the manifest; "
                                                f"the writer default is {DEFAULT_BASE})")
    a = ap.parse_args()
    sys.exit({"convert": cmd_convert}[a.cmd](a))


if __name__ == "__main__":
    main()
