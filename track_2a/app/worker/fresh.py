#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package (stage P0b): the conversion of a PDF that is not in the package.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

Code rules only. No Apertus state is read and no model of Apertus runs. serve_convert.py calls
convert_fresh() of this file for a PDF whose SHA-256 is not in the sample index (contract chapter 4.3).

Profiles
  slim    no Docling in the image: the PDF is refused with the code not_in_package.
  native  the Python of the host. Docling runs with the stored settings of the converter, not changed
          (the step function docling_main of m10_convert: OCR auto, device auto, 4 threads, accurate
          tables). OCR auto is Apple OCR (the package ocrmac) on macOS. If ocrmac is absent, the
          branch runs Docling with no OCR, as the profile full does.
  full    a Linux image with Docling and torch for the CPU. No OCR engine is in the image. Docling
          runs through the same function main of m03_docling_zerlegen with two other arguments:
          "--ocr aus" (no OCR) and "--geraet cpu". All other arguments are the stored ones.
  In the profile native, PARLPDFECH_FRESH_OCR=none and PARLPDFECH_FRESH_DEVICE=cpu give the two
  arguments of the profile full on the host (a measurement aid; the tools stay the tools of the host).

Steps (each one is the step function of the converter copy in the code layout, not a project file)
  1. PDF checks (new code): the PDF mark, a password (code protected_pdf), the page count against
     PARLPDFECH_MAX_PAGES (code too_long), the text layer of each page (code no_text_layer if no page
     has text and no OCR engine runs).
  2. Docling: docling_main of m10_convert (it calls main of m03_docling_zerlegen).
  3. Lines: atoms_of_docling of m10_convert (function dokument of m03_atome, version atome-v3).
  4. Block file: block_file of m10_convert (the functions of m10_docs). The split and the parliament
     are null: an own PDF has none.
  5. Rules: check_identity_record and run_document of m10_rules, check_frozen_method of
     m05_iso_runner. The 3 export fields of the S1 rule are empty, and the admission kind is
     "loader" (the form of the converter for a document with no row in its tables).
  6. Floor decisions: load_floor and checked of m10_pipeline, floor_decisions of m10_cascade. The
     function decide of m10_pipeline is not called: its first act is the split guard, and the guard
     refuses each id that is not a document number.
  7. Record: worker/values_record.py. The value readers (code rules with tiers, m11_values_base) read the
     affair type, the title, the affair number, the two dates, the responder and the first author from
     the block file and the rule file. m11_writer writes the record with one affair, m11_validate checks
     it. No export record exists: the record has no cross-check. A type or a number that the PDF does
     not print is a recorded gap.
     With PARLPDFECH_VALUES=off (or for a PDF of worker/values_hold.json) the earlier record runs:
     worker/pdf_only.py, a container with no affair.

What differs from the conversion of the project, in each profile
  - The tables of the rule chain have no row (worker/fresh_tables.json). The guards of the rule chain
    have no function. The measurement tables that m03_ladder loads at import are empty.
  - The S1 rule gets empty export fields. The rule ids P2 and R1 read export fields.
  - The word counts for line-end hyphens come from this document only.
  - The record is written with no export record (no cross-check of a value).
  - No value of a report of the project applies to the result.

One process makes one conversion: the branch changes module constants of the converter copies in
memory (the pdftotext path) and adds one finder for the module names of the converter.
"""

from __future__ import annotations

import csv
import contextlib
import importlib.machinery
import json
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
import types
from pathlib import Path

FRESH_VERSION = "parlpdfech-fresh/0.1.0"
PACKAGE = Path(__file__).resolve().parents[1]
DOC = "local"
MODE_NUMBER = 3                                   # the mode number of the fresh branch in the layout list
OUT_FOLDER = "daten/gj/package_fresh"
PDF_REL = f"daten/pdf/local/{DOC}.pdf"
PDFTOTEXT_PLACES = ("/usr/bin/pdftotext", "/opt/homebrew/bin/pdftotext", "/usr/local/bin/pdftotext")
RECORD_FILES = ("{d}.gesamt.trig", "{d}.ech.ttl", "{d}.gesamt.rdf.xml", "{d}.ech.rdf.xml", "{d}.ech.yaml",
                "{d}.labels.yaml", "{d}.provenance.yaml", "manifest.json", "validation.json")
OUTPUT_ROLE = {"gesamt_trig": "{d}.gesamt.trig", "ech_ttl": "{d}.ech.ttl", "gesamt_rdfxml": "{d}.gesamt.rdf.xml",
               "ech_rdfxml": "{d}.ech.rdf.xml", "ech_yaml": "{d}.ech.yaml", "labels_yaml": "{d}.labels.yaml",
               "provenance_yaml": "{d}.provenance.yaml"}
MODULE_NAME = re.compile(r"m\d\d_\w+")


# ---------------------------------------------------------------------------------------------- PDF checks
def pdf_check(host, pdf: Path, max_pages: int) -> dict:
    """The checks of the PDF file before a conversion (new code; pypdfium2 reads the file).
    Stops with protected_pdf, too_long, bad_request (no PDF mark) or pdf_unreadable (the file does not open or has no page)."""
    with open(pdf, "rb") as f:
        head = f.read(1024)
    if b"%PDF-" not in head:
        raise host.Stop("bad_request", {"field": "file"}, 3)
    try:
        import pypdfium2 as pdfium  # noqa: PLC0415
    except ImportError:
        host.log("pypdfium2 is absent")
        raise host.stopped("pdf_reader_absent") from None
    try:
        doc = pdfium.PdfDocument(str(pdf))
    except Exception as e:  # noqa: BLE001  (pypdfium2 has one error class for each cause; the text names the cause)
        if "password" in str(e).lower():
            raise host.Stop("protected_pdf", {}, 3) from None
        host.log(f"the PDF does not open: {type(e).__name__}")
        raise host.Stop("pdf_unreadable", {}, 3) from None
    try:
        n = len(doc)
        if n < 1:
            raise host.Stop("pdf_unreadable", {}, 3)
        if n > max_pages:
            raise host.Stop("too_long", {"pages": n, "max_pages": max_pages}, 3)
        chars = []
        for i in range(n):
            try:
                page = doc[i]
                tp = page.get_textpage()
                chars.append(len("".join(tp.get_text_range().split())))
                tp.close()
                page.close()
            except Exception:  # noqa: BLE001  (a page that does not load counts as a page with no text)
                chars.append(0)
    finally:
        with contextlib.suppress(Exception):
            doc.close()
    with_text = sum(1 for c in chars if c > 0)
    return {"pages": n, "max_pages": max_pages, "pages_with_text_layer": with_text,
            "pages_without_text_layer": n - with_text, "text_layer_characters": sum(chars),
            "tool": "pypdfium2 (page count, password, text of each page)"}


def ocr_of_profile(profile: str) -> str:
    """apple: the stored settings run (OCR auto with the package ocrmac). none: Docling runs with no OCR.
    PARLPDFECH_FRESH_OCR=none sets no OCR in the profile native (the settings of the profile full on the host)."""
    if profile != "native" or sys.platform != "darwin" or os.environ.get("PARLPDFECH_FRESH_OCR") == "none":
        return "none"
    try:
        import ocrmac  # noqa: F401, PLC0415
    except ImportError:
        return "none"
    return "apple"


# ---------------------------------------------------------------------------------------------- scratch root
class LayoutFinder:
    """Each module of the converter (name m<2 digits>_...) comes from the scratch root only. One converter file
    puts a fixed folder of its author at the start of the module search path; this finder makes that path
    without effect, and it takes the path out of the search path before the next import reads it (the finder
    is the first one, so Python calls it for each import). An entry is taken out if its last part is src, it
    is not the folder src of the scratch root, and it was not in the search path at the start of the conversion
    (each converter file adds a folder with the name src and no other folder)."""

    src: str = ""
    allowed: frozenset = frozenset()
    removed: int = 0

    @classmethod
    def find_spec(cls, name, path=None, target=None):  # noqa: ARG003
        foreign = [p for p in sys.path if p not in cls.allowed and os.path.basename(p.rstrip("/\\")) == "src"]
        if cls.allowed and foreign:
            cls.removed += len(foreign)
            sys.path[:] = [p for p in sys.path if p not in foreign]
        if not MODULE_NAME.fullmatch(name):
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, [cls.src])
        if spec is None:                 # never a module of another folder with a converter name
            raise ModuleNotFoundError(f"converter module {name} is not in the code layout of the fresh branch")
        return spec


def build_root(host, root: Path, code_dir: Path, pdf: Path, digest: str) -> dict:
    """The scratch root of one fresh run: the converter files of mode 3, the reduced tables, the PDF."""
    man_p = code_dir / "layout_manifest.json"
    if not man_p.is_file():
        host.log("no layout_manifest.json in the code layout: run worker/layout.py")
        raise host.stopped("layout")
    layout = host.read_json(man_p)
    files = [f for f in layout["files"] if MODE_NUMBER in f["modes"]]
    if not files:
        host.log("the code layout holds no file of the fresh branch: run worker/layout.py with the current list")
        raise host.stopped("layout")
    for f in files:
        src = code_dir / f["path"]
        if not src.is_file():
            host.log(f"layout file absent: {f['path']}")
            raise host.stopped("layout")
        host.copy_checked(src, root / f["path"], f["sha256"], "layout")
    host.copy_compiled(layout, code_dir, root, files)
    tables_p = Path(__file__).resolve().parent / "fresh_tables.json"
    generated = []
    for t in host.read_json(tables_p)["tables"]:
        p = root / t["path"]
        if t["form"] == "empty_folder":
            p.mkdir(parents=True, exist_ok=True)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t["text"] if t["form"] == "csv_header" else json.dumps(t["value"], ensure_ascii=False),
                     encoding="utf-8")
        generated.append(t["path"])
    dst = root / PDF_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, dst)
    if host.sha256_file(dst) != digest:
        raise host.stopped("copy")
    return {"generated": generated, "pdf": dst, "layout_files": len(files),
            "tables_sha256": host.sha256_file(tables_p)}


def import_converter(host, root: Path) -> types.SimpleNamespace:
    """Imports the converter modules of the fresh branch from the scratch root and checks their place."""
    LayoutFinder.src = str(root / "src")
    sys.path.insert(0, str(root / "src"))
    LayoutFinder.allowed = frozenset(sys.path)
    sys.meta_path.insert(0, LayoutFinder)
    import m03_sub_common as sc  # noqa: F401, PLC0415  (first: m03_ladder reads its tables at import)
    import m03_ladder  # noqa: F401, PLC0415
    import m05_iso_runner as runner  # noqa: PLC0415
    import m10_rules as rules  # noqa: PLC0415
    import m10_convert as cv  # noqa: PLC0415
    import m03_docling_zerlegen as dz  # noqa: PLC0415
    import m03_atome as at  # noqa: PLC0415
    import m10_pipeline as pipeline  # noqa: PLC0415
    import m10_cascade as cascade  # noqa: PLC0415
    import m10_calibrate as cal  # noqa: PLC0415
    import m10_writer as writer  # noqa: PLC0415
    import m06_converter as mc  # noqa: PLC0415
    import m06_ech_ausgabe as ea  # noqa: PLC0415
    import m03_gold_record as gr  # noqa: PLC0415
    import m03_iso_v4 as v4  # noqa: PLC0415
    import m10_rdf as rdf  # noqa: PLC0415
    import m10_validate as val  # noqa: PLC0415
    m = types.SimpleNamespace(runner=runner, rules=rules, cv=cv, dz=dz, at=at, pipeline=pipeline, cascade=cascade,
                              cal=cal, writer=writer, mc=mc, ea=ea, gr=gr, v4=v4, rdf=rdf, val=val)
    check_module_places(host, root)
    if Path(cv.ROOT).resolve() != root or Path(rdf.ROOT).resolve() != root:
        raise host.stopped("layout")
    return m


def check_module_places(host, root: Path) -> list[str]:
    """Each loaded converter module must be a file of the scratch root. Returns the module names."""
    src = str(root / "src") + os.sep
    names = sorted(n for n, mod in list(sys.modules.items()) if MODULE_NAME.fullmatch(n) and mod is not None)
    other = [n for n in names if not str(getattr(sys.modules[n], "__file__", "") or "").startswith(src)]
    if other:
        host.log(f"converter modules outside the scratch root: {other}")
        raise host.stopped("layout")
    return names


def set_pdftotext(host, m) -> str:
    """The converter names the pdftotext command of one computer. The branch sets the place by platform."""
    found = shutil.which("pdftotext") or next((p for p in PDFTOTEXT_PLACES if Path(p).is_file()), None)
    if not found:
        host.log("no pdftotext command (package poppler-utils)")
        raise host.stopped("pdftotext_absent")
    m.dz.PDFTOTEXT = found
    folder = str(Path(found).parent)
    if folder not in os.environ.get("PATH", "").split(os.pathsep):      # m03_atome calls the command by name
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + folder
    return found


def docling_no_ocr(m, pdf: Path, out_dir: Path, record_dir: Path, name: str, device: str) -> dict:
    """The call of docling_main of m10_convert with one other argument: "--ocr aus" in place of "--ocr auto".
    The function main of m03_docling_zerlegen is the same. Used when no OCR engine is present."""
    cv, dz = m.cv, m.dz
    out_dir.mkdir(parents=True, exist_ok=True)
    record_dir.mkdir(parents=True, exist_ok=True)
    argv = [str(dz.__file__), str(pdf), "--ocr", "aus", "--geraet", device, "--threads", "4", "--tabellen", "genau",
            "--zellabgleich", "an", "--sprachen", cv.LANGUAGES, "--name", name, "--ausgabe", str(out_dir),
            "--ohne-aufwaermen"]
    old_argv, old_analyse = sys.argv, dz.ANALYSE
    sys.argv, dz.ANALYSE = argv, record_dir
    t0 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(sys.stderr):
            dz.main()
    finally:
        sys.argv, dz.ANALYSE = old_argv, old_analyse
    with open(record_dir / f"lauf_{name}.csv", newline="", encoding="utf-8") as f:
        rows = {r["doc_id"]: r for r in csv.DictReader(f)}
    return {"arguments": argv[1:], "rows": rows, "summary": host_read(record_dir / f"lauf_{name}.json"),
            "seconds": round(time.perf_counter() - t0, 3)}


def host_read(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_compact(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")


def package_path(text: str, root: Path) -> str:
    """A path of the scratch root as a path relative to it (no path of this computer goes into a record file)."""
    return text.replace(str(root) + os.sep, "").replace(str(root), ".")


# ---------------------------------------------------------------------------------------------- the conversion
def convert_fresh(host, pdf_path: Path, doc_id: str | None, mode: str, out: Path) -> int:
    """One PDF that is not a sample: checks, Docling, lines, block file, rules, floor decisions, record.
    host is the module serve_convert (output lines, stage events, shared helpers). Returns the exit code."""
    t_all = time.perf_counter()
    started = host.utc_now()
    stages = host.Stages()
    profile = os.environ.get("PARLPDFECH_PROFILE", "native")
    data_dir = Path(os.environ.get("PARLPDFECH_DATA_DIR") or PACKAGE / "data").resolve()
    code_dir = Path(os.environ.get("PARLPDFECH_CODE_DIR") or PACKAGE / "build" / "layout").resolve()
    view_dir = Path(os.environ.get("PARLPDFECH_VIEW_DIR") or PACKAGE / "view").resolve()
    try:
        max_pages = int(os.environ.get("PARLPDFECH_MAX_PAGES") or 25)
    except ValueError:
        max_pages = 25
    pdf_path = Path(pdf_path).resolve()
    out = Path(out).resolve()
    digest = host.sha256_file(pdf_path)
    record_id = f"u-{digest[:16]}" + ("-rules" if mode == "rules" else "")
    d = DOC
    keep = os.environ.get("PARLPDFECH_KEEP_SCRATCH") == "1"
    scratch: Path | None = None
    start_dir = os.getcwd()
    try:
        try:
            # ---- stage 1: PDF checks and Docling
            stages.start("read_pdf")
            if profile == "slim":
                raise host.Stop("not_in_package", {"pdf_sha256": digest, "profile": profile}, 3)
            if doc_id is not None:
                index_p = data_dir / "samples" / "index.json"
                known = {str(s["doc_id"]) for s in host.read_json(index_p)["samples"]} if index_p.is_file() else set()
                raise host.Stop("pdf_differs_from_doc_id" if doc_id in known else "doc_id_unknown", {"doc_id": doc_id}, 3)
            check = pdf_check(host, pdf_path, max_pages)
            ocr = ocr_of_profile(profile)
            if ocr == "none" and check["pages_with_text_layer"] == 0:
                raise host.Stop("no_text_layer", {}, 3)
            os.environ.setdefault("HF_HUB_OFFLINE", "1")                # no request to a model hub
            os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")  # no stored hub token is put into a request
            os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
            if profile == "full" and not os.environ.get("DOCLING_ARTIFACTS_PATH"):
                host.log("profile full: DOCLING_ARTIFACTS_PATH is not set")
                raise host.stopped("docling_models")

            t = time.perf_counter()
            scratch_base = Path(os.environ.get("PARLPDFECH_SCRATCH_DIR") or out.parent).resolve()
            try:
                out.parent.mkdir(parents=True, exist_ok=True)
                if not os.access(scratch_base, os.W_OK | os.X_OK):
                    raise PermissionError
            except OSError as e:
                host.log(f"the parent folder of --out or the scratch folder is not writable: {type(e).__name__}")
                raise host.stopped("out" if scratch_base == out.parent else "scratch") from None
            scratch = Path(tempfile.mkdtemp(prefix="parlpdfech-fresh-", dir=scratch_base)).resolve()
            host.keep_home_clean(scratch)          # before the first import of Docling, torch or a converter file
            try:
                import docling  # noqa: F401, PLC0415
            except ImportError:
                host.log("the package docling is absent in this Python")
                raise host.stopped("docling_absent") from None
            root = scratch / "root"
            facts = build_root(host, root, code_dir, pdf_path, digest)
            pdf = facts["pdf"]
            rel_out = OUT_FOLDER
            folder = root / rel_out / d
            docling_p, atoms_p = root / "daten/iso/docling" / f"{d}.json", root / "daten/iso/atome" / f"{d}.json"
            docs_p, rules_p = root / "daten/gj/docs" / f"{d}.json", root / "daten/gj/rules" / f"{d}.json"
            dec_p = root / rel_out / "decisions" / f"{d}.json"
            if host.TRACE:
                host.TRACE.info = {"mode": "fresh", "doc_id": d, "scratch_root": str(root), "code_dir": str(code_dir),
                                   "data_dir": str(data_dir), "generated_paths": facts["generated"],
                                   "sample_paths": [PDF_REL, f"daten/iso/docling/{d}.json", f"daten/iso/atome/{d}.json",
                                                    f"daten/iso/atome_prompt/{d}.txt", f"daten/gj/docs/{d}.json",
                                                    f"daten/gj/rules/{d}.json"],
                                   "output_prefixes": [f"{rel_out}/", "work/"]}
                host.TRACE.setup = False
            os.chdir(root)
            m = import_converter(host, root)
            pdftotext = set_pdftotext(host, m)
            seconds_setup = round(time.perf_counter() - t, 3)

            device = m.cv.STORED_SETTINGS["geraet"]
            if profile == "full" or os.environ.get("PARLPDFECH_FRESH_DEVICE") == "cpu":
                device = "cpu"
            name = "package_fresh"
            if ocr == "apple":
                run = m.cv.docling_main([pdf], docling_p.parent, root / "work/records", name, device, warmup=False)
            else:
                run = docling_no_ocr(m, pdf, docling_p.parent, root / "work/records", name, device)
            row = run["rows"].get(d) or {}
            if row.get("status") != "success" or not docling_p.is_file():
                host.log(f"Docling status {row.get('status')!r}")
                raise host.stopped("docling_status")
            dk = host.read_json(docling_p)
            if dk.get("sha256") != digest:
                raise host.stopped("docling_input")
            if not dk.get("bloecke") or not (dk.get("text_gesamt") or "").strip():
                # no block with text: a scan with no OCR result, or a page with pictures only
                raise host.Stop("no_text_layer", {}, 3)
            pages = len(dk.get("seiten") or [])
            page_sources = {}
            for s in dk.get("seiten") or []:
                page_sources[s.get("textquelle")] = page_sources.get(s.get("textquelle"), 0) + 1
            docling_info = {
                "arguments": [package_path(str(a), root) for a in run["arguments"]],
                "settings": dk["konfiguration"], "tools": dk["werkzeug"],
                "settings_equal_to_stored": {k: v for k, v in dk["konfiguration"].items()
                                             if m.cv.STORED_SETTINGS.get(k) != v} or "equal",
                "tools_equal_to_stored": {k: v for k, v in dk["werkzeug"].items()
                                          if m.cv.STORED_TOOLS.get(k) != v} or "equal",
                "backend": dk.get("backend"), "status": dk.get("status"), "pages": pages, "blocks": len(dk["bloecke"]),
                "page_text_sources": page_sources, "seconds_convert": float(row.get("sekunden") or 0),
                "seconds_initialize": run["summary"].get("init_s"), "seconds_call": run["seconds"],
                "completeness_against_pdftotext": (dk.get("pruefung") or {}).get("anteil_pdftotext_in_bloecken"),
                "pdftotext": Path(pdftotext).name, "device_argument": device}
            stages.done("read_pdf", "new", {"pages": pages})

            # ---- stage 2: lines (atoms) and the block file
            stages.start("lines")
            am = m.cv.atoms_of_docling(d, docling_p, pdf.parent, atoms_p.parent, root / "daten/iso/atome_prompt")
            bf = m.cv.block_file(d, None, None, docling_p, atoms_p, pdf)
            write_compact(docs_p, bf)
            atoms = host.read_json(atoms_p)
            n_lines, n_blocks = len(atoms["atome"]), len(bf["blocks"])
            stages.done("lines", "new", {"lines": n_lines, "blocks": n_blocks})

            # ---- stage 3: rules and floor decisions
            stages.start("rules")
            identity = m.rules.check_identity_record()
            m.runner.check_frozen_method()
            export_fields = {"found": False, "body_key": "", "affair_id": "", **{k: "" for k in m.runner.EXPORT_FIELDS}}
            rec = m.rules.run_document(d, export_fields, "loader", None)
            rules_p.parent.mkdir(parents=True, exist_ok=True)
            rules_p.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            floor = m.pipeline.load_floor()
            dec = m.cascade.floor_decisions(rec, floor.lookup, d in floor.fit_docs, floor.info)
            dec = m.pipeline.checked(dec, rec)
            if any(b.get("in_sample") for b in dec["blocks"]) or dec["document"]["d1"].get("in_sample"):
                raise host.stopped("in_sample")
            host.write_json(dec_p, dec)
            decisions_sha = host.sha256_file(dec_p)
            stages.done("rules", "new", {"blocks": len(rec["blocks"])})

            # ---- stage 4: Apertus. The provider of stage P0b gives no states.
            if str(Path(__file__).resolve().parent) not in sys.path:
                sys.path.append(str(Path(__file__).resolve().parent))
            import states_provider  # noqa: PLC0415
            prov = states_provider.provider("none")
            if prov.states_for(docs_p, host.sha256_file(docs_p), root / "work") is not None:
                raise host.stopped("states")
            stages.skipped("apertus", "mode_rules" if mode == "rules" else "not_in_package")

            # ---- stage 5: the record of a PDF with no export record, and the RDF files
            stages.start("write")
            vr = host.values_module()
            values_state = vr.state(None, digest)                # pdf, off or held (worker/values_record.py)
            hyphen = host.count_hyphen_decisions(m.gr)
            base = m.writer.check_base(os.environ.get("PARLPDFECH_CALIBRATION_BASE") or "https://parlpdfech.ansv.ch/id/")
            folder.mkdir(parents=True, exist_ok=True)
            measured = None
            signs = None
            if values_state == "pdf":
                measured = vr.calibration_file(root)[1]
                _, rdf_result = vr.write(root, folder, docs_p, rules_p, dec_p, None, None, Path(floor.path), base)
            else:
                import pdf_only  # noqa: PLC0415
                pdf_only.write_record(m, root, folder, docs_p, dec_p, floor.path, atoms_p, docling_p, pdf, digest, base)
                rdf_result = pdf_only.rdf_step(m, root, folder)
            man = host.read_json(folder / "manifest.json")
            n_labels = int(man["counts"]["label_assertions"])
            triples = int(rdf_result["triples"]["union"])
            stages.done("write", "new", {"labels": n_labels, "triples": triples})

            # ---- stage 6: checks, copy of the record, view function
            stages.start("check")
            if values_state == "pdf":
                validation = vr.validate(root, folder, None)
                check_ids = vr.CHECK_IDS
            else:
                validation = pdf_only.validate(m, root, folder)
                check_ids = host.CHECK_IDS
            man = host.read_json(folder / "manifest.json")
            valid = bool(man.get("check_passed") is True and validation.get("passed") is True)
            checks = {"writer_check": man.get("check_passed") is True}
            checks |= host.check_states(validation, check_ids)
            c10 = (validation.get("C10_shacl") or {}).get("status")
            n_skipped = (0 if c10 == "run" else 1) + sum(v is None for v in checks.values())
            n_passed = sum(v is True for v in checks.values()) \
                + (1 if c10 == "run" and (validation.get("C10_shacl") or {}).get("passed") else 0)
            check_module_places(host, root)
            try:                         # the copy to --out has its own note (not a failure of the checks)
                out.mkdir(parents=True, exist_ok=True)
                for n in RECORD_FILES:
                    shutil.copyfile(folder / n.format(d=d), out / n.format(d=d))
                host.relative_paths(out / "validation.json", root)
                # the file of the values, the PDF and the page images (record with values from the PDF only)
                extras = vr.record_extras(folder, out, d, pdf=pdf_path, max_pages=max_pages) \
                    if values_state == "pdf" else {"names": [], "pages": None}
            except OSError as e:
                host.log(f"the record cannot be written to --out: {type(e).__name__}")
                raise host.stopped("out") from None
            for role, n in OUTPUT_ROLE.items():
                if host.sha256_file(out / n.format(d=d)) != man["outputs"][role]["sha256"]:
                    raise host.stopped("copy")
            rdfxml = host.rdfxml_report(out, d, atoms["atome"], None, validation)
            inputs_dir = scratch / "view_inputs"
            inputs_dir.mkdir()
            shutil.copyfile(docling_p, inputs_dir / "docling.json")
            shutil.copyfile(atoms_p, inputs_dir / "atoms.json")
            shutil.copyfile(docs_p, inputs_dir / "blocks.json")
            shutil.copyfile(dec_p, inputs_dir / "decisions.json")
            sec = stages.seconds()
            sec["check"] = round(time.perf_counter() - stages._t["check"], 3)
            sec["total"] = round(time.perf_counter() - t_all, 3)
            run_info = {"record_id": record_id, "origin": "new", "mode": mode, "apertus": "none", "profile": profile,
                        "ocr": ocr, "seconds": dict(sec), "values": values_state}
            if values_state == "pdf":
                # finding S3-03: signs of a response in a document of the kind proposal (a notice of the view)
                signs = vr.response_signs(docs_p, rules_p, man)
                if signs is not None:
                    run_info["response_signs"] = signs
            view_state, view_note = host.run_view(view_dir, out, inputs_dir, run_info)
            stages.done("check", "new", {"passed": int(n_passed), "total": len(checks) + 1, "skipped": n_skipped},
                        note=view_note)
        except host.Stop as e:
            stages.failed(e.detail.get("note") or e.code)
            raise
        except host.Terminated:
            raise
        except (Exception, SystemExit) as e:  # noqa: BLE001  (each failure of a step is an internal stop)
            note = {"read_pdf": "docling", "lines": "lines", "rules": "rules", "apertus": "states", "write": "writer",
                    "check": "validator"}.get(stages.current or "", "setup")
            host.log(f"stopped in stage {stages.current}: {type(e).__name__}: {str(e)[:500]}")
            traceback.print_exc(file=sys.stderr)
            stages.failed(note)
            raise host.stopped(note) from None

        names = [n.format(d=d) for n in RECORD_FILES] + extras["names"] \
            + (["view.json"] if view_state == "written" else [])
        sec = stages.seconds()
        sec["total"] = round(time.perf_counter() - t_all, 3)
        counts = {"pages": pages, "lines": n_lines, "blocks": n_blocks, "labels": n_labels}
        exit_code = 0 if valid else 2
        convert = {
            "schema": host.CONVERT_SCHEMA, "record_id": record_id, "doc_id": None, "pdf_sha256": digest,
            "input": {"kind": "upload", "file_name": pdf_path.name}, "mode": mode, "converter_mode": man.get("mode"),
            "apertus": "none", "origin": "new", "profile": profile, "status": host.STATUS, "valid": valid,
            "valid_rule": "one or more checks failed" if not valid else vr.VALID_RULE if values_state == "pdf"
                          else "the writer check of worker/pdf_only.py and the checks C1 to C9 passed",
            "exit_code": exit_code, "started_utc": started, "finished_utc": host.utc_now(),
            "seconds": {**sec, "setup": seconds_setup,
                        "converter": {"docling_initialize": docling_info["seconds_initialize"],
                                      "docling_convert": docling_info["seconds_convert"], "atoms": am["seconds"],
                                      "write": (man.get("seconds") or {}).get("write"),
                                      "rdf": (man.get("rdf") or {}).get("seconds"),
                                      "validate": (man.get("seconds") or {}).get("validate")}},
            "stages": stages.table(),
            "counts": {**counts, "triples": triples, "apertus_labels": 0,
                       "certain_labels": man["counts"].get("certain_labels"),
                       "unsure_labels": man["counts"].get("unsure_labels"),
                       "label_assertions_by_source": man["counts"].get("label_assertions_by_source"),
                       "text_blocks": man["counts"].get("textblock_records_profile_only")},
            "checks": {**checks, "C10_shacl": c10}, "conformance": man.get("conformance"),
            "files": [{"name": n, "bytes": (out / n).stat().st_size, "sha256": host.sha256_file(out / n)} for n in names],
            "decisions_sha256": decisions_sha, "reference": None,
            "view": {"state": view_state, "note": view_note}, "page_images": extras["pages"],
            "rdfxml": rdfxml, "hyphen_word_counts": hyphen,
            "values": vr.summary(man, bool(measured), signs) if values_state == "pdf" else vr.earlier(values_state),
            "fresh": {"version": FRESH_VERSION, "document_iri": man.get("source_iri"), "export_record": None,
                      "pdf_check": check, "ocr": ocr, "docling": docling_info,
                      "atoms": {"status": am["status"], "complete": am["complete"], "count": am["atom_count"]},
                      "language": bf.get("language"),
                      "rules": {"admission": rec["admission"], "export_fields": "empty (no export record)",
                                "s1_rule_id": rec["document"]["s1"]["rule_id"],
                                "needs_apertus": rec["document"]["d1"]["needs_apertus"],
                                "identity_record_sha256": identity["sha256"]},
                      "reduced_tables": {"file": "worker/fresh_tables.json", "sha256": facts["tables_sha256"],
                                         "paths": facts["generated"]},
                      "states_provider": {"kind": prov.kind},
                      "search_path_entries_removed": LayoutFinder.removed,
                      "sample_of_the_package": False,
                      "development_document": None,
                      "not_measured": "The probabilities of this record were not checked on other documents. This "
                                      "PDF is not one of the samples of the package. The package cannot tell if it "
                                      "is one of the development documents (key development_document null = not "
                                      "known). No value of a report applies."},
            "resources": host.max_rss(), "tools": host.tool_versions(), "worker_version": host.WORKER_VERSION}
        host.write_out(out / "convert.json", convert)
        host.emit({"event": "done", "record_id": record_id, "doc_id": None, "valid": valid, "mode": mode,
                   "apertus": "none", "origin": "new", "pdf_sha256": digest, "seconds": sec, "counts": counts,
                   "files": names + ["convert.json"]})
        return exit_code
    finally:
        with contextlib.suppress(OSError):
            os.chdir(start_dir)
        if host.TRACE:
            host.TRACE.on = False
        if scratch is not None and not keep:
            shutil.rmtree(scratch, ignore_errors=True)
