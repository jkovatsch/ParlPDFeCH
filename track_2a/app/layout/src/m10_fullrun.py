"""Gate GJ (status EXCEPTION), plan chapter 9 item 21, criteria chapters 4 item 7, 10.2, 10.3 and 10.6: the batch
mode of the full run on stored inputs (no Docling), in parallel worker processes, with resume.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream D of
workflow wf_d5120f1f-fd4 (wave 3), for the main agent. Phase 6 (deployment), gate GJ (OPEN). Status: EXCEPTION
(process rule 10), NOT RELEASED. No human checked this file. This file changes no existing file.
Change of 13.10.2026 (stream X2 of the last change round before the design freeze, Claude Opus 5.5). The constant
CODE names src/m10_gaps.py and the label schema. In the mode cascade, the manifest must hold the entry decisions
(chapter 4). The script examines the output folder before a write and before a delete (chapters 2 and 3).

1 Task
  For each document of a list: the decisions of interface 7 (decide() of src/m10_pipeline.py, mode floor or
  cascade), the writer (write_one of src/m10_writer.py), the RDF step (convert_record of src/m10_rdf.py) and the
  validator (validate_record of src/m10_validate.py). Inputs: the stored block files daten/gj/docs/<doc>.json, the
  rule files daten/gj/rules/<doc>.json (SHA-256 of the run record of src/m10_rules.py), the atom files and the
  Docling files at the explicit paths daten/iso/<kind>/<doc>.json, the export records (build_export_records of
  src/m06_converter.py, one call for each batch), and in the mode cascade the states files and the frozen design.
  Docling does not run.
  Mode floor: the floor converter F1 with the floor calibration file (default daten/gj/calibration/floor_v1.json).
  Mode cascade: the design freeze file must exist (load_design() of src/m10_pipeline.py); --entry-d1 and
  --entry-b12 give the entry decisions; --states gives the job folders of the states (the full run:
  daten/gj/states/gpu1_labelled and daten/gj/states/gpu2_bulk). A document without a states file gets the floor
  decisions with the value status unsure (criteria chapter 4 item 7). --r2 and --r2-calibrations: optional R2
  values and their calibration records (chapter 2 of src/m10_pipeline.py).

2 Output folder <out>
  decisions/<doc>.json       the decisions file of the document (interface 7)
  <doc>/                     the files of the writer, of the RDF step and of the validator (manifest.json,
                             validation.json, the YAML, Turtle, RDF/XML and TriG files, export/<doc>.json)
  calibrations.json          mode cascade: the calibration file of the run (the writer reads it)
  parameters.json            the parameters of the folder; a later run with other parameters stops
  runs/run_<n>.json          the run record of each run: the SHA-256 of the scripts before the first value (GJ.2),
                             the inputs, the result and the SHA-256 of each output of each document, the time of
                             each step, the end checks (scripts unchanged, FROZEN_FILES, criteria file)
  runs/run_<n>.events.jsonl  one line for each document when its work ends (resume after a stop)
  The key scripts of the run record names each file of the constant CODE. These files are the scripts of chapter
  1, src/m10_gaps.py and the label schema src/m10_label_schema.yaml. The writer, the RDF step and the validator
  import src/m10_gaps.py.
  A folder <out> that exists and is not empty must hold parameters.json of an earlier run of this script. Else the
  run is refused (exit code 3) before a write, and nothing is deleted.

3 Resume (skip valid outputs)
  A document is skipped if its outputs are valid: manifest.json exists; the writer check and the validation passed;
  each output file and validation.json has the SHA-256 of the manifest; the decisions file, the block file and the
  calibration file have the SHA-256 of the manifest inputs; the base IRI is the base IRI of the run; the writer,
  the RDF step and the validator of the outputs are the scripts now (SHA-256). Else the folder <out>/<doc> is
  made again (it is deleted first).
  The script deletes only a folder that it made. One of these 3 facts is the proof. The file decisions/<doc>.json
  exists: the script writes it before the writer makes the folder. Or the folder holds the manifest of the writer
  for the document. Or the folder is empty. Without this proof the document is an error, and nothing is deleted.
  The check of a document does not compare src/m10_gaps.py and the label schema. Thus parameters.json holds their
  SHA-256 (key output_imports). A later run with another value stops: use a new folder.

4 Guards (process rule 6, criteria chapters 3 and 10)
  Each document passes src/m10_guard.py (dev, validation and group 7; a test document is refused) and must be in
  the run record daten/gj/docs_build.json (2,665 documents). The split of the guard counts (the parliament split).
  A validation or group-7 document is refused without the method freeze manifest daten/gj/freeze_manifest.json
  (criteria 10.2 and 10.3). The manifest must name the SHA-256 of each file of the constant CODE and of the
  calibration file. In the mode cascade it must also name each design file and the design freeze file. In the
  mode cascade the manifest must be a JSON object with the key entry_decisions: {"d1": true|false, "b1_b2":
  true|false}, with JSON booleans. The entry decisions of the run must be equal to it (criteria 10.2 item 2). A
  manifest that is not JSON, has no such key, has one key only or has other types is refused. These checks come
  before the first read of a rule file, a states file or an output of such a document. The console shows only
  counts, doc ids of failed documents and SHA-256 values. No text of a document and no value of a label goes to
  the console.

5 Parallel work
  --workers N processes (default 6, spawn). The documents to make are cut into batches of at most --batch documents
  (default 20; smaller if there are fewer documents than workers times batch). Each worker loads the floor file,
  the frozen design and the calibration file one time, warms the guard cache for the batch, makes the export
  records of the batch in one call, and then makes each document. An error of one document does not stop the
  other documents: the run record gives the error, and the exit code is 2.

6 Commands (from the project folder; one command on one line)
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_fullrun.py run --mode floor|cascade
      --out DIR [--set dev|validation|group7|bulk|all] [ITEM ...] [--workers 6] [--batch 20]
      [--base https://parlpdfech.ansv.ch/id/] [--calibrations daten/gj/calibration/floor_v1.json]
      [--states DIR ...] [--entry-d1 yes|no] [--entry-b12 yes|no] [--design daten/gj/design]
      [--freeze daten/gj/design_freeze.json] [--r2 FILE] [--r2-calibrations FILE]
  ITEM: a doc id or a list file (src/m10_guard.py read_items). bulk: the documents of daten/gj/docs_build.json
  outside daten/gj/sets.json; all: the 2,665 documents of daten/gj/docs_build.json.
  Use an output folder in the project folder (for example daten/gj/fullrun_floor): only then the writer gives the
  paths of the inputs and outputs relative to the project folder. A folder outside it is for checks only.
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_fullrun.py status --out DIR
      Counts of the documents with valid outputs (no new output).
  Exit code: 0 all documents valid; 2 one or more documents not valid; 3 refused.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import multiprocessing as mp
import re
import shutil
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_calibrate as cal  # noqa: E402  (run record helpers, FROZEN_FILES, criteria SHA-256)
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)
import m10_pipeline as pipeline  # noqa: E402  (decide(), load_design(), load_floor(), held_out_gate())

VERSION = "m10-fullrun-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
SRC = ROOT / "src"
GJ = ROOT / "daten/gj"
DOCS_DIR = GJ / "docs"
DOCS_BUILD = GJ / "docs_build.json"
METHOD_FREEZE = GJ / "freeze_manifest.json"
DEFAULT_BASE = "https://parlpdfech.ansv.ch/id/"
DEFAULT_WORKERS = 6
DEFAULT_BATCH = 20
STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
ACTOR = pipeline.ACTOR
CODE = ("m10_fullrun.py", "m10_pipeline.py", "m10_cascade.py", "m10_design.py", "m10_calibrate.py", "m10_guard.py",
        "m10_docs.py", "m10_writer.py", "m10_rdf.py", "m10_validate.py", "m10_gaps.py", "m10_label_schema.yaml")
OUTPUT_SCRIPTS = {"writer": "src/m10_writer.py", "rdf": "src/m10_rdf.py", "validation": "src/m10_validate.py"}
OUTPUT_IMPORTS = ("src/m10_gaps.py", "src/m10_label_schema.yaml")     # the output scripts load them (chapter 3)
PARAMS_SCHEMA = "parlpdfech-gj-fullrun-parameters/1"


class Refusal(Exception):
    """The run is refused (process rule 6, criteria chapters 3 and 10, parameters of the folder)."""


def sha256(p: Path) -> str:
    return guard.sha256_file(Path(p))


def rel(p: Path) -> str:
    return guard.rel(Path(p))


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> str:
    cal.write_json(Path(p), obj)
    return sha256(p)


def code_paths() -> list[Path]:
    return [SRC / n for n in CODE]


def code_sha256() -> dict:
    return {rel(p): sha256(p) for p in code_paths()}


# ------------------------------------------------------------------ documents (chapter 4)
def built_ids() -> set[str]:
    return {Path(p).stem for p in (read_json(DOCS_BUILD).get("outputs") or {})}


def resolve_ids(items: list[str], set_name: str | None) -> list[str]:
    ids: list[str] = []
    for it in items or []:
        ids += guard.read_items(it)
    if set_name:
        sets = read_json(cal.SETS_FILE)
        built = built_ids()
        if set_name in ("dev", "validation", "group7"):
            ids += [str(x) for x in sets[set_name]]
        elif set_name == "bulk":
            labelled = {str(x) for s in ("dev", "validation", "group7") for x in sets[s]}
            ids += [d for d in built if d not in labelled]
        elif set_name == "all":
            ids += list(built)
        else:
            raise Refusal(f"--set {set_name}: not dev, validation, group7, bulk or all")
    out = sorted({str(x).strip() for x in ids}, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))
    if not out:
        raise Refusal("no document: give ITEM or --set")
    return out


def check_documents(ids: list[str]) -> dict:
    """src/m10_guard.py for all documents (one pass), then the run record of src/m10_docs.py and the rule files
    (existence only)."""
    try:
        g = guard.assert_allowed(ids)
    except guard.GuardRefusal as e:
        raise Refusal(str(e)) from None
    built = built_ids()
    missing = [d for d in ids if d not in built or not (DOCS_DIR / f"{d}.json").is_file()]
    if missing:
        raise Refusal(f"{len(missing)} documents are not in {rel(DOCS_BUILD)} or have no block file: {missing[:10]}")
    no_rules = [d for d in ids if not (cal.RULES_DIR / f"{d}.json").is_file()]
    if no_rules:
        raise Refusal(f"{len(no_rules)} documents have no rule file in daten/gj/rules: {no_rules[:10]}")
    return g


def method_freeze_gate(ids: list[str], split_of: dict, need: dict, entry: dict | None) -> dict | None:
    """Criteria 10.2: validation and group-7 documents only with the method freeze manifest, which names the
    SHA-256 of each file of need. No file of such a document is read before this check.
    Mode cascade (entry is not None): the manifest must be JSON with the key entry_decisions. The key holds JSON
    booleans for d1 and b1_b2, and they must be equal to the entry decisions of the run (criteria 10.2 item 2)."""
    held = [d for d in ids if split_of[d] in ("validation", "group7")]
    if not held:
        return None
    n_val = sum(split_of[d] == "validation" for d in held)
    if not METHOD_FREEZE.is_file():
        raise Refusal(f"{n_val} validation and {len(held) - n_val} group-7 documents: no method freeze manifest "
                      f"{rel(METHOD_FREEZE)} (criteria 10.2)")
    text = METHOD_FREEZE.read_text(encoding="utf-8")
    missing = sorted(p for p, h in need.items() if h not in text)
    if missing:
        raise Refusal(f"the method freeze manifest does not name the SHA-256 of {missing}")
    found = None
    if entry is not None:
        try:
            man = json.loads(text)
        except json.JSONDecodeError:
            raise Refusal("the method freeze manifest is not JSON (criteria 10.2 item 2)") from None
        found = man.get("entry_decisions") if isinstance(man, dict) else None
        if not isinstance(found, dict) or any(not isinstance(found.get(k), bool) for k in ("d1", "b1_b2")):
            raise Refusal("the method freeze manifest has no key entry_decisions with true or false for d1 and "
                          "b1_b2 (criteria 10.2 item 2)")
        diff = [k for k in ("d1", "b1_b2") if found[k] != entry[k]]
        if diff:
            raise Refusal(f"the entry decisions of the run differ from the method freeze manifest: {diff}")
    return {"path": rel(METHOD_FREEZE), "sha256": sha256(METHOD_FREEZE), "validation": n_val,
            "group7": len(held) - n_val, "named": need, "entry_decisions_in_manifest": found}


# ------------------------------------------------------------------ output folder (chapters 2 and 3)
def check_out_folder(out: Path) -> None:
    """Refuses a folder with content that is not the folder of an earlier run of this script. Such a folder holds
    parameters.json with the schema of this script. The check writes no file and deletes no file."""
    if not out.exists():
        return
    if not out.is_dir():
        raise Refusal(f"--out {out}: not a folder")
    if not any(out.iterdir()):
        return
    try:
        old = read_json(out / "parameters.json")
    except (OSError, ValueError):
        old = None
    if not isinstance(old, dict) or old.get("schema") != PARAMS_SCHEMA:
        raise Refusal(f"--out {out}: the folder is not empty and has no parameters.json of an earlier run of this "
                      f"script (use a new folder; nothing was deleted)")


def made_by_this_script(out: Path, d: str) -> bool:
    """True if the files show that this script made the folder <out>/<d>. Only such a folder is deleted.
    The script writes decisions/<d>.json before the writer makes the folder. The writer manifest names d."""
    folder = out / d
    if folder.is_symlink() or not folder.is_dir():
        return False
    if (out / "decisions" / f"{d}.json").is_file() or not any(folder.iterdir()):
        return True
    try:
        man = read_json(folder / "manifest.json")
    except (OSError, ValueError):
        return False
    return isinstance(man, dict) and str(man.get("doc_id")) == d and \
        (man.get("writer") or {}).get("path") == OUTPUT_SCRIPTS["writer"]


# ------------------------------------------------------------------ resume (chapter 3)
def valid_output(out: Path, d: str, params: dict) -> tuple[bool, str]:
    folder = out / d
    mp_ = folder / "manifest.json"
    if not mp_.is_file():
        return False, "no manifest"
    try:
        man = read_json(mp_)
    except (OSError, json.JSONDecodeError):
        return False, "manifest not readable"
    val = man.get("validation") or {}
    if not man.get("check_passed") or val.get("passed") is not True:
        return False, "check or validation not passed"
    if man.get("base_iri") != params["base"]:
        return False, "other base IRI"
    files = dict(man.get("outputs") or {})
    files["validation"] = {"path": val.get("file"), "sha256": val.get("sha256")}
    for k, f in files.items():
        p = ROOT / str(f.get("path"))
        if not f.get("path") or not p.is_file() or sha256(p) != f.get("sha256"):
            return False, f"output {k} missing or changed"
    inp = man.get("inputs") or {}
    want = {"decisions": out / "decisions" / f"{d}.json", "docs": DOCS_DIR / f"{d}.json",
            "calibrations": Path(params["calibrations"]["abs"])}
    for k, p in want.items():
        f = inp.get(k) or {}
        if Path(ROOT / str(f.get("path"))).resolve() != p.resolve() or not p.is_file() or sha256(p) != f.get("sha256"):
            return False, f"input {k} changed"
    if params["calibrations"]["sha256"] != (inp.get("calibrations") or {}).get("sha256"):
        return False, "other calibration file"
    now = params["output_scripts"]
    if (man.get("writer") or {}).get("sha256") != now["writer"]:
        return False, "other writer"
    if ((man.get("rdf") or {}).get("script") or {}).get("sha256") != now["rdf"]:
        return False, "other RDF step"
    try:
        v = read_json(ROOT / val["file"])
    except (OSError, json.JSONDecodeError):
        return False, "validation.json not readable"
    if (v.get("script") or {}).get("sha256") != now["validation"]:
        return False, "other validator"
    return True, "valid"


# ------------------------------------------------------------------ worker processes (chapter 5)
_STATE: dict = {}


def worker_state(cfg: dict) -> dict:
    """Per process: the modules, the floor file, the frozen design and the calibration file (loaded one time)."""
    if _STATE.get("key") == cfg["key"]:
        return _STATE
    import m06_converter as mc
    import m10_rdf as rdf
    import m10_validate as val
    import m10_writer as writer
    st = {"key": cfg["key"], "mc": mc, "rdf": rdf, "val": val, "writer": writer}
    st["floor"] = pipeline.load_floor(Path(cfg["floor_file"]))
    st["frozen"] = pipeline.load_design(cfg["design"], cfg["freeze"], require_freeze=True) \
        if cfg["mode"] == "cascade" else None
    st["cals"], st["cal_file"] = writer.load_calibrations(Path(cfg["calibrations"]))
    st["r2"] = read_json(cfg["r2"]) if cfg.get("r2") else {}
    st["sets"] = read_json(cal.SETS_FILE)
    st["dev"] = {str(x) for x in st["sets"]["dev"]}
    _STATE.clear()
    _STATE.update(st)
    return _STATE


def work_batch(ids: list[str], cfg: dict) -> list[dict]:
    t0 = time.perf_counter()
    try:
        st = worker_state(cfg)
        guard.assert_allowed(ids)                         # warms the guard cache of this process for the batch
    except Exception as e:  # noqa: BLE001  (each failure goes into the run record)
        return [{"doc_id": d, "result": "error", "error": f"worker start: {type(e).__name__}: {str(e)[:300]}"}
                for d in ids]
    exp, exp_error = {}, None
    try:
        exp = st["mc"].build_export_records(ids)
    except (Exception, SystemExit) as e:  # noqa: BLE001
        exp_error = f"{type(e).__name__}: {str(e)[:200]}"
    t_exp = time.perf_counter() - t0
    out = []
    for d in ids:
        rec = work_one(d, st, cfg, exp.get(d))
        rec["seconds"]["export_share"] = round(t_exp / len(ids), 3)
        if exp_error and "export" not in rec.get("error", ""):
            rec["export_batch_error"] = exp_error
        out.append(rec)
    return out


def work_one(d: str, st: dict, cfg: dict, exp_record: dict | None) -> dict:
    out = Path(cfg["out"])
    folder = out / d
    res: dict = {"doc_id": d, "result": "error", "seconds": {}}
    t0 = time.perf_counter()
    try:
        if folder.exists() or folder.is_symlink():
            if not made_by_this_script(out, d):
                raise Refusal(f"{d}: the folder {rel(folder)} exists and this script did not make it (no decisions "
                              f"file, no manifest of the writer): it is not deleted")
            shutil.rmtree(folder)
        if exp_record is None:
            exp_record = st["mc"].build_export_records([d]).get(d)
            if exp_record is None:
                raise SystemExit(f"{d}: no export record")
        if cfg["mode"] == "floor":
            dec = pipeline.decide(d, "floor", None, None, False, False, None, floor=st["floor"])
        else:
            dec = pipeline.decide(d, "cascade", st["frozen"], cfg["states"], cfg["entry"]["d1"], cfg["entry"]["b1_b2"],
                                  st["r2"].get(d), floor=st["floor"], dev_ids=st["dev"], sets=st["sets"])
            if dec.get("no_states") and not pipeline.floor_unsure({"calibrations": st["cals"]}, dec):
                raise pipeline.PipelineRefusal(f"{d}: a floor record of a document without states has a threshold a")
        dp = out / "decisions" / f"{d}.json"
        res["decisions_sha256"] = write_json(dp, dec)
        res["no_states"] = bool(dec.get("no_states"))
        if dec.get("states"):
            res["states"] = dec["states"]
        t1 = time.perf_counter()
        st["writer"].write_one(d, out, None, exp_record, st["cals"], st["cal_file"], cfg["base"], DOCS_DIR,
                               out / "decisions")
        t2 = time.perf_counter()
        st["rdf"].convert_record(folder, d, cfg["base"])
        t3 = time.perf_counter()
        v = st["val"].validate_record(folder, d)
        t4 = time.perf_counter()
        ok, why = valid_output(out, d, cfg["params"])
        man = read_json(folder / "manifest.json")
        res.update({"result": "valid" if ok else "not valid", "why": why,
                    "validation_checks": {k: x.get("passed", x.get("status")) for k, x in v.items()
                                          if k.startswith("C") and isinstance(x, dict)},
                    "manifest_sha256": sha256(folder / "manifest.json"),
                    "outputs": {k: f["sha256"] for k, f in man["outputs"].items()} |
                    {"validation": man["validation"]["sha256"]},
                    "counts": {k: man["counts"].get(k) for k in ("label_assertions", "certain_labels", "unsure_labels")
                               if k in (man.get("counts") or {})},
                    "seconds": {"decisions": round(t1 - t0, 3), "write": round(t2 - t1, 3), "rdf": round(t3 - t2, 3),
                                "validate": round(t4 - t3, 3), "total": round(t4 - t0, 3)}})
    except (Exception, SystemExit) as e:  # noqa: BLE001  (one document does not stop the others)
        res["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        res["seconds"]["total"] = round(time.perf_counter() - t0, 3)
    return res


# ------------------------------------------------------------------ the command run
def next_run_path(out: Path) -> Path:
    runs = out / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    n = 1 + len(list(runs.glob("run_*.json")))
    return runs / f"run_{n}.json"


def batches(ids: list[str], workers: int, size: int) -> list[list[str]]:
    if not ids:
        return []
    size = max(1, min(size, math.ceil(len(ids) / max(1, workers))))
    return [ids[i:i + size] for i in range(0, len(ids), size)]


def prepare(args) -> dict:
    """Guards, parameters and the calibration file before the run record (no file of a held-out document is read
    before the guards)."""
    out = Path(args.out).resolve()
    guard.check_path(out)
    if out == ROOT or out.is_relative_to(SRC) or out == GJ or out in (DOCS_DIR, cal.RULES_DIR):
        raise Refusal(f"--out {out}: use a new folder for the run")
    check_out_folder(out)
    mode = args.mode
    ids = resolve_ids(args.items, args.set)
    g = check_documents(ids)
    base = args.base
    if not re.fullmatch(r"https?://[^\s<>\"{}|\\^`]+/", base or ""):       # the rule of check_base of the writer
        raise Refusal(f"base IRI {base!r}: it must start with http:// or https:// and end with /")
    floor =pipeline.load_floor(Path(args.calibrations) if args.calibrations else None)
    frozen, entry, states, r2_info, r2c_info, design_need = None, None, None, None, None, {}
    if mode == "cascade":
        if not args.states or args.entry_d1 is None or args.entry_b12 is None:
            raise Refusal("--mode cascade needs --states, --entry-d1 and --entry-b12")
        frozen = pipeline.load_design(args.design, args.freeze, require_freeze=True)
        entry = {"d1": args.entry_d1 == "yes", "b1_b2": args.entry_b12 == "yes"}
        states = [str(p) for p in pipeline.states_dirs(args.states)]
        for p in states:
            if not Path(p).is_dir():
                raise Refusal(f"--states {p}: no folder")
        design_need = {f"{rel(frozen.design_dir)}/{k}": v for k, v in frozen.files.items()}
        design_need[rel(frozen.freeze_path)] = frozen.freeze["_sha256"]
    elif args.states or args.entry_d1 or args.entry_b12 or args.r2 or args.r2_calibrations:
        raise Refusal("--states, --entry-d1, --entry-b12, --r2 and --r2-calibrations are only for --mode cascade")
    need = code_sha256() | {rel(floor.path): floor.info["sha256"]} | design_need
    held = method_freeze_gate(ids, g["split_of"], need, entry)
    gate = pipeline.held_out_gate(ids, mode, frozen=frozen, floor=floor)
    r2_all, r2c = {}, None
    if mode == "cascade":
        r2_all, r2_info = pipeline.read_r2(args.r2)
        r2c, r2c_info = pipeline.read_r2(args.r2_calibrations)
        cals = pipeline.cascade_calibrations(frozen, entry["d1"], entry["b1_b2"], floor, r2c or None)
        cal_path = out / "calibrations.json"
        text = json.dumps(cals, ensure_ascii=False, indent=1) + "\n"
        if cal_path.is_file() and cal_path.read_text(encoding="utf-8") != text:
            raise Refusal(f"{rel(cal_path)} exists with another content: other parameters (use a new folder)")
        out.mkdir(parents=True, exist_ok=True)
        cal_path.write_text(text, encoding="utf-8")
    else:
        cal_path = floor.path
    params = {"schema": PARAMS_SCHEMA, "mode": mode, "base": base,
              "calibrations": {"path": rel(cal_path), "sha256": sha256(cal_path)},
              "floor": floor.info, "entry": entry, "states": [rel(Path(p)) for p in states] if states else None,
              "design_files": frozen.files if frozen else None,
              "design_freeze": ({"path": rel(frozen.freeze_path), "sha256": frozen.freeze["_sha256"]} if frozen
                                else None),
              "r2": r2_info, "r2_calibrations": r2c_info,
              "output_imports": {p: sha256(ROOT / p) for p in OUTPUT_IMPORTS},
              "output_scripts": {k: sha256(ROOT / v) for k, v in OUTPUT_SCRIPTS.items()}}
    pp = out / "parameters.json"
    if pp.is_file():
        old = read_json(pp)
        a, b = ({k: v for k, v in x.items() if k != "output_scripts"} for x in (old, params))
        if a != b:
            diff = sorted(k for k in set(a) | set(b) if k not in a or k not in b or a[k] != b[k])
            raise Refusal(f"{rel(pp)}: the folder has other parameters {diff} (use a new folder)")
    out.mkdir(parents=True, exist_ok=True)
    write_json(pp, params)
    params["calibrations"]["abs"] = str(cal_path)
    cfg = {"key": f"{out}|{sha256(pp)}", "out": str(out), "mode": mode, "base": base, "floor_file": str(floor.path),
           "design": str(args.design) if args.design else None, "freeze": str(args.freeze) if args.freeze else None,
           "states": states, "entry": entry, "calibrations": str(cal_path),
           "r2": str(Path(args.r2).resolve()) if args.r2 else None, "params": params}
    return {"out": out, "ids": ids, "guard": g, "held": held, "gate": gate, "params": params, "cfg": cfg,
            "r2_documents": len(r2_all)}


def cmd_run(args) -> int:
    t_all = time.perf_counter()
    p = prepare(args)
    out, ids, cfg = p["out"], p["ids"], p["cfg"]
    run_path = next_run_path(out)
    scripts = code_paths()
    rec = pipeline.run_record_start(run_path, f"full run (mode {cfg['mode']}) on {len(ids)} documents", scripts)
    rec.update({"actor": ACTOR, "version": VERSION, "parameters": {k: v for k, v in p["params"].items()},
                "guard": {k: v for k, v in p["guard"].items() if k not in ("split_of", "parliament_of")},
                "held_out_gate": p["gate"], "method_freeze": p["held"], "workers": args.workers, "batch": args.batch})
    rec["parameters"]["calibrations"] = {k: v for k, v in rec["parameters"]["calibrations"].items() if k != "abs"}
    write_json(run_path, rec)
    valid_before = [d for d in ids if valid_output(out, d, p["params"])[0]]
    todo = [d for d in ids if d not in set(valid_before)]
    rec["skipped_valid_outputs"] = len(valid_before)
    (out / "decisions").mkdir(parents=True, exist_ok=True)
    events = run_path.with_suffix(".events.jsonl")
    results: dict[str, dict] = {}
    work = batches(todo, args.workers, args.batch)
    print(json.dumps({"documents": len(ids), "skipped_valid_outputs": len(valid_before), "to_make": len(todo),
                      "batches": len(work), "workers": args.workers, "run": rel(run_path)}), flush=True)
    t_work = time.perf_counter()
    if work:
        ctx = mp.get_context("spawn")
        with cf.ProcessPoolExecutor(max_workers=min(args.workers, len(work)), mp_context=ctx) as ex, \
                open(events, "a", encoding="utf-8") as ev:
            futs = {ex.submit(work_batch, b, cfg): b for b in work}
            for f in cf.as_completed(futs):
                try:
                    rows = f.result()
                except Exception as e:  # noqa: BLE001  (a lost worker: each document of the batch is an error)
                    rows = [{"doc_id": d, "result": "error", "error": f"batch: {type(e).__name__}: {str(e)[:200]}",
                             "seconds": {}} for d in futs[f]]
                for r in rows:
                    results[r["doc_id"]] = r
                    ev.write(json.dumps(r, ensure_ascii=False) + "\n")
                ev.flush()
                done = len(results)
                bad = sum(r["result"] != "valid" for r in results.values())
                print(json.dumps({"done": done, "of": len(todo), "not_valid": bad,
                                  "seconds": round(time.perf_counter() - t_work, 1)}), flush=True)
    wall = time.perf_counter() - t_work
    tot = [r["seconds"]["total"] for r in results.values() if r.get("seconds", {}).get("total") is not None]
    steps = {k: [r["seconds"][k] for r in results.values() if k in r.get("seconds", {})]
             for k in ("export_share", "decisions", "write", "rdf", "validate")}
    not_valid = sorted((d for d, r in results.items() if r["result"] != "valid"), key=int)
    outputs = {d: {"manifest": r.get("manifest_sha256"), "decisions": r.get("decisions_sha256"),
                   **(r.get("outputs") or {})} for d, r in results.items() if r["result"] == "valid"}
    rec.update({"documents": len(ids), "made": len(todo), "valid": len(todo) - len(not_valid),
                "not_valid": not_valid, "errors": {d: results[d].get("error") or results[d].get("why")
                                                   for d in not_valid},
                "documents_without_states": sorted((d for d, r in results.items() if r.get("no_states")), key=int),
                "results": results,
                "outputs_sha256_canonical": hashlib.sha256(json.dumps(outputs, sort_keys=True).encode()).hexdigest(),
                "time": {"wall_seconds_of_the_work": round(wall, 2),
                         "wall_seconds_per_document": round(wall / len(todo), 3) if todo else None,
                         "documents_per_minute": round(60 * len(todo) / wall, 1) if todo and wall > 0 else None,
                         "seconds_per_document_in_a_worker": {
                             "mean": round(statistics.mean(tot), 3) if tot else None,
                             "median": round(statistics.median(tot), 3) if tot else None,
                             "max": max(tot) if tot else None},
                         "mean_seconds_of_each_step": {k: round(statistics.mean(v), 3) if v else None
                                                       for k, v in steps.items()},
                         "seconds_total": round(time.perf_counter() - t_all, 2)},
                "events": {"path": rel(events), "sha256": sha256(events) if events.exists() else None}})
    pipeline.run_record_finish(run_path, rec, scripts)
    print(json.dumps({"documents": len(ids), "skipped_valid_outputs": len(valid_before), "made": len(todo),
                      "valid": rec["valid"], "not_valid": not_valid[:20],
                      "documents_without_states": len(rec["documents_without_states"]), "time": rec["time"],
                      "run": {"path": rel(run_path), "sha256": sha256(run_path)},
                      "frozen_files_different": rec["frozen_files"]["different"]}, indent=1), flush=True)
    return 0 if not not_valid else 2


def cmd_status(args) -> int:
    out = Path(args.out).resolve()
    pp = out / "parameters.json"
    if not pp.is_file():
        raise Refusal(f"{rel(pp)} does not exist")
    params = read_json(pp)
    params["calibrations"]["abs"] = str(ROOT / params["calibrations"]["path"])
    params["output_scripts"] = {k: sha256(ROOT / v) for k, v in OUTPUT_SCRIPTS.items()}
    ids = sorted((p.name for p in out.iterdir() if p.is_dir() and p.name.isdigit()), key=int)
    why = {}
    for d in ids:
        ok, w = valid_output(out, d, params)
        why[w] = why.get(w, 0) + 1
    print(json.dumps({"folder": rel(out), "document_folders": len(ids), "by_result": why}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="gate GJ: batch mode of the full run on stored inputs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--mode", required=True, choices=pipeline.MODES)
    r.add_argument("--out", required=True)
    r.add_argument("--set", default=None, choices=("dev", "validation", "group7", "bulk", "all"))
    r.add_argument("items", nargs="*")
    r.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    r.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    r.add_argument("--base", default=DEFAULT_BASE)
    r.add_argument("--calibrations", default=None, help="the floor calibration file (default floor_v1.json)")
    r.add_argument("--states", nargs="+", default=None)
    r.add_argument("--entry-d1", choices=("yes", "no"), default=None)
    r.add_argument("--entry-b12", choices=("yes", "no"), default=None)
    r.add_argument("--design", default=None)
    r.add_argument("--freeze", default=None)
    r.add_argument("--r2", default=None)
    r.add_argument("--r2-calibrations", default=None)
    s = sub.add_parser("status")
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        return cmd_run(a) if a.cmd == "run" else cmd_status(a)
    except (Refusal, pipeline.PipelineRefusal, guard.GuardRefusal) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
