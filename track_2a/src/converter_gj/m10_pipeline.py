# SPDX-License-Identifier: Apache-2.0
"""Gate GJ (status EXCEPTION), criteria chapters 3, 4 item 7, 7.1 to 7.4, 8.5 and 10.1 to 10.3: one decision function
for the floor mode and the cascade mode (interface 7), the calibration file of a cascade run, the guards of the
held-out sets, and the decisions command of the cascade mode.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream D of
workflow <id> (wave 3), for the AI agent. Phases 4 and 6, gate GJ (OPEN). Status: EXCEPTION (process
rule 10), NOT RELEASED. No human checked this file. This file changes no existing file. src/m10_design.py is frozen
by record (9e6b912e...): this file only calls its functions.

1 Function decide(doc_id, mode, frozen, states_dir, entry_d1, entry_b12, r2)
  floor    floor_decisions() of src/m10_cascade.py with the floor calibration file (src/m10_calibrate.py
           floor-fit, daten/gj/calibration/floor_v1.json). The output is the output of src/m10_cascade.py without a
           change. frozen and states_dir are not used. r2 must be None (the floor converter F1 has no Apertus
           value).
  cascade  assert_apply_allowed() of src/m10_design.py, then the held-out guard of chapter 3, then
           cascade_decisions() of src/m10_design.py with the frozen design of load_design() (frozen). The key
           pipeline names this file. r2: None or {"p", "calibration", ...}; p is clipped to [0.005, 0.995] and
           rounded to 4 decimals (criteria 8.5).
           A document without a states file (more than 32,768 tokens, criteria chapter 4 item 7) gets the floor
           decisions with r2 None (no Apertus value). The key no_states says it. The calibration file of a cascade
           run (chapter 2) has no threshold a for the floor records, so the writer gives each label of the document
           the value status unsure.
  states_dir: a job folder of the states that holds states/<doc>.npz (for example daten/gj/states/gpu1_labelled),
           or a list of job folders (the full run uses gpu1_labelled and gpu2_bulk). A folder named states that
           holds <doc>.npz is also accepted (its parent folder is the job folder). A document with a states file in
           2 or more job folders is refused.
  Keyword arguments: floor (load_floor(); default the floor calibration file), rules and doc (the rule record and
           the block file of the document if they do not come from daten/gj/rules and daten/gj/docs, for example
           src/m10_convert.py with fresh Docling: for the time of the call, load_rule and load_doc of
           src/m10_design.py give these records for this document only), dev_ids (the in-sample documents of the
           heads; default the key dev of daten/gj/sets.json), sets.
  Each output passes check_decisions() of src/m10_cascade.py, else PipelineRefusal.

2 Calibration file of a cascade run (cascade_calibrations())
  calibration_file() of src/m10_design.py for the entry variant, the records of the floor calibration file without
  the key certain_threshold (only for the documents without states: value status unsure), and the R2 records
  (optional, {"calibrations": {...}}). The key floor_lookup of the floor file goes with it, because
  src/m10_calibrate.py measure needs it for the gaps of the floor documents. Two records with the same id stop.

3 Guards (process rule 6, criteria chapters 3 and 10)
  Each document passes src/m10_guard.py (dev, validation and group 7 only; a test document is refused). The split of
  the guard counts (the split of the parliament), not only the sets of daten/gj/sets.json: the 2,371 other documents
  hold 760 validation documents and 11 group-7 documents, and assert_apply_allowed() of src/m10_design.py counts
  only the documents of daten/gj/sets.json.
  Mode cascade: a validation document needs the real design freeze file daten/gj/design_freeze.json (not a dry run,
  no problems, not a synthetic design). A group-7 document also needs the method freeze manifest
  daten/gj/freeze_manifest.json, and the manifest must name the SHA-256 of this file. load_design() refuses a
  freeze file that does not name the SHA-256 of this file, of src/m10_cascade.py and of src/m10_design.py now.
  No states file of a held-out document is opened before these checks.
  Mode floor: a validation document needs the design freeze file, a group-7 document the method freeze manifest
  (freeze_check() of src/m10_calibrate.py), and the freeze file must name the SHA-256 of this file.
  Change of 13.10.2026 (stream X2 of the last change round before the design freeze, Claude Opus 5.5). In the mode
  floor, a validation or group-7 document also needs the real design freeze file, as in the mode cascade. The file
  daten/gj/design_freeze.json must be a JSON object with dry_run false and with no problems. An id that the guard
  does not give back (for example an id with a space) is refused.

4 Command (src/m10_cascade.py --mode cascade calls cascade_command())
  uv run --offline --frozen --no-sync python src/m10_cascade.py --mode cascade --set dev|validation|group7
      [--doc ID ...] --states DIR [DIR ...] --entry-d1 yes|no --entry-b12 yes|no [--design daten/gj/design]
      [--freeze daten/gj/design_freeze.json] [--r2 FILE] [--r2-calibrations FILE] [--out daten/gj/decisions]
      [--label NAME] [--continue-missing]
  The command needs the design freeze file (also for dev). Output: <out>/<doc>.json, <out>/calibrations.json and
  the run record daten/gj/runs/pipeline_cascade_<set>[_<label>].json (the SHA-256 of the scripts before the first
  value, the inputs, each output, the documents without states, the time of each document). validation and
  group7: one run only (criteria 10.3): an existing run record or an existing output stops the run; after a
  technical stop, --continue-missing with a new --label makes only the documents without an output. Only one tool
  makes the one validation run: this command or the runner of the validation run, not both.
  The console shows only counts and SHA-256 values.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_calibrate as cal  # noqa: E402  (floor lookup, clip, run records, freeze_check)
import m10_cascade as cascade  # noqa: E402  (floor mode and check_decisions of interface 7)
import m10_design as design  # noqa: E402  (frozen design and cascade_decisions; frozen by record, not changed)
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)

VERSION = "m10-pipeline-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = ROOT / "daten/gj"
RUNS = GJ / "runs"
CASCADE_SCRIPT = Path(cascade.__file__).resolve()
DESIGN_SCRIPT = Path(design.__file__).resolve()
MODES = ("floor", "cascade")
STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
ACTOR = "AI agent (Claude Opus 5.5), stream D of workflow <id>, for the AI agent"
NO_STATES = "no states file: the floor decisions with the value status unsure (criteria chapter 4 item 7)"
UNSURE_NOTE = ("In a cascade run this record is used only for a document without states (criteria chapter 4 item "
               "7): it has no threshold a, so each label of such a document is unsure.")


class PipelineRefusal(Exception):
    """A document, a file or a mode was refused (process rule 6, criteria chapters 3, 4 and 10)."""


# ------------------------------------------------------------------ small helpers
def sha256(p: Path) -> str:
    return cal.sha256(Path(p))


def rel(p: Path) -> str:
    return cal.rel(Path(p))


def script_info(p: Path, version: str | None = None) -> dict:
    out = {"path": rel(p), "sha256": sha256(p)}
    return out | ({"version": version} if version else {})


def code_sha256() -> dict:
    """The SHA-256 of this file and of the m10 files that a decision uses."""
    return {rel(p): sha256(p) for p in (SCRIPT, CASCADE_SCRIPT, DESIGN_SCRIPT, cal.SCRIPT, Path(guard.__file__))}


# ------------------------------------------------------------------ floor calibration file
@dataclass
class Floor:
    path: Path
    calib: dict
    lookup: cal.FloorLookup
    info: dict                 # {"path", "sha256", "version"}: the key calibration of a floor decisions file
    fit_docs: frozenset


def load_floor(cal_file: Path | None = None) -> Floor:
    """The floor calibration file of src/m10_calibrate.py floor-fit (keys calibrations and floor_lookup), after the
    SHA-256 check of its fit set file."""
    p = Path(cal_file or cal.FLOOR_FILE).resolve()
    if not p.is_file():
        raise PipelineRefusal(f"no floor calibration file {rel(p)} (src/m10_calibrate.py floor-fit)")
    calib = cal.read_json(p)
    if "floor_lookup" not in calib or "calibrations" not in calib:
        raise PipelineRefusal(f"{rel(p)} has no key floor_lookup or calibrations")
    fit_p = ROOT / calib["fit_set"]["path"]
    if sha256(fit_p) != calib["fit_set"]["sha256"]:
        raise PipelineRefusal("the fit set file of the floor calibration file has another SHA-256")
    fit_docs = frozenset(str(x) for x in cal.read_json(fit_p)["documents"])
    info = {"path": rel(p), "sha256": sha256(p), "version": calib.get("version")}
    return Floor(p, calib, cal.FloorLookup(calib), info, fit_docs)


# ------------------------------------------------------------------ frozen design
def load_design(design_dir: Path | None = None, freeze_file: Path | None = None,
                require_freeze: bool = True) -> design.Frozen:
    """load_frozen() of src/m10_design.py. With a freeze file: it must name the SHA-256 of this file, of
    src/m10_cascade.py and of src/m10_design.py now (no change after the freeze, GJ.11)."""
    design_dir = Path(design_dir or design.DESIGN)
    ff = Path(freeze_file or design.FREEZE_FILE)
    if require_freeze and not ff.is_file():
        raise PipelineRefusal(f"no design freeze file {rel(ff)}: the cascade mode uses the design only after the "
                              f"design freeze (criteria chapter 10.1)")
    use = ff if ff.is_file() else None
    try:
        frozen = design.load_frozen(design_dir, use)
    except design.DesignRefusal as e:
        raise PipelineRefusal(str(e)) from None
    if frozen.freeze is not None:
        frozen.freeze["_sha256"] = sha256(ff)
        code = frozen.freeze.get("code") or {}
        changed = [rel(p) for p in (SCRIPT, CASCADE_SCRIPT, DESIGN_SCRIPT) if code.get(rel(p)) != sha256(p)]
        if changed:
            raise PipelineRefusal(f"the freeze file {rel(ff)} does not name the SHA-256 of {changed} now: a file "
                                  f"changed after the freeze, or the file did not exist at the freeze")
    return frozen


# ------------------------------------------------------------------ states files
def states_dirs(states_dir) -> list[Path]:
    if states_dir is None:
        return []
    items = [states_dir] if isinstance(states_dir, (str, Path)) else list(states_dir)
    out = []
    for x in items:
        p = Path(x).resolve()
        if p.name == "states" and not (p / "states").is_dir():
            p = p.parent
        out.append(p)
    return out


def find_states(d: str, states_dir) -> Path | None:
    """The job folder that holds states/<d>.npz, or None. Only file names are examined (no file is opened)."""
    hits = [p for p in states_dirs(states_dir) if design.npz_path(p, d).is_file()]
    if len(hits) > 1:
        raise PipelineRefusal(f"{d}: a states file in {len(hits)} job folders: {[rel(p) for p in hits]}")
    return hits[0] if hits else None


# ------------------------------------------------------------------ guards of the held-out sets (chapter 3)
def real_design_freeze(n_val: int, n_g7: int) -> dict:
    """Mode floor: the design freeze file at the real path, as the mode cascade needs it. Refuses an absent file, a
    file that is not a JSON object, a dry run and a file with problems. Returns the path and the SHA-256."""
    ff = design.FREEZE_FILE
    if not ff.is_file():
        raise PipelineRefusal(f"{n_val} validation and {n_g7} group-7 documents: no design freeze file {rel(ff)} "
                              f"(criteria chapter 3, rules 2 and 3)")
    try:
        fr = cal.read_json(ff)
    except ValueError:
        fr = None
    if not isinstance(fr, dict) or fr.get("dry_run") is not False or fr.get("problems") != []:
        raise PipelineRefusal(f"validation and group-7 documents need the real design freeze file {rel(ff)} "
                              f"(a JSON object, not a dry run, no problems)")
    return {"path": rel(ff), "sha256": sha256(ff)}


def held_out_gate(ids, mode: str, frozen: design.Frozen | None = None, floor: Floor | None = None) -> dict:
    """Refuses validation and group-7 documents (split of src/m10_guard.py) before their freeze. Returns counts."""
    ids = [str(d) for d in ids]
    try:
        g = guard.assert_allowed(ids)
    except guard.GuardRefusal as e:
        raise PipelineRefusal(str(e)) from None
    split = g["split_of"]
    other = [d for d in ids if d not in split]
    if other:
        raise PipelineRefusal(f"{len(other)} ids are not doc ids in the form of src/m10_guard.py (for example an id "
                              f"with a space): {other[:10]}")
    val = [d for d in ids if split[d] == "validation"]
    g7 = [d for d in ids if split[d] == "group7"]
    out = {"documents": len(ids), "dev": sum(split[d] == "dev" for d in ids), "validation": len(val),
           "group7": len(g7)}
    if not (val or g7):
        return out
    if mode == "cascade":
        fr = frozen.freeze if frozen is not None else None
        if fr is None:
            raise PipelineRefusal(f"{len(val)} validation and {len(g7)} group-7 documents: no verified design freeze "
                                  f"file (criteria chapter 3, rules 2 and 3)")
        if frozen.freeze_path != design.FREEZE_FILE.resolve() or fr.get("dry_run") or fr.get("problems") \
                or frozen.synthetic:
            raise PipelineRefusal(f"validation and group-7 documents need the real design freeze file "
                                  f"{rel(design.FREEZE_FILE)} (not a dry run, no problems, not synthetic)")
        if g7:
            if not design.METHOD_FREEZE.is_file():
                raise PipelineRefusal(f"{len(g7)} group-7 documents: no method freeze manifest "
                                      f"{rel(design.METHOD_FREEZE)} (criteria chapter 10.5)")
            if sha256(SCRIPT) not in design.METHOD_FREEZE.read_text(encoding="utf-8"):
                raise PipelineRefusal(f"the method freeze manifest does not name the SHA-256 of {rel(SCRIPT)}")
        out["freeze"] = {"path": rel(design.FREEZE_FILE), "sha256": fr.get("_sha256")}
        return out
    floor = floor or load_floor()
    out["freeze"] = real_design_freeze(len(val), len(g7))
    for name, docs in (("validation", val), ("group7", g7)):
        if not docs:
            continue
        try:
            chk = cal.freeze_check(name, floor.path)
        except SystemExit as e:
            raise PipelineRefusal(f"{len(docs)} {name} documents: {e}") from None
        if sha256(SCRIPT) not in (ROOT / chk["freeze_file"]).read_text(encoding="utf-8"):
            raise PipelineRefusal(f"the freeze file {chk['freeze_file']} does not name the SHA-256 of {rel(SCRIPT)}")
        out[f"freeze_{name}"] = chk
    return out


# ------------------------------------------------------------------ inputs of one document
_DIGESTS: dict = {}


def load_rules(d: str) -> dict:
    """daten/gj/rules/<d>.json after the path guard, with the SHA-256 of the run record of src/m10_rules.py."""
    if not _DIGESTS:
        _DIGESTS.update(cal.stream_digests()[0])
    r = cal.checked_file(cal.RULES_DIR / f"{d}.json", _DIGESTS, "src/m10_rules.py")
    if str(r.get("doc_id")) != str(d):
        raise PipelineRefusal(f"{d}: rule file of another document")
    return r


@contextlib.contextmanager
def design_inputs(d: str, rules: dict | None, doc: dict | None):
    """For the time of the call: load_rule and load_doc of src/m10_design.py give the given records for d."""
    if rules is None and doc is None:
        yield
        return
    for name, x in (("rule record", rules), ("block file", doc)):
        if x is not None and str(x.get("doc_id")) != d:
            raise PipelineRefusal(f"{d}: the {name} is for another document")
    old_rule, old_doc = design.load_rule, design.load_doc

    def load_rule(x: str) -> dict:
        return rules if rules is not None and str(x) == d else old_rule(x)

    def load_doc(x: str) -> dict:
        return doc if doc is not None and str(x) == d else old_doc(x)

    design.load_rule, design.load_doc = load_rule, load_doc
    try:
        yield
    finally:
        design.load_rule, design.load_doc = old_rule, old_doc


def normal_r2(d: str, r2) -> dict | None:
    if r2 is None:
        return None
    if not isinstance(r2, dict) or not isinstance(r2.get("p"), (int, float)) or not 0 <= r2["p"] <= 1 \
            or not isinstance(r2.get("calibration"), str):
        raise PipelineRefusal(f"{d}: r2 must be {{'p': value in [0, 1], 'calibration': id}}")
    return dict(r2, p=design.as_written(r2["p"]))


# ------------------------------------------------------------------ the decision function (chapter 1)
def decide(doc_id, mode: str, frozen: design.Frozen | None, states_dir, entry_d1: bool, entry_b12: bool, r2=None, *,
           floor: Floor | None = None, rules: dict | None = None, doc: dict | None = None,
           dev_ids: set[str] | None = None, sets: dict | None = None) -> dict:
    """Interface 7 for one document (chapter 1 of the docstring)."""
    d = str(doc_id)
    if mode not in MODES:
        raise PipelineRefusal(f"mode {mode!r} is not floor or cascade")
    if mode == "floor":
        if r2 is not None:
            raise PipelineRefusal(f"{d}: the floor mode has no r2 (no Apertus value)")
        floor = floor or load_floor()
        held_out_gate([d], "floor", floor=floor)
        r = rules if rules is not None else load_rules(d)
        if str(r.get("doc_id")) != d:
            raise PipelineRefusal(f"{d}: the rule record is for another document")
        dec = cascade.floor_decisions(r, floor.lookup, d in floor.fit_docs, floor.info)
        return checked(dec, r)
    if frozen is None:
        raise PipelineRefusal(f"{d}: the cascade mode needs the frozen design (load_design())")
    sets = sets or design.load_sets()
    try:
        design.assert_apply_allowed([d], frozen, sets)
    except design.DesignRefusal as e:
        raise PipelineRefusal(str(e)) from None
    held_out_gate([d], "cascade", frozen=frozen)
    r = rules if rules is not None else load_rules(d)
    job = find_states(d, states_dir)
    if job is None:
        floor = floor or load_floor()
        dec = cascade.floor_decisions(r, floor.lookup, d in floor.fit_docs, floor.info)
        dec["no_states"] = {"reason": NO_STATES, "states_dirs": [rel(p) for p in states_dirs(states_dir)],
                            "value_status": "unsure"}
        dec["pipeline"] = script_info(SCRIPT, VERSION)
        return checked(dec, r)
    dev = dev_ids if dev_ids is not None else {str(x) for x in sets["dev"]}
    with design_inputs(d, rules, doc):
        try:
            dec = design.cascade_decisions(d, frozen, job, bool(entry_d1), bool(entry_b12), normal_r2(d, r2), dev)
        except design.DesignRefusal as e:
            raise PipelineRefusal(str(e)) from None
    if dec is None:
        raise PipelineRefusal(f"{d}: the states file disappeared during the call")
    dec["states"] = {"job": rel(job), "file": rel(design.npz_path(job, d)), "sha256": sha256(design.npz_path(job, d))}
    dec["pipeline"] = script_info(SCRIPT, VERSION)
    return checked(dec, r)


def checked(dec: dict, rules: dict) -> dict:
    bad = cascade.check_decisions(dec, rules)
    if bad:
        raise PipelineRefusal(f"{dec.get('doc_id')}: decisions check of src/m10_cascade.py failed: {bad[:5]}")
    return dec


# ------------------------------------------------------------------ calibration file of a cascade run (chapter 2)
def cascade_calibrations(frozen: design.Frozen, entry_d1: bool, entry_b12: bool, floor: Floor,
                         r2_calibrations: dict | None = None) -> dict:
    out = dict(design.calibration_file(frozen, bool(entry_d1), bool(entry_b12))["calibrations"])
    for cid, rec in floor.calib["calibrations"].items():
        if cid in out:
            raise PipelineRefusal(f"calibration id {cid} is in the design records and in the floor records")
        x = {k: v for k, v in rec.items() if k != "certain_threshold"}
        x["calibration_note"] = (str(x.get("calibration_note", "")).rstrip(". ") + ". " + UNSURE_NOTE).strip()
        out[cid] = x
    for cid, rec in ((r2_calibrations or {}).get("calibrations") or {}).items():
        if cid in out:
            raise PipelineRefusal(f"calibration id {cid} of the R2 records is not new")
        out[cid] = rec
    return {"schema": "parlpdfech-gj-calibrations/1", "version": f"cascade-{VERSION}", "status": STATUS,
            "what": "calibration records of a cascade run: design records of the entry variant, floor records "
                    "without a threshold a (documents without states), R2 records",
            "entry": {"d1": bool(entry_d1), "b1_b2": bool(entry_b12)},
            "sources": {"design_files": frozen.files, "design_freeze_sha256": (frozen.freeze or {}).get("_sha256"),
                        "floor": floor.info, "pipeline": script_info(SCRIPT, VERSION)},
            "calibrations": out, "floor_lookup": floor.calib["floor_lookup"]}


def floor_unsure(cals: dict, dec: dict) -> bool:
    """True if no calibration record of the floor labels of dec has a threshold a (each label is unsure)."""
    ids = [dec["document"]["d1"]["calibration"]] + [b["calibration"] for b in dec["blocks"]] + \
        [x["calibration"] for x in dec.get("boundaries") or []]
    return all(cals["calibrations"][c].get("certain_threshold") is None for c in ids)


# ------------------------------------------------------------------ the decisions command of the cascade mode
def read_r2(path) -> tuple[dict, dict | None]:
    if not path:
        return {}, None
    p = Path(path).resolve()
    guard.check_path(p)
    x = cal.read_json(p)
    return {str(k): v for k, v in x.items()}, {"path": rel(p), "sha256": sha256(p)}


def entry_flag(x) -> bool:
    if isinstance(x, bool):
        return x
    if x in ("yes", "no"):
        return x == "yes"
    raise PipelineRefusal(f"entry decision {x!r} is not yes or no")


def write_json(p: Path, obj) -> str:
    cal.write_json(Path(p), obj)
    return sha256(p)


def cascade_command(args) -> int:
    """src/m10_cascade.py --mode cascade (chapter 4)."""
    try:
        return _cascade_command(args)
    except PipelineRefusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 3


def _cascade_command(args) -> int:
    if not args.states or args.entry_d1 is None or args.entry_b12 is None:
        raise PipelineRefusal("--mode cascade needs --states, --entry-d1 and --entry-b12")
    e1, e2 = entry_flag(args.entry_d1), entry_flag(args.entry_b12)
    out_dir = Path(args.out or design.DECISIONS).resolve()
    if not out_dir.is_relative_to(GJ.resolve()):
        raise PipelineRefusal("the output folder must be inside daten/gj")
    t_all = time.perf_counter()
    ids = cal.load_set(args.set, ("dev", "validation", "group7"))
    if args.doc:
        want = [str(x) for x in args.doc]
        if not set(want) <= set(ids):
            raise PipelineRefusal(f"--doc: documents outside the set {args.set}")
        ids = sorted(want, key=int)
    frozen = load_design(args.design, args.freeze, require_freeze=True)
    floor = load_floor(args.calibrations)
    sets = design.load_sets()
    gate = held_out_gate(ids, "cascade", frozen=frozen)
    held = args.set in ("validation", "group7")
    run_path = RUNS / f"pipeline_cascade_{args.set}{'_' + args.label if args.label else ''}.json"
    if held and run_path.exists():
        raise PipelineRefusal(f"one-run rule (criteria 10.3): {rel(run_path)} exists; a continuation needs --label")
    existing = [d for d in ids if (out_dir / f"{d}.json").exists()]
    if held and existing and not args.continue_missing:
        raise PipelineRefusal(f"one-run rule (criteria 10.3): {len(existing)} outputs exist; only --continue-missing")
    if held and args.continue_missing:
        ids = [d for d in ids if d not in existing]
    r2_all, r2_file = read_r2(args.r2)
    r2_cals, r2_cal_file = read_r2(args.r2_calibrations)
    scripts = [SCRIPT, CASCADE_SCRIPT, DESIGN_SCRIPT, cal.SCRIPT, Path(guard.__file__).resolve()]
    RUNS.mkdir(parents=True, exist_ok=True)
    rec = run_record_start(run_path, f"cascade decisions (mode cascade) on the set {args.set}", scripts)
    rec["documents_with_an_output_before_the_run"] = len(existing)
    out_dir.mkdir(parents=True, exist_ok=True)
    cals = cascade_calibrations(frozen, e1, e2, floor, r2_cals or None)
    cal_path = out_dir / "calibrations.json"
    outputs = {rel(cal_path): write_json(cal_path, cals)}
    dev = {str(x) for x in sets["dev"]}
    seconds, no_states, states_sha = {}, [], {}
    counts = {"blocks": 0, "boundaries": 0, "with_r2": 0, "source_d1": {}, "source_blocks": {}}
    for d in ids:
        t0 = time.perf_counter()
        dec = decide(d, "cascade", frozen, args.states, e1, e2, r2_all.get(d), floor=floor, dev_ids=dev, sets=sets)
        if dec.get("no_states"):
            no_states.append(d)
            if not floor_unsure(cals, dec):
                raise PipelineRefusal(f"{d}: a floor record of a document without states has a threshold a")
        else:
            states_sha[dec["states"]["file"]] = dec["states"]["sha256"]
        p = out_dir / f"{d}.json"
        outputs[rel(p)] = write_json(p, dec)
        seconds[d] = round(time.perf_counter() - t0, 4)
        counts["blocks"] += len(dec["blocks"])
        counts["boundaries"] += len(dec["boundaries"])
        counts["with_r2"] += dec.get("r2") is not None
        s = dec["document"]["d1"]["source"]
        counts["source_d1"][s] = counts["source_d1"].get(s, 0) + 1
        for b in dec["blocks"]:
            counts["source_blocks"][b["source"]] = counts["source_blocks"].get(b["source"], 0) + 1
    sv = list(seconds.values())
    rec.update({"mode": "cascade", "set": args.set, "held_out_run": held, "guard": gate, "documents": len(ids),
                "entry": {"d1": e1, "b1_b2": e2},
                "inputs": {"design_files": frozen.files, "design_freeze": {"path": rel(frozen.freeze_path),
                                                                           "sha256": frozen.freeze.get("_sha256")},
                           "floor_calibrations": floor.info, "r2": r2_file, "r2_calibrations": r2_cal_file,
                           rel(cal.SETS_FILE): sha256(cal.SETS_FILE),
                           "states_files_sha256_canonical": hashlib.sha256(json.dumps(states_sha, sort_keys=True)
                                                                           .encode()).hexdigest(),
                           "states_files": states_sha},
                "documents_without_states": no_states, "outputs": outputs, "counts": counts,
                "seconds_per_document": {"mean": round(statistics.mean(sv), 4) if sv else None,
                                         "median": round(statistics.median(sv), 4) if sv else None,
                                         "max": max(sv) if sv else None, "each": seconds},
                "seconds_total": round(time.perf_counter() - t_all, 2)})
    run_record_finish(run_path, rec, scripts)
    print(json.dumps({"set": args.set, "documents": len(ids), "documents_without_states": len(no_states),
                      "entry": rec["entry"], "counts": counts, "out": rel(out_dir),
                      "run": {"path": rel(run_path), "sha256": sha256(run_path)},
                      "frozen_files_different": rec["frozen_files"]["different"]}, indent=1))
    return 0


# ------------------------------------------------------------------ run records (GJ.2)
def run_record_start(path: Path, what: str, scripts: list[Path]) -> dict:
    """The run record holds the SHA-256 of the scripts and of the criteria file before the first value."""
    rec = {"schema": "parlpdfech-gj-run/1", "what": what, "status": "STARTED (no value yet)", "process_status": STATUS,
           "actor": ACTOR, "gate": "GJ (OPEN)", "started": cal.clock(),
           "scripts": {rel(p): sha256(p) for p in scripts},
           "criteria": {"path": rel(cal.CRITERIA), "sha256": sha256(cal.CRITERIA), "expected": cal.CRITERIA_SHA}}
    if rec["criteria"]["sha256"] != cal.CRITERIA_SHA:
        raise PipelineRefusal("the criteria file has another SHA-256 than the value of the protocol")
    write_json(path, rec)
    rec["script_sha256_recorded"] = rec["started"]
    return rec


def run_record_finish(path: Path, rec: dict, scripts: list[Path]) -> dict:
    now = {rel(p): sha256(p) for p in scripts}
    if now != rec["scripts"]:
        rec["status"] = "STOPPED: a script changed during the run"
        write_json(path, rec)
        raise PipelineRefusal("a script changed during the run")
    rec["finished"] = cal.clock()
    rec["status"] = "DONE"
    rec["frozen_files"] = cal.frozen_files()
    write_json(path, rec)
    return rec


if __name__ == "__main__":
    print("library of gate GJ: use src/m10_cascade.py --mode cascade or src/m10_fullrun.py", file=sys.stderr)
    sys.exit(2)
