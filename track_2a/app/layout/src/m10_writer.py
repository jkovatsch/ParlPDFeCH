"""Writer of the gate GJ converter: eCH-0295 instance, provenance side file and label file of one PDF document.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream E,
for the main agent. Phase 6 (deployment), gate GJ (OPEN). Status: EXCEPTION (process rule 10), NOT RELEASED.
Plan: `crisp-dm/00-cross-cutting/plan-full-conversion.md`, chapters 4 item 8, 5.2 item 7, 5.3 and 5.6.
Change of 13.10.2026 (stream G of wave 4, Claude Opus 5.5): item 6, the recorded I95 gaps of addendum A.

1 Inputs for one document
  - The block file `daten/gj/docs/<doc>.json` (interface 2): the Docling blocks in reading order with page,
    Docling label, text, atom ids and character span.
  - The decisions file `daten/gj/decisions/<doc>.json` (interface 7): the document option D1, the option of each
    block with its probabilities, the switch boundaries and the final check R2.
  - The export record of the document (OpenParlData, decision D4) in the structure of
    `src/m06_converter.py export`. The writer reads a stored record (--export) or makes it with the imported
    function `m06_converter.build_export_records` (--build-export).
  - The calibration records (--calibrations, JSON): one record for each calibration id of the decisions file.
  - The atom file and the Docling file at the explicit paths `daten/iso/atome/<doc>.json` and
    `daten/iso/docling/<doc>.json`. The writer never uses a fallback of `m03_iso_paths` (process rule 6).

2 Outputs for one document (folder <out>/<doc>/)
  - <doc>.ech.yaml: the I95 Container instance. The metadata values come from the export record through the
    imported functions of `src/m06_converter.py` and `src/m06_ech_ausgabe.py` (not changed). Each author block
    is one TextBlock with text_type and the verbatim text of its atoms.
  - <doc>.provenance.yaml: the provenance side file (profile 0.2.0, root class ExtractionRecord).
  - <doc>.labels.yaml: the label file (`src/m10_label_schema.yaml` 0.1.0, class LabelRecord).
  - manifest.json: SHA-256 of all inputs and outputs, mode, calibration ids, status EXCEPTION, run time, and the
    keys i95_gaps and conformance (item 6).
  With --rdf: the RDF files of `src/m10_rdf.py`. With --validate: the checks of `src/m10_validate.py`.

3 Author blocks (plan chapter 4 item 8)
  1. An author block is a maximal run of blocks with the same option. The options are submitted, reasoning,
     response and recommendation.
  2. A block with the option none or title in a run does not split the run, and its text is not in the TextBlock.
     A title block goes to the label graph only.
  3. Runs with submitted or reasoning go to Submission.texts. Runs with response or recommendation go to
     ResponseStep.texts. The order is the reading order.
  4. The text of a TextBlock is the wording of the atoms of the blocks of the run, without the atoms with a
     fixed answer (furniture and pictures, E20 7.4.7), in the form of `m03_gold_record.richtext` (G19, without
     G20a), as `m06_converter.block_text` makes it. Check E19 (`m06_converter.e19_problems`) applies.

4 Probabilities and value status
  1. Each label of a rule, of an Apertus head or of a code step has the probability of its option, clipped to
     the interval from 0.005 to 0.995 and rounded to 4 decimals, and the IRI of its calibration record.
  2. Value status: certain if the probability is at the threshold a of the calibration record or above, else
     unsure. A calibration record without a threshold gives unsure.
  3. Final check R2 (plan chapter 3.2 item 6): if R2 and the block path do not agree on the response of the
     executive, the label D1 and the labels of the blocks of the Response family are unsure.
  4. Export values, constants and copies have no probability (plan chapter 9 item 17).

5 Process rule 6
  The writer refuses a document that the split guard `src/m10_guard.py` refuses (it allows dev, validation and
  group 7), and a document without the explicit development files of item 1. If `daten/gj/sets.json` exists,
  the document must be in one of its sets, or the run record `daten/gj/docs_build.json` must list its block file
  (set name bulk). The console shows only document ids, counts and SHA-256 values.

6 Recorded I95 gaps (addendum A to the criteria, rule A1; functions in `src/m10_gaps.py`)
  1. I95 requires affair_type and affair_number of an affair. If the export gives no value, the imported
     `m06_converter.affair_part` writes no slot and one NotMappedRecord. The writer invents no value.
  2. manifest.json names each gap: "i95_gaps" is a list of {"slot": "affair_type" | "affair_number", "cause":
     <fixed text>, "local_value": <local type name of the export> | null}. The list is empty for a record without
     a gap. "conformance" is "i95" for an empty list, else "i95_with_recorded_gaps".
  3. The permitted gap slots are affair_type and affair_number. Each other required I95 slot without a value, and
     a gap slot without the NotMappedRecord of the converter, is a problem: the key check_passed is false.
  4. The rule adds only the two manifest keys. The instance, the side file and the label file do not change.

Usage (from the project folder; one command on one line):
  uv run --offline --no-project --python 3.12 --with linkml==1.11.1 python src/m10_writer.py write --out <dir>
      (--export <dir> | --build-export) --calibrations <file> [--docs daten/gj/docs] [--decisions daten/gj/decisions]
      [--base https://data.parlpdfech.example/] [--rdf] [--validate] DOC [DOC ...]
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_record as gr  # noqa: E402  (signatures of E19; not changed)
import m03_iso_v4 as v4  # noqa: E402  (fixed answers; not changed)
import m06_converter as mc  # noqa: E402  (export record, wording, E19, affair part; not changed)
import m06_ech_ausgabe as ea  # noqa: E402  (V values, metadata checks, YAML writer; not changed)
import m10_docs as docs_text  # noqa: E402  (document text and spans of interface 2, stream B)
import m10_gaps as gp  # noqa: E402  (recorded I95 gaps, addendum A rule A1)
import m10_guard as guard  # noqa: E402  (split guard of process rule 6, stream B)
from m03_iso_paths import iso_path  # noqa: E402  (only to verify that it gives the explicit path)

V = ea.V
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPT = "src/m10_writer.py"
VERSION = "gj-writer-1"
DOCS_DIR = ROOT / "daten/gj/docs"
DECISIONS_DIR = ROOT / "daten/gj/decisions"
SETS_FILE = ROOT / "daten/gj/sets.json"
DOCS_BUILD = ROOT / "daten/gj/docs_build.json"
ATOMS_DIR = ROOT / "daten/iso/atome"
DOCLING_DIR = ROOT / "daten/iso/docling"
LABEL_SCHEMA = SRC / "m10_label_schema.yaml"
WRAPPER = SRC / "m03_ech_export_schema.yaml"
I95 = mc.I95
PROFILE = mc.PROFILE
DEFAULT_BASE = "https://data.parlpdfech.example/"
OPTIONS = ("submitted", "reasoning", "response", "recommendation", "title", "none")
TEXT_OPTIONS = OPTIONS[:4]
FAMILY = {"submitted": "submission", "reasoning": "submission", "response": "response", "recommendation": "response"}
D1_OPTIONS = {"A": "submitted text only (with or without reasoning)",
              "B": "response of the executive only (with or without recommendation)",
              "C": "both", "D": "none of these text parts"}
SOURCE = {"rule": "rule", "apertus_head": "apertus_head", "code": "code_step"}   # interface 7 -> LabelSourceEnum
SPLITS = ("dev", "validation", "group7", "dev_sample")
P_MIN, P_MAX, P_DIGITS = 0.005, 0.995, 4
PROCESS_STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
SYNTHETIC = "synthetic_test_value"
CAL_FIELDS = {"calibration_method", "calibrated_kind", "fit_set_file", "fit_set_digest", "fit_n", "reference_source",
              "in_sample", "target_status", "certain_threshold", "calibration_parameters", "measure_sets",
              "calibration_note"}
PLB = "https://schema.parlpdfech.example/labels/"
AFF = "https://ch.paf.link/schema/affairs/"
RX_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def clip(p: float) -> float:
    """Plan chapter 2.1 item 4: all probabilities are clipped to [0.005, 0.995]."""
    return round(min(max(float(p), P_MIN), P_MAX), P_DIGITS)


def check_base(base: str) -> str:
    if not re.fullmatch(r"https?://[^\s<>\"{}|\\^`]+/", base or ""):
        raise SystemExit(f"base IRI {base!r}: it must start with http:// or https:// and end with /")
    return base


# ------------------------------------------------------------------ guard (process rule 6) and input checks
def guard_docs(ids: list[str]) -> dict:
    """src/m10_guard.py for a list of documents (one pass over the export table; later calls use its cache)."""
    try:
        return guard.assert_allowed([str(d) for d in ids])
    except guard.GuardRefusal as e:
        raise SystemExit(f"refused by src/m10_guard.py: {e}") from None


def explicit_paths(d: str) -> dict[str, Path]:
    """The split guard (src/m10_guard.py: dev, validation and group 7 only) and the explicit development paths of
    the atom file and the Docling file. No fallback of m03_iso_paths."""
    if not re.fullmatch(r"\d+", d):
        raise SystemExit(f"{d!r}: a document id has digits only")
    paths = {"atoms": ATOMS_DIR / f"{d}.json", "docling": DOCLING_DIR / f"{d}.json"}
    for kind, p in paths.items():
        if not p.exists():
            raise SystemExit(f"{d}: no {kind} file at the explicit path {rel(p)}: refused (process rule 6)")
    guard_docs([d])
    if iso_path("atome", d).resolve() != paths["atoms"].resolve() or \
            iso_path("docling", d).resolve() != paths["docling"].resolve():
        raise SystemExit(f"{d}: m03_iso_paths gives another file than the explicit path: refused")
    return paths


def set_of(d: str) -> str | None:
    """The set of the document in daten/gj/sets.json (interface 3), or None if the file does not exist.
    Interface 3 lists only the 294 AI-reference documents. A document outside these sets gets the set name bulk if
    the run record daten/gj/docs_build.json lists its block file (the guard of src/m10_docs.py allowed it). The
    full run (plan chapter 9 item 21) writes these documents too."""
    if not SETS_FILE.exists():
        return None
    sets = read_json(SETS_FILE)
    for name in ("dev", "validation", "group7", "pilot_overrides", "dev_out_of_design"):
        if d in {str(x) for x in sets.get(name) or []}:
            return name
    if f"daten/gj/docs/{d}.json" in built_doc_files():
        return "bulk"
    raise SystemExit(f"{d}: not in a set of {rel(SETS_FILE)} and not in {rel(DOCS_BUILD)}: refused")


_BUILT: set[str] = set()


def built_doc_files() -> set[str]:
    """The block files of the run record of src/m10_docs.py (read one time)."""
    if not _BUILT and DOCS_BUILD.exists():
        _BUILT.update((read_json(DOCS_BUILD).get("outputs") or {}).keys())
    return _BUILT


def check_doc_file(d: str, doc: dict, atoms: list[dict]) -> list[str]:
    """Interface 2: structure of the block file and agreement with the atom file."""
    bad = []
    if str(doc.get("doc_id")) != d:
        bad.append("the block file is for another document")
    if doc.get("split") not in SPLITS:
        bad.append(f"split {doc.get('split')!r} is not one of {SPLITS}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(doc.get("pdf_sha256") or "")):
        bad.append("pdf_sha256 is not a SHA-256")
    by_id = {a["id"]: a for a in atoms}
    seen, ids = set(), []
    for b in doc.get("blocks") or []:
        bid = b.get("block")
        if not re.fullmatch(r"B\d+", str(bid)) or bid in seen:
            bad.append(f"block id {bid!r} is not B<n> or is not unique")
            continue
        seen.add(bid)
        if not isinstance(b.get("page"), int) or b["page"] < 1:
            bad.append(f"{bid}: page is not a positive integer")
        cs, ce = b.get("char_start"), b.get("char_end")
        if not (isinstance(cs, int) and isinstance(ce, int) and 0 <= cs <= ce):
            bad.append(f"{bid}: char_start and char_end are not a range")
        for a in b.get("atoms") or []:
            if a not in by_id:
                bad.append(f"{bid}: atom {a} is not in the atom file")
            elif by_id[a]["block"] != bid:
                bad.append(f"{bid}: atom {a} is in block {by_id[a]['block']} of the atom file")
            ids.append(a)
    if not doc.get("blocks"):
        bad.append("the block file has no block")
    else:
        try:
            docs_text.check_doc(doc)        # the spans give the block texts in m10_docs.doc_text (interface 2)
        except (ValueError, KeyError, TypeError) as e:
            bad.append(f"interface 2 spans: {e}")
    if ids != [a["id"] for a in atoms]:
        bad.append("the atoms of the blocks are not the atoms of the atom file in reading order")
    for path, digest in (doc.get("source_files") or {}).items():
        p = ROOT / path
        if path.startswith("daten/iso/") and p.exists() and sha256(p) != digest:   # only files of daten/iso are read
            bad.append(f"source file {path} has another SHA-256")
    return bad


def check_probs(where: str, probs, allowed) -> list[str]:
    if not isinstance(probs, dict) or not probs:
        return [f"{where}: probs is not a non-empty object"]
    bad = [f"{where}: option {k!r} is not permitted" for k in probs if k not in allowed]
    bad += [f"{where}: probability of {k} is not in [0, 1]" for k, v in probs.items()
            if not isinstance(v, (int, float)) or not 0 <= v <= 1]
    return bad


def check_decisions(d: str, doc: dict, dec: dict, cals: dict) -> list[str]:
    """Interface 7: structure of the decisions file and agreement with the block file."""
    bad = []
    if str(dec.get("doc_id")) != d:
        bad.append("the decisions file is for another document")
    if dec.get("mode") not in ("floor", "cascade"):
        bad.append(f"mode {dec.get('mode')!r} is not floor or cascade")
    used = []
    d1 = (dec.get("document") or {}).get("d1") or {}
    if d1.get("option") not in D1_OPTIONS:
        bad.append("document.d1.option is not A, B, C or D")
    bad += check_probs("d1", d1.get("probs"), D1_OPTIONS)
    if d1.get("option") in D1_OPTIONS and d1.get("option") not in (d1.get("probs") or {}):
        bad.append("d1: no probability for the chosen option")
    if d1.get("source") not in SOURCE:
        bad.append(f"d1: source {d1.get('source')!r} is not rule, apertus_head or code")
    used.append(d1.get("calibration"))
    blocks = dec.get("blocks") or []
    if [b.get("block") for b in blocks] != [b["block"] for b in doc["blocks"]]:
        bad.append("the blocks of the decisions file are not the blocks of the block file in reading order")
    for b in blocks:
        w = f"block {b.get('block')}"
        if b.get("option") not in OPTIONS:
            bad.append(f"{w}: option {b.get('option')!r} is not permitted")
        bad += check_probs(w, b.get("probs"), OPTIONS)
        if b.get("option") in OPTIONS and b.get("option") not in (b.get("probs") or {}):
            bad.append(f"{w}: no probability for the chosen option")
        if b.get("source") not in SOURCE:
            bad.append(f"{w}: source {b.get('source')!r} is not rule, apertus_head or code")
        used.append(b.get("calibration"))
    ids = [b["block"] for b in doc["blocks"]]
    for x in dec.get("boundaries") or []:
        if x.get("after_block") not in ids[:-1] or x.get("kind") != "switch":
            bad.append(f"boundary {x.get('after_block')!r}: not a block before the last block, or kind is not switch")
        if not isinstance(x.get("p"), (int, float)) or not 0 <= x["p"] <= 1:
            bad.append(f"boundary {x.get('after_block')!r}: p is not in [0, 1]")
        used.append(x.get("calibration"))
    if len({x.get("after_block") for x in dec.get("boundaries") or []}) != len(dec.get("boundaries") or []):
        bad.append("two boundaries after the same block")
    r2 = dec.get("r2")
    if r2 is not None:
        if not isinstance(r2.get("p"), (int, float)) or not 0 <= r2["p"] <= 1:
            bad.append("r2: p is not in [0, 1]")
        used.append(r2.get("calibration"))
    for c in sorted({str(c) for c in used}):
        if c not in cals:
            bad.append(f"calibration id {c!r} has no calibration record")
    return bad


def load_calibrations(p: Path | None) -> tuple[dict, dict | None]:
    """The calibration records: {"calibrations": {id: {slots of class Calibration}}} (label schema)."""
    if p is None:
        return {}, None
    raw = read_json(p)
    out = {}
    for cid, c in (raw.get("calibrations") or {}).items():
        if not RX_ID.match(cid):
            raise SystemExit(f"calibration id {cid!r}: only letters, digits, '.', '_' and '-' are permitted")
        extra = set(c) - CAL_FIELDS
        if extra:
            raise SystemExit(f"calibration {cid}: unknown fields {sorted(extra)}")
        for k in ("calibration_method", "target_status"):
            if k not in c:
                raise SystemExit(f"calibration {cid}: field {k} is required")
        out[cid] = c
    return out, {"path": rel(p), "sha256": sha256(p)}


# ------------------------------------------------------------------ runs and switch points
def author_runs(options: list[str]) -> list[tuple[str, list[int]]]:
    """Plan chapter 4 item 8: maximal runs of one text option; blocks with none or title do not split a run."""
    runs: list[tuple[str, list[int]]] = []
    for i, o in enumerate(options):
        if o not in TEXT_OPTIONS:
            continue
        if runs and runs[-1][0] == o:
            runs[-1][1].append(i)
        else:
            runs.append((o, [i]))
    return runs


def path_switches(options: list[str]) -> list[tuple[int, int]]:
    """The switch points of the block path: (index of the last text block of one family, index of the first
    text block of the other family)."""
    out, last = [], None
    for i, o in enumerate(options):
        if o not in TEXT_OPTIONS:
            continue
        if last is not None and FAMILY[options[last]] != FAMILY[o]:
            out.append((last, i))
        last = i
    return out


@contextlib.contextmanager
def minted_namespace(base: str):
    """The writer mints its IRIs below <base>gj/. The imported functions read the namespace from the module
    globals m06_converter.NS and m06_ech_ausgabe.PPD, so the writer sets them for the time of one document."""
    old = mc.NS, ea.PPD
    mc.NS, ea.PPD = f"{base}gj/", base
    try:
        yield
    finally:
        mc.NS, ea.PPD = old


def fix_minted_rules(node, base: str) -> None:
    """The rule text of the minted step IRIs of m06_converter.affair_part names the namespace of the MVP."""
    if isinstance(node, V):
        if node.herkunft.get("derivation") == "identifier_minted" and "/converter/l9/" in node.herkunft.get("rule", ""):
            node.herkunft["rule"] = (f"{base}gj/affair-{{id}}/step/{{step}}/doc-{{doc_id}} (deterministic; base IRI of "
                                     f"the run, {SCRIPT})")
    elif isinstance(node, dict):
        for v in node.values():
            fix_minted_rules(v, base)
    elif isinstance(node, list):
        for v in node:
            fix_minted_rules(v, base)


# ------------------------------------------------------------------ one document
def language(d: str, doc: dict, exp: dict) -> tuple[str | None, dict, list[str]]:
    """The language of the TextBlocks: the export field docs.language (copied_from_metadata), else the language of
    the block file (interface 2; detected_by_rule). The writer does not read the document lists of
    m06_converter.document_language, because they include the lists of the test documents."""
    edoc, abruf, ddatei = exp["doc"], exp["export_retrieved_utc"], exp["doc_export_file"]
    notes = []
    if edoc.get("language") in ea.SPRACHEN:
        if doc.get("language") not in (None, edoc["language"]):
            notes.append(f"the language of the block file ({doc.get('language')}) differs from the export field "
                         f"docs.language ({edoc['language']}); the writer uses the export field")
        return edoc["language"], {"derivation": "copied_from_metadata", "metadata_evidence": [
            ea.beleg_meta(ddatei, "doc", edoc["id"], "language", edoc["language"], abruf)]}, notes
    if doc.get("language") in ea.SPRACHEN:
        return doc["language"], {"derivation": "detected_by_rule", "_augenschein": doc["language"],
                                 "rule": f"the export has no language (docs.language); language of the block file "
                                         f"daten/gj/docs/{d}.json (interface 2 of gate GJ)"}, notes
    return None, {}, notes


def label_threshold(cals: dict, cid: str) -> float | None:
    t = cals[cid].get("certain_threshold")
    return None if t is None else float(t)


def build(d: str, doc: dict, dec: dict, exp: dict, cals: dict, base: str, files: dict) -> dict:
    """The instance (with V values), the side file, the label file and the counts of one document."""
    atoms_list = read_json(files["atoms"]["abs"])["atome"]
    by_id = {a["id"]: a for a in atoms_list}
    fixed = v4.fixed_answers(d)
    liste = [dict(a, ocr=mc.from_ocr(a)) for a in atoms_list]
    edoc, aff = exp["doc"], exp.get("affair")
    abruf, ddatei = exp["export_retrieved_utc"], exp["doc_export_file"]
    aid = aff["id"] if aff else None
    ns = f"{base}gj/"
    record = f"{ns}record/doc-{d}"
    container_iri = f"{ns}i95/affair-{aid}/doc-{d}" if aff else f"{ns}i95/doc-{d}"
    doc_iri = f"{ea.OPD}docs/{d}"
    run_iri = f"{record}/run"
    blocks = doc["blocks"]
    decided = dec["blocks"]
    options = [b["option"] for b in decided]
    nicht: list[dict] = []
    problems: list[str] = []

    lang, lang_h, notes = language(d, doc, exp)
    url_raw = edoc.get("url_oparl")
    url_ev = [ea.beleg_meta(ddatei, "doc", edoc["id"], "url_oparl", url_raw, abruf)]

    def url_v():
        if not url_raw:
            return None
        u = ea.as_uri(url_raw)
        if u == url_raw:
            return V(u, {"derivation": "copied_from_metadata", "metadata_evidence": url_ev})
        return V(u, {"derivation": "normalized_from_metadata", "metadata_evidence": url_ev, "_norm": "uri",
                     "rule": "percent-encoding of the characters that RFC 3986 does not permit (as_uri)"})

    # ---------------------------------------------------------------- probabilities and value status
    def status(p: float, cid: str) -> str:
        t = label_threshold(cals, cid)
        return "certain" if t is not None and p >= t else "unsure"

    r2 = dec.get("r2")
    has_response = any(FAMILY.get(o) == "response" for o in options)
    r2_agree = None if r2 is None else (r2["p"] >= 0.5) == has_response
    unsure_by_r2 = set()
    if r2_agree is False:
        unsure_by_r2 = {i for i, o in enumerate(options) if FAMILY.get(o) == "response"}

    # ---------------------------------------------------------------- author blocks (plan chapter 4 item 8)
    runs = author_runs(options)
    tb_records: list[dict] = []
    texte: dict[str, list] = {"submission": [], "response": []}
    e19 = {"text_blocks": 0, "characters": 0, "hyphens": 0, "markers": 0, "problems": []}
    run_of_block: dict[int, dict] = {}
    for k, (opt, idx) in enumerate(runs, 1):
        ids = [a for i in idx for a in blocks[i]["atoms"] if a not in fixed]
        r = {"k": k, "option": opt, "blocks": [blocks[i]["block"] for i in idx], "idx": idx, "ids": ids,
             "global_uri": f"{record}/textblock/{k}", "mapping_status": "profile_only"}
        for i in idx:
            run_of_block[i] = r
        if not any((by_id[a].get("text") or "").strip() for a in ids):
            r["not_mapped_reason"] = "The blocks of the author block have no text atom (all atoms are fixed or empty)"
            r["text"], r["tc"] = "", {"hyphens_removed": [], "list_markers_removed": [], "empty_atoms": list(ids),
                                      "nfc_changed": False}
            tb_records.append(r)
            continue
        text, ch = mc.block_text(d, ids)
        tc = mc.profile_changes(ch)
        bad = mc.e19_problems(d, by_id, ids, text, tc)
        e19["text_blocks"] += 1
        e19["characters"] += len(gr.signature_text(text))
        e19["hyphens"] += len(tc["hyphens_removed"])
        e19["markers"] += len(tc["list_markers_removed"])
        e19["problems"] += [f"author block {k}: {b}" for b in bad]
        r |= {"text": text, "tc": tc}
        tb_records.append(r)
        if aff is None:
            r["not_mapped_reason"] = "The export record has no affair for the document"
            continue
        label_iris = ", ".join(f"{record}/label/{blocks[i]['block']}-slot" for i in idx)
        h_text = {"derivation": "extracted_from_pdf", "_textblock": {"tb": {"text": text}, "record": r},
                  "rule": f"author block {k} (option {opt}; Docling blocks {', '.join(r['blocks'])}; plan-full-conversion.md "
                          f"chapter 4 item 8): wording of its atoms without fixed atoms with m03_gold_record.richtext "
                          f"(G19, without G20a); evidence in the TextBlockRecord {r['global_uri']}"}
        neu = {"text": V(text, h_text)}
        if lang:
            neu["text_language"] = V(lang, dict(lang_h))
        neu["text_type"] = V(opt, {"derivation": "fixed_by_schema", "_enum": ("i95", "TextTypeEnum"),
                                   "rule": f"text type of the author block = option {opt} of its blocks in the decisions "
                                           f"file (mode {dec['mode']}); the probabilities are in the label graph: "
                                           f"{label_iris}"})
        u = url_v()
        if u is not None:
            neu["document_url"] = u
        r["mapping_status"] = "in_ech_instance"
        r["ziel"] = FAMILY[opt]
        texte[FAMILY[opt]].append((neu, r))

    # ---------------------------------------------------------------- instance (I95 Container)
    container = {"__entity__": (container_iri, "Container"),
                 "global_uri": V(container_iri, {"derivation": "identifier_minted",
                                                 "rule": f"{ns}i95/affair-{{id}}/doc-{{doc_id}} (deterministic; base "
                                                         f"IRI of the run, {SCRIPT})"})}
    with minted_namespace(base):
        if aff is None:
            nicht.append({"not_mapped_item": "Affair", "not_mapped_reason": "The export record has no affair for the "
                          "document", "candidate_source": files["export"]["path"]})
        else:
            container["affairs"] = [mc.affair_part(d, exp, aff, edoc, abruf, liste, lang, True, texte, nicht)]
        fix_minted_rules(container, base)
        eintraege, ohne = [], []
        instanz = ea.entpacken(container, eintraege=eintraege, ohne=ohne)
        pfade = {}
        for pfad, ent, _, v in eintraege:
            if v.herkunft["derivation"] == "extracted_from_pdf":
                pfade[id(v.herkunft["_textblock"]["record"])] = (ea.pfad_text(pfad[:-1]), ent)
        D = SimpleNamespace(meta=exp | {"affair": aff or {"id": None}}, liste=liste, ref={"units": []})
        chk = mc.check_values(D, {"tb_records": []}, eintraege, ohne)
    # addendum A, rule A1: the absent required I95 slots of the instance are recorded gaps, or they are problems
    gaps, gap_problems = gp.writer_gaps(instanz, nicht, aff)
    problems += gap_problems
    nicht.append({"not_mapped_item": "Document (FRBR work, expression, manifestation)", "not_mapped_reason":
                  "eCH-0295 has only document_url on a TextBlock; the side file gives the source document",
                  "candidate_value": doc_iri, "candidate_source": "docs"})
    nicht.append({"not_mapped_item": "Sponsorships", "not_mapped_reason":
                  "not in the scope of this writer (data minimisation, as src/m06_ech_ausgabe.py); the contributors "
                  "export gives person ids", "candidate_source": "contributors"})
    for b in decided:
        if b["option"] == "title":
            nicht.append({"not_mapped_item": f"Title block {b['block']}", "not_mapped_reason":
                          "A title block from the PDF goes to the label graph only; Affair.title comes from the export "
                          "record (J4)", "candidate_value": f"{record}/block/{b['block']}",
                          "candidate_source": f"label {record}/label/{b['block']}-slot"})
    for r in tb_records:
        if r["mapping_status"] == "profile_only":
            nicht.append({"not_mapped_item": f"TextBlock of author block {r['k']} ({r['option']})",
                          "not_mapped_reason": r["not_mapped_reason"], "candidate_value": r["global_uri"],
                          "candidate_source": "TextBlockRecord"})
        else:
            r["instance_path"], r["about_entity"] = pfade[id(r)]

    # ---------------------------------------------------------------- side file (profile 0.2.0)
    block_status = {}
    for i, b in enumerate(decided):
        p = clip(b["probs"][b["option"]])
        block_status[i] = "unsure" if i in unsure_by_r2 else status(p, b["calibration"])
    af = read_json(files["atoms"]["abs"])
    fp = hashlib.sha256(json.dumps([[a["id"], a["zeichen"]] for a in af["atome"]], separators=(",", ":"))
                        .encode("utf-8")).hexdigest()
    run = {"script_name": SCRIPT,
           "decomposition_source": f"block options of the decisions file {files['decisions']['path']} (SHA-256 "
                                   f"{files['decisions']['sha256']}, mode {dec['mode']}); blocks {files['docs']['path']} "
                                   f"(SHA-256 {files['docs']['sha256']}); export record {files['export']['path']} "
                                   f"(SHA-256 {files['export']['sha256']})",
           "decomposition_accepted": False,
           "taxonomy_version": "plan-full-conversion.md version 1, chapter 4 item 8: author blocks from the options "
                               "of the Docling blocks (gate GJ, EXCEPTION)",
           "atom_version": f"{af.get('version', '')} {af.get('erzeugt_utc', '')}".strip(),
           "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": utc_now()}
    src = {"global_uri": doc_iri, "local_id": d}
    if edoc.get("url_oparl"):
        src["manifestation_url"] = ea.as_uri(edoc["url_oparl"])
    if (edoc.get("url") or "").startswith("http"):
        src["publisher_url"] = ea.as_uri(edoc["url"])
    src["file_sha256"] = doc["pdf_sha256"]
    if edoc.get("hash"):
        src["export_hash"] = edoc["hash"]
    src |= {"docling_json_sha256": af.get("quelle_sha256") or "", "atom_fingerprint": fp,
            "page_count": len(read_json(files["docling"]["abs"])["seiten"])}
    if lang:
        src["document_language"] = lang
        src["document_language_source"] = lang_h.get("rule") or "export (docs.language)"
    else:
        src["document_language_source"] = "no language: the export and the block file give no language"
    src["document_kind"] = (f"gate GJ record, mode {dec['mode']}, D1 option {dec['document']['d1']['option']} "
                            f"({D1_OPTIONS[dec['document']['d1']['option']]})")
    tbr = []
    for r in tb_records:
        x = {"global_uri": r["global_uri"]}
        if r["mapping_status"] == "in_ech_instance":
            x |= {"about_entity": r["about_entity"], "instance_path": r["instance_path"],
                  "ech_slot": f"{mc.STEP_CLASS[r['ziel']]}.texts", "ech_text_type": r["option"]}
        else:
            x["about_entity"] = (f"{ea.OPD}affairs/{aid}" if aff else container_iri)
        x |= {"section_key": r["option"], "mapping_status": r["mapping_status"]}
        if r.get("not_mapped_reason"):
            x["not_mapped_reason"] = r["not_mapped_reason"]
        x["extent_value_status"] = "certain" if all(block_status[i] == "certain" for i in r["idx"]) else "unsure"
        x["text_form"] = "richtext"
        if r["mapping_status"] == "profile_only":
            x["text_content"] = r["text"]
        x |= {"char_count": len(r["text"]), "source_document": doc_iri,
              "units": [{"unit_id": blocks[i]["block"], "unit_type": r["option"],
                         "atom_evidence": [mc.atom_ev(by_id[a]) for a in blocks[i]["atoms"] if a not in fixed]}
                        for i in r["idx"]],
              "text_changes": r["tc"]}
        x["units"] = [u for u in x["units"] if u["atom_evidence"]] or x["units"][:1]
        tbr.append(x)
    werte = []
    for pfad, ent, slot, v in eintraege:
        h, w = v.herkunft, v.wert
        vr = {"about_entity": ent, "instance_path": ea.pfad_text(pfad), "ech_slot": slot,
              "recorded_value": f"sha256:{ea.sha256_text(w)}" if h["derivation"] == "extracted_from_pdf" else str(w),
              "derivation": h["derivation"]}
        if h.get("rule"):
            vr["rule_applied"] = h["rule"]
        vr["mapping_match"] = h.get("match", "not_applicable")
        for k_in, k_out in (("metadata_evidence", "metadata_evidence"), ("pdf_evidence", "pdf_evidence"),
                            ("alternativen", "alternatives")):
            if h.get(k_in):
                vr[k_out] = h[k_in]
        vr["pdf_consistency"] = h.get("konsistenz", "not_checked")
        werte.append(vr)
    prov = {"global_uri": f"{ns}provenance/doc-{d}", "describes_delivery": container_iri,
            "ech_schema_version": ea.FASSUNG_TEXT["i95"], "pipeline_run": run, "source_documents": [src],
            "text_block_records": tbr, "value_records": werte, "not_mapped_records": nicht,
            "verbatim_check": {
                "check_method": "Each leaf value needs a ValueRecord. Each author block: its letters (no markup, no white "
                                "space) are the letters of the Docling wording of its atoms (without fixed atoms) after "
                                "the recorded changes only (line-end hyphens, list markers at the atom start, empty "
                                "atoms, NFC). Metadata values against the export record, terms against the "
                                "enumerations of I95.",
                "text_blocks_checked": e19["text_blocks"], "characters_checked": e19["characters"],
                "hyphens_removed_count": e19["hyphens"], "list_markers_removed_count": e19["markers"],
                "metadata_values_checked": chk["metadaten"], "leaves_without_provenance": len(chk["ohne_herkunft"]),
                "check_passed": not chk["fehler"] and not e19["problems"]}}

    # ---------------------------------------------------------------- label file (label schema 0.1.0)
    import m10_rdf as rdf
    iri_of = rdf.slot_iris(WRAPPER)
    pages = [b["page"] for b in blocks]
    whole = {"page": min(pages), "last_page": max(pages), "span_start": min(b["char_start"] for b in blocks),
             "span_end": max(b["char_end"] for b in blocks)}

    def prob_label(gid, subject, predicate, obj, kind, x, probs, extra) -> dict:
        p = clip(probs[obj])
        cid = str(x["calibration"])
        la = {"global_uri": gid, "label_subject": subject, "label_predicate": predicate, "label_object": obj,
              "label_kind": kind, "label_source": SOURCE[x.get("source", "apertus_head")], "label_probability": p,
              "option_probabilities": [{"option_value": k, "label_probability": clip(v)} for k, v in probs.items()],
              "value_status": status(p, cid), "calibration": f"{base}calibration/{cid}", "model_run": run_iri}
        return la | extra

    labels = []
    d1 = dec["document"]["d1"]
    d1_label = prob_label(f"{record}/label/d1", doc_iri, f"{PLB}documentTextParts", d1["option"], "document_text_parts",
                          d1, d1["probs"], {})
    if d1.get("rule_id"):
        d1_label["rule_id"] = str(d1["rule_id"])
    d1_label |= whole
    if r2_agree is False:
        d1_label["value_status"] = "unsure"
        d1_label["label_note"] = "unsure: the final check R2 does not agree with the block path"
    labels.append(d1_label)
    if r2 is not None:
        yes = r2["p"] >= 0.5
        r2_label = prob_label(f"{record}/label/r2", doc_iri, f"{PLB}executiveResponse", "yes" if yes else "no",
                              "executive_response", {"calibration": r2["calibration"], "source": "apertus_head"},
                              {"yes": r2["p"], "no": 1 - r2["p"]}, whole)
        r2_label["label_note"] = ("final check R2 (frozen head H): the document holds a response of the executive"
                                  + ("; it agrees with the block path" if r2_agree else
                                     "; it does not agree with the block path"))
        labels.append(r2_label)
    for i, (b, x) in enumerate(zip(blocks, decided, strict=True)):
        extra = {"page": b["page"], "span_start": b["char_start"], "span_end": b["char_end"]}
        if x.get("tier"):
            extra["tier"] = str(x["tier"])
        if isinstance(x.get("in_sample"), bool):
            extra["in_sample"] = x["in_sample"]
        r = run_of_block.get(i)
        if r is not None and r.get("instance_path") and x["option"] == r["option"]:
            extra |= {"about_entity": r["about_entity"], "instance_path": r["instance_path"]}
        la = prob_label(f"{record}/label/{b['block']}-slot", f"{record}/block/{b['block']}", f"{AFF}textType",
                        x["option"], "block_slot", x, x["probs"], extra)
        if i in unsure_by_r2:
            la["value_status"] = "unsure"
            la["label_note"] = "unsure: the final check R2 does not agree with the block path"
        labels.append(la)
    pos = {b["block"]: i for i, b in enumerate(blocks)}
    boundary_source = "code" if dec["mode"] == "cascade" else "rule"   # interface 7 gives no source for a boundary
    for x in dec.get("boundaries") or []:
        i = pos[x["after_block"]]
        a, n = blocks[i], blocks[i + 1]
        labels.append(prob_label(f"{record}/label/switch-after-{a['block']}", f"{record}/boundary/after-{a['block']}",
                                 f"{PLB}authorSwitch", "switch", "author_switch",
                                 x | {"source": x.get("source", boundary_source)},
                                 {"switch": x["p"], "no_switch": 1 - x["p"]},
                                 {"page": n["page"], "last_page": max(a["page"], n["page"]),
                                  "span_start": min(a["char_end"], n["char_start"]),
                                  "span_end": max(a["char_end"], n["char_start"]),
                                  "label_note": f"switch between block {a['block']} and block {n['block']}"}))
    for pfad, ent, _, v in eintraege:
        h = v.herkunft
        name = next(x for x in reversed(pfad) if isinstance(x, str))
        path = ea.pfad_text(pfad)
        gid = f"{record}/label/value-{re.sub(r'[^A-Za-z0-9_]+', '-', path).strip('-')}"
        if h["derivation"] == "extracted_from_pdf":
            r = h["_textblock"]["record"]
            bl = [blocks[i] for i in r["idx"]]
            labels.append({"global_uri": f"{record}/label/textblock-{r['k']}-text", "label_subject": r["global_uri"],
                           "label_predicate": iri_of["text"], "label_object": f"sha256:{sha256_text(v.wert)}",
                           "label_kind": "text_wording", "label_source": "copy", "model_run": run_iri,
                           "page": min(b["page"] for b in bl), "last_page": max(b["page"] for b in bl),
                           "span_start": min(b["char_start"] for b in bl), "span_end": max(b["char_end"] for b in bl),
                           "about_entity": ent, "instance_path": path,
                           "label_note": "verbatim copy of the atoms of the author block (check E19); the text changes "
                                         "are in the TextBlockRecord"})
            continue
        if h["derivation"] in ("copied_from_metadata", "normalized_from_metadata", "mapped_from_metadata"):
            src_kind, kind = "export", "export_value"
        elif h["derivation"] in ("identifier_from_metadata", "identifier_minted"):
            src_kind, kind = "constant", "constant_value"
        elif h["derivation"] == "fixed_by_schema" and ".texts[" not in path:
            src_kind, kind = "constant", "constant_value"      # text_type title of Affair.title (J4)
        else:
            # the text_type of an author block (the block labels give its probabilities) and a language of the
            # block file (detected_by_rule; no calibration record): the ValueRecord of the side file only
            continue
        subject = str(v.wert) if name == "global_uri" else ent
        labels.append({"global_uri": gid, "label_subject": subject, "label_predicate": iri_of.get(name, f"{AFF}{name}"),
                       "label_object": str(v.wert), "label_kind": kind, "label_source": src_kind, "model_run": run_iri,
                       "about_entity": ent, "instance_path": path,
                       "label_note": f"derivation {h['derivation']} (ValueRecord of the provenance side file)"})
    used = sorted({la["calibration"].rsplit("/", 1)[1] for la in labels if "calibration" in la})
    synthetic = any(cals[c]["calibration_method"] == SYNTHETIC for c in used)
    label_run = {"global_uri": run_iri, "script_name": SCRIPT, "run_mode": dec["mode"],
                 "process_status": (PROCESS_STATUS + "; synthetic values for a code check: not a result") if synthetic
                 else PROCESS_STATUS,
                 "input_files": [{"file_role": k, "file_path": f["path"], "file_digest": f["sha256"]}
                                 for k, f in files.items()],
                 "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": utc_now()}
    calibrations = [{"global_uri": f"{base}calibration/{c}"} | cals[c] for c in used]
    label_rec = {"global_uri": f"{record}/label-record", "describes_record": record, "ech_delivery": container_iri,
                 "source_document": doc_iri, "label_run": label_run, "label_assertions": labels,
                 "calibrations": calibrations}
    switches = path_switches(options)
    covered = {pos[x["after_block"]] for x in dec.get("boundaries") or []}
    return {"instance": instanz, "provenance": prov, "labels": label_rec, "record": record, "container": container_iri,
            "i95_gaps": gaps, "conformance": gp.conformance(gaps),
            "synthetic": synthetic, "calibrations": used, "check_passed": prov["verbatim_check"]["check_passed"] and not problems,
            "problems": problems + e19["problems"] + chk["fehler"], "notes": notes,
            "counts": {"blocks": len(blocks), "block_options": {o: options.count(o) for o in OPTIONS if o in options},
                       "author_blocks": len(runs),
                       "textblocks_by_slot": {s: len(texte[s]) for s in texte},
                       "textblock_records_profile_only": sum(1 for r in tb_records if r["mapping_status"] == "profile_only"),
                       "path_switch_points": len(switches),
                       "path_switch_points_without_boundary_label": sum(
                           1 for a, b in switches if not any(a <= c < b for c in covered)),
                       "boundary_labels": len(dec.get("boundaries") or []),
                       "label_assertions": len(labels),
                       "label_assertions_by_source": {s: sum(1 for la in labels if la["label_source"] == s)
                                                      for s in sorted({la["label_source"] for la in labels})},
                       "certain_labels": sum(1 for la in labels if la.get("value_status") == "certain"),
                       "unsure_labels": sum(1 for la in labels if la.get("value_status") == "unsure"),
                       "r2_agrees_with_block_path": r2_agree,
                       "d1_option": d1["option"],
                       "leaf_values": len(eintraege), "value_records": len(werte),
                       "e19": {"text_blocks": e19["text_blocks"], "characters": e19["characters"],
                               "hyphens_removed": e19["hyphens"], "list_markers_removed": e19["markers"],
                               "problems": len(e19["problems"])},
                       "metadata_check": {"values_checked": chk["metadaten"], "problems": len(chk["fehler"]),
                                          "leaves_without_provenance": len(chk["ohne_herkunft"])}}}


def file_info(p: Path) -> dict:
    return {"path": rel(p), "sha256": sha256(p), "abs": Path(p).resolve()}


def write_one(d: str, out_dir: Path, export_dir: Path | None, exp_record: dict | None, cals: dict, cal_file: dict | None,
              base: str, docs_dir: Path = DOCS_DIR, decisions_dir: Path = DECISIONS_DIR) -> dict:
    """Writes the three YAML files and the manifest of one document. Returns the manifest."""
    t0 = time.perf_counter()
    paths = explicit_paths(d)
    doc_p, dec_p = Path(docs_dir) / f"{d}.json", Path(decisions_dir) / f"{d}.json"
    for p in (doc_p, dec_p):
        if not p.exists():
            raise SystemExit(f"{d}: no file {rel(p)}")
    doc, dec = read_json(doc_p), read_json(dec_p)
    in_set = set_of(d)
    atoms = read_json(paths["atoms"])["atome"]
    bad = check_doc_file(d, doc, atoms) + check_decisions(d, doc, dec, cals)
    if bad:
        raise SystemExit(f"{d}: input check failed: {bad[:8]}")
    if exp_record is None:
        exp_p = Path(export_dir) / f"{d}.json"
        if not exp_p.exists():
            raise SystemExit(f"{d}: no export record {rel(exp_p)}")
    else:
        exp_p = out_dir / d / "export" / f"{d}.json"
        write_json(exp_p, exp_record)
    exp = read_json(exp_p)
    if str(exp.get("doc_id")) != d or str((exp.get("doc") or {}).get("id")) != d:
        raise SystemExit(f"{d}: the export record is for another document")
    files = {"docs": file_info(doc_p), "decisions": file_info(dec_p), "export": file_info(exp_p),
             "atoms": file_info(paths["atoms"]), "docling": file_info(paths["docling"])}
    if cal_file:
        files["calibrations"] = {"path": cal_file["path"], "sha256": cal_file["sha256"], "abs": ROOT / cal_file["path"]}
    b = build(d, doc, dec, exp, cals, base, files)
    folder = out_dir / d
    outs = {"ech_yaml": folder / f"{d}.ech.yaml", "provenance_yaml": folder / f"{d}.provenance.yaml",
            "labels_yaml": folder / f"{d}.labels.yaml"}
    note = " Synthetic values for a code check: not a result." if b["synthetic"] else ""
    ea.schreibe_yaml(outs["ech_yaml"], b["instance"],
                     f"# eCH-0295 instance (I95, root class Container), {SCRIPT} ({VERSION}), document {d}\n"
                     f"# Gate GJ, status EXCEPTION, NOT RELEASED.{note} Side files: {d}.provenance.yaml, {d}.labels.yaml\n")
    ea.schreibe_yaml(outs["provenance_yaml"], b["provenance"],
                     f"# Provenance side file (src/m06_ech_profil.yaml version 0.2.0) of {d}.ech.yaml\n")
    ea.schreibe_yaml(outs["labels_yaml"], b["labels"],
                     f"# Label file (src/m10_label_schema.yaml version 0.1.0, class LabelRecord) of {d}.ech.yaml.{note}\n")
    seconds = round(time.perf_counter() - t0, 3)
    man = {"schema": "parlpdfech-gj-record/1", "doc_id": d, "status": PROCESS_STATUS,
           "synthetic_values": b["synthetic"], "mode": dec["mode"], "split": doc["split"], "gj_set": in_set,
           "base_iri": base, "record_iri": b["record"], "container_iri": b["container"],
           "named_graphs": {g: f"{b['record']}/{g}" for g in ("ech-0295", "provenance", "atoms", "labels")},
           "writer": {"path": SCRIPT, "version": VERSION, "sha256": sha256(Path(__file__)), "run_date": clock()},
           "reused_files": {p: sha256(ROOT / p) for p in ("src/m06_converter.py", "src/m06_ech_ausgabe.py",
                                                          "src/m03_gold_record.py", "src/m03_iso_v4.py",
                                                          "src/m03_iso_paths.py")},
           "schemas": {"i95": {"path": rel(I95), "sha256": sha256(I95)},
                       "wrapper": {"path": rel(WRAPPER), "sha256": sha256(WRAPPER)},
                       "profile": {"path": rel(PROFILE), "sha256": sha256(PROFILE), "version": "0.2.0"},
                       "labels": {"path": rel(LABEL_SCHEMA), "sha256": sha256(LABEL_SCHEMA), "version": "0.1.0"}},
           "inputs": {k: {"path": f["path"], "sha256": f["sha256"]} for k, f in files.items()},
           "model": {k: dec[k] for k in ("model", "template", "template_sha256", "heads", "calibration") if k in dec}
                    or "the decisions file (interface 7) names no model, template or head",
           "calibration_ids": b["calibrations"], "conformance": b["conformance"], "i95_gaps": b["i95_gaps"],
           "check_passed": b["check_passed"],
           "problems": b["problems"], "notes": b["notes"], "counts": b["counts"],
           "outputs": {k: {"path": rel(p), "sha256": sha256(p), "bytes": p.stat().st_size} for k, p in outs.items()},
           "seconds": {"write": seconds}}
    write_json(folder / "manifest.json", man)
    return man


def cmd_write(args) -> int:
    started = clock()
    base = check_base(args.base)
    out_dir = Path(args.out).resolve()
    docs = [str(x) for x in args.docs_ids]
    guard_docs(docs)               # one pass of the split guard for all documents
    for d in docs:
        explicit_paths(d)          # guard and explicit paths before any export file is read
    cals, cal_file = load_calibrations(Path(args.calibrations).resolve() if args.calibrations else None)
    exp_records = mc.build_export_records(docs) if args.build_export else {}
    rows = []
    for n, d in enumerate(docs, 1):
        man = write_one(d, out_dir, Path(args.export).resolve() if args.export else None, exp_records.get(d), cals,
                        cal_file, base, Path(args.docs), Path(args.decisions))
        if args.rdf or args.validate:
            import m10_rdf as rdf
            rdf.convert_record(out_dir / d, d, base)
        if args.validate:
            import m10_validate as val
            val.validate_record(out_dir / d, d)
        man = read_json(out_dir / d / "manifest.json")
        rows.append({"doc_id": d, "check_passed": man["check_passed"], "seconds": man["seconds"],
                     "conformance": man["conformance"], "i95_gaps": [g["slot"] for g in man["i95_gaps"]],
                     "validation_passed": (man.get("validation") or {}).get("passed")})
        print(f"{n}/{len(docs)} {d}: TextBlocks {man['counts']['textblocks_by_slot']}, labels "
              f"{man['counts']['label_assertions']}, check passed {man['check_passed']}, conformance "
              f"{man['conformance']}, validation {rows[-1]['validation_passed']}, seconds {man['seconds']}", flush=True)
    summary = {"schema": "parlpdfech-gj-write/1", "status": PROCESS_STATUS, "run_date": started, "finished": clock(),
               "script": {"path": SCRIPT, "sha256": sha256(Path(__file__))}, "base_iri": base,
               "calibrations": cal_file, "documents": len(rows), "per_document": rows}
    write_json(out_dir / "write.json", summary)
    ok = all(r["check_passed"] and r["validation_passed"] is not False for r in rows)
    print(json.dumps({"documents": len(rows), "all_checks_passed": ok, "write_json": rel(out_dir / "write.json")}, indent=1))
    return 0 if ok else 2


def main() -> None:
    ap = argparse.ArgumentParser(description="gate GJ writer: eCH-0295 instance, provenance side file, label file")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("write")
    p.add_argument("--out", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--export", help="folder with the stored export records <doc>.json")
    g.add_argument("--build-export", action="store_true", help="make the export records from daten/roh/exports")
    p.add_argument("--calibrations", required=True, help="JSON file with the calibration records")
    p.add_argument("--docs", default=str(DOCS_DIR))
    p.add_argument("--decisions", default=str(DECISIONS_DIR))
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--rdf", action="store_true", help="also write the RDF files (src/m10_rdf.py)")
    p.add_argument("--validate", action="store_true", help="also run the checks of src/m10_validate.py (implies --rdf)")
    p.add_argument("docs_ids", nargs="+", metavar="DOC")
    a = ap.parse_args()
    sys.exit({"write": cmd_write}[a.cmd](a))


if __name__ == "__main__":
    main()
