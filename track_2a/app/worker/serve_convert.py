#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package (stages P0a and P0b): one conversion in one process.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

Command (contract chapter 4.1)
  serve_convert.py --sample <doc id> --mode auto|rules --out <dir> [--data-dir D]
  serve_convert.py --pdf <file> [--doc-id N] --mode auto|rules --out <dir> [--data-dir D]

Modes
  auto   a sample: the decisions of candidate B1-S from the stored Apertus states of the sample
         (the functions worker_state and decisions_of of the batch tool m10_fullrun2).
  rules  the floor decisions from the stored rule record (decide of m10_pipeline with the mode floor,
         as the batch tool m10_fullrun does it in the floor mode). No Apertus state is read.
  Then, in the two modes: the record whose head values are read from the PDF (worker/values_record.py:
  the value readers of m11_values_base, write_record and rdf_step of m11_writer, validate_record of
  m11_validate). The export record of the sample is the cross-check only. The worker imports these
  functions. It does not change a converter file.
  The earlier record path (write_one of m10_writer, convert_record of m10_rdf, validate_record of
  m10_validate: head values from the export) runs with PARLPDFECH_VALUES=off and for a sample that
  worker/values_hold.json names.

How one run works
  1. The worker makes a scratch root: copies of the converter files of the code layout
     (PARLPDFECH_CODE_DIR, made by worker/layout.py) and the stored inputs of the sample
     (<data dir>/samples/<doc>/) under their project paths. It checks the SHA-256 of each copy.
  2. It writes 5 small registry files for the run (one row for the sample) and gives the split guard a
     table in memory. worker/layout_files.json lists these files and what they replace.
  3. It imports the converter from the scratch root and runs the steps.
  4. It copies the 9 converter files to --out, adds view.json (view function) and convert.json, and
     deletes the scratch root.
  The worker reads nothing from the project folders src/ and daten/. PARLPDFECH_TRACE=FILE writes
  the list of each opened path of a run to FILE.

Standard output: JSON lines (contract chapter 4.2). Standard error: a log.
Exit codes: 0 valid record; 2 record written, one or more checks failed; 3 refused; 4 internal stop.

A PDF that is not a sample: convert_fresh() calls the fresh branch worker/fresh.py (stage P0b, code rules
only, profiles native and full). The profile slim refuses such a PDF with the code not_in_package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import sys
import tempfile
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

WORKER_VERSION = "parlpdfech-worker/0.1.0"
STATUS = "EXCEPTION, NOT RELEASED"
CONVERT_SCHEMA = "parlpdfech-convert/1"
PACKAGE = Path(__file__).resolve().parents[1]
STAGES = ("read_pdf", "lines", "rules", "apertus", "write", "check")
OUT_FOLDER = {"auto": "daten/gj/fullrun_b1s_dev",       # the folder of the reference run (contract chapter 4.4)
              "rules": "daten/gj/package_rules"}
DESIGN_B1S = "daten/gj/design_b1s/design_b1s.json"
SET_NAMES = ("dev", "dev_out_of_design", "validation", "group7", "pilot_overrides")
RECORD_FILES = ("{d}.gesamt.trig", "{d}.ech.ttl", "{d}.gesamt.rdf.xml", "{d}.ech.rdf.xml", "{d}.ech.yaml",
                "{d}.labels.yaml", "{d}.provenance.yaml", "manifest.json", "validation.json")
OUTPUT_ROLE = {"gesamt_trig": "{d}.gesamt.trig", "ech_ttl": "{d}.ech.ttl", "gesamt_rdfxml": "{d}.gesamt.rdf.xml",
               "ech_rdfxml": "{d}.ech.rdf.xml", "ech_yaml": "{d}.ech.yaml", "labels_yaml": "{d}.labels.yaml",
               "provenance_yaml": "{d}.provenance.yaml"}
CHECK_IDS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme",
             "C7_C8_labels", "C9_e19")
APERTUS_SOURCES = ("apertus_head", "code")     # interface 7 names; the writer writes code as code_step


# ---------------------------------------------------------------------------------------------- output lines
_OUT = None


def protect_stdout() -> None:
    """Standard output holds only the JSON lines of the worker. Each other print goes to standard error."""
    global _OUT
    sys.stdout.flush()
    _OUT = os.fdopen(os.dup(1), "w", encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr


def emit(obj: dict) -> None:
    out = _OUT or sys.stdout
    out.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    out.flush()


def log(msg: str) -> None:
    print(f"[worker] {msg}", file=sys.stderr, flush=True)


class Stop(Exception):
    """The run ends with the line failed. exit 3: refused before a conversion. exit 4: internal stop."""

    def __init__(self, code: str, detail: dict | None = None, exit_code: int = 3):
        super().__init__(code)
        self.code, self.detail, self.exit_code = code, detail or {}, exit_code


def stopped(note: str) -> Stop:
    return Stop("converter_stopped", {"note": note}, 4)


class Terminated(BaseException):
    """The server stopped the process (SIGTERM)."""


class Stages:
    """The stage events of contract chapter 4.2."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self._t: dict[str, float] = {}
        self.current: str | None = None

    def start(self, sid: str) -> None:
        self.current = sid
        self._t[sid] = time.perf_counter()
        emit({"event": "stage", "id": sid, "state": "running"})

    def done(self, sid: str, origin: str, counts: dict, note: str | None = None) -> None:
        row = {"event": "stage", "id": sid, "state": "done", "origin": origin,
               "seconds": round(time.perf_counter() - self._t[sid], 3), "counts": counts}
        if note:
            row["note"] = note
        self.rows[sid] = row
        self.current = None
        emit(row)

    def skipped(self, sid: str, reason: str) -> None:
        row = {"event": "stage", "id": sid, "state": "skipped", "reason": reason}
        self.rows[sid] = row
        emit(row)

    def failed(self, reason: str) -> None:
        sid = self.current
        if sid is None:
            return
        row = {"event": "stage", "id": sid, "state": "failed",
               "seconds": round(time.perf_counter() - self._t[sid], 3), "reason": reason}
        self.rows[sid] = row
        self.current = None
        emit(row)

    def seconds(self) -> dict:
        return {s: self.rows.get(s, {}).get("seconds", 0) or 0 for s in STAGES}

    def table(self) -> list[dict]:
        return [{k: v for k, v in self.rows[s].items() if k != "event"} for s in STAGES if s in self.rows]


# ---------------------------------------------------------------------------------------------- small helpers
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def write_out(p: Path, obj) -> None:
    """write_json for a file of --out. A failure of the file system gives the note out."""
    try:
        write_json(p, obj)
    except OSError as e:
        log(f"{p.name} cannot be written to --out: {type(e).__name__}")
        raise stopped("out") from None


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def max_rss() -> dict:
    """The peak memory of this process in bytes. ru_maxrss is in bytes on macOS and in kilobytes on Linux."""
    try:
        import resource
        raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (ImportError, OSError, ValueError):
        return {"max_rss_bytes": None, "ru_maxrss_raw": None, "ru_maxrss_unit": None, "platform": sys.platform}
    unit = "bytes" if sys.platform == "darwin" else "kilobytes"
    return {"max_rss_bytes": raw if unit == "bytes" else raw * 1024, "ru_maxrss_raw": raw, "ru_maxrss_unit": unit,
            "platform": sys.platform}


def tool_versions() -> dict:
    from importlib.metadata import PackageNotFoundError, version
    out = {"python": ".".join(str(x) for x in sys.version_info[:3]), "platform": sys.platform}
    for name in ("numpy", "scipy", "rdflib", "linkml", "linkml-runtime", "PyYAML"):
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


# ---------------------------------------------------------------------------------------------- XML 1.0 handling
# The RDF step writes RDF/XML with rdflib. XML 1.0 permits only these characters (production Char):
# U+0009, U+000A, U+000D, U+0020 to U+D7FF, U+E000 to U+FFFD, U+10000 to U+10FFFF.
# An atom text with another character (measured in 2 of 1,793 development documents: U+0007) gives an
# RDF/XML file that no XML parser reads. The TriG file and the Turtle file hold the character as an
# escape and parse. The worker does not change the files of the RDF step. It records the fact.
_XML10_FORBIDDEN = re.compile("[^\u0009\u000a\u000d\u0020-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")


def xml10_forbidden(text: str) -> list[str]:
    """The characters of text that XML 1.0 cannot hold, as sorted code point names (for example U+0007)."""
    return sorted({f"U+{ord(c):04X}" for c in _XML10_FORBIDDEN.findall(text)})


def strings_of(obj):
    """Each string value of a JSON value."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings_of(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings_of(v)


def xml_well_formed(data: bytes) -> tuple[bool, str | None]:
    """True if an XML 1.0 parser (expat of the standard library) reads the bytes to the end."""
    from xml.parsers import expat
    parser = expat.ParserCreate()
    try:
        parser.Parse(data, True)
    except expat.ExpatError as e:
        return False, f"{expat.ErrorString(e.code)} (line {e.lineno}, column {e.offset})"
    return True, None


def rdfxml_report(record_dir: Path, d: str, atoms: list[dict], export: dict | None, validation: dict | None) -> dict:
    """The state of the two RDF/XML files of a record (new code of the package, not a converter step).
    representable is false if an XML parser does not read a file. Then the TriG file is the reference form."""
    files = []
    for name in (f"{d}.gesamt.rdf.xml", f"{d}.ech.rdf.xml"):
        p = record_dir / name
        if not p.is_file():
            files.append({"name": name, "well_formed": None, "error": "absent"})
            continue
        ok, err = xml_well_formed(p.read_bytes())
        files.append({"name": name, "well_formed": ok, "error": err})
    bad_atoms = [{"atom_id": a.get("id"), "code_points": cp} for a in atoms
                 if (cp := xml10_forbidden("".join(strings_of(a))))]
    export_cp = xml10_forbidden("".join(strings_of(export))) if export is not None else []
    representable = all(f["well_formed"] is True for f in files)
    c2 = {x.get("file"): x.get("parsed") for x in ((validation or {}).get("C2_parse") or {}).get("results") or []}
    out = {"representable": representable, "files": files,
           "xml10_forbidden_characters": {"atoms": bad_atoms, "export_record": export_cp,
                                          "code_points": sorted({c for a in bad_atoms for c in a["code_points"]}
                                                                | set(export_cp))},
           "reference_form": f"{d}.gesamt.trig",
           "trig_parsed": c2.get(f"{d}.gesamt.trig"), "turtle_parsed": c2.get(f"{d}.ech.ttl")}
    if not representable:
        out["note"] = ("One or more RDF/XML files are not well-formed XML 1.0. The files are the bytes of the RDF "
                       "step, not changed. Use the TriG file. Check C2_parse of validation.json fails for this record.")
    elif bad_atoms or export_cp:
        out["note"] = "An input holds a character that XML 1.0 cannot hold, but the RDF/XML files are well-formed."
    return out


# ---------------------------------------------------------------------------------------------- trace (proof tool)
class Trace:
    """PARLPDFECH_TRACE=FILE: each path that the process opens or lists, each subprocess and each
    network call (Python audit events). The file is a build record. A normal run does not use it."""

    EVENTS_LIST = ("os.listdir", "os.scandir", "glob.glob")
    EVENTS_NET = ("socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto", "urllib.Request")

    def __init__(self, path: str) -> None:
        self.path = Path(path).resolve()
        self.opened: set[str] = set()          # after the scratch root is made: the reads of the converter
        self.opened_setup: set[str] = set()    # before: the start of Python and the copies into the scratch root
        self.setup = True
        self.listed: set[str] = set()
        self.subprocess: list[str] = []
        self.network: list[str] = []
        self.info: dict = {}
        self.on = True
        sys.addaudithook(self._hook)

    def _hook(self, event: str, args) -> None:
        if not self.on:
            return
        try:
            if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
                p = os.fspath(args[0])
                (self.opened_setup if self.setup else self.opened).add(
                    os.path.abspath(p.decode() if isinstance(p, bytes) else p))
            elif event in self.EVENTS_LIST and args and isinstance(args[0], (str, bytes, os.PathLike)):
                p = os.fspath(args[0])
                self.listed.add(os.path.abspath(p.decode() if isinstance(p, bytes) else p))
            elif event == "subprocess.Popen":
                self.subprocess.append(str(args[0]))
            elif event in self.EVENTS_NET:
                frames = [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in traceback.extract_stack(limit=9)[:-1]]
                self.network.append({"event": event, "address": repr(args[1])[:80] if len(args) > 1 else None,
                                     "stack": frames})
        except Exception:  # noqa: BLE001  (a trace problem never stops a run)
            pass

    def write(self) -> None:
        self.on = False
        imported = sorted({os.path.abspath(f) for m in list(sys.modules.values())
                           if isinstance(f := getattr(m, "__file__", None), str)})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        obj = {"schema": "parlpdfech-trace/1", **self.info, "opened": sorted(self.opened),
               "opened_setup": sorted(self.opened_setup), "imported": imported, "listed": sorted(self.listed),
               "subprocess": self.subprocess, "network": self.network}
        self.path.write_text(json.dumps(obj, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")


TRACE: Trace | None = None


# ---------------------------------------------------------------------------------------------- scratch root
def keep_home_clean(scratch: Path) -> None:
    """The library pystow (a dependency of linkml-runtime, through prefixmaps and curies) makes its data folder
    and one README.md file when it is imported. With no setting, the place is the folder .data in the home folder
    of the user. PYSTOW_HOME puts it below the scratch folder of the job, which the worker deletes at the end.
    The worker sets the variable before the first import of a converter file.
    The folder for temporary files of the process and of its child processes (TMPDIR) is also a folder below the
    scratch folder of the job: Docling and torch make temporary files and one folder whose name holds the name
    of the user account."""
    os.environ["PYSTOW_HOME"] = str(scratch / "pystow")
    tmp = scratch / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ["TMPDIR"] = str(tmp)
    tempfile.tempdir = None            # the module tempfile reads TMPDIR again


def copy_checked(src: Path, dst: Path, want: str, note: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if sha256_file(dst) != want:
        log(f"SHA-256 of {dst.name} differs from the recorded value")
        raise stopped(note)


def copy_compiled(layout: dict, code_dir: Path, root: Path, files: list[dict]) -> int:
    """Copies the compiled files of layout.py into the scratch root (same modification times, so Python uses
    them). A compiled file is copied only if its SHA-256 is the value that layout.py recorded in the manifest.
    A file with another SHA-256, or a manifest with no record, gives no copy: Python then compiles the source
    file, whose SHA-256 was checked. Returns the number of copies."""
    cache = code_dir / "src" / "__pycache__"
    recorded = {c["name"]: c["sha256"] for c in layout.get("compiled") or []}
    copied = 0
    if not cache.is_dir() or not recorded:
        return copied
    (root / "src" / "__pycache__").mkdir(parents=True, exist_ok=True)
    for f in files:
        if f["path"].startswith("src/") and f["path"].endswith(".py"):
            pyc = cache / f"{Path(f['path']).stem}.{sys.implementation.cache_tag}.pyc"
            if not pyc.is_file():
                continue
            if recorded.get(pyc.name) != sha256_file(pyc):
                log(f"compiled file {pyc.name}: not the file of the layout build; not used")
                continue
            shutil.copy2(pyc, root / "src" / "__pycache__" / pyc.name)
            copied += 1
    return copied


def relative_paths(path: Path, root: Path) -> int:
    """validation.json of a record with a failed parse check holds error texts of the parser with the
    absolute path of the scratch root. The worker makes these paths relative (the text of the scratch root
    is removed). No other byte changes. Returns the number of replacements. A file with no such path is
    not written again."""
    text = path.read_text(encoding="utf-8")
    count = text.count(str(root))
    if not count:
        return 0
    for form in (f"file://{root}/", f"{root}/", f"file://{root}", str(root)):
        text = text.replace(form, "")
    path.write_text(text, encoding="utf-8")
    return count


def check_states(validation: dict, check_ids) -> dict:
    """The result of each check of validation.json: True (passed), False (failed) or None (the validator did
    not run the check: it stops after a failed parse check)."""
    out = {}
    for k in check_ids:
        entry = validation.get(k)
        out[k] = None if not isinstance(entry, dict) or "passed" not in entry else entry.get("passed") is True
    return out


def build_root(root: Path, code_dir: Path, sample_dir: Path, sample: dict, mode: str) -> dict:
    """The scratch root: the converter files of the mode, the inputs of the sample, the registry files of the
    run. Returns the facts that the run needs."""
    n = 2 if mode == "auto" else 1
    d = sample["doc_id"]
    man_p = code_dir / "layout_manifest.json"
    if not man_p.is_file():
        log("no layout_manifest.json in the code layout: run worker/layout.py")
        raise stopped("layout")
    layout = read_json(man_p)
    by_path = {f["path"]: f for f in layout["files"]}
    for f in layout["files"]:
        if n not in f["modes"]:
            continue
        src = code_dir / f["path"]
        if not src.is_file():
            log(f"layout file absent: {f['path']}")
            raise stopped("layout")
        copy_checked(src, root / f["path"], f["sha256"], "layout")
    copy_compiled(layout, code_dir, root, [f for f in layout["files"] if n in f["modes"]])
    placed, sha_of = [], {}
    for f in sample["files"]:
        if f.get("project_path") is None or n not in f["modes"] or f["name"] == "export.json":
            continue
        copy_checked(sample_dir / f["name"], root / f["project_path"], f["sha256"], "sample")
        placed.append(f["project_path"])
        sha_of[f["name"]] = f["sha256"]
    path_of = {f["name"]: f["project_path"] for f in sample["files"]}
    export_entry = next(f for f in sample["files"] if f["name"] == "export.json")
    if sha256_file(sample_dir / "export.json") != export_entry["sha256"]:
        raise stopped("sample")
    # registry files of the run (worker/layout_files.json key generated_for_each_run)
    generated = ["daten/gj/sets.json", "daten/gj/docs_build.json", "daten/gj/runs/m10_rules_run.json",
                 "daten/gj/labels_build.json"]
    write_json(root / generated[0], {k: ([d] if k in (sample.get("sets") or []) else []) for k in SET_NAMES})
    write_json(root / generated[1], {"outputs": {path_of["blocks.json"]: sha_of["blocks.json"]}})
    write_json(root / generated[2], {"outputs": {path_of["rules.json"]: sha_of["rules.json"]}})
    write_json(root / generated[3], {"outputs": {}})
    facts = {"placed": placed, "generated": generated, "by_path": by_path, "path_of": path_of}
    if mode == "auto":
        r2 = read_json(sample_dir / "r2.json")
        write_json(root / r2["source"]["path"], {d: r2["value"]})
        generated.append(r2["source"]["path"])
        facts["r2_values"] = root / r2["source"]["path"]
        facts["r2_calibrations"] = root / r2["calibrations"]["path"]
        facts["states_job"] = root / sample["states_job"]
        if DESIGN_B1S not in by_path:
            raise stopped("layout")
        facts["design_b1s_sha256"] = by_path[DESIGN_B1S]["sha256"]
    return facts


def set_guard_table(guard, d: str, blocks: dict) -> None:
    """The split guard of the converter gets one table in memory: the parliament of the sample with the split
    dev. The package holds no split table and no list of protected ids. A block file with another split stops."""
    if blocks.get("split") != "dev" or not blocks.get("parliament"):
        log("the block file of the sample does not have the split dev")
        raise stopped("guard")
    parl = str(blocks["parliament"])
    guard._TABLES = guard.Tables(roles={parl: "Training"}, path2={parl: "dev"}, group7=frozenset(guard.GROUP7),
                                 r8=frozenset(), protected=frozenset(), bodies={d: {parl}}, sources={}, exempt={},
                                 from_disk=False)


def count_hyphen_decisions(gr) -> dict:
    """A counter around default_keep_hyphen of m03_gold_record. It does not change a result. The word counts of
    that function come from the atoms in the scratch root: the sample document only (see README, limits)."""
    counter = {"scope": "the atoms of this document only", "line_end_hyphen_decisions": 0, "decided_by_word_counts": 0}
    orig = gr.default_keep_hyphen

    def counted(left: str, right: str) -> bool:
        result = orig(left, right)
        try:
            counter["line_end_hyphen_decisions"] += 1
            if left and not left[-1:].isdigit() and not right[:1].isdigit():
                v = gr.hyphen_vocab()
                if v.get((left + right).lower(), 0) != v.get(f"{left}-{right}".lower(), 0):
                    counter["decided_by_word_counts"] += 1
        except Exception:  # noqa: BLE001  (the counter never stops a run)
            pass
        return result

    gr.default_keep_hyphen = counted
    return counter


# ---------------------------------------------------------------------------------------------- view
def run_view(view_dir: Path, record_dir: Path, inputs_dir: Path, run_info: dict) -> tuple[str, str | None]:
    """Calls make_view of view/site_view.py and writes view.json. Returns (state, note). A problem of the view
    never stops the conversion: the record then has no view.json, and the stage check carries a note."""
    if not (view_dir / "site_view.py").is_file():
        return "absent", "view_absent"
    try:
        if str(view_dir) not in sys.path:
            sys.path.insert(0, str(view_dir))
        import site_view  # noqa: PLC0415
        view = site_view.make_view(record_dir, inputs_dir, run_info)
        text = json.dumps(view, ensure_ascii=False, indent=1) + "\n"
        try:
            (record_dir / "view.json").write_text(text, encoding="utf-8")
        except OSError as e:
            log(f"view.json cannot be written to --out: {type(e).__name__}")
            raise stopped("out") from None
    except Stop:
        raise
    except (Exception, SystemExit) as e:  # noqa: BLE001
        log(f"view function failed: {type(e).__name__}: {str(e)[:300]}")
        traceback.print_exc(file=sys.stderr)
        (record_dir / "view.json").unlink(missing_ok=True)
        return "failed", "view_failed"
    return "written", None


# ---------------------------------------------------------------------------------------------- one sample
def values_module():
    """worker/values_record.py (the folder of this file is not in the module search path of each caller)."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.append(here)
    import values_record  # noqa: PLC0415
    return values_record


def convert_sample(sample_dir: Path, mode: str, out: Path, code_dir: Path, view_dir: Path, profile: str,
                   input_info: dict, scratch_base: Path) -> int:
    t_all = time.perf_counter()
    vr = values_module()
    started = utc_now()
    stages = Stages()
    sample = read_json(sample_dir / "sample.json")
    d = str(sample["doc_id"])
    record_id = f"s-{d}" + ("-rules" if mode == "rules" else "")
    apertus = "stored" if mode == "auto" else "none"
    values_state = vr.state(d, sample.get("pdf_sha256"))    # pdf, off or held (worker/values_record.py)
    scratch = Path(tempfile.mkdtemp(prefix="parlpdfech-", dir=scratch_base)).resolve()
    keep_home_clean(scratch)
    root = scratch / "root"
    keep = os.environ.get("PARLPDFECH_KEEP_SCRATCH") == "1"
    seconds_setup = 0.0
    folder: Path | None = None
    try:
        try:
            # set-up: scratch root (not a stage of the contract; its time is in convert.json key seconds.setup)
            t = time.perf_counter()
            facts = build_root(root, code_dir, sample_dir, sample, mode)
            rel_out = OUT_FOLDER[mode]
            out_dir = root / rel_out
            folder = out_dir / d
            if TRACE:
                TRACE.info = {"mode": mode, "doc_id": d, "scratch_root": str(root), "code_dir": str(code_dir),
                              "data_dir": str(sample_dir.parent.parent), "sample_paths": facts["placed"],
                              "generated_paths": facts["generated"],
                              "output_prefixes": [f"{rel_out}/{d}/", f"{rel_out}/decisions/"]}
                TRACE.setup = False
            os.chdir(root)
            sys.path.insert(0, str(root / "src"))
            seconds_setup = round(time.perf_counter() - t, 3)

            # stage 1: the stored Docling output of the PDF
            stages.start("read_pdf")
            docling = read_json(sample_dir / "docling.json")
            if docling.get("sha256") != sample["pdf_sha256"] or str(docling.get("doc_id")) != d:
                raise stopped("sample")
            pages = len(docling.get("seiten") or [])
            stages.done("read_pdf", "stored", {"pages": pages})

            # stage 2: the stored lines (atoms) and the stored block file
            stages.start("lines")
            atoms = read_json(sample_dir / "atoms.json")
            blocks = read_json(sample_dir / "blocks.json")
            n_lines, n_blocks = len(atoms["atome"]), len(blocks["blocks"])
            stages.done("lines", "stored", {"lines": n_lines, "blocks": n_blocks})

            # stage 3: the stored rule record; in the mode rules also the floor decisions
            stages.start("rules")
            rules = read_json(sample_dir / "rules.json")
            import m10_guard as guard  # noqa: PLC0415
            set_guard_table(guard, d, blocks)
            import m10_fullrun as fr  # noqa: PLC0415
            import m10_pipeline as pipeline  # noqa: PLC0415
            if Path(fr.ROOT).resolve() != root:
                raise stopped("layout")
            base = fr.DEFAULT_BASE
            export = read_json(sample_dir / "export.json")
            dec, st, cfg, fr2 = None, None, None, None
            if mode == "rules":
                cal_path = Path(pipeline.cal.FLOOR_FILE)
                params = {"base": base, "calibrations": {"abs": str(cal_path), "sha256": sha256_file(cal_path)},
                          "output_scripts": {k: fr.sha256(root / v) for k, v in fr.OUTPUT_SCRIPTS.items()}}
                cfg = {"key": f"{out_dir}|rules", "out": str(out_dir), "mode": "floor", "base": base,
                       "floor_file": str(cal_path), "calibrations": str(cal_path), "design": None, "freeze": None,
                       "params": params}
                st = fr.worker_state(cfg)
                dec = pipeline.decide(d, "floor", None, None, False, False, None, floor=st["floor"])
                decisions_sha = fr.write_json(out_dir / "decisions" / f"{d}.json", dec)
            stages.done("rules", "stored", {"blocks": len(rules["blocks"])})

            # stage 4: the decisions of candidate B1-S from the stored Apertus states (mode auto only)
            if mode == "rules":
                stages.skipped("apertus", "mode_rules")
                n_apertus = 0
            else:
                stages.start("apertus")
                import m10_fullrun2 as fr2  # noqa: PLC0415
                cal_path = out_dir / "calibrations.json"
                opts = {"design_b1s_sha256": facts["design_b1s_sha256"]}
                frozen = pipeline.load_design(None, None, require_freeze=True)
                cand = fr2.CANDIDATES["b1s"](opts, frozen)
                params = {"schema": fr2.PARAMS_SCHEMA, "candidate": cand.name, "candidate_label": cand.label,
                          "entry": cand.entry, "candidate_files": cand.files, "base": base,
                          "calibrations": {"path": fr2.rel(cal_path), "sha256": sha256_file(cal_path),
                                           "abs": str(cal_path)},
                          "output_scripts": {k: fr2.sha256(root / v) for k, v in fr.OUTPUT_SCRIPTS.items()}}
                cfg = {"key": f"{out_dir}|auto", "out": str(out_dir), "candidate": "b1s", "candidate_options": opts,
                       "base": base, "floor_file": str(pipeline.cal.FLOOR_FILE), "states": [str(facts["states_job"])],
                       "calibrations": str(cal_path), "r2": [str(facts["r2_values"])],
                       "r2_calibrations": [str(facts["r2_calibrations"])], "held_out_allowed": False, "params": params}
                st = fr2.worker_state(cfg)
                gate = st["cand"].gate([d])
                dec = fr2.decisions_of(d, st, cfg, gate)
                if dec.get("fallback") or dec.get("no_states"):
                    log("the candidate gave the floor fallback for a sample with a states file")
                    raise stopped("decisions")
                decisions_sha = fr2.write_json(out_dir / "decisions" / f"{d}.json", dec)
                n_apertus = sum(b.get("source") in APERTUS_SOURCES for b in dec["blocks"]) \
                    + sum(x.get("source") in APERTUS_SOURCES for x in dec.get("boundaries") or []) \
                    + (dec["document"]["d1"].get("source") in APERTUS_SOURCES) + (dec.get("r2") is not None)
                stages.done("apertus", "stored", {"labels": int(n_apertus)})

            # stage 5: writer and RDF step
            stages.start("write")
            hyphen = count_hyphen_decisions(sys.modules["m03_gold_record"])
            measured = None
            signs = None
            if values_state == "pdf":
                # the head values are read from the PDF; the export record is the cross-check only
                measured = vr.calibration_file(root)[1]
                vr.write(root, folder, root / facts["path_of"]["blocks.json"], root / facts["path_of"]["rules.json"],
                         out_dir / "decisions" / f"{d}.json", export, base, Path(cal_path))
            else:
                st["writer"].write_one(d, out_dir, None, export, st["cals"], st["cal_file"], base, fr.DOCS_DIR,
                                       out_dir / "decisions")
                st["rdf"].convert_record(folder, d, base)
            man = read_json(folder / "manifest.json")
            n_labels = int(man["counts"]["label_assertions"])
            triples = int(man["rdf"]["triples"]["union"])
            stages.done("write", "new", {"labels": n_labels, "triples": triples})

            # stage 6: validator, copy of the record, view function
            stages.start("check")
            if values_state == "pdf":
                vr.validate(root, folder, export)
                check_ids = vr.CHECK_IDS
            else:
                st["val"].validate_record(folder, d)
                check_ids = CHECK_IDS
                if mode == "auto":
                    state = fr2.document_state(out_dir, d, params)
                    valid, why = state["result"] == "valid", state["why"]
                else:
                    valid, why = fr.valid_output(out_dir, d, params)
            man = read_json(folder / "manifest.json")
            validation = read_json(folder / "validation.json")
            if values_state == "pdf":
                valid = man.get("check_passed") is True and validation.get("passed") is True
                why = vr.VALID_RULE if valid else "one or more checks failed"
            checks = {"writer_check": man.get("check_passed") is True}
            checks |= check_states(validation, check_ids)
            c10 = (validation.get("C10_shacl") or {}).get("status")
            # a check that the validator did not run counts as not run, not as failed
            n_skipped = (0 if c10 == "run" else 1) + sum(v is None for v in checks.values())
            n_passed = sum(v is True for v in checks.values()) \
                + (1 if c10 == "run" and (validation.get("C10_shacl") or {}).get("passed") else 0)
            # the copy to --out has its own note: a failure here is not a failure of the validator
            try:
                out.mkdir(parents=True, exist_ok=True)
                for name in RECORD_FILES:
                    shutil.copyfile(folder / name.format(d=d), out / name.format(d=d))
                validation_paths = relative_paths(out / "validation.json", root)
                # the file of the values, the PDF and the page images (record with values from the PDF only)
                extras = vr.record_extras(folder, out, d, sample_dir=sample_dir) if values_state == "pdf" \
                    else {"names": [], "pages": None}
            except OSError as e:
                log(f"the record cannot be written to --out: {type(e).__name__}")
                raise stopped("out") from None
            for role, name in OUTPUT_ROLE.items():
                if sha256_file(out / name.format(d=d)) != man["outputs"][role]["sha256"]:
                    raise stopped("copy")
            rdfxml = rdfxml_report(out, d, atoms["atome"], export, validation)
            inputs_dir = scratch / "view_inputs"
            inputs_dir.mkdir()
            for name in ("docling.json", "atoms.json", "blocks.json", "export.json"):
                shutil.copyfile(sample_dir / name, inputs_dir / name)
            shutil.copyfile(out_dir / "decisions" / f"{d}.json", inputs_dir / "decisions.json")
            sec = stages.seconds()
            sec["check"] = round(time.perf_counter() - stages._t["check"], 3)
            sec["total"] = round(time.perf_counter() - t_all, 3)
            run_info = {"record_id": record_id, "origin": "stored", "mode": mode, "apertus": apertus,
                        "profile": profile, "seconds": dict(sec), "values": values_state}
            if values_state == "pdf":
                # finding S3-03: signs of a response in a document of the kind proposal (a notice of the view)
                signs = vr.response_signs(root / facts["path_of"]["blocks.json"], root / facts["path_of"]["rules.json"],
                                          read_json(folder / "manifest.json"))
                if signs is not None:
                    run_info["response_signs"] = signs
            view_state, view_note = run_view(view_dir, out, inputs_dir, run_info)
            stages.done("check", "new", {"passed": int(n_passed), "total": len(checks) + 1, "skipped": n_skipped},
                        note=view_note)
        except Stop as e:
            stages.failed(e.detail.get("note") or e.code)
            raise
        except (Exception, SystemExit) as e:  # noqa: BLE001  (each failure of a converter step is an internal stop)
            note = {"read_pdf": "sample", "lines": "sample", "rules": "rules", "apertus": "decisions",
                    "write": "writer", "check": "validator"}.get(stages.current or "", "setup")
            if stages.current == "write" and folder is not None and (folder / "manifest.json").is_file():
                note = "rdf"
            log(f"stopped in stage {stages.current}: {type(e).__name__}: {str(e)[:500]}")
            traceback.print_exc(file=sys.stderr)
            stages.failed(note)
            raise stopped(note) from None

        # convert.json and the last line
        names = [n.format(d=d) for n in RECORD_FILES] + extras["names"] \
            + (["view.json"] if view_state == "written" else [])
        sec = stages.seconds()
        sec["total"] = round(time.perf_counter() - t_all, 3)
        counts = {"pages": pages, "lines": n_lines, "blocks": n_blocks, "labels": n_labels}
        ref_p, reference = sample_dir / "reference.json", None
        if mode == "auto" and ref_p.is_file() and values_state != "pdf":
            # the reference run has the earlier record form (head values from the export): it is the reference
            # of the earlier record path only
            ref = read_json(ref_p)
            reference = {"decisions_sha256_equal": ref.get("decisions_sha256") == decisions_sha,
                         "outputs_sha256_equal": {r: man["outputs"][r]["sha256"] == (ref.get("outputs") or {}).get(r)
                                                  for r in OUTPUT_ROLE},
                         "note": "A file that holds the run time has another SHA-256 than the reference file. The "
                                 "RDF step writes the elements of an RDF/XML file in another sequence in each run. "
                                 "worker/check_worker.py compares these files after the replacement of the run time "
                                 "and as graphs."}
        exit_code = 0 if valid else 2
        convert = {"schema": CONVERT_SCHEMA, "record_id": record_id, "doc_id": d, "pdf_sha256": sample["pdf_sha256"],
                   "input": input_info, "mode": mode, "converter_mode": man.get("mode"), "apertus": apertus,
                   "origin": "stored", "profile": profile, "status": STATUS, "valid": bool(valid),
                   "valid_rule": why, "exit_code": exit_code, "started_utc": started, "finished_utc": utc_now(),
                   "seconds": {**sec, "setup": seconds_setup,
                               "converter": {k: man.get("seconds", {}).get(k) for k in ("write", "validate")}
                               | {"rdf": (man.get("rdf") or {}).get("seconds")}},
                   "stages": stages.table(),
                   "counts": {**counts, "triples": triples, "apertus_labels": int(n_apertus),
                              "certain_labels": man["counts"].get("certain_labels"),
                              "unsure_labels": man["counts"].get("unsure_labels"),
                              "label_assertions_by_source": man["counts"].get("label_assertions_by_source")},
                   "checks": {**checks, "C10_shacl": c10}, "conformance": validation.get("conformance"),
                   "files": [{"name": n, "bytes": (out / n).stat().st_size, "sha256": sha256_file(out / n)}
                             for n in names],
                   "decisions_sha256": decisions_sha, "reference": reference,
                   "view": {"state": view_state, "note": view_note}, "page_images": extras["pages"],
                   "rdfxml": rdfxml, "hyphen_word_counts": hyphen,
                   "values": vr.summary(man, bool(measured), signs) if values_state == "pdf" else vr.earlier(values_state),
                   "validation_paths_made_relative": validation_paths,
                   "resources": max_rss(), "tools": tool_versions(), "worker_version": WORKER_VERSION}
        write_out(out / "convert.json", convert)
        emit({"event": "done", "record_id": record_id, "doc_id": d, "valid": bool(valid), "mode": mode,
              "apertus": apertus, "origin": "stored", "pdf_sha256": sample["pdf_sha256"], "seconds": sec,
              "counts": counts, "files": names + ["convert.json"]})
        return exit_code
    finally:
        try:
            os.chdir(scratch_base)
        except OSError:
            pass
        if TRACE:
            TRACE.on = False          # the removal of the scratch folder opens its folders by relative names
        if not keep:
            shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------------------------- a PDF that is not a sample
def convert_fresh(pdf_path: Path, doc_id: str | None, mode: str, out_dir: Path, emit) -> int:  # noqa: ARG001
    """The hook of contract chapter 4.3 for a PDF whose SHA-256 is not in the sample index. Stage P0b: the fresh
    branch worker/fresh.py (code rules only; profile slim: the code not_in_package). This file gives itself to the
    branch as the host: the output lines, the stage events and the shared helpers are the ones of this file."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.append(here)
    import fresh  # noqa: PLC0415
    return fresh.convert_fresh(sys.modules[__name__], pdf_path, doc_id, mode, out_dir)


# ---------------------------------------------------------------------------------------------- command line
class Parser(argparse.ArgumentParser):
    def error(self, message: str):
        log(f"arguments: {message}")
        raise Stop("bad_request", {"field": "arguments"}, 3)


def run(argv: list[str]) -> int:
    ap = Parser(prog="serve_convert.py", add_help=False)
    ap.add_argument("--sample")
    ap.add_argument("--pdf")
    ap.add_argument("--doc-id")
    ap.add_argument("--mode", default="auto", choices=("auto", "rules"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-dir")
    a = ap.parse_args(argv)
    if bool(a.sample) == bool(a.pdf):
        raise Stop("bad_request", {"field": "sample" if a.sample else "file"}, 3)
    if a.doc_id is not None and not a.doc_id.isdigit():
        raise Stop("bad_request", {"field": "doc_id"}, 3)
    out = Path(a.out).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Stop("bad_request", {"field": "out"}, 3)
    data_dir = Path(a.data_dir or os.environ.get("PARLPDFECH_DATA_DIR") or PACKAGE / "data").resolve()
    code_dir = Path(os.environ.get("PARLPDFECH_CODE_DIR") or PACKAGE / "build" / "layout").resolve()
    view_dir = Path(os.environ.get("PARLPDFECH_VIEW_DIR") or PACKAGE / "view").resolve()
    profile = os.environ.get("PARLPDFECH_PROFILE", "native")
    index_p = data_dir / "samples" / "index.json"
    if not index_p.is_file():
        log("no samples/index.json in the data folder")
        raise stopped("samples")
    samples = {str(s["doc_id"]): s for s in read_json(index_p)["samples"]}
    if a.sample:
        d = a.sample.strip()
        if d not in samples:
            raise Stop("sample_unknown", {"doc_id": d}, 3)
        input_info = {"kind": "sample", "file_name": None}
    else:
        pdf = Path(a.pdf).resolve()
        if not pdf.is_file():
            raise Stop("bad_request", {"field": "file"}, 3)
        digest = sha256_file(pdf)
        hit = [k for k, s in samples.items() if s.get("pdf_sha256") == digest]
        if not hit:
            os.environ["PARLPDFECH_DATA_DIR"] = str(data_dir)      # the fresh branch reads the same data folder
            return convert_fresh(pdf, a.doc_id, a.mode, out, emit)
        d = hit[0]
        if a.doc_id is not None and a.doc_id != d:
            raise Stop("pdf_differs_from_doc_id", {"doc_id": a.doc_id}, 3)
        input_info = {"kind": "upload", "file_name": pdf.name}
    if a.mode not in (samples[d].get("modes") or []):
        raise Stop("bad_request", {"field": "mode"}, 3)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        log(f"the parent folder of --out cannot be made: {type(e).__name__}")
        raise stopped("out") from None
    scratch_base = Path(os.environ.get("PARLPDFECH_SCRATCH_DIR") or out.parent).resolve()
    if not os.access(scratch_base, os.W_OK | os.X_OK):
        log("the scratch folder is not writable")
        raise stopped("out" if scratch_base == out.parent else "scratch")
    return convert_sample(data_dir / "samples" / d, a.mode, out, code_dir, view_dir, profile, input_info, scratch_base)


def main(argv: list[str] | None = None) -> int:
    global TRACE
    if os.environ.get("PARLPDFECH_TRACE"):
        TRACE = Trace(os.environ["PARLPDFECH_TRACE"])
    protect_stdout()

    def on_term(*_):
        raise Terminated()

    signal.signal(signal.SIGTERM, on_term)
    try:
        return run(list(sys.argv[1:] if argv is None else argv))
    except Stop as e:
        emit({"event": "failed", "code": e.code, "detail": e.detail})
        return e.exit_code
    except Terminated:
        log("stopped by a signal")
        return 143
    except (Exception, SystemExit) as e:  # noqa: BLE001
        log(f"internal stop: {type(e).__name__}: {str(e)[:500]}")
        traceback.print_exc(file=sys.stderr)
        emit({"event": "failed", "code": "converter_stopped", "detail": {"note": "internal"}})
        return 4
    finally:
        if TRACE:
            TRACE.write()


if __name__ == "__main__":
    sys.exit(main())
