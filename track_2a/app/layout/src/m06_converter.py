"""Converter eCH writer: the last stage of the converter (gate 3a version 4, condition 5).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), step
converter eCH writer, for the main agent. Status: NOT RELEASED. This file gives no gate result.

1 Task
  Input for one document: the output record of the frozen runner `src/m05_iso_runner.py` (files
  `<run>/records/<doc>.json` and `<run>/nos4/<doc>.json`, with `<run>/run.json`) and the export record of the
  document (OpenParlData, decision D4). Output: one eCH-0295 instance (I95, root class Container) and one
  provenance side file (profile `src/m06_ech_profil.yaml` version 0.2.0, root class ExtractionRecord).
  The rules are in chapter 7 of E20 version 5.0 (`crisp-dm/03-data-preparation/isolation-level-e20.md`).

2 Rules
  1. Claim flag true at L9: each converter block (E20 7.4) is one TextBlock in the slot of its coarse answer:
     submitted in Submission.texts, response in ResponseStep.texts. The TextBlock has no text_type (E20 7.2).
     Its text is the wording of the text atoms of the block. The fixed atoms are not in it (E20 7.4.7).
  2. The wording comes from `m03_gold_record.richtext` (form of rule G19 of the gold set record). The writer
     makes no text (E19). The text-layer typography of rule G20a is off: the profile has no slot for that
     change, and the side file must record each change. Thus the text is the Docling wording of the atoms
     with only these changes: removed line-end hyphens, removed list markers, empty atoms, NFC (all recorded).
  3. The TextBlockRecord of each such block has `extent_value_status: unsure` (D2, E20 7.7).
  4. A block with the coarse answer summary does not give the step of its author (E20 7.7). It goes into the
     side file only (mapping_status profile_only), also with `extent_value_status: unsure`.
  5. Claim flag false: the instance gets the metadata values and no TextBlock from the PDF. The side file gives
     the reason (NotMappedRecord with the abstention reason of the runner).
  6. Affair.title comes from the export record: one TextBlock for each language with a value in title_de,
     title_fr, title_it and title_rm (J4, G24). The writer never takes the title from the PDF.
  7. The metadata values come from the export record with the functions of `src/m06_ech_ausgabe.py` (I95
     branch): affair number, affair type, local id, title, submission date, response date, responder,
     document URL, language. This file imports these functions and does not change them.

3 Checks before a file is written
  1. The SHA-256 of each runner record is equal to the value in `<run>/run.json`.
  2. The atom ids of the record are the atom ids of the atoms file, and the atoms file has the SHA-256 that the
     runner recorded.
  3. The L9 answers of the record are the `nos4` answers after the map `SLOT_NOTITLE` of
     `daten/iso/ladder/ladder.json` and the block form (E20 7.4.2 and 7.4.3).
  4. The S1 export fields of the export record have the SHA-256 that the runner recorded.
  5. E19 for each text block: the letters of the text are the letters of its atoms after the recorded changes
     (`m03_gold_record.signature_text` and `signature_atoms`). Each removed hyphen is the last character of its
     atom. Each removed list marker starts its atom. Each empty atom has no text or is a picture.
  6. Each leaf value of the instance has a ValueRecord. The metadata values agree with the export record
     (`m06_ech_ausgabe.herkunft_pruefen`).

4 Process rule 6
  The console shows only counts, document ids, claim flags and SHA-256 values. The output and the export
  records of a test document must be in `daten/gold/final_v4`. A group 7 document is refused.

Usage (from the project folder; one command on one line):
  uv run --no-project --python 3.12 --with pyyaml==6.0.3 python src/m06_converter.py export --out <dir> DOC ...
  uv run --no-project --python 3.12 --with pyyaml==6.0.3 python src/m06_converter.py convert --run <runner out>
      --export <dir> --out <dir> [--doc DOC ...] [--validate]
  uv run --no-project --python 3.12 --with pyyaml==6.0.3 python src/m06_converter.py validate --out <dir>
Output of convert: <out>/instances/<doc>.yaml, <out>/provenance/<doc>.yaml, <out>/convert.json.
Output of validate: <out>/validation.json (linkml-validate, linkml==1.11.1 with uvx --offline).
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_record as gr  # noqa: E402  (wording, text form and E19 signatures; not changed)
import m03_iso_v4 as v4  # noqa: E402  (atoms, fixed answers, answer sets)
import m03_sub_common as sc  # noqa: E402  (families, role_of, test parliaments)
import m06_ech_ausgabe as ea  # noqa: E402  (metadata values from the export; not changed)
from m03_iso_paths import TEST, iso_path, pdf_path  # noqa: E402

V = ea.V
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "src/m06_converter.py"
VERSION = "converter-ech-writer-1"
FINAL_V4 = ROOT / "daten/gold/final_v4"
PDF_INDEX = ROOT / "daten/analyse/pdf/docs_pdf_index.csv.gz"
LADDER_JSON = ROOT / "daten/iso/ladder/ladder.json"
TEST_LISTS = (ROOT / "daten/gold/test.csv", ROOT / "daten/gold/bulk_test.csv")
I95 = ea.SCHEMA["i95"]
PROFILE = ea.PROFIL
LEVEL = "L9"
EXPORT_FIELDS = ("category_de", "category_harmonized", "name_klasse")   # S1 export fields of the runner
SLOT_OF = {"submitted": "submission", "response": "response"}           # coarse answer -> step of the instance
STEP_CLASS = ea.SCHRITT_KLASSE["i95"]                                    # Submission, ResponseStep
NS = f"{ea.PPD}converter/l9/"                                            # minted IRIs of this writer
HYPHENS = "-\u00ad\u2010"
# changes of m03_gold_record.richtext that the profile cannot record; they must stay empty (rule 2)
NO_PROFILE_SLOT = ("removed_furniture_atoms", "ocr_corrections", "text_layer_corrections", "superscripts",
                   "subscripts", "paragraph_starts", "continued_elements", "form_overrides", "heading_ranks",
                   "empty_cells")
AFFAIRS_FILE = "daten/roh/exports/affairs.ndjson.gz"
EVENTS_FILE = "daten/roh/exports/events.ndjson.gz"


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canonical_sha(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ guards (process rule 6)
def read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_ids() -> frozenset:
    return frozenset(r["doc_id"].strip() for p in TEST_LISTS if p.exists() for r in read_csv(p))


def is_test_doc(d: str, body_key: str = "") -> bool:
    _, _, test_parl = sc._protected()
    return iso_path("atome", d).is_relative_to(TEST) or d in test_ids() or (bool(body_key) and body_key in test_parl)


def check_docs(docs: list[str], dirs: list[Path], body: dict[str, str] | None = None) -> None:
    """Refuse a group 7 document. The files of a test document go only into daten/gold/final_v4."""
    g7 = v4.final_docs()
    for d in docs:
        if d in g7:
            raise SystemExit(f"{d}: group 7 document: refused")
        if is_test_doc(d, (body or {}).get(d, "")):
            for p in dirs:
                if not Path(p).resolve().is_relative_to(FINAL_V4.resolve()):
                    raise SystemExit(f"{d}: test document: output only in daten/gold/final_v4 (process rule 6): refused")


# ------------------------------------------------------------------ export record (decision D4)
def index_rows(ids: list[str]) -> dict[str, dict]:
    """The rows of the PDF index (the export record of the runner) for the documents."""
    want, got = set(ids), {}
    with gzip.open(PDF_INDEX, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["id"] in want:
                got[r["id"]] = r
    return got


def build_export_records(ids: list[str]) -> dict[str, dict]:
    """The export records of the documents, in the structure of m06_ech_ausgabe.metadaten_auszug: the docs row
    (without the full text), the docs rows of the same affair, the affair, its events, the council groups of
    its parliament and the body. One pass over each export file."""
    idx = index_rows(ids)
    missing = [d for d in ids if d not in idx]
    if missing:
        raise SystemExit(f"no row in the PDF index: {missing}")
    out = {d: {"doc_id": d, "body_key": idx[d]["body_key"], "pdf_index_row": {k: idx[d].get(k, "") for k in (
        "id", "body_key", "affair_id", *EXPORT_FIELDS)}, "affair_docs": [], "events": [], "groups": []} for d in ids}
    by_body: dict[str, list[str]] = {}
    for d in ids:
        by_body.setdefault(idx[d]["body_key"], []).append(d)
    for b, ds in sorted(by_body.items()):
        datei = ea.EXPORTE / "docs" / f"docs_{b}.ndjson.gz"
        aids = {int(idx[d]["affair_id"]): d for d in ds if idx[d]["affair_id"]}
        for r in ea._zeilen(datei, lambda s, aids=aids, ds=ds: any(ea._feld(s, "affair_id", a) for a in aids)
                            or any(ea._feld(s[:20], "id", d) for d in ds)):
            r.pop("text", None)
            r.pop("tika_metadata", None)
            if str(r.get("id")) in ds:
                out[str(r["id"])]["doc"] = r
            for a, d in aids.items():
                if r.get("affair_id") == a:
                    out[d]["affair_docs"].append({k: r.get(k) for k in ("id", "name", "date", "language", "category_de",
                                                                         "category_fr", "format", "url_oparl")})
        for d in ds:
            out[d]["doc_export_file"] = rel(datei)
    aff_ids: dict[int, list[str]] = {}
    for d in ids:
        doc = out[d].get("doc")
        if doc is None:
            raise SystemExit(f"{d}: no docs row in the export")
        if doc.get("affair_id") is not None:
            aff_ids.setdefault(int(doc["affair_id"]), []).append(d)
    for r in ea._zeilen(ea.EXPORTE / "affairs.ndjson.gz", lambda s: any(ea._feld(s[:20], "id", a) for a in aff_ids)):
        for d in aff_ids.get(r["id"], []):
            out[d]["affair"] = r
    for r in ea._zeilen(ea.EXPORTE / "events.ndjson.gz", lambda s: any(ea._feld(s, "affair_id", a) for a in aff_ids)):
        for d in aff_ids.get(r.get("affair_id"), []):
            out[d]["events"].append(r)
    body_ids: dict[int, list[str]] = {}
    for d in ids:
        if "affair" in out[d]:
            body_ids.setdefault(out[d]["affair"]["body_id"], []).append(d)
    for r in ea._zeilen(ea.EXPORTE / "groups.ndjson.gz", lambda s: any(ea._feld(s, "body_id", b) for b in body_ids)):
        if r.get("body_id") in body_ids and r.get("type_harmonized") in ("council_executive", "council_legislative"):
            for d in body_ids[r["body_id"]]:
                out[d]["groups"].append({k: v for k, v in r.items() if k != "contact"})
    for r in ea._zeilen(ea.EXPORTE / "bodies.ndjson.gz", lambda s: any(ea._feld(s[:20], "id", b) for b in body_ids)):
        for d in body_ids.get(r["id"], []):
            out[d]["body"] = r
    retrieved = (ea.EXPORTE / "abgerufen_utc.txt").read_text(encoding="utf-8").strip()
    for d, a in out.items():
        a["export_retrieved_utc"] = retrieved
        a["events"].sort(key=lambda e: (e.get("date") or "", e.get("position") or 0))
    return out


def cmd_export(args) -> int:
    ids = [str(d) for d in args.docs]
    out_dir = Path(args.out)
    check_docs(ids, [out_dir], {d: r["body_key"] for d, r in index_rows(ids).items()})
    recs = build_export_records(ids)
    files = {}
    for d, r in recs.items():
        p = out_dir / f"{d}.json"
        write_json(p, r)
        files[d] = {"sha256": sha256(p), "affair": "affair" in r, "events": len(r["events"]), "groups": len(r["groups"])}
    print(json.dumps({"documents": len(recs), "folder": rel(out_dir), "files": files}, indent=1))
    return 0


# ------------------------------------------------------------------ runner records
def load_run(run_dir: Path, ids: list[str] | None) -> tuple[dict, dict[str, dict]]:
    """run.json and the records of the documents. Each record must have the SHA-256 of run.json."""
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    per = run["per_document"]
    ids = ids or list(per)
    out = {}
    for d in ids:
        if d not in per:
            raise SystemExit(f"{d}: not in {rel(run_dir / 'run.json')}")
        rp, np_ = run_dir / "records" / f"{d}.json", run_dir / "nos4" / f"{d}.json"
        if sha256(rp) != per[d]["record_sha256"] or sha256(np_) != per[d]["nos4_sha256"]:
            raise SystemExit(f"{d}: the runner record or the nos4 file differs from run.json")
        out[d] = {"record": json.loads(rp.read_text(encoding="utf-8")), "path": rp, "sha256": per[d]["record_sha256"],
                  "nos4_path": np_, "nos4_sha256": per[d]["nos4_sha256"]}
    return run, out


def l9_view(nos4: list[str], ids: list[str], fixed: dict[str, str]) -> list[str]:
    """Map SLOT_NOTITLE and block form (E20 7.2, 7.4.2 and 7.4.3), as m03_ladder.converter_view does it."""
    m = json.loads(LADDER_JSON.read_text(encoding="utf-8"))["rule_library"]["collapse_maps"]["SLOT_NOTITLE"]
    hm = [m[x] for x in nos4]
    first = next((i for i, x in enumerate(hm) if x in v4.TEXT), None)
    if first is None:
        return hm
    out, prev = list(hm), hm[first]
    for i, x in enumerate(hm):
        if x in v4.TEXT:
            prev = x
        elif ids[i] not in fixed:
            out[i] = prev
    return out


def blocks(answers: list[str]) -> list[tuple[str, list[int]]]:
    """Blocks of E20 7.4.1: maximal runs of one coarse text answer over the text atoms. Atoms without a text
    answer between two runs of the same answer do not split it (same rule as m03_ladder.blocks)."""
    out, cur, cls = [], [], None
    for i, x in enumerate(answers):
        if x in v4.TEXT:
            if cls is not None and x != cls:
                out.append((cls, cur))
                cur = []
            cls = x
            cur.append(i)
    if cur:
        out.append((cls, cur))
    return out


def check_record(d: str, rec: dict, atoms_list: list[dict], fixed: dict[str, str], exp: dict) -> list[str]:
    """Checks 3.2 to 3.4 of the header. Returns the problems (atom ids and counts only)."""
    bad = []
    ids = [a["id"] for a in atoms_list]
    if rec.get("doc_id") != d:
        bad.append("the record is for another document")
    if rec["ids"] != ids:
        bad.append("the atom ids of the record differ from the atoms file")
    if rec["inputs"]["atome"]["sha256"] != sha256(iso_path("atome", d)):
        bad.append("the atoms file differs from the file that the runner read")
    if len(rec["nos4"]) != len(ids) or len(rec["l9"]["answers"]) != len(ids):
        bad.append("the answer lists do not have one answer for each atom")
    elif l9_view(rec["nos4"], ids, fixed) != rec["l9"]["answers"]:
        bad.append("the L9 answers are not the nos4 answers after the map and the block form")
    if rec["l9"].get("map") != "SLOT_NOTITLE" or rec["l9"].get("unit") != "block":
        bad.append("the record does not give the map SLOT_NOTITLE with the block unit")
    if sc.role_of(sc.FAMILY[x] for x in rec["nos4"] if x in v4.TEXT) != rec["converter_role"]:
        bad.append("the converter role differs from the role of the nos4 answers")
    if any(ids[i] in fixed for _, idx in blocks(rec["l9"]["answers"]) for i in idx):
        bad.append("an atom with a fixed answer has a text answer")
    row = exp.get("pdf_index_row") or {}
    if canonical_sha({k: row.get(k, "") for k in EXPORT_FIELDS}) != rec["export_record"]["fields_sha256"]:
        bad.append("the S1 export fields differ from the fields that the runner read")
    doc = exp.get("doc") or {}
    if str(doc.get("id")) != d:
        bad.append("the export record has another docs row")
    return bad


# ------------------------------------------------------------------ wording and E19
@contextlib.contextmanager
def docling_wording():
    """Rule 2 of the header: m03_gold_record.richtext without the text-layer typography (G20a)."""
    old = gr.TYPOGRAPHY_FROM_TEXT_LAYER
    gr.TYPOGRAPHY_FROM_TEXT_LAYER = False
    try:
        yield
    finally:
        gr.TYPOGRAPHY_FROM_TEXT_LAYER = old


def block_text(d: str, ids: list[str]) -> tuple[str, dict]:
    """The rich text of the atoms of one block (form of G19) and the record of its changes."""
    with docling_wording():
        text, ch = gr.richtext(d, ids, False, None)
    extra = [k for k in NO_PROFILE_SLOT if ch.get(k)]
    if extra:
        raise SystemExit(f"{d}: the wording has changes that the profile cannot record: {extra}")
    return text, ch


def profile_changes(ch: dict) -> dict:
    return {"hyphens_removed": list(ch["hyphens_removed"]),
            "list_markers_removed": [{"range_start": m["range_start"], "range_end": m["range_end"]}
                                     for m in ch["list_markers_removed"]],
            "empty_atoms": list(ch["empty_atoms"]), "nfc_changed": bool(ch["nfc_changed"])}


def e19_problems(d: str, by_id: dict, ids: list[str], text: str, tc: dict) -> list[str]:
    """Check 3.5 of the header for one text block (tc: the recorded changes of the profile)."""
    bad = []
    if gr.signature_text(text) != gr.signature_atoms(d, ids, tc):
        bad.append("the letters of the text differ from the letters of the atoms after the recorded changes")
    pos = {}
    for a in ids:
        z0, z1 = by_id[a]["zeichen"]
        for p in range(z0, z1):
            pos[p] = a
    for p in tc["hyphens_removed"]:
        a = pos.get(p)
        t = (by_id[a].get("text") or "") if a else ""
        i = p - by_id[a]["zeichen"][0] if a else -1
        if a is None or not (0 <= i < len(t)) or t[i] not in HYPHENS or i != len(t.rstrip()) - 1:
            bad.append(f"removed hyphen at {p} is not a line-end hyphen of an atom of the block")
    for m in tc["list_markers_removed"]:
        a = pos.get(m["range_start"])
        t = (by_id[a].get("text") or "") if a else ""
        mo = gr.MARKER.match(t)
        z0 = by_id[a]["zeichen"][0] if a else 0
        if a is None or not mo or (z0 + mo.start(1), z0 + mo.end()) != (m["range_start"], m["range_end"]):
            bad.append(f"removed list marker at {m['range_start']} is not the marker at the start of an atom")
    for a in tc["empty_atoms"]:
        if a not in ids or ((by_id[a].get("text") or "").strip() and by_id[a].get("label") != "picture"):
            bad.append(f"empty atom {a} has text")
    return bad


# ------------------------------------------------------------------ instance and side file
def from_ocr(a: dict) -> bool:
    return any("OCR" in h for h in (a.get("hinweise") or []))


def atom_ev(x: dict) -> dict:
    """AtomEvidence of one atom (same fields as m03_gold_record.atom_evidence)."""
    b = x.get("zeilenrahmen") or x.get("rahmen") or [0, 0, 0, 0]
    return {"atom_id": x["id"], "page_number": x["seite"],
            "bbox": {"bbox_left": b[0], "bbox_top": b[1], "bbox_right": b[2], "bbox_bottom": b[3]},
            "char_start": x["zeichen"][0], "char_end": x["zeichen"][1], "from_ocr": from_ocr(x)}


LANGUAGE_LISTS = (ROOT / "daten/analyse/lehrer_stichprobe/auswahl_lehrer.csv", ROOT / "daten/iso/gruppen.csv",
                  ROOT / "daten/iso/pool.csv", ROOT / "daten/gold/test.csv", ROOT / "daten/gold/bulk_test.csv",
                  ROOT / "daten/gold/extension.csv", ROOT / "daten/gold/bulk_train.csv")


def document_language(d: str, doc: dict, ddatei: str, abruf: str) -> tuple[str | None, dict]:
    """The language of the document, as m06_ech_ausgabe.dokument_laden gives it: the export field docs.language
    (copied_from_metadata); else the automatic language of the document list (detected_by_rule; column sprache,
    see the header of src/m03_lehrer_stichprobe.py); else no language."""
    if doc.get("language") in ea.SPRACHEN:
        return doc["language"], {"derivation": "copied_from_metadata", "metadata_evidence": [
            ea.beleg_meta(ddatei, "doc", doc["id"], "language", doc["language"], abruf)]}
    for p in LANGUAGE_LISTS:
        if not p.exists():
            continue
        row = next((r for r in read_csv(p) if r.get("doc_id") == d), None)
        if row and row.get("sprache") in ea.SPRACHEN:
            src = f", source {row['sprache_quelle']}" if row.get("sprache_quelle") else ""
            return row["sprache"], {"derivation": "detected_by_rule", "_augenschein": row["sprache"],
                                    "rule": f"the export has no language (docs.language); column sprache of {rel(p)}{src} "
                                            f"(export field, else the function-word rule on the export text, else the "
                                            f"language of the parliament; src/m03_lehrer_stichprobe.py)"}
    return None, {}


def build(d: str, run_rec: dict, exp: dict, exp_path: Path) -> dict:
    """The instance (with V values), the raw data of the side file and the checks for one document."""
    rec = run_rec["record"]
    atoms_list = v4.atoms_of(d)
    by_id = {a["id"]: a for a in atoms_list}
    fixed = v4.fixed_answers(d)
    problems = check_record(d, rec, atoms_list, fixed, exp)
    if problems:
        raise SystemExit(f"{d}: runner record check failed: {problems}")
    liste = [dict(a, ocr=from_ocr(a)) for a in atoms_list]      # m06_ech_ausgabe reads the key ocr
    meta, doc, aff = exp, exp["doc"], exp.get("affair")
    abruf, ddatei = exp["export_retrieved_utc"], exp["doc_export_file"]
    claim = rec["claims"][LEVEL]
    claimed = bool(claim["claimed"])
    aid = aff["id"] if aff else None
    affair_iri = f"{ea.OPD}affairs/{aid}" if aff else None
    container_iri = f"{NS}i95/affair-{aid}/doc-{d}"
    doc_iri = f"{ea.OPD}docs/{d}"
    nicht: list[dict] = []

    # language and document URL of the PDF TextBlocks (as m06_ech_ausgabe.dokument_laden does it)
    lang, lang_h = document_language(d, doc, ddatei, abruf)
    url_raw = doc.get("url_oparl")
    url_ev = [ea.beleg_meta(ddatei, "doc", doc["id"], "url_oparl", url_raw, abruf)]

    def url_v():
        if not url_raw:
            return None
        u = ea.as_uri(url_raw)
        if u == url_raw:
            return V(u, {"derivation": "copied_from_metadata", "metadata_evidence": url_ev})
        return V(u, {"derivation": "normalized_from_metadata", "metadata_evidence": url_ev, "_norm": "uri",
                     "rule": "percent-encoding of the characters that RFC 3986 does not permit (as_uri)"})

    # ---------------------------------------------------------------- converter blocks (E20 7.4)
    ans = rec["l9"]["answers"]
    blks = blocks(ans)
    tb_records: list[dict] = []
    texte: dict[str, list] = {"submission": [], "response": []}
    e19 = {"text_blocks": 0, "characters": 0, "hyphens": 0, "markers": 0, "problems": []}
    if claimed:
        for k, (cls, idx) in enumerate(blks, 1):
            ids = [rec["ids"][i] for i in idx]
            text, ch = block_text(d, ids)
            tc = profile_changes(ch)
            bad = e19_problems(d, by_id, ids, text, tc)
            e19["text_blocks"] += 1
            e19["characters"] += len(gr.signature_text(text))
            e19["hyphens"] += len(tc["hyphens_removed"])
            e19["markers"] += len(tc["list_markers_removed"])
            e19["problems"] += [f"block {k}: {b}" for b in bad]
            tb_iri = f"{NS}affair-{aid}/doc-{d}/textblock/{k}"
            r = {"k": k, "cls": cls, "ids": ids, "text": text, "tc": tc, "global_uri": tb_iri,
                 "mapping_status": "profile_only"}
            tb_records.append(r)
            if cls == "summary":
                r["not_mapped_reason"] = ("The coarse answer summary does not give the step of its author "
                                          "(E20 version 5.0, chapter 7.7)")
                continue
            if cls not in SLOT_OF:
                raise SystemExit(f"{d}: a claimed document has the coarse answer {cls} (E20 7.3)")
            if aff is None:
                r["not_mapped_reason"] = "The export record has no affair for the document"
                continue
            h_text = {"derivation": "extracted_from_pdf", "_textblock": {"tb": {"text": text}, "record": r},
                      "rule": f"converter block {k} (coarse answer {cls}, isolation level L9, block unit, E20 version 5.0 "
                              f"chapter 7.4): wording of its text atoms with m03_gold_record.richtext (G19, without "
                              f"G20a); evidence in the TextBlockRecord {tb_iri}"}
            neu = {"text": V(text, h_text)}
            if lang:
                neu["text_language"] = V(lang, dict(lang_h))
            u = url_v()
            if u is not None:
                neu["document_url"] = u
            r["mapping_status"] = "in_ech_instance"
            r["ziel"] = SLOT_OF[cls]
            texte[SLOT_OF[cls]].append((neu, r))
    else:
        nicht.append({"not_mapped_item": "TextBlocks of the PDF (Submission.texts and ResponseStep.texts)",
                      "not_mapped_reason": f"The converter does not claim the document at the isolation level L9 (claim "
                                           f"flag false): {claim.get('abstention_reason')}. The instance has only the "
                                           f"metadata values (E20 version 5.0, chapter 7.7).",
                      "candidate_value": f"converter blocks: {len(blks)}; converter role {rec['converter_role']}; S1 rule "
                                         f"role {rec['s1']['rule_role']}; S1 combined role {rec['s1']['combined_role']}",
                      "candidate_source": f"runner record {rel(run_rec['path'])} (SHA-256 {run_rec['sha256']})"})

    container = {"__entity__": (container_iri, "Container"),
                 "global_uri": V(container_iri, {"derivation": "identifier_minted",
                                                 "rule": "{namespace}/converter/l9/i95/affair-{id}/doc-{doc_id}"})}
    if aff is None:
        nicht.append({"not_mapped_item": "Affair", "not_mapped_reason": "The export record has no affair for the document",
                      "candidate_source": rel(exp_path)})
    else:
        container["affairs"] = [affair_part(d, meta, aff, doc, abruf, liste, lang, claimed, texte, nicht)]
    nicht.append({"not_mapped_item": "Document (FRBR work, expression, manifestation)", "not_mapped_reason":
                  "eCH-0295 has only document_url on a TextBlock; the side file gives the source document",
                  "candidate_value": doc_iri, "candidate_source": "docs"})
    nicht.append({"not_mapped_item": "Sponsorships", "not_mapped_reason":
                  "not in the scope of this writer (data minimisation, as src/m06_ech_ausgabe.py); the contributors "
                  "export gives person ids", "candidate_source": "contributors"})
    for r in tb_records:
        if r["mapping_status"] == "profile_only":
            nicht.append({"not_mapped_item": f"TextBlock of converter block {r['k']} ({r['cls']})",
                          "not_mapped_reason": r["not_mapped_reason"], "candidate_value": r["global_uri"],
                          "candidate_source": "TextBlockRecord"})
    return {"container": container, "tb_records": tb_records, "nicht": nicht, "affair_iri": affair_iri,
            "container_iri": container_iri, "doc_iri": doc_iri, "lang": lang, "lang_h": lang_h, "claimed": claimed, "rec": rec,
            "blocks": blks, "e19": e19, "atoms": atoms_list, "liste": liste, "aid": aid}


def affair_part(d, meta, aff, doc, abruf, liste, lang, claimed, texte, nicht) -> dict:
    """The Affair of the instance: the I95 branch of m06_ech_ausgabe.instanz_bauen for the metadata values,
    with the TextBlocks of the converter blocks. Affair.title only from the export record (J4)."""
    aid = aff["id"]
    affair_iri = f"{ea.OPD}affairs/{aid}"
    has_type = any(aff.get(f) is not None for f in ("type_name_de", "type_name_fr", "type_name_it", "type_harmonized_id"))
    typ = ea.typ_bestimmen(aff, "i95", abruf) if has_type else None
    affair = {"__entity__": (affair_iri, ea.I95_KLASSE.get(typ.wert if typ else "", "Affair"))}
    affair["global_uri"] = V(affair_iri, {"derivation": "identifier_from_metadata",
                                          "rule": f"{ea.OPD}affairs/{{id}} (OpenParlData API, provisional; E3, F19)",
                                          "metadata_evidence": [ea.beleg_meta(AFFAIRS_FILE, "affair", aid, "id", aid, abruf)],
                                          "_muster": (f"{ea.OPD}affairs/{{}}", aid)})
    if aff.get("external_id"):
        affair["local_id"] = ea.wert_meta(str(aff["external_id"]), ea.beleg_meta(AFFAIRS_FILE, "affair", aid, "external_id",
                                                                                aff["external_id"], abruf),
                                          rule="id in the information system of the parliament (external_id)")
    if aff.get("number") not in (None, ""):
        fs = ea.fundstellen(str(aff["number"]), liste)
        affair["affair_number"] = ea.wert_meta(str(aff["number"]), ea.beleg_meta(AFFAIRS_FILE, "affair", aid, "number",
                                                                                 aff["number"], abruf),
                                               pdf_evidence=fs, konsistenz="confirmed" if fs else "not_found")
    else:
        nicht.append({"not_mapped_item": "Affair.affair_number", "not_mapped_reason": "the export record has no number",
                      "candidate_source": "affairs.number"})
    if typ is not None:
        affair["affair_type"] = typ
    else:
        nicht.append({"not_mapped_item": "Affair.affair_type", "not_mapped_reason":
                      "the term list gives no value of the I95 AffairTypeEnum (I95 has no value other)",
                      "candidate_value": str(aff.get("type_name_de") or aff.get("type_name_fr") or aff.get("type_name_it") or ""),
                      "candidate_source": "affairs.type_name_*"})
    titel = []
    for s in ("de", "fr", "it", "rm"):
        t = aff.get(f"title_{s}")
        if not t:
            continue
        b = ea.beleg_meta(AFFAIRS_FILE, "affair", aid, f"title_{s}", t, abruf)
        fs = ea.fundstellen(t, liste) if s == lang else []
        tv = ea.wert_meta(t, b, pdf_evidence=fs, konsistenz=("confirmed" if fs else "not_found") if s == lang else "not_checked")
        lv = V(s, {"derivation": "normalized_from_metadata", "rule": "language code from the field name title_<language>",
                   "metadata_evidence": [b], "_norm": "feldsprache"})
        titel.append({"text": tv, "text_language": lv,
                      "text_type": V("title", {"derivation": "fixed_by_schema",
                                               "rule": "title of the affair from the export record -> TextTypeEnum title (J4)",
                                               "_enum": ("i95", "TextTypeEnum")})})
    if titel:
        affair["title"] = titel
    else:
        nicht.append({"not_mapped_item": "Affair.title", "not_mapped_reason":
                      "the export record has no title; the writer never takes the title from the PDF (E20 7.6, J4)",
                      "candidate_source": "affairs.title_*"})

    gefunden = ea.daten_im_pdf(liste)

    def step_head(art: str) -> dict:
        iri = f"{NS}affair-{aid}/step/{art}/doc-{d}"
        return {"__entity__": (iri, STEP_CLASS[art]),
                "global_uri": V(iri, {"derivation": "identifier_minted",
                                      "rule": "{namespace}/converter/l9/affair-{id}/step/{step}/doc-{doc_id} (deterministic, "
                                              "provisional namespace)"})}

    # submission
    ev_in, ev_resp = ea.ereignis(meta, ea.EREIGNIS_EINGEREICHT), ea.ereignis(meta, ea.EREIGNIS_BEANTWORTET)
    s_texte, s_date = texte["submission"], None
    if ev_in and ev_in.get("date"):
        b = ea.beleg_meta(EVENTS_FILE, "event", ev_in["id"], "date", ev_in["date"], abruf)
        s_date = ea.datum_wert(ev_in["date"], b, gefunden, "event with title_harmonized_id 1 (submitted)")
    leg = ea.gruppe(meta, "council_legislative")
    steps = {}
    if s_texte or s_date:
        st = step_head("submission")
        if s_date:
            st["submission_date"] = s_date
        if s_texte:
            st["texts"] = [n for n, _ in s_texte]
        if leg:
            nicht.append({"not_mapped_item": "Parliament (chamber)", "not_mapped_reason":
                          "I95 has no slot for the parliament on the affair or on Submission",
                          "candidate_value": f"{ea.OPD}groups/{leg['id']}", "candidate_source": "groups (council_legislative)"})
        steps["submission"] = st
    # response of the executive
    r_texte, r_date = texte["response"], None
    exe = ea.gruppe(meta, "council_executive")
    if ev_resp and ev_resp.get("date"):
        b = ea.beleg_meta(EVENTS_FILE, "event", ev_resp["id"], "date", ev_resp["date"], abruf)
        r_date = ea.datum_wert(ev_resp["date"], b, gefunden, "event with title_harmonized_id 6 (answered)")
    elif r_texte and (doc.get("date") or ""):
        b = ea.beleg_meta(meta["doc_export_file"], "doc", doc["id"], "date", doc["date"], abruf)
        r_date = ea.datum_wert(doc["date"], b, gefunden, "no single response event (title_harmonized_id 6); date "
                                                         "of the response document", "close")
    if r_texte or r_date:
        st = step_head("response")
        if r_date:
            r_date.herkunft["rule"] += "; I95 has no response date: end of the response step (date_end_actual)"
            r_date.herkunft["match"] = "close"
            st["date_end_actual"] = r_date
        if exe and any(exe.get(f) for f in ("name_de", "name_fr", "name_it")):
            st["responder"] = ea.gruppen_referenz(exe, lang or "", "i95", abruf,
                                                  "the only active group council_executive of the parliament")
        if r_texte:
            st["texts"] = [n for n, _ in r_texte]
        steps["response"] = st
    for e in meta["events"]:
        if e.get("title_harmonized_id") in (ea.EREIGNIS_EINGEREICHT, ea.EREIGNIS_BEANTWORTET):
            continue
        nicht.append({"not_mapped_item": f"event {e.get('title_harmonized_de') or e.get('title_de')}",
                      "not_mapped_reason": "not in the scope of this writer (only the submission and the response step)",
                      "candidate_value": (e.get("date") or "")[:10], "candidate_source": f"events {e['id']}"})
    if "submission" in steps:
        affair["submission"] = steps["submission"]
    if "response" in steps:
        affair["response_steps"] = [steps["response"]]
    return affair


def check_values(D, roh: dict, eintraege: list, ohne: list) -> dict:
    """Check 3.6: m06_ech_ausgabe.herkunft_pruefen for all values; the URI form of a URL separately."""
    uri = [e for e in eintraege if e[3].herkunft.get("_norm") == "uri"]
    rest = [e for e in eintraege if e[3].herkunft.get("_norm") != "uri"]
    res = ea.herkunft_pruefen(D, "i95", {"tb_records": []}, rest, ohne)
    for pfad, _, _, v in uri:
        src = v.herkunft["metadata_evidence"][0]["source_value"]
        if v.wert != ea.as_uri(src):
            res["fehler"].append(f"{ea.pfad_text(pfad)}: the URI form differs from as_uri of the export value")
        res["metadaten"] += 1
    return res


def side_file(d: str, run_rec: dict, exp: dict, exp_path: Path, b: dict, eintraege: list, pfade: dict,
              chk: dict) -> dict:
    """The provenance side file (profile version 0.2.0, root class ExtractionRecord)."""
    rec, doc = b["rec"], exp["doc"]
    af = json.loads(iso_path("atome", d).read_text(encoding="utf-8"))
    fp = hashlib.sha256(json.dumps([[a["id"], a["zeichen"]] for a in af["atome"]], separators=(",", ":"))
                        .encode("utf-8")).hexdigest()
    pdf = pdf_path(d)
    run = {"script_name": SCRIPT,
           "decomposition_source": f"converter answers of {rec['runner_version']} (method nos4, isolation level L9): "
                                   f"{rel(run_rec['path'])} (SHA-256 {run_rec['sha256']}); export record {rel(exp_path)} "
                                   f"(SHA-256 {sha256(exp_path)})",
           "decomposition_accepted": False,
           "taxonomy_version": "E20 version 5.0, chapter 7: isolation level L9, map SLOT_NOTITLE, block unit",
           "atom_version": f"{af.get('version', '')} {af.get('erzeugt_utc', '')}".strip(),
           "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": utc_now()}
    src = {"global_uri": b["doc_iri"], "local_id": d}
    if doc.get("url_oparl"):
        src["manifestation_url"] = ea.as_uri(doc["url_oparl"])
    if (doc.get("url") or "").startswith("http"):
        src["publisher_url"] = ea.as_uri(doc["url"])
    if pdf.exists():
        src["file_sha256"] = sha256(pdf)
    if doc.get("hash"):
        src["export_hash"] = doc["hash"]
    src |= {"docling_json_sha256": af.get("quelle_sha256") or "", "atom_fingerprint": fp,
            "page_count": len(json.loads(iso_path("docling", d).read_text(encoding="utf-8"))["seiten"])}
    if b["lang"]:
        src["document_language"] = b["lang"]
        src["document_language_source"] = b["lang_h"].get("rule") or "export (docs.language)"
    else:
        src["document_language_source"] = "no language: the export and the document lists give no language"
    src["document_kind"] = (f"claimed at L9, converter role {rec['converter_role']}" if b["claimed"]
                            else "not claimed at L9")
    by_id = {a["id"]: a for a in b["atoms"]}
    tbr = []
    for r in b["tb_records"]:
        x = {"global_uri": r["global_uri"]}
        if r["mapping_status"] == "in_ech_instance":
            path, ent = pfade[id(r)]
            x |= {"about_entity": ent, "instance_path": path, "ech_slot": f"{STEP_CLASS[r['ziel']]}.texts"}
        else:
            x["about_entity"] = b["affair_iri"] or b["container_iri"]
        x |= {"section_key": r["cls"], "mapping_status": r["mapping_status"]}
        if r.get("not_mapped_reason"):
            x["not_mapped_reason"] = r["not_mapped_reason"]
        x["extent_value_status"] = "unsure"
        x["text_form"] = "richtext"
        if r["mapping_status"] == "profile_only":
            x["text_content"] = r["text"]
        x |= {"char_count": len(r["text"]), "source_document": b["doc_iri"],
              "units": [{"unit_id": f"block-{r['k']}", "unit_type": r["cls"],
                         "atom_evidence": [atom_ev(by_id[a]) for a in r["ids"]]}],
              "text_changes": r["tc"]}
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
    e19 = b["e19"]
    out = {"global_uri": f"{ea.PPD}provenance/converter-l9/i95/affair-{b['aid']}/doc-{d}",
           "describes_delivery": b["container_iri"], "ech_schema_version": ea.FASSUNG_TEXT["i95"],
           "pipeline_run": run, "source_documents": [src], "text_block_records": tbr, "value_records": werte,
           "not_mapped_records": b["nicht"],
           "verbatim_check": {
               "check_method": "Each leaf value needs a ValueRecord. Each text block: its letters (no markup, no white "
                               "space) are the letters of the Docling wording of its atoms after the recorded changes "
                               "only (line-end hyphens, list markers at the atom start, empty atoms, NFC). Metadata "
                               "values against the export record, terms against the enumerations of I95.",
               "text_blocks_checked": e19["text_blocks"], "characters_checked": e19["characters"],
               "hyphens_removed_count": e19["hyphens"], "list_markers_removed_count": e19["markers"],
               "metadata_values_checked": chk["metadaten"], "leaves_without_provenance": len(chk["ohne_herkunft"]),
               "check_passed": not chk["fehler"] and not e19["problems"]}}
    return out


def convert_one(d: str, run_rec: dict, exp: dict, exp_path: Path, out_dir: Path) -> dict:
    b = build(d, run_rec, exp, exp_path)
    eintraege, ohne = [], []
    instanz = ea.entpacken(b["container"], eintraege=eintraege, ohne=ohne)
    pfade = {}
    for pfad, ent, _, v in eintraege:
        if v.herkunft["derivation"] == "extracted_from_pdf":
            pfade[id(v.herkunft["_textblock"]["record"])] = (ea.pfad_text(pfad[:-1]), ent)
    D = SimpleNamespace(meta=exp | {"affair": exp.get("affair") or {"id": None}}, liste=b["liste"], ref={"units": []})
    chk = check_values(D, b, eintraege, ohne)
    prov = side_file(d, run_rec, exp, exp_path, b, eintraege, pfade, chk)
    ip, pp = out_dir / "instances" / f"{d}.yaml", out_dir / "provenance" / f"{d}.yaml"
    ea.schreibe_yaml(ip, instanz, f"# eCH-0295 instance (I95, root class Container), {SCRIPT} ({VERSION}), document {d}\n"
                                  f"# Isolation level L9 (E20 version 5.0, chapter 7). Side file: provenance/{d}.yaml\n")
    ea.schreibe_yaml(pp, prov, f"# Provenance side file (src/m06_ech_profil.yaml version 0.2.0) of instances/{d}.yaml\n")
    in_inst = [r for r in b["tb_records"] if r["mapping_status"] == "in_ech_instance"]
    return {"doc_id": d, "claimed_L9": b["claimed"], "converter_role": b["rec"]["converter_role"],
            "abstention_reason": b["rec"]["claims"][LEVEL]["abstention_reason"],
            "converter_blocks": [c for c, _ in b["blocks"]],
            "textblocks_in_instance": len(in_inst),
            "textblocks_in_instance_by_slot": {s: sum(1 for r in in_inst if r["ziel"] == s) for s in ("submission", "response")},
            "textblock_records_profile_only": sum(1 for r in b["tb_records"] if r["mapping_status"] == "profile_only"),
            "extent_value_status_unsure": len(b["tb_records"]),
            "title_textblocks_from_export": len(instanz.get("affairs", [{}])[0].get("title") or []) if instanz.get("affairs") else 0,
            "leaf_values": len(eintraege), "value_records": len(prov["value_records"]),
            "not_mapped_records": len(prov["not_mapped_records"]),
            "e19": {"text_blocks": b["e19"]["text_blocks"], "characters": b["e19"]["characters"],
                    "hyphens_removed": b["e19"]["hyphens"], "list_markers_removed": b["e19"]["markers"],
                    "problems": len(b["e19"]["problems"])},
            "metadata_check": {"values_checked": chk["metadaten"], "problems": len(chk["fehler"]),
                               "leaves_without_provenance": len(chk["ohne_herkunft"])},
            "check_passed": prov["verbatim_check"]["check_passed"],
            "problems_detail": b["e19"]["problems"] + chk["fehler"],
            "runner_record": {"path": rel(run_rec["path"]), "sha256": run_rec["sha256"]},
            "export_record": {"path": rel(exp_path), "sha256": sha256(exp_path)},
            "instance": {"path": rel(ip), "sha256": sha256(ip)}, "provenance": {"path": rel(pp), "sha256": sha256(pp)}}


def cmd_convert(args) -> int:
    started = clock()
    run_dir, exp_dir, out_dir = Path(args.run).resolve(), Path(args.export).resolve(), Path(args.out).resolve()
    if (out_dir / "convert.json").exists():
        raise SystemExit(f"{rel(out_dir)} has a convert.json: one run only for each output folder")
    run, recs = load_run(run_dir, [str(x) for x in args.doc] if args.doc else None)
    exps = {}
    for d in recs:
        p = exp_dir / f"{d}.json"
        if not p.exists():
            raise SystemExit(f"{d}: no export record in {rel(exp_dir)}")
        exps[d] = (json.loads(p.read_text(encoding="utf-8")), p)
    check_docs(list(recs), [out_dir, exp_dir, run_dir], {d: e[0].get("body_key", "") for d, e in exps.items()})
    rows = []
    for n, d in enumerate(recs, 1):
        row = convert_one(d, recs[d], exps[d][0], exps[d][1], out_dir)
        rows.append(row)
        print(f"{n}/{len(recs)} {d}: claim L9 {row['claimed_L9']}, TextBlocks from the PDF {row['textblocks_in_instance']}, "
              f"check passed {row['check_passed']}", flush=True)
    summary = {"schema": "parlpdfech-converter-ech/1", "status": "NOT RELEASED", "version": VERSION,
               "run_date": started, "finished": clock(),
               "script": {"path": SCRIPT, "sha256": sha256(Path(__file__))},
               "reused_files": {p: sha256(ROOT / p) for p in ("src/m03_gold_record.py", "src/m06_ech_ausgabe.py",
                                                              "src/m03_iso_v4.py", "src/m03_sub_common.py")},
               "profile": {"path": rel(PROFILE), "sha256": sha256(PROFILE)}, "i95": {"path": rel(I95), "sha256": sha256(I95)},
               "ladder_json_sha256": sha256(LADDER_JSON),
               "runner_run": {"path": rel(run_dir / "run.json"), "sha256": sha256(run_dir / "run.json"),
                              "runner_sha256": run["runner"]["sha256"], "cscs_mode": run.get("cscs_mode")},
               "documents": len(rows), "claimed_L9": sum(1 for r in rows if r["claimed_L9"]),
               "all_checks_passed": all(r["check_passed"] for r in rows), "per_document": rows}
    write_json(out_dir / "convert.json", summary)
    code = 0
    if args.validate:
        code = validate(out_dir, [r["doc_id"] for r in rows])
    print(json.dumps({"documents": len(rows), "claimed_L9": summary["claimed_L9"],
                      "all_checks_passed": summary["all_checks_passed"], "convert_json": rel(out_dir / "convert.json"),
                      "sha256": sha256(out_dir / "convert.json")}, indent=1))
    return code if summary["all_checks_passed"] else 2


# ------------------------------------------------------------------ validation (linkml-validate)
def linkml_validate(schema: Path, cls: str, data: Path) -> dict:
    """linkml-validate as src/m06_ech_ausgabe.py calls it (uvx --offline, linkml==1.11.1). Messages stay in the
    result file only (they can hold values of a document)."""
    p = subprocess.run(ea.UVX + ["linkml-validate", "-s", str(schema), "-C", cls, str(data)],
                       capture_output=True, text=True, timeout=900)
    errors = [z for z in p.stdout.splitlines() if z.startswith("[ERROR]")]
    ok = p.returncode == 0 and not errors and "No issues found" in p.stdout
    return {"schema": rel(schema), "class": cls, "file": rel(data), "sha256": sha256(data), "valid": ok,
            "errors": len(errors), "messages": [z[:400] for z in errors] or ([] if ok else p.stderr.strip().splitlines()[-3:])}


def validate(out_dir: Path, docs: list[str] | None = None) -> int:
    out_dir = Path(out_dir).resolve()
    docs = docs or sorted(p.stem for p in (out_dir / "instances").glob("*.yaml"))
    jobs = [(d, "instance", I95, "Container", out_dir / "instances" / f"{d}.yaml") for d in docs]
    jobs += [(d, "provenance", PROFILE, "ExtractionRecord", out_dir / "provenance" / f"{d}.yaml") for d in docs]
    with ThreadPoolExecutor(max_workers=4) as pool:
        res = list(pool.map(lambda j: {"doc_id": j[0], "kind": j[1]} | linkml_validate(j[2], j[3], j[4]), jobs))
    out = {"schema": "parlpdfech-converter-validation/1", "run_date": clock(), "linkml": ea.LINKML,
           "files": len(res), "valid": sum(1 for r in res if r["valid"]), "results": res}
    write_json(out_dir / "validation.json", out)
    print(json.dumps({"files": len(res), "valid": out["valid"],
                      "per_document": {d: {r["kind"]: r["valid"] for r in res if r["doc_id"] == d} for d in docs},
                      "validation_json": rel(out_dir / "validation.json")}, indent=1))
    return 0 if out["valid"] == len(res) else 2


def cmd_validate(args) -> int:
    return validate(Path(args.out), [str(x) for x in args.doc] if args.doc else None)


def main() -> None:
    ap = argparse.ArgumentParser(description="converter eCH writer (isolation level L9)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export")
    p.add_argument("--out", required=True)
    p.add_argument("docs", nargs="+")
    p = sub.add_parser("convert")
    p.add_argument("--run", required=True)
    p.add_argument("--export", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--doc", nargs="*")
    p.add_argument("--validate", action="store_true")
    p = sub.add_parser("validate")
    p.add_argument("--out", required=True)
    p.add_argument("--doc", nargs="*")
    a = ap.parse_args()
    sys.exit({"export": cmd_export, "convert": cmd_convert, "validate": cmd_validate}[a.cmd](a))


if __name__ == "__main__":
    main()
