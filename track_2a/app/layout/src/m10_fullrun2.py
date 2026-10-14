"""Gate GJ (status EXCEPTION), plan chapters 4, 5.3, 5.6 and 6.6, criteria chapters 4 item 7, 8.5, 8.6, 10.2 and 10.3,
addenda A, C and D: the batch conversion for a candidate of the block step (first candidate: B1-S).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream F of
workflow wf_5fc6a473-7f0, for the main agent. Phase 6 (deployment), gate GJ (OPEN). Status: EXCEPTION (process rule
10), NOT RELEASED. No human checked this file. This file changes no existing file. It is an addition after the
design freeze. The frozen batch tool src/m10_fullrun.py knows only the floor mode and the cascade of the frozen
design. This file imports its functions and adds the decisions of a candidate.

1 Task
  For each document of a list: (1) the decisions of the candidate (interface 7), (2) the writer (write_one of
  src/m10_writer.py), the RDF step (convert_record of src/m10_rdf.py) and the validator (validate_record of
  src/m10_validate.py). Docling does not run. No model runs. The inputs are the stored block files, rule files,
  atom files, export records and states files.

2 Candidate b1s (B1-S, addendum D)
  Decisions: b1s_decisions of src/m10_b1s.py. This is the function of the one validation run of B1-S. It uses the
  frozen B1 head with its frozen temperature on the states of the document, the form and the values of
  daten/gj/design_b1s/design_b1s.json, and lora_decisions of src/m10_lora_design.py. The entry values are the
  values of the variant d1n_b1sy: the S1 rule decides the document option (entry d1 no), and B1-S decides the
  non-certain blocks (entry b1_s yes). A certain block keeps the rule option.
  Design: design_check of src/m10_b1s.py (the addenda B, C and D, each output file of the design, the code of the
  design). The SHA-256 of design_b1s.json must be the value of --design-b1s-sha256 (the value of the protocol).
  The design freeze file must have the SHA-256 of the protocol (FREEZE_SHA of src/m10_lora_design.py).
  States: the job folder that holds states/<doc>.npz (find_states of src/m10_pipeline.py; default: gpu1_labelled
  and gpu2_bulk). The rule record comes from load_rules of src/m10_pipeline.py (SHA-256 of the run record of
  src/m10_rules.py) and goes to the design functions through design_inputs of src/m10_pipeline.py.
  Floor fallback: a document without a states file gets the floor decisions with the value status unsure
  (criteria chapter 4 item 7): decide() of src/m10_pipeline.py gives them. A document for which the B2 form has no
  path with a weight above 0 gets the same floor decisions (the rule of the validation run of B1-S). The key
  fallback of the decisions file gives the cause. Each other error is an error of the document.
  Gate object: src/m10_lora_design.py decide_gate accepts only the documents of daten/gj/sets.json. This file
  makes the gate object for the documents that passed the guards of chapter 5. No other check is left out.
  A second candidate (for example b1l with LoRA logits files) needs one function that returns a Candidate, and
  one entry in CANDIDATES.

3 Calibration file of the run (<out>/calibrations.json)
  cascade_calibrations of src/m10_pipeline.py on the calibration records of the candidate: the records of the
  entry variant (calibration_file of src/m10_design.py), the floor records without a threshold a (documents with
  the floor fallback) and the R2 records. --validation-calibrations FILE (optional): the calibration file of the
  records of the finished validation run of the candidate (daten/gj/validation_b1s/decisions_records/
  calibrations.json). For an id that is in both files, the keys target_status, measure_sets and calibration_note
  come from that file (the GJ.13 result of the validation run). Each other key must be equal, else the run stops.
  That file holds aggregate values of the finished validation run only.
  --r2 FILE ... and --r2-calibrations FILE ...: the R2 values and their calibration records (src/m10_r2_step0b.py
  apply makes one file for each job). An id in 2 value files stops. Records with an equal id must be equal. With
  --r2, each document with a states file must have an R2 value. A document with the floor fallback gets no R2.

4 Output folder <out> (the layout of src/m10_fullrun.py)
  decisions/<doc>.json, <doc>/ (manifest.json, validation.json, the YAML, Turtle, RDF/XML and TriG files,
  export/<doc>.json), calibrations.json, parameters.json, runs/run_<n>.json, runs/run_<n>.events.jsonl.
  A folder <out> that exists and is not empty must hold parameters.json of this script (schema PARAMS_SCHEMA).
  Else the run is refused (exit code 3) before a write, and nothing is deleted. A folder of src/m10_fullrun.py is
  refused too. The script deletes only a document folder that it made (made_by_this_script of
  src/m10_fullrun.py). <out> must be in the project folder: the writer gives paths relative to it.
  Resume: a document is skipped if its outputs are valid (valid_output of src/m10_fullrun.py and the rule of
  chapter 6). A later run with other parameters stops: use a new folder.

5 Guards (process rule 6, criteria chapters 3 and 10)
  Each document passes src/m10_guard.py and must be in daten/gj/docs_build.json with a rule file
  (check_documents of src/m10_fullrun.py). The split of the guard counts (the split of the parliament).
  While the method freeze manifest daten/gj/freeze_manifest.json does not exist, the run refuses each document
  that is not a dev document. This script never writes that file. With the manifest (method_freeze_gate of
  src/m10_fullrun.py): it must name the SHA-256 of each file of CODE, of the floor calibration file, of each
  design file, of the design freeze file and of each file of the candidate. It must be a JSON object with the key
  entry_decisions, and that key must hold the entry values of the candidate (for b1s: "d1": false, "b1_s": true).
  Then held_out_gate of src/m10_pipeline.py applies too. The key split of the block file daten/gj/docs/<doc>.json
  must be the split of the guard. These checks come before the first read of a rule file, a states file or an
  output of a document. A worker makes the guard check again and refuses a document that is not dev, unless the
  manifest check passed. The console shows counts, doc ids of failed documents and SHA-256 values only.

6 Result of a document
  valid      valid_output of src/m10_fullrun.py is true, and the rule of GJ.12 is true for the document (gj12 of
             src/m10_validation_run.py: all files, writer check, checks C1 to C9, 0 linkml errors, conformance by
             addendum A, rule A2). A document with a recorded I95 gap is valid with the conformance
             i95_with_recorded_gaps. C10 (SHACL) is information.
  not valid  the outputs exist, and a check failed. error: a step stopped.
  The run record gives for each document: the result, the conformance, the gap slots, the counts of certain and
  unsure labels, the floor fallback, the SHA-256 of each output and the time of each step. It gives the counts by
  result, by conformance and by value status, and the time values. The run record holds the SHA-256 of each file
  of CODE before the first value (GJ.2). At the end it compares them again.

7 Commands (from the project folder; one command on one line)
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_fullrun2.py run --candidate b1s
      --set dev|ITEM ... --out DIR --design-b1s-sha256 SHA [--workers 6] [--batch 20]
      [--r2 FILE ...] [--r2-calibrations FILE ...] [--validation-calibrations FILE] [--states DIR ...]
      [--base https://parlpdfech.ansv.ch/id/] [--calibrations daten/gj/calibration/floor_v1.json]
  --set dev: each document of daten/gj/docs_build.json with the guard split dev (1,793 documents). ITEM: a doc id
  or a list file (src/m10_guard.py read_items).
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_fullrun2.py status --out DIR
  Exit code: 0 all documents valid; 2 one or more documents not valid; 3 refused.
  Check script: uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_fullrun2_test.py
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import dataclasses
import hashlib
import json
import multiprocessing as mp
import re
import shutil
import statistics
import sys
import time
import types
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)
import m10_fullrun as fr  # noqa: E402  (frozen batch tool: batches, resume, folder rules, method freeze gate)
import m10_pipeline as pipeline  # noqa: E402  (floor fallback, design_inputs, calibration file, run record)
import m10_gaps as gaps  # noqa: E402  (conformance names of addendum A)

VERSION = "m10-fullrun2-1"
SCRIPT = Path(__file__).resolve()
ROOT = fr.ROOT
SRC = fr.SRC
GJ = fr.GJ
DOCS_DIR = fr.DOCS_DIR
STATUS = fr.STATUS
ACTOR = "workflow sub-agent (Claude Opus 5.5), stream F of workflow wf_5fc6a473-7f0, for the main agent"
DEFAULT_BASE = fr.DEFAULT_BASE
DEFAULT_STATES = (GJ / "states/gpu1_labelled", GJ / "states/gpu2_bulk")
PARAMS_SCHEMA = "parlpdfech-gj-fullrun2-parameters/1"
NO_PATH = "no path with a weight above 0"                # the ValueError text of m10_b2x.b2x_document
STATUS_KEYS = ("target_status", "measure_sets", "calibration_note")
CODE = ("m10_fullrun2.py", "m10_fullrun.py", "m10_pipeline.py", "m10_b1s.py", "m10_lora_design.py",
        "m10_lora_validation.py", "m10_validation_run.py", "m10_b2x.py", "m10_cascade.py", "m10_design.py",
        "m10_calibrate.py", "m10_guard.py", "m10_docs.py", "m10_score.py", "m06_converter.py", "m10_writer.py",
        "m10_rdf.py", "m10_validate.py", "m10_gaps.py", "m10_label_schema.yaml")

Refusal = fr.Refusal
sha256, rel, read_json, write_json = fr.sha256, fr.rel, fr.read_json, fr.write_json


def code_paths() -> list[Path]:
    return [SRC / n for n in CODE]


def code_sha256() -> dict:
    return {rel(p): sha256(p) for p in code_paths()}


def by_id(ids) -> list[str]:
    return sorted({str(x).strip() for x in ids}, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))


# ------------------------------------------------------------------ candidates (chapter 2)
@dataclass
class Candidate:
    """One candidate of the block step. A new candidate needs one function that returns this object."""
    name: str
    label: str
    entry: dict                 # the entry values of the decisions, of the parameters and of the manifest check
    files: dict                 # {path: SHA-256} of each file of the candidate (parameters, method freeze manifest)
    info: dict                  # facts for the parameters file (JSON)
    records: dict               # calibration records in the form of daten/gj/design/calibration_records.json
    decide: Callable            # (doc id, job folder of the states, r2, gate, dev ids) -> decisions (interface 7)
    gate: Callable              # (doc ids) -> the gate object that decide needs


def candidate_b1s(opts: dict, frozen) -> Candidate:
    """B1-S (addendum D) with the entry values of the variant d1n_b1sy."""
    import m10_b1s as b1s  # noqa: PLC0415  (the examined tool of B1-S; its decision function)
    import m10_lora_design as ld  # noqa: PLC0415  (gate object, FREEZE_SHA)
    want = opts.get("design_b1s_sha256")
    if not want:
        raise Refusal("--candidate b1s needs --design-b1s-sha256 (the SHA-256 of design_b1s.json of the protocol)")
    if frozen.freeze is None or frozen.freeze.get("_sha256") != ld.FREEZE_SHA:
        raise Refusal(f"{rel(pipeline.design.FREEZE_FILE)} does not have the SHA-256 of the protocol")
    cfg = types.SimpleNamespace(design_b1s=b1s.OUT_DESIGN, real=True, design_b1s_sha=want)
    try:
        des, info = b1s.design_check(cfg, frozen)
    except (b1s.RunRefusal, ld.LoraRefusal, pipeline.design.DesignRefusal) as e:
        raise Refusal(f"design of B1-S: {e}") from None
    entry = {"d1": False, "b1_b2": False, "b1_s": True}

    def decide(d: str, job: Path, r2: dict | None, gate, dev_ids: set[str]) -> dict:
        return b1s.b1s_decisions(d, gate, frozen, des, job, entry["d1"], entry["b1_s"], r2, dev_ids)

    def gate(ids) -> "ld.Gate":
        ids = [str(d) for d in ids]
        return ld.Gate(frozenset(ids), {"documents": len(ids), "made_by": rel(SCRIPT)})

    files = {info["design_b1s_json"]["path"]: des.sha256, **des.files, **info["criteria"]["files"]}
    facts = {"design_b1s_json": info["design_b1s_json"], "form": des.form, "strength": des.strength,
             "temperature_b1": des.T, "temperature_b2": des.T2, "thresholds": info["thresholds"],
             "variant": "d1n_b1sy", "decision_function": "m10_b1s.b1s_decisions"}
    return Candidate("b1s", f"{b1s.CANDIDATE} (addendum D)", entry, files, facts, des.records, decide, gate)


CANDIDATES: dict[str, Callable] = {"b1s": candidate_b1s}


# ------------------------------------------------------------------ documents and guards (chapter 5)
def resolve_ids(items: list[str]) -> list[str]:
    """--set: the word dev (each built document with the guard split dev), doc ids and list files."""
    ids: list[str] = []
    for it in items or []:
        if it == "dev":
            built = sorted(fr.built_ids())
            try:
                split = guard.assert_allowed(built)["split_of"]
            except guard.GuardRefusal as e:
                raise Refusal(str(e)) from None
            ids += [d for d in built if split.get(d) == "dev"]
        else:
            ids += guard.read_items(it)
    out = by_id(ids)
    if not out:
        raise Refusal("no document: give --set dev or doc ids or a list file")
    return out


def manifest_entry_check(entry: dict) -> dict:
    """The key entry_decisions of the method freeze manifest must hold the entry values of the candidate."""
    try:
        man = json.loads(fr.METHOD_FREEZE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise Refusal("the method freeze manifest is not JSON (criteria 10.2 item 2)") from None
    found = man.get("entry_decisions") if isinstance(man, dict) else None
    keys = [k for k, v in entry.items() if v or k == "d1"]
    if not isinstance(found, dict) or any(not isinstance(found.get(k), bool) or found[k] != entry[k] for k in keys):
        raise Refusal(f"the method freeze manifest does not hold the entry decisions {({k: entry[k] for k in keys})} "
                      f"of the candidate in the key entry_decisions (criteria 10.2 item 2)")
    return {k: found[k] for k in keys}


def split_gate(ids: list[str], split_of: dict, need: dict, cand: Candidate, frozen) -> dict:
    """Refuses each document that is not dev while the method freeze manifest does not exist. With the manifest:
    the checks of chapter 5. Then the key split of each block file must be the split of the guard."""
    other = [d for d in ids if d not in split_of]
    if other:
        raise Refusal(f"{len(other)} ids are not doc ids in the form of src/m10_guard.py: {other[:10]}")
    by = Counter(split_of[d] for d in ids)
    held = [d for d in ids if split_of[d] != "dev"]
    out = {"documents": len(ids), "by_split": dict(by), "method_freeze": None, "held_out_allowed": False}
    if held:
        if not fr.METHOD_FREEZE.is_file():
            raise Refusal(f"{len(held)} documents are not dev documents ({ {k: v for k, v in by.items() if k != 'dev'} })"
                          f": refused, because the method freeze manifest {rel(fr.METHOD_FREEZE)} does not exist "
                          f"(criteria 10.2 and 10.3; this script does not write it)")
        mf = fr.method_freeze_gate(ids, split_of, need, None)
        mf["entry_decisions_in_manifest"] = manifest_entry_check(cand.entry)
        mf["held_out_gate"] = pipeline.held_out_gate(ids, "cascade", frozen=frozen)
        out.update({"method_freeze": mf, "held_out_allowed": True})
    wrong = [d for d in ids if read_json(DOCS_DIR / f"{d}.json").get("split") != split_of[d]]
    if wrong:
        raise Refusal(f"{len(wrong)} block files have another key split than the guard: {wrong[:10]}")
    return out


# ------------------------------------------------------------------ R2 and calibration file (chapter 3)
def load_r2_files(values: list[str] | None, records: list[str] | None) -> tuple[dict, dict, dict]:
    """({doc: R2 entry}, {calibration id: record}, the paths and SHA-256 values)."""
    import m10_validation_run as vr  # noqa: PLC0415  (load_r2: p as written, criteria 8.5)
    if bool(values) != bool(records):
        raise Refusal("--r2 and --r2-calibrations go together")
    r2, recs, info = {}, {}, {"r2": [], "r2_calibrations": []}
    try:
        for f in values or []:
            p = Path(f).resolve()
            x = vr.load_r2(p)
            twice = sorted(set(x) & set(r2), key=int)
            if twice:
                raise Refusal(f"{rel(p)}: {len(twice)} documents have an R2 value in 2 files: {twice[:10]}")
            r2.update(x)
            info["r2"].append({"path": rel(p), "sha256": sha256(p), "documents": len(x)})
        for f in records or []:
            p = Path(f).resolve()
            for cid, rec in vr.load_calibration_records(p).items():
                if recs.setdefault(cid, rec) != rec:
                    raise Refusal(f"{rel(p)}: the calibration record {cid} is not equal to the record of another file")
            info["r2_calibrations"].append({"path": rel(p), "sha256": sha256(p)})
    except (vr.RunRefusal, guard.GuardRefusal, OSError, ValueError) as e:
        raise Refusal(f"R2 files: {e}") from None
    missing = sorted({v["calibration"] for v in r2.values()} - set(recs))
    if missing:
        raise Refusal(f"R2: calibration ids without a record: {missing}")
    return r2, recs, info


def measured_status(cals: dict, path: Path) -> dict:
    """Chapter 3, --validation-calibrations: the keys of STATUS_KEYS from the calibration file of the records of
    the finished validation run. Changes cals["calibrations"]. Returns the record of the change."""
    p = Path(path).resolve()
    guard.check_path(p)
    other = read_json(p).get("calibrations")
    if not isinstance(other, dict):
        raise Refusal(f"{rel(p)}: no key calibrations")
    changed, own = [], cals["calibrations"]
    for cid in sorted(set(own) & set(other)):
        a, b = own[cid], other[cid]
        diff = sorted(k for k in set(a) | set(b) if k not in STATUS_KEYS and a.get(k) != b.get(k))
        if diff:
            raise Refusal(f"{rel(p)}: the record {cid} differs in {diff} from the record of this run")
        if any(a.get(k) != b.get(k) for k in STATUS_KEYS):
            own[cid] = {**a, **{k: b[k] for k in STATUS_KEYS if k in b}}
            changed.append(cid)
    return {"path": rel(p), "sha256": sha256(p), "ids_in_both_files": len(set(own) & set(other)),
            "records_with_the_status_of_that_file": changed,
            "target_status": {cid: own[cid].get("target_status") for cid in changed}}


def run_calibrations(cand: Candidate, frozen, floor, r2_records: dict, validation_cals: str | None) -> dict:
    """The calibration file of the run (chapter 3)."""
    design = dataclasses.replace(frozen, records=cand.records)
    cals = pipeline.cascade_calibrations(design, cand.entry["d1"], True, floor,
                                         {"calibrations": r2_records} if r2_records else None)
    cals.update({"version": f"{cand.name}-{VERSION}", "candidate": cand.label, "entry": cand.entry,
                 "what": f"calibration records of a run of the candidate {cand.label}: the records of its entry "
                         "variant, floor records without a threshold a (documents with the floor fallback), R2 "
                         "records"})
    cals["sources"] = {**cals["sources"], "candidate_files": cand.files, "fullrun2": pipeline.script_info(SCRIPT, VERSION),
                       "validation_calibrations": measured_status(cals, Path(validation_cals))
                       if validation_cals else None}
    return cals


# ------------------------------------------------------------------ output folder (chapter 4)
def check_out_folder(out: Path) -> None:
    """Refuses a folder with content that is not the folder of an earlier run of this script. The check writes no
    file and deletes no file."""
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


def document_state(out: Path, d: str, params: dict) -> dict:
    """Chapter 6: the result of one document from its files (no new output)."""
    import m10_validation_run as vr  # noqa: PLC0415  (gj12: the rule of GJ.12 for the documents of a folder)
    ok, why = fr.valid_output(out, d, params)
    res: dict = {"result": "not valid", "why": why, "conformance": None}
    if not (out / d / "manifest.json").is_file() or not (out / d / "validation.json").is_file():
        return res
    try:
        g = vr.gj12(types.SimpleNamespace(ids=[d], records_out=out), {})
        man = read_json(out / d / "manifest.json")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        return res | {"why": f"{why}; files not readable ({type(e).__name__})"}
    conf = [k for k, n in g["conformance"].items() if n]
    rule = g["documents_valid"] == 1
    counts = man.get("counts") or {}
    val = man.get("validation") or {}
    res.update({"result": "valid" if ok and rule else "not valid",
                "why": why if not ok else "valid" if rule else "the rule of GJ.12 is not met",
                "conformance": conf[0] if len(conf) == 1 else None,
                "i95_gap_slots": [k for k, n in g["recorded_gap_slots"].items() if n],
                "checks": val.get("checks"), "c10_shacl": val.get("shacl"),
                "labels": {k: counts.get(k) for k in ("label_assertions", "certain_labels", "unsure_labels")},
                "manifest_sha256": sha256(out / d / "manifest.json"),
                "outputs": {k: f["sha256"] for k, f in (man.get("outputs") or {}).items()} |
                {"validation": val.get("sha256")}})
    return res


# ------------------------------------------------------------------ worker processes
_STATE: dict = {}


def worker_state(cfg: dict) -> dict:
    """Per process: the modules, the floor file, the frozen design, the candidate, the calibration file and the R2
    values (loaded one time)."""
    if _STATE.get("key") == cfg["key"]:
        return _STATE
    import m06_converter as mc  # noqa: PLC0415
    import m10_rdf as rdf  # noqa: PLC0415
    import m10_validate as val  # noqa: PLC0415
    import m10_writer as writer  # noqa: PLC0415
    st = {"key": cfg["key"], "mc": mc, "rdf": rdf, "val": val, "writer": writer}
    st["floor"] = pipeline.load_floor(Path(cfg["floor_file"]))
    st["frozen"] = pipeline.load_design(None, None, require_freeze=True)
    st["cand"] = CANDIDATES[cfg["candidate"]](cfg["candidate_options"], st["frozen"])
    if st["cand"].files != cfg["params"]["candidate_files"]:
        raise Refusal("a file of the candidate changed after the start of the run")
    st["cals"], st["cal_file"] = writer.load_calibrations(Path(cfg["calibrations"]))
    st["r2"] = load_r2_files(cfg["r2"], cfg["r2_calibrations"])[0]
    st["sets"] = pipeline.design.load_sets()
    st["dev"] = {str(x) for x in st["sets"]["dev"]}
    _STATE.clear()
    _STATE.update(st)
    return _STATE


def work_batch(ids: list[str], cfg: dict) -> list[dict]:
    t0 = time.perf_counter()
    try:
        st = worker_state(cfg)
        split = guard.assert_allowed(ids)["split_of"]                 # also warms the guard cache of this process
        if not cfg["held_out_allowed"] and any(split.get(d) != "dev" for d in ids):
            raise Refusal("a document of the batch is not a dev document")
        gate = st["cand"].gate(ids)
    except (Exception, SystemExit) as e:  # noqa: BLE001  (each failure goes into the run record)
        return [{"doc_id": d, "result": "error", "error": f"worker start: {type(e).__name__}: {str(e)[:300]}",
                 "seconds": {}} for d in ids]
    exp, exp_error = {}, None
    try:
        exp = st["mc"].build_export_records(ids)
    except (Exception, SystemExit) as e:  # noqa: BLE001
        exp_error = f"{type(e).__name__}: {str(e)[:200]}"
    t_exp = time.perf_counter() - t0
    out = []
    for d in ids:
        rec = work_one(d, st, cfg, exp.get(d), gate)
        rec["seconds"]["export_share"] = round(t_exp / len(ids), 3)
        if exp_error and "export" not in rec.get("error", ""):
            rec["export_batch_error"] = exp_error
        out.append(rec)
    return out


def decisions_of(d: str, st: dict, cfg: dict, gate) -> dict:
    """Chapter 2: the decisions of the candidate, or the floor decisions with the value status unsure."""
    cand, frozen = st["cand"], st["frozen"]
    rules = pipeline.load_rules(d)
    job = pipeline.find_states(d, cfg["states"])
    dec, why = None, None
    if job is None:
        why = pipeline.NO_STATES
    else:
        try:
            with pipeline.design_inputs(d, rules, None):
                dec = cand.decide(d, job, st["r2"].get(d), gate, st["dev"])
        except ValueError as e:
            if NO_PATH not in str(e):
                raise
            why = f"the B2 form has no path ({str(e)[:120]}): the floor decisions with the value status unsure"
        if dec is None and why is None:
            raise pipeline.PipelineRefusal(f"{d}: the candidate gave no decisions for a document with a states file")
    if dec is None:
        dec = pipeline.decide(d, "cascade", frozen, cfg["states"] if job is None else (), cand.entry["d1"], False, None,
                              floor=st["floor"], rules=rules, dev_ids=st["dev"], sets=st["sets"])
        if not dec.get("no_states") or not pipeline.floor_unsure({"calibrations": st["cals"]}, dec):
            raise pipeline.PipelineRefusal(f"{d}: the floor fallback is not a floor record without a threshold a")
        if job is not None:
            del dec["no_states"]
        dec["fallback"] = {"reason": why, "value_status": "unsure", "states_file": job is not None}
        dec["entry"] = dict(cand.entry)
    else:
        p = pipeline.design.npz_path(job, d)
        dec["states"] = {"job": rel(job), "file": rel(p), "sha256": sha256(p)}
    dec.setdefault("candidate", cand.label)               # the decision function of a candidate can give it
    dec["fullrun2"] = pipeline.script_info(SCRIPT, VERSION)
    return pipeline.checked(dec, rules)


def work_one(d: str, st: dict, cfg: dict, exp_record: dict | None, gate) -> dict:
    out = Path(cfg["out"])
    folder = out / d
    res: dict = {"doc_id": d, "result": "error", "seconds": {}}
    t0 = time.perf_counter()
    try:
        if folder.exists() or folder.is_symlink():
            if not fr.made_by_this_script(out, d):
                raise Refusal(f"{d}: the folder {rel(folder)} exists and this script did not make it (no decisions "
                              f"file, no manifest of the writer): it is not deleted")
            shutil.rmtree(folder)
        if exp_record is None:
            exp_record = st["mc"].build_export_records([d]).get(d)
            if exp_record is None:
                raise SystemExit(f"{d}: no export record")
        dec = decisions_of(d, st, cfg, gate)
        res["decisions_sha256"] = write_json(out / "decisions" / f"{d}.json", dec)
        res["floor_fallback"] = (dec.get("fallback") or {}).get("reason")
        res["no_states"] = bool(dec.get("no_states"))
        res["r2"] = dec.get("r2") is not None
        if dec.get("states"):
            res["states"] = dec["states"]
        t1 = time.perf_counter()
        st["writer"].write_one(d, out, None, exp_record, st["cals"], st["cal_file"], cfg["base"], DOCS_DIR,
                               out / "decisions")
        t2 = time.perf_counter()
        st["rdf"].convert_record(folder, d, cfg["base"])
        t3 = time.perf_counter()
        st["val"].validate_record(folder, d)
        t4 = time.perf_counter()
        res.update(document_state(out, d, cfg["params"]))
        res["seconds"] = {"decisions": round(t1 - t0, 3), "write": round(t2 - t1, 3), "rdf": round(t3 - t2, 3),
                          "validate": round(t4 - t3, 3), "total": round(time.perf_counter() - t0, 3)}
    except (Exception, SystemExit) as e:  # noqa: BLE001  (one document does not stop the others)
        res["result"] = "error"
        res["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        res["seconds"]["total"] = round(time.perf_counter() - t0, 3)
    return res


# ------------------------------------------------------------------ the command run
def prepare(args) -> dict:
    """Guards, parameters and the calibration file before the run record. No rule file, no states file and no
    output of a document is read before the guards."""
    out = Path(args.out).resolve()
    guard.check_path(out)
    if not out.is_relative_to(ROOT) or out == ROOT or out.is_relative_to(SRC) or out == GJ \
            or out in (DOCS_DIR, fr.cal.RULES_DIR):
        raise Refusal(f"--out {out}: use a new folder in the project folder for the run")
    check_out_folder(out)
    if args.candidate not in CANDIDATES:
        raise Refusal(f"--candidate {args.candidate!r}: not one of {sorted(CANDIDATES)}")
    if not re.fullmatch(r"https?://[^\s<>\"{}|\\^`]+/", args.base or ""):      # the rule of check_base of the writer
        raise Refusal(f"base IRI {args.base!r}: it must start with http:// or https:// and end with /")
    ids = resolve_ids(args.set)
    g = fr.check_documents(ids)
    floor = pipeline.load_floor(Path(args.calibrations) if args.calibrations else None)
    frozen = pipeline.load_design(None, None, require_freeze=True)
    opts = {"design_b1s_sha256": args.design_b1s_sha256}
    cand = CANDIDATES[args.candidate](opts, frozen)
    states = [str(p) for p in pipeline.states_dirs(args.states or DEFAULT_STATES)]
    for p in states:
        if not Path(p).is_dir():
            raise Refusal(f"--states {p}: no folder")
    design_need = {f"{rel(frozen.design_dir)}/{k}": v for k, v in frozen.files.items()}
    design_need[rel(frozen.freeze_path)] = frozen.freeze["_sha256"]
    need = code_sha256() | {rel(floor.path): floor.info["sha256"]} | design_need | cand.files
    gate = split_gate(ids, g["split_of"], need, cand, frozen)
    with_states = [d for d in ids if pipeline.find_states(d, states) is not None]        # file names only
    r2, r2_records, r2_info = load_r2_files(args.r2, args.r2_calibrations)
    without_r2 = [d for d in with_states if d not in r2] if args.r2 else []
    if without_r2:
        raise Refusal(f"R2: {len(without_r2)} documents with a states file have no R2 value: {without_r2[:10]}")
    cals = run_calibrations(cand, frozen, floor, r2_records, args.validation_calibrations)
    cal_path = out / "calibrations.json"
    text = json.dumps(cals, ensure_ascii=False, indent=1) + "\n"
    if cal_path.is_file() and cal_path.read_text(encoding="utf-8") != text:
        raise Refusal(f"{rel(cal_path)} exists with another content: other parameters (use a new folder)")
    params = {"schema": PARAMS_SCHEMA, "candidate": cand.name, "candidate_label": cand.label, "entry": cand.entry,
              "candidate_info": cand.info, "candidate_files": cand.files, "base": args.base,
              "calibrations": {"path": rel(cal_path), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()},
              "floor": floor.info, "states": [rel(Path(p)) for p in states], "design_files": frozen.files,
              "design_freeze": {"path": rel(frozen.freeze_path), "sha256": frozen.freeze["_sha256"]},
              "r2": r2_info["r2"], "r2_calibrations": r2_info["r2_calibrations"],
              "validation_calibrations": cals["sources"]["validation_calibrations"],
              "output_imports": {p: sha256(ROOT / p) for p in fr.OUTPUT_IMPORTS},
              "output_scripts": {k: sha256(ROOT / v) for k, v in fr.OUTPUT_SCRIPTS.items()}}
    pp = out / "parameters.json"
    if pp.is_file():
        old = read_json(pp)
        a, b = ({k: v for k, v in x.items() if k != "output_scripts"} for x in (old, params))
        if a != b:
            diff = sorted(k for k in set(a) | set(b) if k not in a or k not in b or a[k] != b[k])
            raise Refusal(f"{rel(pp)}: the folder has other parameters {diff} (use a new folder)")
    out.mkdir(parents=True, exist_ok=True)
    cal_path.write_text(text, encoding="utf-8")
    write_json(pp, params)
    params["calibrations"]["abs"] = str(cal_path)
    cfg = {"key": f"{out}|{sha256(pp)}", "out": str(out), "candidate": cand.name, "candidate_options": opts,
           "base": args.base, "floor_file": str(floor.path), "states": states, "calibrations": str(cal_path),
           "r2": [str(Path(f).resolve()) for f in args.r2 or []],
           "r2_calibrations": [str(Path(f).resolve()) for f in args.r2_calibrations or []],
           "held_out_allowed": gate["held_out_allowed"], "params": params}
    return {"out": out, "ids": ids, "guard": g, "gate": gate, "params": params, "cfg": cfg, "candidate": cand,
            "documents_with_a_states_file": len(with_states),
            "documents_without_a_states_file": [d for d in ids if d not in set(with_states)],
            "documents_with_r2": sum(d in r2 for d in ids)}


def summary(ids: list[str], rows: dict) -> dict:
    """Chapter 6: the counts by result, by conformance and by value status."""
    by_result = Counter(r["result"] for r in rows.values())
    valid = [r for r in rows.values() if r["result"] == "valid"]
    conf = Counter(str(r.get("conformance")) for r in valid)
    lab = {k: sum(int((r.get("labels") or {}).get(k) or 0) for r in valid)
           for k in ("label_assertions", "certain_labels", "unsure_labels")}
    slots = Counter(s for r in valid for s in r.get("i95_gap_slots") or [])
    fb = {d: r["floor_fallback"] for d, r in rows.items() if r.get("floor_fallback")}
    return {"documents": len(ids), "by_result": {k: by_result.get(k, 0) for k in ("valid", "not valid", "error")},
            "valid_by_conformance": {k: conf.get(k, 0) for k in gaps.CONFORMANCE} |
            {k: n for k, n in conf.items() if k not in gaps.CONFORMANCE},
            "recorded_gap_slots_of_the_valid_documents": {k: slots.get(k, 0) for k in gaps.GAP_SLOTS},
            "labels_of_the_valid_documents_by_value_status": {
                "certain": lab["certain_labels"], "unsure": lab["unsure_labels"],
                "label_assertions": lab["label_assertions"],
                "note": "label_assertions also counts the labels without a probability (export, constant, copy)"},
            "documents_with_the_floor_fallback": {"count": len(fb), "documents": by_id(fb),
                                                  "reasons": dict(Counter(v.split(" (")[0].split(":")[0]
                                                                          for v in fb.values()))},
            "valid_documents_with_r2": sum(1 for r in valid if r.get("r2")),
            "c10_shacl_information": dict(Counter(str(r.get("c10_shacl")) for r in valid))}


def cmd_run(args) -> int:
    t_all = time.perf_counter()
    p = prepare(args)
    out, ids, cfg, cand = p["out"], p["ids"], p["cfg"], p["candidate"]
    run_path = fr.next_run_path(out)
    scripts = code_paths()
    rec = pipeline.run_record_start(run_path, f"batch conversion of the candidate {cand.label} on {len(ids)} "
                                              f"documents", scripts)
    rec.update({"actor": ACTOR, "version": VERSION,
                "parameters": {k: ({x: y for x, y in v.items() if x != "abs"} if k == "calibrations" else v)
                               for k, v in p["params"].items()},
                "guard": {k: v for k, v in p["guard"].items() if k not in ("split_of", "parliament_of")},
                "split_gate": p["gate"], "workers": args.workers, "batch": args.batch,
                "documents_with_a_states_file": p["documents_with_a_states_file"],
                "documents_without_a_states_file": p["documents_without_a_states_file"],
                "documents_with_r2": p["documents_with_r2"]})
    write_json(run_path, rec)
    before = {d: document_state(out, d, p["params"]) for d in ids if (out / d / "manifest.json").is_file()}
    kept = {d: r | {"doc_id": d, "skipped": "valid outputs of an earlier run"} for d, r in before.items()
            if r["result"] == "valid"}
    for d, r in kept.items():
        dec = read_json(out / "decisions" / f"{d}.json")
        r.update({"floor_fallback": (dec.get("fallback") or {}).get("reason"), "r2": dec.get("r2") is not None,
                  "no_states": bool(dec.get("no_states"))})
    todo = [d for d in ids if d not in kept]
    rec["skipped_valid_outputs"] = len(kept)
    (out / "decisions").mkdir(parents=True, exist_ok=True)
    events = run_path.with_suffix(".events.jsonl")
    results: dict[str, dict] = {}
    work = fr.batches(todo, args.workers, args.batch)
    print(json.dumps({"candidate": cand.name, "documents": len(ids), "skipped_valid_outputs": len(kept),
                      "to_make": len(todo), "batches": len(work), "workers": args.workers,
                      "documents_without_a_states_file": len(p["documents_without_a_states_file"]),
                      "run": rel(run_path)}), flush=True)
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
                bad = sum(r["result"] != "valid" for r in results.values())
                print(json.dumps({"done": len(results), "of": len(todo), "not_valid": bad,
                                  "seconds": round(time.perf_counter() - t_work, 1)}), flush=True)
    wall = time.perf_counter() - t_work
    tot = [r["seconds"]["total"] for r in results.values() if r.get("seconds", {}).get("total") is not None]
    steps = {k: [r["seconds"][k] for r in results.values() if k in r.get("seconds", {})]
             for k in ("export_share", "decisions", "write", "rdf", "validate")}
    all_rows = kept | results
    not_valid = by_id(d for d, r in all_rows.items() if r["result"] != "valid")
    outputs = {d: {"manifest": r.get("manifest_sha256"), "decisions": r.get("decisions_sha256"),
                   **(r.get("outputs") or {})} for d, r in results.items() if r["result"] == "valid"}
    rec.update({"documents": len(ids), "made": len(todo), "valid": len(ids) - len(not_valid), "not_valid": not_valid,
                "errors": {d: all_rows[d].get("error") or all_rows[d].get("why") for d in not_valid},
                "summary": summary(ids, all_rows), "results": results, "results_of_skipped_documents": kept,
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
                         "seconds_of_each_document": {d: r["seconds"].get("total") for d, r in results.items()},
                         "seconds_total": round(time.perf_counter() - t_all, 2)},
                "events": {"path": rel(events), "sha256": sha256(events) if events.exists() else None}})
    pipeline.run_record_finish(run_path, rec, scripts)
    print(json.dumps({"documents": len(ids), "skipped_valid_outputs": len(kept), "made": len(todo),
                      "valid": rec["valid"], "not_valid": not_valid[:20],
                      "summary": {k: v for k, v in rec["summary"].items() if k != "documents"},
                      "time": {k: v for k, v in rec["time"].items() if k != "seconds_of_each_document"},
                      "run": {"path": rel(run_path), "sha256": sha256(run_path)},
                      "frozen_files_different": rec["frozen_files"]["different"]}, indent=1), flush=True)
    return 0 if not not_valid else 2


def cmd_status(args) -> int:
    out = Path(args.out).resolve()
    pp = out / "parameters.json"
    if not pp.is_file() or read_json(pp).get("schema") != PARAMS_SCHEMA:
        raise Refusal(f"{rel(pp)} does not exist or is not a parameters file of this script")
    params = read_json(pp)
    params["calibrations"]["abs"] = str(ROOT / params["calibrations"]["path"])
    params["output_scripts"] = {k: sha256(ROOT / v) for k, v in fr.OUTPUT_SCRIPTS.items()}
    ids = by_id(p.name for p in out.iterdir() if p.is_dir() and p.name.isdigit())
    rows = {d: document_state(out, d, params) for d in ids}
    print(json.dumps({"folder": rel(out), "document_folders": len(ids),
                      "by_why": dict(Counter(r["why"] for r in rows.values())),
                      "summary": summary(ids, rows)}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="gate GJ: batch conversion for a candidate of the block step")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--candidate", required=True, help=f"one of {sorted(CANDIDATES)}")
    r.add_argument("--set", required=True, nargs="+", help="dev, or doc ids and list files")
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=fr.DEFAULT_WORKERS)
    r.add_argument("--batch", type=int, default=fr.DEFAULT_BATCH)
    r.add_argument("--base", default=DEFAULT_BASE)
    r.add_argument("--design-b1s-sha256", default=None, help="candidate b1s: the SHA-256 of design_b1s.json")
    r.add_argument("--r2", nargs="+", default=None)
    r.add_argument("--r2-calibrations", nargs="+", default=None)
    r.add_argument("--validation-calibrations", default=None)
    r.add_argument("--states", nargs="+", default=None, help="job folders of the states (default: both full jobs)")
    r.add_argument("--calibrations", default=None, help="the floor calibration file (default floor_v1.json)")
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
