"""Gate GJ (status EXCEPTION), plan chapters 5.1 and 5.2: the command from one PDF file to the RDF files of one
document, and the fresh Docling check of plan chapter 5.2 item 2.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream CLI,
for the main agent; step 6 with src/m10_pipeline.py (--apertus stored): stream D of workflow wf_d5120f1f-fd4
(wave 3). Stream X2 of the last change round before the design freeze (13.10.2026) added src/m10_gaps.py to the
run record. Phases 4 and 6, gate GJ (OPEN). Status: EXCEPTION (process rule 10), NOT RELEASED. This file
changes no existing file. The command convert writes only below <out>/<doc>/. The command check-docling writes only
below daten/gj/cli/. No network, no VM, no MLX, no CSCS.

1 Command convert (plan chapter 5.2)
  Input: one PDF file and its OpenParlData doc id (plan chapter 5.1).
  1. Guard (src/m10_guard.py): the doc id (rules G1 to G9: no test document, no unknown id, split dev, validation
     or group 7), the path of the PDF (no folder of test documents) and the SHA-256 of the PDF. The SHA-256 must be
     equal to the value of the stored Docling output and of the lists. The writer accepts only the documents of
     daten/gj/sets.json and of the run record daten/gj/docs_build.json (2,665 documents), so this file refuses
     other documents before step 2. A validation document or a group-7 document is refused before the freeze
     (criteria chapters 3 and 10.3): the freeze file (daten/gj/design_freeze.json for validation,
     daten/gj/freeze_manifest.json for group 7) must exist and name the SHA-256 of this file, of
     src/m10_cascade.py, of src/m10_calibrate.py and of the floor calibration file. The modes that cannot run
     (item 6) stop here too, before Docling.
  2. Docling and atoms. --docling fresh (default): the unchanged function main of src/m03_docling_zerlegen.py with
     the settings of the 2,665 stored outputs (chapter 3), then the unchanged function dokument of
     src/m03_atome.py with the version atome-v3 (as src/m03_gold_prepare.py does it). --docling stored: the stored
     outputs daten/iso/docling/<doc>.json and daten/iso/atome/<doc>.json after the SHA-256 check of item 1 (plan
     chapter 4 item 1).
  3. The block file of interface 2 through the functions of src/m10_docs.py (doc_text, block_spans, check_doc,
     build_one for --docling stored).
  4. Comparison of the fresh outputs with the stored outputs (only counts, ids and equality, as chapter 2 item 3).
  5. Rules: run_document of src/m10_rules.py (frozen nos4 chain, no CSCS) after its identity record check.
  6. Decisions (interface 7) through decide() of src/m10_pipeline.py. --apertus none: the floor mode (floor
     converter F1, floor_decisions() of src/m10_cascade.py). --apertus stored: the cascade mode with the frozen
     design: the design freeze file daten/gj/design_freeze.json must exist and name the SHA-256 of
     src/m10_pipeline.py, src/m10_cascade.py and src/m10_design.py (load_design() of src/m10_pipeline.py); the
     states file <states-dir>/states/<doc>.npz must exist (--states-dir: the job folder of the states, for example
     daten/gj/states/gpu1_labelled); --entry-d1 and --entry-b12 give the entry decisions. The states belong to
     the stored block file: the block file of step 3 must be equal to daten/gj/docs/<doc>.json (without the key
     source_files), else the command stops (with --docling fresh, the comparison of step 4 gives this). The rule
     record of step 5 and the block file of step 3 go to the design (no stored file of the document is read in
     steps 5 to 7). Output: work/decisions/<doc>.json and work/calibrations.json (the calibration file of a
     cascade run, chapter 2 of src/m10_pipeline.py). Without one of these inputs the command stops with a message
     before step 2. R2 is not in this command (r2 None). --apertus vm: not implemented; the command stops with a
     message.
  7. Writer, RDF step and validator: write_one of src/m10_writer.py, convert_record of src/m10_rdf.py and
     validate_record of src/m10_validate.py.
  With --docling fresh, steps 5 to 7 read the fresh files: for the time of these steps, the name iso_path in each
  loaded module, the folders of the writer and of the RDF step and the input files of the rules point to the fresh
  files of this document. A read guard stops the run if a step opens a stored file of this document
  (daten/iso/<kind>/<doc>.*, daten/gj/docs/<doc>.json) or a file in a folder of test documents.
  Output: <out>/<doc>/ with the files of the writer, of the RDF step and of the validator (plan chapter 5.3), and
  convert.json: the run record (SHA-256 of this file first, then the SHA-256 of all inputs and outputs, the clock
  times and the time of each step; at the end the FROZEN_FILES check of src/m05_gate3a_v4_measure.py, the SHA-256
  of the criteria file and the check that no script changed during the run). Work files: <out>/<doc>/work/.
  The folder <out> must be in the project folder, because src/m03_atome.py writes paths relative to it.

2 Command check-docling (plan chapter 5.2 item 2)
  1. Selection (fixed before the run): the validation documents of the run record daten/gj/docs_build.json whose
     PDF is at the explicit path daten/pdf/bulk/<doc>.pdf and whose stored Docling output names this path, with
     --max-pages pages or less. The guard allows each document first. Sort the parliaments by body key. Take the
     lowest doc id of each parliament, then the second lowest of each parliament, until there are --n documents.
     If no selected document used the fallback backend pypdfium2 and a candidate with this backend exists, the
     lowest such candidate replaces the last selected document.
  2. Docling runs again on the PDF files into daten/gj/cli/docling_check/docling/ (one call of main, with the warm-up
     of the stored runs), then the atoms and the block files. The stored files are not changed.
  3. Comparison with the stored Docling output, the stored atoms and the stored block file of each document: block
     count, block ids, block texts, Docling labels, pages, block spans, the whole text, atom ids, atom spans, atom
     texts and the block file of interface 2. The check reads no label and no model output. It gives no method
     value. The console and the record show ids and counts only, no text.
  4. Output: daten/gj/cli/docling_check/check.json (selection, guard, settings, time for each document, result,
     and the end checks of the command convert).

3 Settings of the stored Docling outputs (all 2,665 files of daten/iso/docling, 12.10.2026)
  ocr auto (ocrmac, Apple Vision, accurate), device auto (layout model on MPS), 4 threads, accurate tables, cell
  matching on, OCR languages de-DE, fr-FR, it-IT, en-US, backend docling-parse with the fallback backend pypdfium2
  for pages in one colour (19 documents), document timeout 900 s. Tools: docling 2.133.0, docling-core 2.99.0,
  docling-parse 7.22.1, docling-ibm-models 4.0.3, torch 2.14.1, ocrmac 1.0.1, pdftotext 26.04.0. Atoms: atome-v3.
  --device cpu is possible, but it is not the setting of the stored outputs.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_convert.py --pdf FILE --doc-id ID
      --apertus none|stored|vm [--states-dir DIR --entry-d1 yes|no --entry-b12 yes|no] --out DIR
      [--base https://parlpdfech.ansv.ch/id/] [--docling fresh|stored] [--device auto] [--allow-final-group7]
  uv run --offline --frozen --no-sync python src/m10_convert.py check-docling [--n 10] [--max-pages 40]
"""

from __future__ import annotations

import argparse
import builtins
import contextlib
import csv
import hashlib
import io
import json
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_docs as docs_text  # noqa: E402  (interface 2, stream B)
import m10_guard as guard  # noqa: E402  (split guard of process rule 6, stream B)

VERSION = "m10-convert-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = ROOT / "daten/gj"
CLI = GJ / "cli"
CHECK_DIR = CLI / "docling_check"
DOCS_BUILD = GJ / "docs_build.json"
SETS = GJ / "sets.json"
STORED_RULES = GJ / "rules"
DESIGN_FREEZE = GJ / "design_freeze.json"
BULK = ROOT / "daten/pdf/bulk"
DEFAULT_BASE = "https://parlpdfech.ansv.ch/id/"
STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
ATOMS_VERSION = "atome-v3"
ISO_KINDS = {"atome": "json", "docling": "json", "atome_prompt": "txt"}
LANGUAGES = "de-DE,fr-FR,it-IT,en-US"
STORED_SETTINGS = {"ocr": "auto", "ocr_engine": "ocrmac (Apple Vision, accurate)",
                   "ocr_sprachen": ["de-DE", "fr-FR", "it-IT", "en-US"], "geraet": "auto", "threads": 4,
                   "tabellen": "genau", "zellabgleich": True, "backend": "docling-parse",
                   "layout_modell": "layout_heron", "document_timeout_s": 900}
STORED_TOOLS = {"docling": "2.133.0", "docling-core": "2.99.0", "docling-parse": "7.22.1",
                "docling-ibm-models": "4.0.3", "torch": "2.14.1", "ocrmac": "1.0.1",
                "pdftotext": "pdftotext version 26.04.0"}
FALLBACK_BACKEND = "pypdfium2 (Ersatz)"
# folders of test documents: a read in these folders stops a run (process rule 6)
TEST_FOLDERS = ("daten/gold/test/", "daten/pdf/test_dokumente/", "daten/pdf/blind_final/",
                "daten/cls/final_prep/sealed/", "daten/score26/")
TEACHER = "daten/pdf/lehrer_stichprobe/"


class Stop(RuntimeError):
    """The command stops with a message (refusal or failed check)."""


# ------------------------------------------------------------------ small helpers
def sha256(p: Path) -> str:
    return guard.sha256_file(Path(p))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel(p: Path) -> str:
    return guard.rel(Path(p))


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def script_record() -> dict:
    """The SHA-256 of this file and of the m10 files it imports (first entry of each run record). The writer, the
    RDF step and the validator import src/m10_gaps.py (addendum A to the criteria), so the record names it."""
    out = {rel(SCRIPT): sha256(SCRIPT)}
    for name in ("m10_guard", "m10_docs", "m10_rules", "m10_pipeline", "m10_cascade", "m10_calibrate", "m10_design",
                 "m10_writer", "m10_rdf", "m10_validate", "m10_gaps", "m03_docling_zerlegen", "m03_atome"):
        p = SCRIPT.parent / f"{name}.py"
        if p.exists():
            out[rel(p)] = sha256(p)
    return out


def end_checks(rec: dict) -> dict:
    """GJ.4 and GJ.2 facts at the end of a run: the FROZEN_FILES of src/m05_gate3a_v4_measure.py (function of
    src/m10_calibrate.py), the SHA-256 of the criteria file, and the scripts of the run record unchanged."""
    import m10_calibrate as cal
    crit = {"path": rel(cal.CRITERIA), "sha256": sha256(cal.CRITERIA), "value_of_the_protocol": cal.CRITERIA_SHA}
    return {"frozen_files": cal.frozen_files(), "criteria": crit | {"equal": crit["sha256"] == cal.CRITERIA_SHA},
            "scripts_unchanged": script_record() == rec["script"]}


def files_info(paths: dict) -> dict:
    return {k: {"path": rel(p), "sha256": sha256(p)} for k, p in paths.items() if p is not None and Path(p).exists()}


# ------------------------------------------------------------------ step 1: guard
def built_ids() -> set[str]:
    """The doc ids of the block files of src/m10_docs.py (run record daten/gj/docs_build.json)."""
    return {Path(p).stem for p in (read_json(DOCS_BUILD).get("outputs") or {})}


def guard_document(d: str, pdf: Path, allow_final_group7: bool = False) -> dict:
    """Guard of step 1. Stops on each refusal. Reads the PDF bytes only after the guard allows the doc id."""
    d = str(d).strip()
    try:
        g = guard.assert_allowed([d])
        guard.check_path(pdf, d)
    except guard.GuardRefusal as e:
        raise Stop(f"refused by src/m10_guard.py: {e}") from None
    if not Path(pdf).is_file():
        raise Stop(f"{d}: the PDF file {rel(pdf)} does not exist")
    if d not in built_ids():
        raise Stop(f"{d}: not in daten/gj/docs_build.json: the writer accepts only the 2,665 documents of the run "
                   f"record of src/m10_docs.py (refused)")
    import m03_iso_v4 as v4           # final_docs = the 8 documents of the final group 7 of gate 3a version 3
    if d in v4.final_docs() and not allow_final_group7:
        raise Stop(f"{d}: document of the final group 7 of gate 3a version 3: only with --allow-final-group7 "
                   f"(the rules refuse it else)")
    pc = guard.check_pdf(d, Path(pdf))
    if not pc["equal"]:
        raise Stop(f"{d}: the SHA-256 of the PDF is not the value of the stored Docling output or of the lists "
                   f"(refused)")
    return {"doc_id": d, "split": g["split_of"][d], "parliament": g["parliament_of"][d], "pdf": pc,
            "guard_summary": {k: v for k, v in g.items() if k not in ("split_of", "parliament_of")},
            "guard_tables": guard.tables().sources}


# ------------------------------------------------------------------ read guard (process rule 6, fresh inputs)
@contextlib.contextmanager
def read_guard(d: str | None, block_stored: bool):
    """Records each opened file in a folder of test documents, and (block_stored) each opened stored file of the
    document d. The caller stops the run if the list is not empty. The file names in the list are paths only."""
    hits: list[str] = []
    stored = set()
    if d is not None and block_stored:
        stored = {(ROOT / "daten/iso" / k / f"{d}.{e}").resolve() for k, e in ISO_KINDS.items()}
        stored |= {(GJ / "docs" / f"{d}.json").resolve()}
    orig = builtins.open

    def check(file) -> None:
        if not isinstance(file, (str, os.PathLike)):
            return
        s = os.fspath(file)
        if isinstance(s, bytes) or "daten" not in s:
            return
        r = rel(Path(s))
        if any(f in r + ("/" if not r.endswith("/") else "") for f in TEST_FOLDERS):
            hits.append(r)
        elif r.startswith(TEACHER) and (d is None or Path(r).name != f"{d}.pdf"):
            hits.append(r)
        elif stored and Path(s).resolve() in stored:
            hits.append(r)

    def guarded_open(file, *a, **k):
        check(file)
        return orig(file, *a, **k)

    builtins.open = guarded_open
    io.open = guarded_open
    try:
        yield hits
    finally:
        builtins.open = orig
        io.open = orig


# ------------------------------------------------------------------ step 2: Docling and atoms
def tool_versions() -> dict:
    import m03_docling_zerlegen as dz
    return dz.versionen()


def docling_main(pdfs: list[Path], out_dir: Path, record_dir: Path, name: str, device: str, warmup: bool) -> dict:
    """The unchanged function main of src/m03_docling_zerlegen.py for the PDF files. Its run files go to
    record_dir (the module constant ANALYSE points there for the time of the call)."""
    import m03_docling_zerlegen as dz
    out_dir.mkdir(parents=True, exist_ok=True)
    record_dir.mkdir(parents=True, exist_ok=True)
    argv = [str(dz.__file__), *[str(p) for p in pdfs], "--ocr", "auto", "--geraet", device, "--threads", "4",
            "--tabellen", "genau", "--zellabgleich", "an", "--sprachen", LANGUAGES, "--name", name,
            "--ausgabe", str(out_dir)]
    if not warmup:
        argv.append("--ohne-aufwaermen")
    old_argv, old_analyse = sys.argv, dz.ANALYSE
    sys.argv, dz.ANALYSE = argv, record_dir
    t0 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(sys.stderr):      # the console lines of main go to stderr
            dz.main()
    finally:
        sys.argv, dz.ANALYSE = old_argv, old_analyse
    seconds = time.perf_counter() - t0
    with open(record_dir / f"lauf_{name}.csv", newline="", encoding="utf-8") as f:
        rows = {r["doc_id"]: r for r in csv.DictReader(f)}
    summary = read_json(record_dir / f"lauf_{name}.json")
    return {"arguments": argv[1:], "rows": rows, "summary": summary, "seconds": round(seconds, 3),
            "files": {rel(record_dir / f"lauf_{name}.csv"): sha256(record_dir / f"lauf_{name}.csv"),
                      rel(record_dir / f"lauf_{name}.json"): sha256(record_dir / f"lauf_{name}.json")}}


def atoms_of_docling(d: str, docling_json: Path, pdf_dir: Path, atoms_dir: Path, prompt_dir: Path) -> dict:
    """atome-v3 through the unchanged function dokument of src/m03_atome.py (as src/m03_gold_prepare.py). The PDF
    must be <pdf_dir>/<d>.pdf (text layer of pdftotext)."""
    import m03_atome as at
    atoms_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    old = at.PDF, at.DOCLING
    at.PDF, at.DOCLING = Path(pdf_dir).resolve(), Path(docling_json).parent.resolve()
    t0 = time.perf_counter()
    try:
        aus, zeile = at.dokument(Path(docling_json).resolve(), None, at.VERSION_V3)
    finally:
        at.PDF, at.DOCLING = old
    ap = atoms_dir / f"{d}.json"
    ap.write_text(json.dumps(aus, ensure_ascii=False, indent=1), encoding="utf-8")
    pp = prompt_dir / f"{d}.txt"
    pp.write_text(at.prompt_text(aus["atome"], mit_legende=True, fassung=at.VERSION_V3), encoding="utf-8")
    return {"atoms": ap, "prompt": pp, "status": zeile.get("status"), "complete": zeile.get("vollstaendig"),
            "atom_count": int(zeile.get("atome") or 0), "seconds": round(time.perf_counter() - t0, 3)}


# ------------------------------------------------------------------ step 3: block file (interface 2)
def block_file(d: str, split: str, parliament: str, docling_p: Path, atoms_p: Path, pdf: Path) -> dict:
    """The block file of interface 2 from a Docling output and its atoms, with the checks and the functions of
    src/m10_docs.py (as build_one, for files at any path)."""
    import m05_cls_data as cd
    db, ab = Path(docling_p).read_bytes(), Path(atoms_p).read_bytes()
    dk, at = json.loads(db), json.loads(ab)
    if str(dk.get("doc_id")) != d or str(at.get("doc_id")) != d:
        raise Stop(f"{d}: the doc id of the Docling output or of the atoms differs")
    if dk.get("status") != "success" or at.get("status") != "success":
        raise Stop(f"{d}: Docling output or atoms without the status success")
    if dk.get("gesamttext_trenner") != docs_text.SEP:
        raise Stop(f"{d}: other block separator in the Docling output")
    if at.get("version") != ATOMS_VERSION or at.get("quelle_sha256") != sha256_bytes(db):
        raise Stop(f"{d}: the atoms are not {ATOMS_VERSION} of this Docling output")
    if (at.get("textschicht") or {}).get("pdf_sha256") != dk.get("sha256"):
        raise Stop(f"{d}: the atoms did not read the text layer of the PDF of the Docling output")
    blocks = dk["bloecke"]
    if [b["id"] for b in blocks] != [f"B{i}" for i in range(1, len(blocks) + 1)]:
        raise Stop(f"{d}: the block ids are not B1..Bn in order")
    atoms_of: dict[str, list[str]] = defaultdict(list)
    for x in at["atome"]:
        atoms_of[x["block"]].append(x["id"])
    if set(atoms_of) != {b["id"] for b in blocks}:
        raise Stop(f"{d}: the blocks of the atoms and the Docling blocks differ")
    text = docs_text.doc_text(blocks)
    if text != dk["text_gesamt"]:
        raise Stop(f"{d}: doc_text differs from text_gesamt")
    spans = docs_text.block_spans(blocks)
    if any(list(sp) != list(b["zeichen"]) for b, sp in zip(blocks, spans)):
        raise Stop(f"{d}: a block span differs from the Docling key zeichen")
    lang = cd.language(text)
    out = {"doc_id": d, "parliament": parliament, "split": split, "pdf_sha256": dk["sha256"],
           "language": None if lang == "unk" else lang,
           "blocks": [{"block": b["id"], "page": int(b["seite"]), "docling_label": b["label"], "text": b["text"],
                       "atoms": atoms_of[b["id"]], "char_start": s, "char_end": e}
                      for b, (s, e) in zip(blocks, spans)],
           "source_files": {rel(docling_p): sha256_bytes(db), rel(atoms_p): sha256_bytes(ab), rel(pdf): sha256(pdf)}}
    docs_text.check_doc(out)
    return out


# ------------------------------------------------------------------ step 4: comparison with the stored outputs
def _first(ids: list[str], k: int = 5) -> list[str]:
    return ids[:k]


def compare_outputs(d: str, fresh: dict, stored: dict) -> dict:
    """fresh, stored: {"docling": dict, "atoms": dict, "block_file": dict or None}. Counts and ids only."""
    fd, sd = fresh["docling"], stored["docling"]
    fb, sb = fd["bloecke"], sd["bloecke"]
    res: dict = {"doc_id": d}
    res["status"] = {"fresh": fd.get("status"), "stored": sd.get("status")}
    res["backend"] = {"fresh": fd.get("backend"), "stored": sd.get("backend")}
    res["pages"] = {"fresh": len(fd.get("seiten") or []), "stored": len(sd.get("seiten") or [])}
    res["page_sizes_equal"] = [(p["breite"], p["hoehe"]) for p in fd.get("seiten") or []] == \
        [(p["breite"], p["hoehe"]) for p in sd.get("seiten") or []]
    res["block_count"] = {"fresh": len(fb), "stored": len(sb)}
    res["block_ids_equal"] = [b["id"] for b in fb] == [b["id"] for b in sb]
    n = min(len(fb), len(sb))
    by = {"text": [], "label": [], "page": [], "span": [], "bbox": [], "text_source": []}
    for x, y in zip(fb[:n], sb[:n]):
        if x["text"] != y["text"]:
            by["text"].append(x["id"])
        if x["label"] != y["label"]:
            by["label"].append(x["id"])
        if x.get("seite") != y.get("seite"):
            by["page"].append(x["id"])
        if list(x["zeichen"]) != list(y["zeichen"]):
            by["span"].append(x["id"])
        if x.get("bbox") != y.get("bbox"):
            by["bbox"].append(x["id"])
        if x.get("text_quelle") != y.get("text_quelle"):
            by["text_source"].append(x["id"])
    res["blocks_different"] = {k: {"count": len(v), "first": _first(v)} for k, v in by.items()}
    res["whole_text_equal"] = fd.get("text_gesamt") == sd.get("text_gesamt")
    res["whole_text_chars"] = {"fresh": len(fd.get("text_gesamt") or ""), "stored": len(sd.get("text_gesamt") or "")}
    fa, sa = fresh["atoms"]["atome"], stored["atoms"]["atome"]
    res["atom_count"] = {"fresh": len(fa), "stored": len(sa)}
    res["atom_ids_equal"] = [a["id"] for a in fa] == [a["id"] for a in sa]
    ab = {"span": [], "text": [], "page": [], "line_box": [], "features": []}
    if res["atom_ids_equal"]:
        for x, y in zip(fa, sa):
            if list(x["zeichen"]) != list(y["zeichen"]):
                ab["span"].append(x["id"])
            if x.get("text") != y.get("text"):
                ab["text"].append(x["id"])
            if x.get("seite") != y.get("seite"):
                ab["page"].append(x["id"])
            if x.get("zeilenrahmen") != y.get("zeilenrahmen"):
                ab["line_box"].append(x["id"])
            if x.get("merkmale") != y.get("merkmale"):
                ab["features"].append(x["id"])
    else:
        fi, si = [a["id"] for a in fa], [a["id"] for a in sa]
        res["atom_ids_only_fresh"] = {"count": len(set(fi) - set(si)), "first": _first(sorted(set(fi) - set(si)))}
        res["atom_ids_only_stored"] = {"count": len(set(si) - set(fi)), "first": _first(sorted(set(si) - set(fi)))}
    res["atoms_different"] = {k: {"count": len(v), "first": _first(v)} for k, v in ab.items()}
    res["atoms_complete"] = {"fresh": (fresh["atoms"].get("pruefung") or {}).get("vollstaendig"),
                             "stored": (stored["atoms"].get("pruefung") or {}).get("vollstaendig")}
    if fresh.get("block_file") is not None and stored.get("block_file") is not None:
        x = {k: v for k, v in fresh["block_file"].items() if k != "source_files"}
        y = {k: v for k, v in stored["block_file"].items() if k != "source_files"}
        res["block_file_equal"] = x == y
    # kinds of difference (the 5 items of the task first, then the information items)
    kinds = []
    if res["block_count"]["fresh"] != res["block_count"]["stored"]:
        kinds.append("block_count")
    if not res["block_ids_equal"]:
        kinds.append("block_ids")
    if by["text"]:
        kinds.append("block_texts")
    if not res["atom_ids_equal"]:
        kinds.append("atom_ids")
    if by["span"] or ab["span"] or not res["whole_text_equal"]:
        kinds.append("character_spans")
    if ab["text"]:
        kinds.append("atom_texts")
    info = []
    for k in ("label", "page", "bbox", "text_source"):
        if by[k]:
            info.append(f"block_{k}")
    for k in ("page", "line_box", "features"):
        if ab[k]:
            info.append(f"atom_{k}")
    if res["status"]["fresh"] != res["status"]["stored"]:
        info.append("status")
    if res["backend"]["fresh"] != res["backend"]["stored"]:
        info.append("backend")
    if res["pages"]["fresh"] != res["pages"]["stored"] or not res["page_sizes_equal"]:
        info.append("pages")
    if res.get("block_file_equal") is False:
        info.append("block_file")
    res["result"] = "equal" if not kinds else "different"
    res["kinds"] = kinds
    res["other_differences"] = info
    return res


def stored_outputs(d: str) -> dict | None:
    """The stored Docling output, atoms and block file of d (explicit paths), or None if one is missing."""
    try:
        dp, ap = guard.iso_file("docling", d), guard.iso_file("atome", d)
    except guard.GuardRefusal:
        return None
    bp = GJ / "docs" / f"{d}.json"
    return {"docling": read_json(dp), "atoms": read_json(ap), "block_file": read_json(bp) if bp.exists() else None,
            "files": {"docling": {"path": rel(dp), "sha256": sha256(dp)}, "atoms": {"path": rel(ap), "sha256": sha256(ap)},
                      "block_file": {"path": rel(bp), "sha256": sha256(bp)} if bp.exists() else None}}


# ------------------------------------------------------------------ fresh inputs for steps 5 to 7
def clear_caches() -> None:
    """The caches of the rule chain that hold atoms of a document (m03_ladder, m03_iso_v4)."""
    for modname, names in (("m03_iso_v4", ("atoms_of",)), ("m03_ladder", ("fixed_idx", "carried"))):
        mod = sys.modules.get(modname)
        for n in names:
            f = getattr(mod, n, None) if mod else None
            if hasattr(f, "cache_clear"):
                f.cache_clear()
    lad = sys.modules.get("m03_ladder")
    cache = getattr(lad, "_CARRIED_CACHE", None) if lad else None
    if isinstance(cache, dict):
        cache.clear()


@contextlib.contextmanager
def fresh_inputs(d: str, files: dict):
    """For the time of steps 5 to 7: iso_path(kind, d) gives the fresh file of the kind for this document (all other
    documents and kinds keep the stored path). The explicit folders of src/m10_writer.py and src/m10_rdf.py and the
    input files of src/m10_rules.py point to the fresh files. files: {"atome", "docling", "atome_prompt"} -> Path."""
    import m03_iso_paths as ip
    import m10_rdf as rdf
    import m10_rules as rules
    import m10_writer as writer
    orig = ip.iso_path

    def redirected(kind: str, doc_id: str, ext: str = "json") -> Path:
        if str(doc_id) == d and kind in files and ext == ISO_KINDS[kind]:
            return Path(files[kind])
        return orig(kind, doc_id, ext)

    patched = [m for m in list(sys.modules.values()) if m is not None and getattr(m, "iso_path", None) is orig]
    consts = [(writer, "ATOMS_DIR", Path(files["atome"]).parent), (writer, "DOCLING_DIR", Path(files["docling"]).parent),
              (rdf, "ATOMS_DIR", Path(files["atome"]).parent)]
    saved = [(m, n, getattr(m, n)) for m, n, _ in consts]
    orig_input_files = rules.input_files

    def input_files(x: str) -> dict:
        if str(x) != d:
            return orig_input_files(x)
        return {k: {"path": rel(files[k]), "sha256": sha256(files[k])} for k in ("atome", "docling")}

    for m in patched:
        m.iso_path = redirected
    for m, n, v in consts:
        setattr(m, n, v)
    rules.input_files = input_files
    clear_caches()
    try:
        yield {"modules": sorted(m.__name__ for m in patched)}
    finally:
        for m in list(sys.modules.values()):    # also the modules that were imported during the context
            if m is not None and getattr(m, "iso_path", None) is redirected:
                m.iso_path = orig
        for m, n, v in saved:
            setattr(m, n, v)
        rules.input_files = orig_input_files
        clear_caches()


# ------------------------------------------------------------------ step 5: rules
def rules_record(d: str, allow_final_group7: bool, fresh: bool, force_loader: bool = False) -> dict:
    """run_document of src/m10_rules.py for one document (identity record checked first, no CSCS). force_loader
    (check script only): a known document runs as a loader document also with equal atoms."""
    import m03_sub_common as sc
    import m05_iso_runner as runner
    import m10_rules as rules
    ident = rules.check_identity_record()
    frozen = runner.check_frozen_method()
    exports, split, kind = rules.admit_all([d], allow_final=allow_final_group7)
    admission = kind[d]
    hidden = None
    docs = sc.load()
    if fresh and admission == "known":
        # the loaded record of d comes from the stored atoms; with other fresh atoms the document runs as a
        # loader document (m10_rules chapter 4 item 2) and the loaded record is put back after the run
        import m03_iso_v4 as v4
        if force_loader or [a["id"] for a in v4.atoms_of(d)] != docs[d].ids or v4.fixed_answers(d) != docs[d].fixed:
            hidden = docs.pop(d)
            admission = "loader"
    try:
        rec = rules.run_document(d, exports[d], admission, split[d])
    finally:
        if hidden is not None:
            docs[d] = hidden
    return {"record": rec, "identity_record": ident, "frozen_method": frozen, "admission": admission,
            "loaded_record_hidden": hidden is not None}


def compare_rules(rec: dict, d: str) -> dict:
    """The rule record against the stored rule file daten/gj/rules/<d>.json, without the input files and the
    admission kind (run facts)."""
    p = STORED_RULES / f"{d}.json"
    if not p.exists():
        return {"stored_file": None, "equal": None}
    st = read_json(p)
    skip = {"inputs", "admission"}
    a = {k: v for k, v in rec.items() if k not in skip}
    b = {k: v for k, v in st.items() if k not in skip}
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return {"stored_file": {"path": rel(p), "sha256": sha256(p)}, "equal": not diff, "different_keys": diff}


# ------------------------------------------------------------------ step 6: decisions (interface 7)
def decisions(d: str, mode: str, block_doc: dict, rules_rec: dict, work: Path, states_dir: Path | None,
              entry: tuple[str | None, str | None] = (None, None)) -> dict:
    """The decisions file and the calibration file of the mode. Returns {"decisions": path, "calibrations": path,
    "info": {...}}."""
    check_mode(d, mode, states_dir, entry)
    if mode == "stored":
        return cascade_stored(d, block_doc, rules_rec, work, states_dir, entry)
    return floor(d, rules_rec, work)


def pipeline_module():
    try:
        import m10_pipeline as pipeline
    except ImportError as e:
        raise Stop(f"step 6 needs src/m10_pipeline.py ({e})") from None
    return pipeline


def check_mode(d: str, mode: str, states_dir: Path | None, entry: tuple[str | None, str | None] = (None, None)) -> None:
    """Stops for the modes that cannot run now (the command calls it before step 2 and again in step 6)."""
    if mode == "vm":
        raise Stop("--apertus vm is not implemented yet: the VM job of this command does not exist (use --apertus "
                   "none, or --apertus stored after the design freeze)")
    if mode == "stored":
        if states_dir is None:
            raise Stop("--apertus stored needs --states-dir")
        pipeline = pipeline_module()
        try:
            job = pipeline.find_states(d, states_dir)
        except pipeline.PipelineRefusal as e:
            raise Stop(f"--apertus stored: {e}") from None
        if job is None:
            raise Stop(f"--apertus stored: no states file {rel(Path(states_dir))}/states/{d}.npz for this document "
                       f"(--states-dir is the job folder of the states, for example daten/gj/states/gpu1_labelled)")
        if not DESIGN_FREEZE.is_file():
            raise Stop(f"--apertus stored: the frozen design files do not exist yet ({rel(DESIGN_FREEZE)} is missing; "
                       f"criteria chapter 10.1). The command does not use states before the design freeze.")
        if None in entry:
            raise Stop("--apertus stored needs --entry-d1 and --entry-b12 (the entry decisions of criteria chapter 7)")
        try:
            pipeline.load_design(None, DESIGN_FREEZE, require_freeze=True)
        except pipeline.PipelineRefusal as e:
            raise Stop(f"--apertus stored: {e}") from None
    elif entry != (None, None):
        raise Stop("--entry-d1 and --entry-b12 are only for --apertus stored")


def floor_calibration_file() -> Path:
    import m10_calibrate as cal
    return cal.FLOOR_FILE


def floor(d: str, rules_rec: dict, work: Path, cal_file: Path | None = None) -> dict:
    """Floor converter F1 (criteria 7.4): decide() of src/m10_pipeline.py with the mode floor (floor_decisions and
    check_decisions of src/m10_cascade.py) and the calibration file of src/m10_calibrate.py floor-fit (key
    floor_lookup; the key calibrations is the file format of the writer)."""
    pipeline = pipeline_module()
    import m10_calibrate as cal
    import m10_cascade as cascade
    cal_file = Path(cal_file or cal.FLOOR_FILE)
    try:
        fl = pipeline.load_floor(cal_file)
        dec = pipeline.decide(d, "floor", None, None, False, False, None, floor=fl, rules=rules_rec)
    except pipeline.PipelineRefusal as e:
        raise Stop(f"--apertus none: {e}") from None
    p = work / "decisions" / f"{d}.json"
    write_json(p, dec)
    info = {"pipeline": {"path": rel(pipeline.SCRIPT), "sha256": sha256(pipeline.SCRIPT), "version": pipeline.VERSION},
            "cascade": {"path": rel(Path(cascade.__file__)), "sha256": sha256(Path(cascade.__file__)),
                        "version": cascade.VERSION},
            "calibrate": {"path": rel(Path(cal.__file__)), "sha256": sha256(Path(cal.__file__)), "version": cal.VERSION},
            "calibration_file": fl.info, "in_sample": d in fl.fit_docs}
    stored = cascade.OUT_DIR / f"{d}.json"
    if stored.is_file():           # information: the decisions of the cascade run of stream D (dev only)
        a, b = read_json(stored), dec
        skip = ("calibration", "cascade")          # provenance: the calibration file and the SHA-256 of the script
        info["equal_to_stored_floor_decisions"] = {
            "path": rel(stored), "sha256": sha256(stored),
            "equal": {k: v for k, v in a.items() if k not in skip} == {k: v for k, v in b.items() if k not in skip},
            "compared_without_keys": list(skip),
            "cascade_script_sha256_equal":
                (a.get("cascade") or {}).get("sha256") == (b.get("cascade") or {}).get("sha256")}
    return {"decisions": p, "calibrations": cal_file, "info": info}


def stored_block_file_equal(d: str, bf: dict, stored_bf: dict | None) -> None:
    """--apertus stored: the states belong to the stored block file (the prompt of interface 5 comes from it)."""
    if stored_bf is None:
        raise Stop(f"{d}: --apertus stored: no stored block file daten/gj/docs/{d}.json")
    x = {k: v for k, v in bf.items() if k != "source_files"}
    y = {k: v for k, v in stored_bf.items() if k != "source_files"}
    if x != y:
        raise Stop(f"{d}: --apertus stored: the block file differs from the stored block file daten/gj/docs/{d}.json; "
                   f"the states belong to the stored block file (use --apertus none)")


def cascade_stored(d: str, block_doc: dict, rules_rec: dict, work: Path, states_dir: Path,
                   entry: tuple[str, str]) -> dict:
    """--apertus stored (chapter 1 item 6): decide() of src/m10_pipeline.py with the mode cascade and the frozen
    design; the block file and the rule record of this command go to the design."""
    pipeline = pipeline_module()
    e1, e2 = entry[0] == "yes", entry[1] == "yes"
    try:
        frozen = pipeline.load_design(None, DESIGN_FREEZE, require_freeze=True)
        fl = pipeline.load_floor()
        dec = pipeline.decide(d, "cascade", frozen, states_dir, e1, e2, None, floor=fl, rules=rules_rec, doc=block_doc)
        cals = pipeline.cascade_calibrations(frozen, e1, e2, fl)
    except pipeline.PipelineRefusal as e:
        raise Stop(f"--apertus stored: {e}") from None
    if dec.get("no_states"):
        raise Stop(f"{d}: --apertus stored: the states file is missing")
    p = work / "decisions" / f"{d}.json"
    write_json(p, dec)
    cp = work / "calibrations.json"
    write_json(cp, cals)
    info = {"pipeline": {"path": rel(pipeline.SCRIPT), "sha256": sha256(pipeline.SCRIPT), "version": pipeline.VERSION},
            "design_freeze": {"path": rel(DESIGN_FREEZE), "sha256": sha256(DESIGN_FREEZE)},
            "design_files": frozen.files, "entry": {"d1": e1, "b1_b2": e2}, "states": dec.get("states"),
            "template_sha256": dec.get("template_sha256"), "model": dec.get("model"),
            "calibration_file": {"path": rel(cp), "sha256": sha256(cp)}}
    return {"decisions": p, "calibrations": cp, "info": info}


def held_out_check(split: str, apertus: str) -> dict | None:
    """Criteria chapters 3 and 10.3: no output of a method for a validation or group-7 document before the freeze.
    After the freeze, the freeze file must name the SHA-256 of this file and of the files of the method."""
    if split == "dev":
        return None
    try:
        import m10_calibrate as cal
    except ImportError:
        raise Stop(f"split {split}: no run before the freeze (criteria 10); src/m10_calibrate.py is missing") from None
    try:
        out = cal.freeze_check(split, floor_calibration_file())
    except SystemExit as e:
        raise Stop(f"split {split} (criteria 3 and 10.3): {e}") from None
    f = ROOT / out["freeze_file"]
    if sha256(SCRIPT) not in f.read_text(encoding="utf-8"):
        raise Stop(f"split {split}: the freeze file {out['freeze_file']} does not name the SHA-256 of {rel(SCRIPT)}")
    return out | {"apertus": apertus}


# ------------------------------------------------------------------ step 7: writer, RDF step, validator
def write_record(d: str, out: Path, work_docs: Path, work_dec: Path, cal_path: Path, base: str) -> dict:
    import m06_converter as mc
    import m10_rdf as rdf
    import m10_validate as val
    import m10_writer as writer
    base = writer.check_base(base)
    cals, cal_file = writer.load_calibrations(Path(cal_path).resolve())
    t0 = time.perf_counter()
    exp = mc.build_export_records([d])
    if d not in exp:
        raise Stop(f"{d}: no export record (OpenParlData export)")
    man = writer.write_one(d, out, None, exp[d], cals, cal_file, base, work_docs, work_dec)
    t1 = time.perf_counter()
    rdf.convert_record(out / d, d, base)
    t2 = time.perf_counter()
    res = val.validate_record(out / d, d)
    t3 = time.perf_counter()
    man = read_json(out / d / "manifest.json")
    return {"manifest": man, "validation": res, "seconds": {"write": round(t1 - t0, 3), "rdf": round(t2 - t1, 3),
                                                            "validate": round(t3 - t2, 3)}}


# ------------------------------------------------------------------ command convert
def convert(args) -> int:
    started, t_all = clock(), time.perf_counter()
    rec: dict = {"schema": "parlpdfech-gj-convert/1", "version": VERSION, "status": STATUS,
                 "script": script_record(), "started": started,
                 "actor": "workflow sub-agent (Claude Opus 5.5), stream CLI of gate GJ",
                 "arguments": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items() if k != "func"}}
    d = str(args.doc_id).strip()
    out = Path(args.out).resolve()
    if not out.is_relative_to(ROOT.resolve()):
        raise Stop(f"--out {out}: the folder must be in the project folder {ROOT} (src/m03_atome.py writes paths "
                   f"relative to it)")
    pdf_in = Path(args.pdf).resolve()
    seconds: dict = {}
    t = time.perf_counter()
    g = guard_document(d, pdf_in, args.allow_final_group7)
    rec["held_out_check"] = held_out_check(g["split"], args.apertus)
    entry = (args.entry_d1, args.entry_b12)
    states_dir = Path(args.states_dir) if args.states_dir else None
    check_mode(d, args.apertus, states_dir, entry)
    seconds["guard"] = round(time.perf_counter() - t, 3)
    rec["guard"] = {k: g[k] for k in ("split", "parliament", "pdf", "guard_summary")}
    folder = out / d
    work = folder / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    rec_path = folder / "convert.json"
    write_json(rec_path, rec | {"result": "running"})      # the script SHA-256 is in the record before any output
    fresh = args.docling == "fresh"
    files: dict[str, Path] = {}
    with read_guard(d, block_stored=False) as hits_a:
        if fresh:
            if pdf_in.name == f"{d}.pdf" and pdf_in.is_relative_to(ROOT.resolve()):
                pdf = pdf_in
            else:                     # main of m03_docling_zerlegen takes the doc id from the file name
                pdf = work / "pdf" / f"{d}.pdf"
                pdf.parent.mkdir(parents=True)
                shutil.copyfile(pdf_in, pdf)
                if sha256(pdf) != g["pdf"]["sha256"]:
                    raise Stop(f"{d}: the copy of the PDF has another SHA-256")
            t = time.perf_counter()
            run = docling_main([pdf], work / "docling", work / "records", f"convert_{d}", args.device, warmup=False)
            seconds["docling"] = round(time.perf_counter() - t, 3)
            row = run["rows"].get(d) or {}
            if row.get("status") != "success":
                raise Stop(f"{d}: Docling status {row.get('status')!r} (not success)")
            files["docling"] = work / "docling" / f"{d}.json"
            t = time.perf_counter()
            am = atoms_of_docling(d, files["docling"], pdf.parent, work / "atome", work / "atome_prompt")
            seconds["atoms"] = round(time.perf_counter() - t, 3)
            files["atome"], files["atome_prompt"] = am["atoms"], am["prompt"]
            dk = read_json(files["docling"])
            rec["docling"] = {"arguments": run["arguments"], "run_files": run["files"],
                              "settings_equal_to_stored": {k: v for k, v in dk["konfiguration"].items()
                                                           if STORED_SETTINGS.get(k) != v} or "equal",
                              "tools_equal_to_stored": {k: v for k, v in dk["werkzeug"].items()
                                                        if STORED_TOOLS.get(k) != v} or "equal",
                              "backend": dk["backend"], "pages": len(dk["seiten"]), "blocks": len(dk["bloecke"]),
                              "docling_seconds": float(row.get("sekunden") or 0), "atoms": {k: v for k, v in am.items()
                                                                                            if k not in ("atoms", "prompt")}}
            t = time.perf_counter()
            bf = block_file(d, g["split"], g["parliament"], files["docling"], files["atome"], pdf)
            seconds["block_file"] = round(time.perf_counter() - t, 3)
            st = stored_outputs(d)
            rec["comparison_with_stored"] = (compare_outputs(d, {"docling": dk, "atoms": read_json(files["atome"]),
                                                                "block_file": bf}, st) | {"stored_files": st["files"]}
                                             if st else "no stored outputs")
            if args.apertus == "stored":
                stored_block_file_equal(d, bf, st["block_file"] if st else None)
        else:
            t = time.perf_counter()
            bf, info = docs_text.build_one(d, g["split"], g["parliament"], guard.list_sha256())
            seconds["block_file"] = round(time.perf_counter() - t, 3)
            files = {k: guard.iso_file(k, d) for k in ISO_KINDS}
            rec["docling"] = {"mode": "stored outputs after the SHA-256 check of the PDF", "info": info}
            if args.apertus == "stored":
                sp = GJ / "docs" / f"{d}.json"
                stored_block_file_equal(d, bf, read_json(sp) if sp.is_file() else None)
    if hits_a:
        raise Stop(f"{d}: read guard: {len(hits_a)} reads in folders of test documents: {hits_a[:3]}")
    docs_dir = work / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    bf_path = docs_dir / f"{d}.json"
    bf_path.write_text(json.dumps(bf, ensure_ascii=False) + "\n", encoding="utf-8")
    rec["inputs"] = files_info({"pdf": pdf_in, **files, "block_file": bf_path})
    ctx = fresh_inputs(d, files) if fresh else contextlib.nullcontext({"modules": []})
    with ctx as patched, read_guard(d, block_stored=fresh) as hits_b:
        rec["fresh_inputs_redirect"] = patched["modules"]
        t = time.perf_counter()
        rr = rules_record(d, args.allow_final_group7, fresh)
        seconds["rules"] = round(time.perf_counter() - t, 3)
        rules_p = work / "rules" / f"{d}.json"
        rules_p.parent.mkdir(parents=True, exist_ok=True)
        rules_p.write_text(json.dumps(rr["record"], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        rec["rules"] = {"file": {"path": rel(rules_p), "sha256": sha256(rules_p)}, "admission": rr["admission"],
                        "loaded_record_hidden": rr["loaded_record_hidden"], "identity_record": rr["identity_record"],
                        "needs_apertus": rr["record"]["document"]["d1"]["needs_apertus"]}
        t = time.perf_counter()
        dec = decisions(d, args.apertus, bf, rr["record"], work, states_dir, entry)
        seconds["decisions"] = round(time.perf_counter() - t, 3)
        rec["decisions"] = {"mode": args.apertus, "files": files_info({"decisions": dec["decisions"],
                                                                      "calibrations": dec["calibrations"]}),
                            "info": dec.get("info")}
        wr = write_record(d, out, docs_dir, Path(dec["decisions"]).parent, dec["calibrations"], args.base)
        seconds.update(wr["seconds"])
    if hits_b:
        raise Stop(f"{d}: read guard: {len(hits_b)} reads of stored files of this document or of folders of test "
                   f"documents during steps 5 to 7: {hits_b[:3]}")
    rec["rules"]["comparison_with_stored_rule_file"] = compare_rules(rr["record"], d)
    man, val = wr["manifest"], wr["validation"]
    outputs = {k: v for k, v in man["outputs"].items()}
    vp = folder / "validation.json"
    if vp.exists():
        outputs["validation"] = {"path": rel(vp), "sha256": sha256(vp)}
    outputs["manifest"] = {"path": rel(folder / "manifest.json"), "sha256": sha256(folder / "manifest.json")}
    seconds["total"] = round(time.perf_counter() - t_all, 3)
    rec |= {"outputs": outputs, "writer_check_passed": man["check_passed"], "validation_passed": val["passed"],
            "validation_checks": {k: v["passed"] for k, v in val.items() if k.startswith("C") and isinstance(v, dict)
                                  and "passed" in v},
            "shacl": (val.get("C10_shacl") or {}).get("status"), "counts": man["counts"],
            "seconds": seconds, "end_checks": end_checks(rec), "finished": clock(),
            "result": "valid" if man["check_passed"] and val["passed"] else "not valid"}
    write_json(rec_path, rec)
    print(json.dumps({"doc_id": d, "result": rec["result"], "validation_checks": rec["validation_checks"],
                      "comparison_with_stored": (rec.get("comparison_with_stored") or {}).get("result")
                      if isinstance(rec.get("comparison_with_stored"), dict) else rec.get("comparison_with_stored"),
                      "rules_equal_to_stored": rec["rules"]["comparison_with_stored_rule_file"]["equal"],
                      "frozen_files_different": rec["end_checks"]["frozen_files"]["different"],
                      "seconds": seconds, "record": rel(rec_path), "record_sha256": sha256(rec_path)}, indent=1))
    return 0 if rec["result"] == "valid" else 2


# ------------------------------------------------------------------ command check-docling
def select_check_docs(n: int, max_pages: int) -> dict:
    """Selection rule of chapter 2 item 1. It uses only the keys quelle, backend and seiten of the stored Docling
    outputs of the candidates (no text, no label)."""
    ids = sorted(built_ids(), key=int)
    g = guard.assert_allowed(ids)
    cand = []
    for d in ids:
        if g["split_of"][d] != "validation":
            continue
        pdf = BULK / f"{d}.pdf"
        if not pdf.is_file():
            continue
        dk = read_json(guard.iso_file("docling", d))
        if dk.get("quelle") != f"daten/pdf/bulk/{d}.pdf" or len(dk.get("seiten") or []) > max_pages:
            continue
        cand.append({"doc_id": d, "parliament": g["parliament_of"][d], "backend": dk.get("backend"),
                     "pages": len(dk.get("seiten") or [])})
    by_parl: dict[str, list[dict]] = defaultdict(list)
    for c in cand:
        by_parl[c["parliament"]].append(c)
    order = sorted(by_parl)
    chosen: list[dict] = []
    rank = 0
    while len(chosen) < n and any(len(by_parl[p]) > rank for p in order):
        for p in order:
            if len(chosen) < n and len(by_parl[p]) > rank:
                chosen.append(by_parl[p][rank])
        rank += 1
    replaced = None
    fb = [c for c in cand if c["backend"] == FALLBACK_BACKEND]
    if chosen and fb and not any(c["backend"] == FALLBACK_BACKEND for c in chosen):
        replaced = chosen[-1]["doc_id"]
        chosen[-1] = fb[0]
    return {"rule": "chapter 2 item 1 of src/m10_convert.py", "candidates": len(cand),
            "candidate_parliaments": len(order), "candidates_with_fallback_backend": len(fb),
            "replaced_for_fallback_backend": replaced, "documents": chosen}


def check_docling(args) -> int:
    started, t_all = clock(), time.perf_counter()
    folder = CHECK_DIR
    if folder.exists() and any(folder.iterdir()) and not args.force:
        raise Stop(f"{rel(folder)} exists: one run only (give --force to make it again)")
    folder.mkdir(parents=True, exist_ok=True)
    rec: dict = {"schema": "parlpdfech-gj-docling-check/1", "version": VERSION, "status": STATUS,
                 "script": script_record(), "started": started,
                 "actor": "workflow sub-agent (Claude Opus 5.5), stream CLI of gate GJ",
                 "purpose": "plan chapter 5.2 item 2: fresh Docling on validation PDFs against the stored outputs; "
                            "inputs only, no label and no model output, no method value",
                 "settings": {"device": args.device, "n": args.n, "max_pages": args.max_pages,
                              "stored_settings": STORED_SETTINGS, "stored_tools": STORED_TOOLS}}
    sel = select_check_docs(args.n, args.max_pages)
    rec["selection"] = sel
    ids = [c["doc_id"] for c in sel["documents"]]
    g = guard.assert_allowed(ids, allowed=("validation",))
    rec["guard"] = {k: v for k, v in g.items() if k not in ("split_of", "parliament_of")}
    rec["guard_tables"] = guard.tables().sources
    pdfs = []
    for d in ids:
        p = BULK / f"{d}.pdf"
        pc = guard.check_pdf(d, p)
        if not pc["equal"]:
            raise Stop(f"{d}: the SHA-256 of the PDF differs from the stored value")
        pdfs.append(p)
    rec["pdfs"] = {d: {"path": rel(p), "sha256": sha256(p)} for d, p in zip(ids, pdfs)}
    rec["tools_now"] = tool_versions()
    rec["tools_equal_to_stored"] = {k: v for k, v in rec["tools_now"].items() if STORED_TOOLS.get(k) != v} or "equal"
    write_json(folder / "check.json", rec | {"result": "running"})
    with read_guard(None, block_stored=False) as hits:
        run = docling_main(pdfs, folder / "docling", folder / "records", "gj_docling_check", args.device, warmup=True)
        per_doc = []
        for d, p in zip(ids, pdfs):
            row = run["rows"].get(d) or {}
            item = {"doc_id": d, "parliament": g["parliament_of"][d], "docling_status": row.get("status"),
                    "docling_seconds": float(row.get("sekunden") or 0), "pages": int(row.get("seiten") or 0)}
            if row.get("status") != "success":
                item["result"] = "Docling failed"
                per_doc.append(item)
                continue
            dpath = folder / "docling" / f"{d}.json"
            am = atoms_of_docling(d, dpath, p.parent, folder / "atome", folder / "atome_prompt")
            t = time.perf_counter()
            bf = block_file(d, "validation", g["parliament_of"][d], dpath, am["atoms"], p)
            bp = folder / "docs" / f"{d}.json"
            write_json(bp, bf)
            item["block_file_seconds"] = round(time.perf_counter() - t, 3)
            item["atoms_seconds"] = am["seconds"]
            st = stored_outputs(d)
            cmp = compare_outputs(d, {"docling": read_json(dpath), "atoms": read_json(am["atoms"]), "block_file": bf}, st)
            item |= {"stored_docling_seconds": st["docling"].get("laufzeit_s"),
                     "total_seconds": round(item["docling_seconds"] + am["seconds"] + item["block_file_seconds"], 3),
                     "fresh_files": files_info({"docling": dpath, "atoms": am["atoms"], "block_file": bp}),
                     "stored_files": st["files"], "comparison": cmp, "result": cmp["result"]}
            per_doc.append(item)
    if hits:
        raise Stop(f"read guard: {len(hits)} reads in folders of test documents: {hits[:3]}")
    rec["docling_run"] = {"arguments": run["arguments"], "run_files": run["files"], "summary": run["summary"],
                          "seconds": run["seconds"]}
    rec["documents"] = per_doc
    res = Counter(x["result"] for x in per_doc)
    kinds = Counter(k for x in per_doc for k in (x.get("comparison") or {}).get("kinds", []))
    other = Counter(k for x in per_doc for k in (x.get("comparison") or {}).get("other_differences", []))
    rec["summary"] = {"documents": len(per_doc), "results": dict(res), "kinds_of_difference": dict(kinds),
                      "other_differences": dict(other),
                      "seconds_per_document": {x["doc_id"]: x.get("total_seconds") for x in per_doc}}
    rec["end_checks"] = end_checks(rec)
    rec["finished"], rec["seconds"] = clock(), round(time.perf_counter() - t_all, 3)
    rec["result"] = "all equal" if res.get("equal", 0) == len(per_doc) else "differences"
    write_json(folder / "check.json", rec)
    print(json.dumps({"result": rec["result"], "summary": rec["summary"],
                      "frozen_files_different": rec["end_checks"]["frozen_files"]["different"],
                      "per_document": [{k: x.get(k) for k in ("doc_id", "result", "pages", "docling_seconds",
                                                              "total_seconds")} | {
                          "kinds": (x.get("comparison") or {}).get("kinds"),
                          "other": (x.get("comparison") or {}).get("other_differences")} for x in per_doc],
                      "record": rel(folder / "check.json"), "record_sha256": sha256(folder / "check.json")}, indent=1))
    return 0


# ------------------------------------------------------------------ command line
def parser_convert() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="m10_convert.py", description="gate GJ: one PDF file to RDF (plan chapter 5.2)")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--apertus", required=True, choices=("none", "stored", "vm"))
    ap.add_argument("--states-dir", default=None, help="job folder of the states with states/<doc>.npz, for example "
                                                       "daten/gj/states/gpu1_labelled (only for --apertus stored)")
    ap.add_argument("--entry-d1", default=None, choices=("yes", "no"), help="entry decision of D1 (--apertus stored)")
    ap.add_argument("--entry-b12", default=None, choices=("yes", "no"),
                    help="entry decision of B1 and B2 (--apertus stored)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--docling", default="fresh", choices=("fresh", "stored"))
    ap.add_argument("--device", default=STORED_SETTINGS["geraet"], choices=("auto", "cpu", "mps"))
    ap.add_argument("--allow-final-group7", action="store_true")
    return ap


def parser_check() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="m10_convert.py check-docling",
                                 description="gate GJ: fresh Docling check on validation PDFs (plan chapter 5.2 item 2)")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--device", default=STORED_SETTINGS["geraet"], choices=("auto", "cpu", "mps"))
    ap.add_argument("--force", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] == "check-docling":
            return check_docling(parser_check().parse_args(argv[1:]))
        if argv and argv[0] == "convert":
            argv = argv[1:]
        return convert(parser_convert().parse_args(argv))
    except Stop as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
