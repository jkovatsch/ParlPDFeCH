#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the Apertus states provider of a new document (the worker side).

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude
Opus 5.5), 15./16.10.2026, for the main agent of session ad54858c.

Task
  The worker calls this file in its own process. This file never imports torch or MLX. It
    - reads the settings of the Apertus step from the environment (settings),
    - starts worker/apertus_states.py as a subprocess for one block file, with a time limit (run_states),
    - accepts a states file that was made before for exactly this block file (stored_states; a test aid that
      needs no model),
    - reads a states file for the heads (load_states; also a file with fewer layers than 7, for example the
      layer 20 only of a remote backend),
    - copies the 3 head files into the scratch root and checks their SHA-256 (copy_heads).
  The heads, the combined reader, the writer and the validator are NOT in this file (worker/values_apertus.py and
  the m12 converter files).

Kinds of the provider (the kinds of worker/states_provider.py)
  local   apertus_states.py runs Apertus-v1.5-8B on a GPU of this computer, or on a GPU of another computer
          through a backend of a file apertus_backend_<name>.py (for example 'remote').
  stored  PARLPDFECH_APERTUS_STATES names one npz file. It is accepted only if its template, its model fingerprint,
          its suffix ids and the SHA-256 of each prompt text are those of THIS block file.

Environment (tools/convert.sh sets it from data/apertus/setup.json)
  PARLPDFECH_APERTUS             off (default) | local | stored
  PARLPDFECH_APERTUS_PYTHON      the Python of the subprocess (default: the Python of the worker)
  PARLPDFECH_APERTUS_MODEL_DIR   the text branch folder (local backends)
  PARLPDFECH_APERTUS_BACKEND     auto | mlx | cuda | mps | cpu (or a registered backend)
  PARLPDFECH_APERTUS_TIMEOUT     seconds for the subprocess (default 1500)
  PARLPDFECH_APERTUS_DEADLINE    optional: the end of the time for the read-out (seconds since 1970, from the start
                                 of the job: tools/convert.sh). The subprocess then gets at most the time up to it,
                                 so that the worker writes the record of the rules before the time limit of the job
  PARLPDFECH_APERTUS_HEADS_DIR   the folder with the 3 head files; PARLPDFECH_APERTUS_HEADS_SOURCE hf | local
  PARLPDFECH_APERTUS_STATES      kind stored: the npz file
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "parlpdfech-apertus-provider/0.1.0"
WORKER_DIR = Path(__file__).resolve().parent
STATES_SCRIPT = WORKER_DIR / "apertus_states.py"
WANT_FP = "apertus-v1.5-8b-text-bf16:c10cd28db5bd3adf6043a5047a1435dedc5c3e55c45d5abc2ca82baf2a7786c3"
TEMPLATE_SHA256 = "54abf49ab788b2779b7bd00d8ebfb99abb3daf0fbe076e274fec30851dca81f6"
MODES = ("off", "local", "stored")
DEFAULT_TIMEOUT = 1500
KILL_GRACE = 5.0
MIN_LIMIT = 60.0              # a read-out with less time left is not started (the record of the rules is written)
REMOTE_MARGIN = 30.0          # the client of a remote backend ends this many seconds before the limit of the subprocess
REMOTE_DEFAULT = 1560.0       # DEFAULT_READOUT_TIMEOUT of worker/apertus_backend_remote.py
# The 3 head files of the fixed run of 13.10.2026 (daten/gj_values/heads2/ of the project) and their SHA-256.
HEADS_FILES = {
    "heads2.npz": "535444329391fbe1c1fe4847bb9a97f9f227424d311342285a45eaa780428c2f",
    "entry.json": "49f554ecf366506eddf32953521aa10fa8dd9a7d2fbf6c087819f494d8d7e56a",
    "calibration_dev_combined.json": "17a98be027a5769a68198f97358d52ef5cbe3bca1be4783eb6714cc3b751cb89",
}
HEADS_REL = "daten/gj_values/heads2"          # the place of the head files below the SCRATCH root
# Plain words for the reasons of apertus_states.py (exit key of its record) and of this file.
REASONS = {
    "prefix_too_long": "the document is longer than 32,768 tokens (no cut, no states)",
    "token_problems": "the token check of the prompts failed",
    "template_differs": "the prompt template is not the template of the heads",
    "block_file_bad": "the block file is not in the form of the converter",
    "model_absent": "no model folder (make setup-apertus)",
    "fingerprint_differs": "the model folder is not the model of the heads (make setup-apertus)",
    "no_gpu": "no GPU on this computer",
    "backend_absent": "the asked backend is not available",
    "memory_too_small": "this computer or its GPU has too little memory for the model (a Mac with 32 GB or an "
                        "NVIDIA GPU with 24 GB is needed)",
    "memory_low": "not enough free memory for the model",
    "not_finite": "a state value is not finite",
    "timeout": "the read-out took longer than the time limit",
    "no_record": "the read-out ended with no record",
    "states_unreadable": "the states file cannot be read for the heads",
    "stored_states_differ": "the stored states file is not for this block file",
    "heads_absent": "the head files are absent (make setup-apertus)",
    "heads_differ": "a head file has another SHA-256",
    "error": "the read-out stopped with an error",
    "record_error": "the record with the Apertus values stopped with an error (the record of the rules was written)",
    # the backend remote (worker/apertus_backend_remote.py; the read-out service of a GPU computer, APERTUS_URL)
    "remote_url_absent": "APERTUS_URL is not set",
    "remote_url_bad": "APERTUS_URL is not a right address of the read-out service",
    "remote_plain_http": "APERTUS_URL is plain http to another computer (use an ssh tunnel or https)",
    "remote_token_bad": "APERTUS_TOKEN has a character that is not visible ASCII",
    "remote_unreachable": "the read-out service of APERTUS_URL does not answer",
    "remote_timeout": "the read-out service gave no answer in time",
    "remote_unauthorized": "the read-out service refused the token (APERTUS_TOKEN)",
    "remote_forbidden": "the read-out service refused the request",
    "remote_busy": "the read-out service is busy with another document",
    "remote_ending": "the read-out service is ending",
    "remote_time_limit": "the read-out took longer than the time limit of the service",
    "remote_too_large": "the prompt texts are larger than the limit of the service",
    "remote_redirect": "the read-out service answered with a redirect (not followed)",
    "remote_not_service": "APERTUS_URL does not name the read-out service",
    "remote_protocol": "the read-out service speaks another protocol",
    "remote_fingerprint_differs": "the read-out service has another model than the model of the heads",
    "remote_bad_answer": "the answer of the read-out service failed a check",
    "remote_error": "the read-out service answered with an error",
}


class Unavailable(Exception):
    """The Apertus step cannot run for this document. .reason is a key of REASONS (or of a remote backend)."""

    def __init__(self, reason: str, message: str | None = None):
        super().__init__(message or REASONS.get(reason, reason))
        self.reason = reason


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def settings(env=None) -> dict:
    env = os.environ if env is None else env
    mode = env.get("PARLPDFECH_APERTUS", "off") or "off"
    if mode not in MODES:
        raise ValueError(f"PARLPDFECH_APERTUS={mode!r}: not one of {MODES}")
    try:
        timeout = float(env.get("PARLPDFECH_APERTUS_TIMEOUT") or DEFAULT_TIMEOUT)
    except ValueError:
        timeout = float(DEFAULT_TIMEOUT)
    try:
        deadline = float(env.get("PARLPDFECH_APERTUS_DEADLINE") or 0) or None
    except ValueError:
        deadline = None
    return {"mode": mode, "python": env.get("PARLPDFECH_APERTUS_PYTHON") or sys.executable, "deadline": deadline,
            "model_dir": env.get("PARLPDFECH_APERTUS_MODEL_DIR") or None,
            "backend": env.get("PARLPDFECH_APERTUS_BACKEND") or "auto", "timeout": timeout,
            "heads_dir": env.get("PARLPDFECH_APERTUS_HEADS_DIR") or None,
            "heads_source": env.get("PARLPDFECH_APERTUS_HEADS_SOURCE") or "local",
            "states": env.get("PARLPDFECH_APERTUS_STATES") or None}


def mode(env=None) -> str:
    return settings(env)["mode"]


def child_env(env=None) -> dict:
    """The environment of the subprocess: a copy of the worker environment (a remote backend reads its URL and its
    token there; this file never reads a token), plus the rules of the local read-out."""
    e = dict(os.environ if env is None else env)
    e.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
             TOKENIZERS_PARALLELISM="false", PYTORCH_MPS_HIGH_WATERMARK_RATIO="1.0",
             PYTORCH_MPS_LOW_WATERMARK_RATIO="0.9", PYTHONUNBUFFERED="1")
    e.pop("PYTORCH_ENABLE_MPS_FALLBACK", None)
    return e


def expected_suffix_ids(block_doc: dict) -> list[str]:
    return ["Q0", "Q1"] + [f"Q2.{b['block']}" for b in block_doc["blocks"]]


# ---------------------------------------------------------------------------------------------- states files

def load_states(npz: Path, doc_id: str | None = None):
    """The states of one document for the heads (an object of the class States of m11_value_heads2_data).
    A file with the 7 layers of the fixed run: m11_value_heads2_data.read_states (no change). A file with fewer
    layers (for example the layer 20 only of a remote backend): the same checks, and the heads read layer 20; a
    question for another layer stops with ValueError."""
    import numpy as np  # noqa: PLC0415
    import m11_value_heads2_data as hd  # noqa: PLC0415  (a converter module of the scratch root)
    with np.load(Path(npz), allow_pickle=False) as z:
        layers = [int(k) for k in z["layers"]]
    if layers == list(hd.LAYERS):
        return hd.read_states(npz, doc_id)

    class LayerStates(hd.States):
        def __init__(self, d, suffix_ids, lay, states, tsha):  # noqa: PLR0913
            self.doc_id, self.suffix_ids = str(d), [str(s) for s in suffix_ids]
            self.layers, self.states, self.template_sha256 = [int(k) for k in lay], states, tsha
            if self.suffix_ids[:2] != ["Q0", "Q1"] or any(not s.startswith("Q2.B") for s in self.suffix_ids[2:]):
                raise hd.OtherSuffixIds(f"{self.doc_id}: the suffix ids are not Q0, Q1 and then Q2.B<n>")
            if 20 not in self.layers:
                raise ValueError(f"{self.doc_id}: the states file has no layer 20")
            if states.dtype != np.float16 or states.shape != (len(self.suffix_ids), len(self.layers), hd.HIDDEN):
                raise ValueError(f"{self.doc_id}: the states do not have the form [suffixes, layers, 4096] in float16")

    with np.load(Path(npz), allow_pickle=False) as z:
        d = str(z["doc_id"])
        tsha = str(z["template_sha256"]) if "template_sha256" in z.files else None
        st = LayerStates(d, z["suffix_ids"], z["layers"], z["states"], tsha)
    if doc_id is not None and d != str(doc_id):
        raise ValueError(f"{doc_id}: the states file has the doc id {d}")
    if tsha != hd.TEMPLATE_SHA256:
        raise ValueError(f"{d}: the states file has another template SHA-256")
    return st


def check_states_file(npz: Path, block_doc: dict, item: dict | None = None) -> list[str]:
    """The problems of a states file against one block file (empty list: the file belongs to the block file).
    item: the prompt item of m11_prompts_values (with it, the SHA-256 of each prompt text is compared too)."""
    import numpy as np  # noqa: PLC0415
    probs = []
    with np.load(Path(npz), allow_pickle=False) as z:
        keys = set(z.files)
        get = lambda k: str(z[k]) if k in keys else None  # noqa: E731
        if get("template_sha256") != TEMPLATE_SHA256:
            probs.append("template")
        if get("model_fingerprint") != WANT_FP:
            probs.append("model_fingerprint")
        if [str(s) for s in z["suffix_ids"]] != expected_suffix_ids(block_doc):
            probs.append("suffix_ids")
        if item is not None:
            if get("prefix_text_sha256") != sha256_text(item["prefix"]):
                probs.append("prefix_text")
            if "suffix_text_sha256" not in keys or [str(s) for s in z["suffix_text_sha256"]] != \
                    [sha256_text(s["text"]) for s in item["suffixes"]]:
                probs.append("suffix_text")
        if "states" not in keys or z["states"].dtype != np.float16 or not np.isfinite(z["states"]).all():
            probs.append("states")
        if "layers" not in keys or 20 not in [int(k) for k in z["layers"]]:
            probs.append("layer_20")
    return probs


# ---------------------------------------------------------------------------------------------- the 2 kinds

def run_states(root: Path, block_file: Path, work_dir: Path, s: dict | None = None, log=None) -> dict:
    """Kind local: apertus_states.py run in a subprocess for one block file. Result:
      {"state": "done", "kind": "local", "npz", "record", "backend", "seconds"} or
      {"state": "failed", "kind": "local", "reason", "message", "record", "seconds"}.
    A BaseException of the worker (for example SIGTERM of the server) stops the subprocess (TERM, then KILL after
    5 s) and goes on. The standard output of the subprocess goes to <work_dir>/states.log (numbers only)."""
    s = settings() if s is None else s
    root, block_file, work_dir = Path(root).resolve(), Path(block_file).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    npz, rec_p, log_p = work_dir / "states.npz", work_dir / "states_run.json", work_dir / "states.log"
    for p in (npz, rec_p):
        if p.exists():
            p.unlink()
    cmd = [s["python"], "-I", "-B", str(STATES_SCRIPT), "run", "--root", str(root), "--block-file", str(block_file),
           "--out", str(npz), "--record", str(rec_p), "--backend", s["backend"]]
    if s.get("model_dir"):
        cmd += ["--model-dir", str(s["model_dir"])]
    t0 = time.time()
    # the time limit of the subprocess: PARLPDFECH_APERTUS_TIMEOUT, and at most the time up to the deadline of the job
    limit = float(s["timeout"])
    if s.get("deadline"):
        limit = min(limit, float(s["deadline"]) - t0)
    if limit < MIN_LIMIT:
        msg = f"the job has less than {MIN_LIMIT:.0f} s left for the read-out (time limit of the job)"
        if log:
            log(f"apertus: not run (timeout): {msg}")
        return {"state": "failed", "kind": "local", "reason": "timeout", "message": msg, "record": None,
                "seconds": 0.0, "exit_code": None}
    env = child_env()
    # a remote backend: its client must end before this limit (else the service stays busy with no client)
    cap = max(MIN_LIMIT / 2, limit - REMOTE_MARGIN)
    try:
        cur = float(env.get("APERTUS_REMOTE_TIMEOUT") or REMOTE_DEFAULT)
    except ValueError:
        cur = REMOTE_DEFAULT
    if cap < cur:
        env["APERTUS_REMOTE_TIMEOUT"] = str(int(cap))
    reason = None
    with open(log_p, "wb") as out:
        proc = subprocess.Popen(cmd, cwd=str(root), stdin=subprocess.DEVNULL, stdout=out, stderr=None, env=env)
        try:
            proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            reason = "timeout"
            stop(proc)
        except BaseException:
            stop(proc)
            raise
    seconds = round(time.time() - t0, 2)
    rec = None
    if rec_p.is_file():
        try:
            rec = json.loads(rec_p.read_text(encoding="utf-8"))
        except ValueError:
            rec = None
    if reason is None:
        reason = (rec or {}).get("exit") or "no_record"
    if reason != "ok":
        msg = (rec or {}).get("message") or REASONS.get(reason, reason)
        if log:
            log(f"apertus: not run ({reason}): {msg}")
        return {"state": "failed", "kind": "local", "reason": reason, "message": msg, "record": rec,
                "seconds": seconds, "exit_code": proc.returncode}
    try:
        block_doc = json.loads(Path(block_file).read_bytes())
        probs = check_states_file(npz, block_doc)
        load_states(npz, None)
    except Exception as e:  # noqa: BLE001
        probs = [f"{type(e).__name__}: {str(e)[:120]}"]
    if probs:
        return {"state": "failed", "kind": "local", "reason": "states_unreadable", "message": "; ".join(probs),
                "record": rec, "seconds": seconds}
    return {"state": "done", "kind": "local", "npz": npz, "record": rec, "backend": rec.get("backend"),
            "seconds": seconds}


def stop(proc: subprocess.Popen) -> None:
    """TERM to the subprocess, KILL after KILL_GRACE seconds."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=KILL_GRACE)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def stored_states(block_file: Path, npz: Path, work_dir: Path) -> dict:
    """Kind stored: accept the npz file only for exactly this block file (a test aid; no model runs). The file is
    copied to <work_dir>/states.npz. Needs the converter module m11_prompts_values (the scratch root)."""
    import numpy as np  # noqa: PLC0415
    import m11_prompts_values as pv  # noqa: PLC0415
    block_doc = json.loads(Path(block_file).read_bytes())
    item = pv.item(block_doc, "all")
    if not Path(npz).is_file():
        return {"state": "failed", "kind": "stored", "reason": "stored_states_differ", "message": "no states file"}
    probs = check_states_file(npz, block_doc, item)
    if probs:
        return {"state": "failed", "kind": "stored", "reason": "stored_states_differ",
                "message": "differs: " + ", ".join(probs)}
    work_dir.mkdir(parents=True, exist_ok=True)
    dest = work_dir / "states.npz"
    shutil.copyfile(npz, dest)
    with np.load(dest, allow_pickle=False) as z:
        facts = {k: str(z[k]) for k in ("version", "dtype", "attn", "sdpa", "model_fingerprint") if k in z.files}
    rec = {"backend": "stored", "exit": "ok", "stored_file_sha256": sha256_file(dest), "stored_npz": facts,
           "n_passes": len(item["suffixes"])}
    return {"state": "done", "kind": "stored", "npz": dest, "record": rec, "backend": "stored", "seconds": 0.0}


# ---------------------------------------------------------------------------------------------- heads files

def copy_heads(src_dir: Path | str | None, root: Path) -> dict:
    """Copy the 3 head files to <root>/daten/gj_values/heads2/ and check each SHA-256 (Unavailable on a problem)."""
    if not src_dir or not Path(src_dir).is_dir():
        raise Unavailable("heads_absent")
    dest = Path(root) / HEADS_REL
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, want in HEADS_FILES.items():
        src = Path(src_dir) / name
        if not src.is_file():
            raise Unavailable("heads_absent", f"{name} is absent in the heads folder (make setup-apertus)")
        shutil.copyfile(src, dest / name)
        got = sha256_file(dest / name)
        if got != want:
            raise Unavailable("heads_differ", f"{name} has the SHA-256 {got[:12]}..., not {want[:12]}...")
        out[name] = got
    return out
