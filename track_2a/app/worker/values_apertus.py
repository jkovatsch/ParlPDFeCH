#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the record of the Apertus mode (values of the rules and of the Apertus heads).

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.
Actor: workflow sub-agent (Claude Opus 5.5), builder B of the Apertus build of 15./16.10.2026, for the main agent.

Task
  The Apertus provider (worker/apertus_provider.py: a local run on MLX, CUDA, MPS or CPU, a remote GPU, or a stored
  states file) gives the layer-20 states of one block file. This file makes the record from them. It is the
  Apertus form of worker/values_record.py, and it uses these converter files of the code layout (import from the
  scratch root):
    m12_apertus_values   heads output (final head of heads2.npz), combined reader of the fixed run, place of the
                         Apertus type, near marks, calibration file of the Apertus mode
    m12_writer           write_record and rdf_step (a new version of m11_writer; the frozen file does not change)
    m12_validate         validate_record (checks C1 to C22; C22 reads the heads output of the record again)
  The heads, the combined reader, the writer and the validator run on this computer, also when the states come
  from a remote GPU. No file of this module holds document text: heads.json (the heads output) stays in the
  scratch root.

Functions (the order of one conversion)
  prepare(root, heads_dir)                 the 3 heads files into root/daten/gj_values/heads2 (SHA-256 pinned),
                                           and the merged calibration file (root/daten/gj_values/apertus/...)
  heads_output(root, block_file, rule_file, states)   the heads on the states; writes root/work/apertus/heads.json
  combined(root, block_file, rule_file, ho, backend)  the values of the combined reader with place and near marks
  write(root, folder, ..., res, facts)     the record files and the RDF files (m12_writer)
  validate(root, folder, export)           the checks (m12_validate); stops if the calibration file is not the
                                           calibration file of the Apertus mode
  record_facts(...), facts_for_convert(...)  the facts of the manifest key apertus_values and of convert.json
  state_of(provider_result)                local, remote, stored or failed (key apertus_values.state)

Use in the worker (stage 4 to 6 of fresh.py or serve_convert.py, worker mode auto, values state pdf; a sketch):
  s = apertus_provider.settings()
  prep = values_apertus.prepare(root, Path(s["heads_dir"]), source=s["heads_source"])
  r = apertus_provider.run_states(root, docs_p, root / "work/apertus", s)        # or stored_states(...)
  if r["state"] == "done":
      ho = values_apertus.heads_output(root, docs_p, rules_p, r["npz"])
      res = values_apertus.combined(root, docs_p, rules_p, ho, r["backend"])
      facts = values_apertus.record_facts(r["record"], prep, ho, res, r["backend"])
      man, rdf = values_apertus.write(root, folder, docs_p, rules_p, dec_p, export, base, block_cal, res, facts,
                                      calibration_base=...)
      validation = values_apertus.validate(root, folder, export)          # check ids CHECK_IDS, rule VALID_RULE
      convert["apertus_values"] = values_apertus.facts_for_convert(values_apertus.state_of(r), None, r["record"],
                                                                   ho, res, prep, r["backend"])
  else: the rules path of worker/values_record.py, and facts_for_convert("failed", r["reason"], ...)

The hooks of the worker (integration step of 16.10.2026; fresh.py and serve_convert.py call only these functions)
  active(worker_mode, values_state)        True only if PARLPDFECH_APERTUS is local or stored, the worker mode is
                                           auto and the values state is pdf. Else the rules path runs unchanged.
  read_out(root, block_file, rule_file)    stage 4: prepare, the provider (local subprocess, remote backend or
                                           stored states) and heads_output. Each problem (also an exception of
                                           this file or of a converter file) gives the state failed with a reason
                                           (no exception): the record is then the record of the rules
                                           (worker/values_record.py).
  record_and_check(...)                    stage 5 and the checks: record_step, then validate. An exception of
                                           either gives the state failed with the reason record_error (the type of
                                           the exception only), the record folder is emptied, and the caller writes
                                           the record of the rules. (fix step of 16.10.2026)
  record_step(...)                         stage 5: combined, record_facts and write (m12_writer)
  convert_facts(ro, res)                   the key apertus_values of convert.json. For a reason of a remote backend
                                           its message is the fixed text of apertus_provider.REASONS (no port and
                                           no text of the service in the record folder)
"""

from __future__ import annotations

import gc
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

VERSION = "parlpdfech-values-apertus/0.1.0"
HEADS_REL = "daten/gj_values/heads2"
PRODUCT_CAL_REL = "daten/gj_values/round4/calibration_dev_all.json"
MERGED_REL = "daten/gj_values/apertus/calibration_values_apertus.json"
WORK_REL = "work/apertus"
HEADS_FILES = {"heads2.npz": "535444329391fbe1c1fe4847bb9a97f9f227424d311342285a45eaa780428c2f",
               "entry.json": "49f554ecf366506eddf32953521aa10fa8dd9a7d2fbf6c087819f494d8d7e56a",
               "calibration_dev_combined.json": "17a98be027a5769a68198f97358d52ef5cbe3bca1be4783eb6714cc3b751cb89"}
PRODUCT_CAL_SHA256 = "e48e7a8d8efdd1e10b68071df85275dc0c5b69e004bb8051b2aecd2a1d4229d7"
# the SHA-256 of the merged calibration file (m12_apertus_values.write_merged of the 2 pinned inputs; 16.10.2026)
MERGED_SHA256 = "e7c4769626d76195ed777b1501fd2ce03b419aa896a182e183825d5ae47f192f"
KIND = "from_rule_chain"
MODEL = "swiss-ai/Apertus-v1.5-8B, text branch, bf16"
MODEL_FINGERPRINT = "apertus-v1.5-8b-text-bf16:c10cd28db5bd3adf6043a5047a1435dedc5c3e55c45d5abc2ca82baf2a7786c3"
CHECK_IDS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme",
             "C7_C8_labels", "C9_e19", "C11_wording_at_span", "C12_one_label_for_each_pdf_value",
             "C13_no_export_value_in_the_record", "C14_cross_check", "C15_slot_states",
             "C16_probability_and_calibration", "C17_recorded_gaps", "C18_minted_iris", "C19_value_forms",
             "C20_value_follows_from_wording", "C21_floor",
             "C22_values_from_the_readers")
VALID_RULE = ("the writer check of src/m12_writer.py and each check of src/m12_validate.py that ran (C1 to C9, "
              "C11 to C22) passed")
EQUALITY_NOTE = ("The heads were fit on torch CUDA bf16 states (one H100). Other kernels give other bf16 noise: a "
                 "value near a threshold can differ from the fixed run (mark near).")
TESTED_ON = ("macOS arm64 (Apple M4, 32 GB): MLX, torch MPS and torch CPU, 15./16.10.2026. Linux, Windows and "
             "NVIDIA CUDA: not tested.")


class Unavailable(Exception):
    """The Apertus mode cannot run for this document (a reason code; the conversion gives the rules record)."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _av():
    import m12_apertus_values as av  # noqa: PLC0415  (from the scratch root)
    return av


def _check_place(mod, root: Path, strict_root: bool) -> None:
    if strict_root and Path(mod.__file__).resolve().parents[1] != Path(root).resolve():
        raise RuntimeError(f"{mod.__name__} is not the file of the scratch root")


# ------------------------------------------------------------------ heads files and calibration
def prepare(root: Path, heads_dir: Path, source: str = "local", strict_root: bool = True) -> dict:
    """Copies the 3 heads files of heads_dir to root/HEADS_REL (each SHA-256 must be the pinned value), then writes
    the merged calibration file. source: 'hf:<repo>@<revision>' or 'local' (a fact for the record)."""
    root, heads_dir = Path(root), Path(heads_dir)
    av = _av()
    _check_place(av, root, strict_root)
    dest = root / HEADS_REL
    dest.mkdir(parents=True, exist_ok=True)
    got = {}
    for name, want in HEADS_FILES.items():
        src = heads_dir / name
        if not src.is_file():
            raise Unavailable("heads_absent", f"the heads folder has no file {name}")
        digest = sha256_file(src)
        if digest != want:
            raise Unavailable("heads_differ", f"{name} has another SHA-256 than the pinned file")
        if not (dest / name).is_file() or sha256_file(dest / name) != want:
            shutil.copyfile(src, dest / name)
        got[name] = digest
    product = root / PRODUCT_CAL_REL
    if not product.is_file() or sha256_file(product) != PRODUCT_CAL_SHA256:
        raise Unavailable("calibration_differs", f"{PRODUCT_CAL_REL} is absent or is not the product file")
    merged, merged_sha = av.write_merged(root, product, dest / "calibration_dev_combined.json")
    if MERGED_SHA256 is not None and merged_sha != MERGED_SHA256:
        raise Unavailable("calibration_differs", "the merged calibration file has another SHA-256 than the pinned file")
    return {"heads_sha256": got, "merged_calibration": {"path": MERGED_REL, "sha256": merged_sha},
            "heads_source": source}


# ------------------------------------------------------------------ heads, combined reader
def _doc(block_file: Path, rule_file: Path | None):
    import m11_values_base as vb  # noqa: PLC0415  (from the scratch root)
    vb.load_rule_modules()
    return vb.load_from_block_file(block_file, rule_file)


def heads_output(root: Path, block_file: Path, rule_file: Path | None, states) -> dict:
    """The heads output of the document (final head). states: the path of a states file (form of
    daten/gj/states/values_dev/states/<id>.npz, also with the layer 20 only; read by apertus_provider.load_states,
    or by m11_value_heads2_data.read_states if that file is absent; template SHA-256 checked), a states object of
    these functions, or a dict {"q0": [4096], "q1": [4096], "q2": [blocks, 4096], "block_ids": [...]} of layer-20
    states. Writes root/WORK_REL/heads.json and returns the output."""
    import m11_value_heads2 as h2  # noqa: PLC0415  (from the scratch root)
    import m11_value_heads2_data as hd  # noqa: PLC0415
    root = Path(root)
    av = _av()
    doc = _doc(block_file, rule_file)
    heads = h2.Heads2.load(root / HEADS_REL / "heads2.npz")
    if heads.models <= h2.FINAL:
        raise Unavailable("heads_differ", "the heads file has no final head")
    if isinstance(states, dict):
        ho = av.heads_output(doc, heads, states["q0"], states["q1"], states["q2"], list(states["block_ids"]))
    elif isinstance(states, (str, Path)):
        try:
            import apertus_provider as prov  # noqa: PLC0415  (worker folder; reads a file with fewer layers too)
            st = prov.load_states(Path(states), None)
        except ImportError:
            st = hd.read_states(Path(states), None)
        ho = av.heads_output_from_states(doc, st, heads)
    else:
        ho = av.heads_output_from_states(doc, states, heads)
    p = root / WORK_REL / "heads.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ho, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ho


def combined(root: Path, block_file: Path, rule_file: Path | None, ho: dict, backend: str) -> dict:
    """The values of the combined reader (strict False, final head, entry.json, weak tiers of the product file: the
    rules of cmd_apply of the fixed run), with the place of an Apertus type and the near marks of the backend."""
    import m11_values_cascade as cvc  # noqa: PLC0415  (from the scratch root)
    import m11_values_combined as cmb  # noqa: PLC0415
    root = Path(root)
    av = _av()
    doc = _doc(block_file, rule_file)
    entry = json.loads((root / HEADS_REL / "entry.json").read_text(encoding="utf-8"))
    weak = cmb.weak_tiers(root / PRODUCT_CAL_REL)
    rule = cvc.read_document(doc, strict=False)
    return av.combined_values(doc, ho, entry, weak, rule, strict=False, backend=backend)


# ------------------------------------------------------------------ facts
def record_facts(run_rec: dict | None, prep: dict | None, ho: dict | None, res: dict | None,
                 backend: str | None) -> dict:
    """The manifest key apertus_values (no path of the user, no wording of the PDF)."""
    run_rec = run_rec or {}
    prep = prep or {}
    out = {"version": VERSION, "backend": backend, "device": run_rec.get("device"), "dtype": run_rec.get("dtype", "bfloat16"),
           "model": MODEL, "model_fingerprint": run_rec.get("model_fingerprint", MODEL_FINGERPRINT),
           "versions": run_rec.get("versions"),
           "heads": {"heads2_npz_sha256": (prep.get("heads_sha256") or {}).get("heads2.npz"),
                     "entry_sha256": (prep.get("heads_sha256") or {}).get("entry.json"),
                     "calibration_combined_sha256": (prep.get("heads_sha256") or {}).get("calibration_dev_combined.json"),
                     "merged_calibration_sha256": (prep.get("merged_calibration") or {}).get("sha256"),
                     "model": "final (index 5)", "layer": 20, "source": prep.get("heads_source")},
           "equality_note": EQUALITY_NOTE, "tested_on": TESTED_ON}
    if ho is not None and res is not None:
        out |= _av().summary_facts(ho, res)
    return out


def state_of(provider_result: dict | None) -> str:
    """The state of the key apertus_values of convert.json for a result of apertus_provider (run_states or
    stored_states): local, remote (a backend name that starts with remote), stored or failed."""
    r = provider_result or {}
    if r.get("state") != "done":
        return "failed"
    if r.get("kind") == "stored":
        return "stored"
    return "remote" if str(r.get("backend") or "").startswith("remote") else "local"


def facts_for_convert(state: str, reason: str | None, run_rec: dict | None, ho: dict | None, res: dict | None,
                      prep: dict | None, backend: str | None, seconds: dict | None = None) -> dict:
    """The key apertus_values of convert.json. state: local, remote, stored, failed or off."""
    out = {"state": state, "reason": reason} | record_facts(run_rec, prep, ho, res, backend)
    rr = run_rec or {}
    out["seconds"] = dict(seconds or {}) | {k: rr.get(k) for k in ("load_seconds", "prefill_seconds", "suffix_seconds",
                                                                   "seconds") if rr.get(k) is not None}
    out["passes"] = rr.get("n_passes")
    out["tokens"] = {"prefix": rr.get("n_prefix_tokens"), "suffix": rr.get("n_suffix_tokens")}
    out["peak_bytes"], out["peak_kind"] = rr.get("peak_bytes"), rr.get("peak_kind")
    if rr.get("host"):
        out["remote_host"] = rr.get("host")                 # the host of the URL only (no path, no token)
    return out


# ------------------------------------------------------------------ record and checks
def write(root: Path, folder: Path, block_file: Path, rule_file: Path | None, decisions: Path, export: dict | None,
          base: str | None, block_calibrations: Path, res: dict, facts: dict, calibration_base: str | None = None,
          strict_root: bool = True) -> tuple[dict, dict]:
    """write_record and rdf_step of m12_writer with the values of combined() and the merged calibration file."""
    import m12_writer as w12  # noqa: PLC0415  (from the scratch root)
    root = Path(root)
    _check_place(w12, root, strict_root)
    calibration = root / MERGED_REL
    if not calibration.is_file():
        raise RuntimeError("the merged calibration file is absent: call prepare first")
    if w12.CALIBRATION_REL != MERGED_REL:
        raise RuntimeError("the calibration file of m12_writer is not the file of the Apertus mode")
    folder.mkdir(parents=True, exist_ok=True)
    apertus = dict(facts, heads_json=root / WORK_REL / "heads.json", entry_json=root / HEADS_REL / "entry.json")
    w12.write_record(block_file, rule_file, decisions, res["fields"], calibration, export, folder, base,
                     block_calibrations=block_calibrations, root=root, calibration_base=calibration_base,
                     kind=KIND, apertus=apertus)
    rdf_result = w12.rdf_step(folder, root=root)
    man = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    return man, rdf_result


def validate(root: Path, folder: Path, export: dict | None, strict_root: bool = True) -> dict:
    """validate_record of m12_validate. It opens the calibration file of the Apertus mode by its own path below the
    root and stops if the result does not say "the product file" (of the Apertus mode)."""
    import m12_validate as v12  # noqa: PLC0415  (from the scratch root)
    root = Path(root)
    _check_place(v12, root, strict_root)
    if v12.CALIBRATION_REL != MERGED_REL:
        raise RuntimeError("the calibration file of m12_validate is not the file of the Apertus mode")
    res = v12.validate_record(folder, root=root, export_record=export, kind=KIND)
    used = res.get("calibration_file") or {}
    want = sha256_file(root / MERGED_REL)
    if used.get("is_product_file") is not True or used.get("sha256") != want:
        raise RuntimeError("the validator did not use the calibration file of the Apertus mode")
    return res


# ------------------------------------------------------------------ hooks of the worker (fresh.py, serve_convert.py)
def _provider():
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.append(here)
    import apertus_provider as prov  # noqa: PLC0415  (worker folder)
    return prov


def active(worker_mode: str, values_state: str) -> bool:
    """True only if PARLPDFECH_APERTUS is local or stored, the worker mode is auto and the values state is pdf.
    With False the worker runs the rules path with no change (worker/values_record.py)."""
    if worker_mode != "auto" or values_state != "pdf":
        return False
    return _provider().mode() != "off"


def free_memory() -> None:
    """Frees the caches of this process before the read-out subprocess loads the model (the Docling models of
    stage 1 stay loaded; only the free cache of torch goes back to the system)."""
    gc.collect()
    torch = sys.modules.get("torch")
    if torch is None:
        return
    try:
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            torch.mps.empty_cache()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:  # noqa: BLE001  (a help only)
        pass


def read_out(root: Path, block_file: Path, rule_file: Path | None, log=None) -> dict:
    """Stage 4 of the Apertus mode for one block file. Returns a dict:
      state     local, remote, stored or failed (key apertus_values.state of convert.json)
      reason    None, or a reason code (apertus_provider.REASONS, or a code of prepare)
      message   None, or a short text of the reason (no document text)
      run       the result of apertus_provider.run_states or stored_states (None if prepare failed)
      prep      the result of prepare (None if it failed)
      ho        the heads output (None if the state is failed)
      backend   the backend name of the run record (for example mlx or remote:cuda), or None
      seconds   {prepare, read_out, heads}
    A problem of the provider, of the heads files or of this code never raises an Exception: the caller then writes
    the record of the rules. (A BaseException, for example the stop signal of the worker, goes on.)"""
    out = {"state": "failed", "reason": None, "message": None, "run": None, "prep": None, "ho": None,
           "backend": None, "seconds": {}}
    try:
        return _read_out(out, root, block_file, rule_file, log)
    except (Exception, SystemExit) as e:  # noqa: BLE001  (each failure gives the record of the rules)
        out.update(state="failed", ho=None, backend=None, reason="error",
                   message=f"the Apertus step stopped with {type(e).__name__}")
        if log:
            log(f"apertus: not run (error): {type(e).__name__}")
        return out


def _read_out(out: dict, root: Path, block_file: Path, rule_file: Path | None, log=None) -> dict:
    prov = _provider()
    root = Path(root)
    s = prov.settings()
    t0 = time.perf_counter()
    try:
        if not s.get("heads_dir"):
            raise Unavailable("heads_absent", "PARLPDFECH_APERTUS_HEADS_DIR is not set (make setup-apertus)")
        out["prep"] = prepare(root, Path(s["heads_dir"]), source=s.get("heads_source") or "local")
    except (Unavailable, prov.Unavailable) as e:
        out.update(reason=e.reason, message=str(e)[:300])
        return out
    out["seconds"]["prepare"] = round(time.perf_counter() - t0, 3)
    work = root / WORK_REL
    t1 = time.perf_counter()
    if s["mode"] == "stored":
        r = prov.stored_states(Path(block_file), Path(s["states"] or root / "no-states-file.npz"), work)
    else:
        free_memory()
        r = prov.run_states(root, Path(block_file), work, s, log=log)
    out["run"] = r
    out["seconds"]["read_out"] = round(time.perf_counter() - t1, 3)
    if r.get("state") != "done":
        out.update(reason=r.get("reason") or "error", message=(r.get("message") or "")[:300] or None)
        return out
    t2 = time.perf_counter()
    try:
        ho = heads_output(root, Path(block_file), rule_file, r["npz"])
    except Unavailable as e:
        out.update(reason=e.reason, message=str(e)[:300])
        return out
    except ValueError as e:              # the states file does not fit the heads (template, layers, suffix ids)
        out.update(reason="states_unreadable", message=f"{type(e).__name__}: {str(e)[:200]}")
        return out
    out["seconds"]["heads"] = round(time.perf_counter() - t2, 3)
    out.update(state=state_of(r), ho=ho, backend=r.get("backend"))
    return out


def record_step(root: Path, folder: Path, block_file: Path, rule_file: Path | None, decisions: Path,
                export: dict | None, base: str | None, block_calibrations: Path, ro: dict,
                calibration_base: str | None = None) -> tuple[dict, dict, dict]:
    """Stage 5 of the Apertus mode (ro: a result of read_out with the state local, remote or stored): the combined
    reader, the facts of the manifest and write (m12_writer). Returns (manifest, key rdf, result of combined)."""
    res = combined(root, block_file, rule_file, ro["ho"], ro["backend"])
    facts = record_facts((ro.get("run") or {}).get("record"), ro.get("prep"), ro["ho"], res, ro["backend"])
    man, rdf_result = write(root, folder, block_file, rule_file, decisions, export, base, block_calibrations, res,
                            facts, calibration_base=calibration_base)
    return man, rdf_result, res


def fail_record(ro: dict, e: BaseException, folder: Path, log=None) -> None:
    """After an exception of record_step or validate: ro gets the state failed (reason record_error, the type of
    the exception only), and the record folder (below the scratch root) is emptied for the record of the rules."""
    ro.update(state="failed", reason="record_error",
              message=f"the record with the Apertus values stopped with {type(e).__name__}; the record has the code "
                      f"rules only")
    if log:
        log(f"apertus: record_error ({type(e).__name__}); the record gets the code rules only")
    folder = Path(folder)
    if folder.is_dir():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)


def record_and_check(root: Path, folder: Path, block_file: Path, rule_file: Path | None, decisions: Path,
                     export: dict | None, base: str | None, block_calibrations: Path, ro: dict,
                     calibration_base: str | None = None, log=None) -> tuple[dict, dict, dict] | None:
    """Stage 5 of the Apertus mode and its checks: record_step, then validate (m12_validate). Returns (key rdf,
    result of combined, result of validate), or None after an exception of either: then ro has the state failed
    with the reason record_error, the record folder is empty, and the caller writes the record of the rules."""
    try:
        _, rdf_result, res = record_step(root, folder, block_file, rule_file, decisions, export, base,
                                         block_calibrations, ro, calibration_base=calibration_base)
        validation = validate(root, folder, export)
    except (Exception, SystemExit) as e:  # noqa: BLE001  (m12_validate stops with SystemExit for a missing input)
        fail_record(ro, e, folder, log)
        return None
    return rdf_result, res, validation


def convert_facts(ro: dict, res: dict | None) -> dict:
    """The key apertus_values of convert.json for a result of read_out (and of record_step)."""
    run = ro.get("run") or {}
    out = facts_for_convert(ro["state"], ro.get("reason"), run.get("record"), ro.get("ho"), res, ro.get("prep"),
                            ro.get("backend"), seconds=ro.get("seconds"))
    msg = ro.get("message")
    if msg and str(ro.get("reason") or "").startswith("remote_"):
        # the record folder names only the host of APERTUS_URL (no port, no text of the service): a fixed text
        msg = _provider().REASONS.get(str(ro["reason"]), str(ro["reason"]))
    if msg:
        out["message"] = msg
    out["kind"] = run.get("kind")
    return out
