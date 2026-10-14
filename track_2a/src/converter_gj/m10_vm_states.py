# SPDX-License-Identifier: Apache-2.0
"""Gate GJ (EXCEPTION), phase 4: the VM extractor of the shared-prefix readouts (plan 3.1, 3.6; chapter 5.2 item 4).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream C,
for the AI agent. No human checked this file. This file does not change an existing file. Status of all outputs:
EXCEPTION (process rule 10, protocol 12.10.2026 18:40), NOT RELEASED.

1 Input: a job folder (interface 5 of the build streams)
  template.json  {template_id, sha256, system_text_source, prefix_format, d1_question, b1_question, options}
  items.jsonl    one line for each document: {doc_id, prefix, suffixes: [{id, text}], n_prefix_chars}
                 prefix = the full chat-template text up to the end of the document part, as the model sees it
                 (with the BOS text "<s>" of the chat template). suffix text = question with lettered options, end
                 of the user turn, assistant prefix "Antwort:".
  manifest.json  optional (src/m10_job.py pack): SHA-256 of template.json and items.jsonl and the model
                 fingerprint of the Mac. If it exists, the SHA-256 values must agree, else the run stops.
  The file reads items.jsonl two times: one time to examine it (keeps byte offsets only), one time for the passes
  (one line at a time). So the guest RAM (6.4 GB) holds the text of one document only.

2 Token ids (the same function for training and for inference: tokenize_item)
  prefix ids = tokenizer(prefix, add_special_tokens=False); suffix ids = tokenizer(suffix text,
  add_special_tokens=False) for each suffix. The model sees prefix ids + suffix ids. The tokenizer must give exactly
  one BOS at the start of the prefix and no BOS in a suffix, else the run stops before the model load.
  Boundary note (measured with the Apertus tokenizer on synthetic text, 12.10.2026): a cut before the "\n\n" that
  separates the document and the question gives other ids than one tokenization of the joined text (the pair
  ".\n\n" is one token); a cut after "\n\n" gave equal ids in 4 of 4 cases. src/m10_prompts.py (version
  m10-prompts-1) starts each suffix with "\n\n", so the ids differ from the joined text at the boundary when the
  last block ends with such a character. Training and inference use the same ids, so the readouts stay consistent.
  Each output file records for the first suffix if prefix ids + suffix ids are equal to the ids of the joined text
  (boundary_equal_first_suffix).
  Letters: the tokens " A" ... " F" (one token each; Apertus: 1349, 1398, 1359, 1407, 1436, 1439). This is the form
  of the R2 options " A" and " B" of src/m05_cls_apertus.py (answer after "Antwort:").

3 Passes (one document)
  a. prefill: the prefix ids in chunks of 2,048 tokens from position 0 into one DynamicCache.
  b. suffix: the suffix ids in one forward pass on top of the cache (positions n_prefix ... n_prefix + n - 1).
  c. readout: the residual state after decoder layer k at the last suffix token, for each k of --layers.
  d. letter_logprobs: log-softmax over the full vocabulary of lm_head(final-norm state at the last suffix token),
     at the 6 letter tokens (zero-shot diagnostic only; not normalized over the options).
  e. crop: the cache goes back to n_prefix tokens (the key and value tensors of each layer are cut to the first
     n_prefix positions; the code examines the length after each crop). So each suffix sees the whole document and
     only its own question; no readout sees another readout.
  --sdpa no-cudnn (default): the cuDNN attention kernel is off, because it builds a new kernel plan for each new
  sequence length (about 1.2 s; see set_sdpa). auto = the torch default (as m07).
  --batch B (default 1 = the plan layout): B suffixes in one forward pass, right padding, the prefix cache repeated
  B times. Real tokens never see the pad tokens (they come later, causal mask). Use B > 1 only after an equality
  smoke (compare against B = 1 with the command compare). B is made smaller for long prefixes: B * n_prefix <=
  --batch-token-budget.

4 Index convention (against src/m07_h_vm_states.py)
  m07: a forward hook on model.model.layers[k - 1] keeps output[0, -1]: the residual stream after decoder layer k,
  before the final norm. This file uses the same hooks. So layer k here is layer k of m07 and the same unit as the
  R2 readout of head H (layer 16).
  output_hidden_states (transformers 5.x, capture_outputs): hidden_states[0] = input embeddings, hidden_states[k] =
  output of decoder layer k for k = 1 ... 31, and hidden_states[32] = last_hidden_state = the state after the final
  norm (tie_last_hidden_states). So hidden_states[k] is equal to the hook value for k < 32 only. For k = 32 the hook
  value (and m07) is the residual stream before the final norm. The check script src/m10_vm_states_test.py
  examines this on a small model. For this reason the file uses hooks, not output_hidden_states.

5 Output folder (interface 6)
  states/<doc_id>.npz: suffix_ids (str), layers (int16), states float16 [n_suffix, n_layers, hidden],
    letter_logprobs float32 [n_suffix, 6], n_prefix_tokens int64, n_suffix_tokens int64 [n_suffix]; also doc_id,
    letters, letter_token_ids, prefix_text_sha256, suffix_text_sha256 [n_suffix], prefix_tokens_sha256,
    suffix_tokens_sha256 [n_suffix], boundary_equal_first_suffix, template_id, template_sha256 (as declared),
    template_json_sha256, model, model_fingerprint, code_sha256, version, dtype, attn, sdpa, batch (used),
    batch_setting, prefill_chunk, made. No document text.
  run_aNN.json: the run record of attempt NN (SHA-256 of inputs and outputs, model path, template SHA-256,
    versions, times, ms for each suffix pass, GPU memory peak, guest RAM peak, free disk, fresh-prefill checks).
  skips.jsonl: documents without an output (too_long, oom, doc_timeout, not_finite, error) with the reason.
  outputs.json: SHA-256 of each output file (written at the end of each attempt; the fetch reads it).
  status.json, drive.json, driver.pid, logs/: the driver (command drive).

6 Rules of the process
  No network: socket connections are refused (the guard of m07). HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE are 1.
  GPU lock /opt/apertus/runs/gpu.lock (flock, the protocol of m07_lora_train.py): taken before torch and the model
  load, released after the last pass. --wait-lock waits.
  Self-timeout: --doc-timeout for each document and --total-timeout for the process. At a timeout a watchdog thread
  writes the run record and a line in skips.jsonl (document timeout) and stops the process (exit code 124 for a
  document, 125 for the total). The flock ends with the process.
  Resume: a document with a valid output file is not done again (same suffix ids, layers, texts, template,
  model fingerprint, code SHA-256, dtype, attention kernel policy (--sdpa) and batch setting; finite float16
  states). A document in skips.jsonl is not done again (--retry-skipped changes this).
  --check-fresh N: for N suffixes (the last suffix of each document first, then a middle suffix) the file computes
  the state again (a) with a fresh cache: prefill of the prefix, then the suffix (expected difference 0: this is the
  crop check and the determinism check) and (b) with the prefill rule of m07 on the joined ids (ids[:-1] in chunks,
  then the last token alone). It reports the largest absolute differences.

7 Commands
  VM:  /opt/apertus/venv/bin/python -I m10_vm_states.py run   --job DIR --out DIR [--wait-lock] [options]
       /opt/apertus/venv/bin/python -I m10_vm_states.py drive --job DIR --out DIR [--wait-lock] [options]
  any: python m10_vm_states.py compare --a DIR --b DIR     (numpy only: largest differences of two output folders)
  Mac check with a small model: python src/m10_vm_states_test.py
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import gc
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

VERSION = "m10-vm-states-1"
VM_MODEL_DIR = "/opt/apertus/models/apertus-v1.5-8b-text-bf16"
VM_GPU_LOCK = "/opt/apertus/runs/gpu.lock"
DEFAULT_LAYERS = (8, 12, 16, 20, 24, 28, 32)
PREFILL_CHUNK = 2048
LETTERS = ("A", "B", "C", "D", "E", "F")
LETTER_FORM = " {}"                       # the R2 option form " A", " B" of m05_cls_apertus
APERTUS_LETTER_IDS = (1349, 1398, 1359, 1407, 1436, 1439)
APERTUS_N_LAYERS = 32
APERTUS_HIDDEN = 4096
MAX_PREFIX_TOKENS = 32768                 # E18 / K13: no cut; a longer document gets no output
DOC_TIMEOUT_S = 900.0
TOTAL_TIMEOUT_S = 8 * 3600.0
BATCH_TOKEN_BUDGET = 65536
RC_DOC_TIMEOUT = 124
RC_TOTAL_TIMEOUT = 125
MAX_ATTEMPTS = 6
TEMPLATE_KEYS = ("template_id", "sha256", "system_text_source", "prefix_format", "d1_question", "b1_question",
                 "options")
ITEM_KEYS = ("doc_id", "prefix", "suffixes", "n_prefix_chars")
RX_DOC = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}$")
RX_SUFFIX = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
SKIP_REASONS_FINAL = ("too_long", "oom", "doc_timeout", "not_finite", "error")
NPZ_KEYS = ("doc_id", "suffix_ids", "layers", "states", "letter_logprobs", "n_prefix_tokens", "n_suffix_tokens",
            "letters", "letter_token_ids", "prefix_text_sha256", "suffix_text_sha256", "prefix_tokens_sha256",
            "suffix_tokens_sha256", "boundary_equal_first_suffix", "template_id", "template_sha256",
            "template_json_sha256", "model", "model_fingerprint", "code_sha256", "version", "dtype", "attn", "sdpa",
            "batch", "batch_setting", "prefill_chunk", "made")


# ---------------------------------------------------------------- helpers

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def sha256_json(x) -> str:
    """Same definition as m05_cls_apertus.sha256_json."""
    return sha256_bytes(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def code_sha() -> str:
    return sha256_file(os.path.abspath(__file__))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


def append_jsonl(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            with contextlib.suppress(ValueError):
                out.append(json.loads(line))
    return out


def model_fingerprint(model_dir: Path) -> str:
    """Same definition as m07_h_vm_states.model_fingerprint and m05_cls_apertus.model_fingerprint."""
    h = hashlib.sha256()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                 "model.safetensors.index.json"):
        p = model_dir / name
        if p.exists():
            h.update(name.encode() + b"\0" + p.read_bytes())
    for p in sorted(model_dir.glob("*.safetensors")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    return "apertus-v1.5-8b-text-bf16:" + h.hexdigest()


def parse_layers(s: str) -> tuple[int, ...]:
    ks = tuple(int(x) for x in str(s).split(",") if x.strip())
    if not ks or len(set(ks)) != len(ks) or any(k < 1 for k in ks) or list(ks) != sorted(ks):
        raise SystemExit(f"--layers must be distinct ascending numbers >= 1: {s!r}")
    return ks


def free_bytes(p: Path) -> int | None:
    with contextlib.suppress(OSError):
        return int(shutil.disk_usage(p).free)
    return None


def network_guard() -> None:
    """Copy of the guard of m07_h_vm_states.py: refuse each socket connection (except Unix sockets)."""
    orig = socket.socket.connect

    def deny(self, addr, *a, **k):
        if self.family == getattr(socket, "AF_UNIX", None):
            return orig(self, addr, *a, **k)
        raise RuntimeError(f"m10_vm_states: network connection refused ({addr})")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = lambda *a, **k: deny(socket.socket(), a[0] if a else None)


@contextlib.contextmanager
def gpu_lock(path: str, wait: bool, rec: dict):
    """Same protocol as m07_h_vm_states.gpu_lock and m07_lora_train.gpu_lock: flock, then one line 'pid N since T'."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a+")
    t0 = time.time()
    try:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError:
            f.seek(0)
            raise SystemExit(f"GPU lock {path} is held by another process: {f.read().strip()!r}")
        rec["lock_wait_seconds"] = round(time.time() - t0, 1)
        rec["lock_taken"] = now()
        f.seek(0)
        f.truncate()
        f.write(f"pid {os.getpid()} since {now()} (m10_vm_states)\n")
        f.flush()
        yield
    finally:
        with contextlib.suppress(Exception):
            f.seek(0)
            f.truncate()
            f.flush()
        with contextlib.suppress(Exception):
            fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        rec["lock_released"] = now()


# ---------------------------------------------------------------- guest memory (copy of m07_lora_train)

def meminfo() -> dict:
    out = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":", 1)
        out[k] = int(v.split()[0]) * 1024
    return out


def proc_status(key: str) -> int | None:
    with contextlib.suppress(OSError):
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith(key + ":"):
                return int(line.split()[1]) * 1024
    return None


class MemSampler(threading.Thread):
    """Guest memory use (MemTotal - MemAvailable) every 0.2 s: peak and lowest available value (Linux only)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_ev = threading.Event()
        self.peak_used = 0
        self.min_avail = None
        self.total = None

    def run(self):
        while not self.stop_ev.is_set():
            with contextlib.suppress(Exception):
                m = meminfo()
                self.total = m["MemTotal"]
                used = m["MemTotal"] - m["MemAvailable"]
                self.peak_used = max(self.peak_used, used)
                self.min_avail = m["MemAvailable"] if self.min_avail is None else min(self.min_avail, m["MemAvailable"])
            self.stop_ev.wait(0.2)

    def result(self) -> dict:
        return {"guest_total_bytes": self.total, "guest_used_peak_bytes": self.peak_used or None,
                "guest_available_min_bytes": self.min_avail, "process_vmhwm_bytes": proc_status("VmHWM")}


# ---------------------------------------------------------------- watchdog (self-timeout)

class Watchdog(threading.Thread):
    """Total and per-document deadlines. On a deadline: on_expire(kind, doc_id) is called one time. The default
    action of cmd_run writes the run record and stops the process with os._exit (a hung GPU call does not return)."""

    def __init__(self, total_s: float, doc_s: float, on_expire, tick: float = 1.0):
        super().__init__(daemon=True)
        self.total_end = time.time() + float(total_s)
        self.doc_s = float(doc_s)
        self.doc = None
        self.doc_end = None
        self.on_expire = on_expire
        self.tick = tick
        self.fired = None
        self.stop_ev = threading.Event()
        self.lock = threading.Lock()

    def doc_start(self, doc_id: str) -> None:
        with self.lock:
            self.doc = doc_id
            self.doc_end = time.time() + self.doc_s

    def doc_done(self) -> None:
        with self.lock:
            self.doc = None
            self.doc_end = None

    def run(self):
        while not self.stop_ev.wait(self.tick):
            t = time.time()
            with self.lock:
                doc, dend = self.doc, self.doc_end
            kind = "total" if t > self.total_end else ("doc" if dend is not None and t > dend else None)
            if kind:
                self.fired = (kind, doc)
                self.on_expire(kind, doc)
                return


# ---------------------------------------------------------------- job folder

def read_template(job: Path) -> dict:
    p = job / "template.json"
    t = json.loads(p.read_text(encoding="utf-8"))
    miss = [k for k in TEMPLATE_KEYS if k not in t]
    if miss:
        raise SystemExit(f"template.json: keys absent: {miss}")
    return t


def check_item(x: dict, lineno: int) -> list[str]:
    """Format errors of one items.jsonl line (interface 5)."""
    err = []
    miss = [k for k in ITEM_KEYS if k not in x]
    if miss:
        return [f"line {lineno}: keys absent: {miss}"]
    d = x["doc_id"]
    if not isinstance(d, str) or not RX_DOC.match(d):
        err.append(f"line {lineno}: doc_id {d!r} is not a safe file name")
    if not isinstance(x["prefix"], str) or not x["prefix"]:
        err.append(f"line {lineno}: prefix is empty or not a string")
    elif x["n_prefix_chars"] != len(x["prefix"]):
        err.append(f"line {lineno}: n_prefix_chars {x['n_prefix_chars']} != len(prefix) {len(x['prefix'])}")
    sf = x["suffixes"]
    if not isinstance(sf, list) or not sf:
        err.append(f"line {lineno}: suffixes is empty or not a list")
        return err
    ids = []
    for j, s in enumerate(sf):
        if not isinstance(s, dict) or set(s) < {"id", "text"}:
            err.append(f"line {lineno}: suffix {j} has no id or no text")
            continue
        if not isinstance(s["id"], str) or not RX_SUFFIX.match(s["id"]):
            err.append(f"line {lineno}: suffix id {s['id']!r} is not valid")
        if not isinstance(s["text"], str) or not s["text"]:
            err.append(f"line {lineno}: suffix {s.get('id')!r} has an empty text")
        ids.append(s["id"])
    if len(set(ids)) != len(ids):
        err.append(f"line {lineno}: suffix ids are not unique")
    return err


def scan_items(job: Path) -> tuple[list[dict], dict]:
    """First read of items.jsonl: format check; returns the index (doc_id, byte offset and length, suffix ids,
    text SHA-256 values) without the texts."""
    p = job / "items.jsonl"
    index, errors, seen = [], [], set()
    n_suffix = 0
    n_chars = 0
    with open(p, "rb") as f:
        lineno, off = 0, 0
        for raw in f:
            lineno += 1
            ln = len(raw)
            if raw.strip():
                try:
                    x = json.loads(raw)
                except ValueError as e:
                    errors.append(f"line {lineno}: not JSON ({e})")
                    off += ln
                    continue
                e = check_item(x, lineno) if isinstance(x, dict) else [f"line {lineno}: not an object"]
                if e:
                    errors += e
                elif x["doc_id"] in seen:
                    errors.append(f"line {lineno}: doc_id {x['doc_id']} occurs two times")
                else:
                    seen.add(x["doc_id"])
                    sids = [s["id"] for s in x["suffixes"]]
                    index.append({"doc_id": x["doc_id"], "offset": off, "length": ln, "suffix_ids": sids,
                                  "prefix_text_sha256": sha256_text(x["prefix"]),
                                  "suffix_text_sha256": [sha256_text(s["text"]) for s in x["suffixes"]],
                                  "n_prefix_chars": len(x["prefix"])})
                    n_suffix += len(sids)
                    n_chars += len(x["prefix"])
            off += ln
    if errors:
        raise SystemExit("items.jsonl format errors (first 20):\n  " + "\n  ".join(errors[:20]))
    if not index:
        raise SystemExit("items.jsonl holds no document")
    return index, {"docs": len(index), "suffixes": n_suffix, "prefix_chars": n_chars}


def read_item(job: Path, entry: dict) -> dict:
    with open(job / "items.jsonl", "rb") as f:
        f.seek(entry["offset"])
        x = json.loads(f.read(entry["length"]))
    assert x["doc_id"] == entry["doc_id"] and sha256_text(x["prefix"]) == entry["prefix_text_sha256"]
    return x


def job_files_sha(job: Path) -> dict:
    out = {n: sha256_file(job / n) for n in ("template.json", "items.jsonl")}
    if (job / "manifest.json").exists():
        out["manifest.json"] = sha256_file(job / "manifest.json")
    return out


def check_manifest(job: Path, files: dict) -> dict | None:
    p = job / "manifest.json"
    if not p.exists():
        return None
    man = json.loads(p.read_text(encoding="utf-8"))
    for n in ("template.json", "items.jsonl"):
        want = (man.get("files") or {}).get(n)
        if want != files[n]:
            raise SystemExit(f"manifest.json: SHA-256 of {n} differs ({want} != {files[n]})")
    return man


# ---------------------------------------------------------------- tokens

def letter_ids(tok) -> list[int]:
    out = []
    for L in LETTERS:
        ids = tok.encode(LETTER_FORM.format(L), add_special_tokens=False)
        if len(ids) != 1:
            raise SystemExit(f"letter {L!r}: the form {LETTER_FORM.format(L)!r} is not one token: {ids}")
        out.append(int(ids[0]))
    return out


def tokenize_item(tok, x: dict) -> tuple[list[int], list[list[int]]]:
    """The one token rule of the readouts (training and inference): prefix and each suffix separately, no special
    tokens added by the tokenizer. The ids of the model input are prefix ids + suffix ids."""
    pre = [int(i) for i in tok(x["prefix"], add_special_tokens=False)["input_ids"]]
    suf = [[int(i) for i in s] for s in tok([s["text"] for s in x["suffixes"]], add_special_tokens=False)["input_ids"]]
    return pre, suf


def token_problems(tok, pre: list[int], suf: list[list[int]]) -> list[str]:
    p = []
    bos = tok.bos_token_id
    if bos is not None:
        if not pre or pre[0] != bos:
            p.append(f"the prefix ids do not start with BOS {bos}")
        if len(pre) > 1 and pre[1] == bos:
            p.append("the prefix ids start with two BOS")
        if any(bos in s for s in suf):
            p.append("a suffix holds BOS")
    if any(len(s) == 0 for s in suf):
        p.append("a suffix has no tokens")
    return p


# ---------------------------------------------------------------- output files

def write_npz(p: Path, arrays: dict) -> None:
    import numpy as np
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    tmp = p.with_name(f".{p.stem}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(p)


def valid_output(p: Path, entry: dict, ctx: dict) -> tuple[bool, str]:
    """A valid output file of the same job, layers, model and code (the resume rule)."""
    import numpy as np
    if not p.exists():
        return False, "absent"
    try:
        with np.load(p, allow_pickle=False) as z:
            miss = [k for k in NPZ_KEYS if k not in z.files]
            if miss:
                return False, f"keys absent {miss[:3]}"
            if str(z["doc_id"]) != entry["doc_id"]:
                return False, "doc_id"
            if [str(s) for s in z["suffix_ids"].tolist()] != entry["suffix_ids"]:
                return False, "suffix_ids"
            if tuple(int(k) for k in z["layers"]) != tuple(ctx["layers"]):
                return False, "layers"
            if str(z["prefix_text_sha256"]) != entry["prefix_text_sha256"]:
                return False, "prefix text"
            if [str(s) for s in z["suffix_text_sha256"].tolist()] != entry["suffix_text_sha256"]:
                return False, "suffix text"
            for k in ("template_json_sha256", "model_fingerprint", "code_sha256", "dtype", "sdpa"):
                if str(z[k]) != str(ctx[k]):
                    return False, k
            if int(z["batch_setting"]) != int(ctx["batch_setting"]):
                return False, "batch_setting"
            s = z["states"]
            n = len(entry["suffix_ids"])
            if s.dtype != np.float16 or s.ndim != 3 or s.shape[:2] != (n, len(ctx["layers"])):
                return False, "states shape"
            if ctx.get("hidden") and s.shape[2] != ctx["hidden"]:
                return False, "hidden size"
            if not np.isfinite(s).all():
                return False, "states not finite"
            if z["letter_logprobs"].shape != (n, len(LETTERS)) or z["n_suffix_tokens"].shape != (n,):
                return False, "letter_logprobs or n_suffix_tokens shape"
    except Exception as e:  # noqa: BLE001
        return False, f"unreadable ({type(e).__name__})"
    return True, "valid"


def outputs_manifest(out: Path) -> dict:
    files = sorted([*out.glob("states/*.npz"), *out.glob("run_a*.json"), *out.glob("skips.jsonl")])
    return {str(p.relative_to(out)): sha256_file(p) for p in files}


def write_outputs_json(out: Path, extra: dict | None = None) -> str:
    files = outputs_manifest(out)
    obj = {"version": VERSION, "made": now(), "n_state_files": sum(1 for k in files if k.startswith("states/")),
           "files": files, **(extra or {})}
    write_json(out / "outputs.json", obj)
    return sha256_file(out / "outputs.json")


# ---------------------------------------------------------------- model passes (torch only inside these functions)

class Engine:
    """Model, hooks and the pass functions. layers: decoder layers k (1-based) of the readout."""

    def __init__(self, model, tok, layers: tuple[int, ...], device: str):
        import torch
        self.torch = torch
        self.model = model
        self.inner = model.model
        self.tok = tok
        self.layers = tuple(layers)
        self.dev = torch.device(device)
        self.cuda = self.dev.type == "cuda"
        self.n_layers = len(self.inner.layers)
        self.letter_ids = letter_ids(tok)
        self.letter_ix = torch.tensor(self.letter_ids, dtype=torch.long, device=self.dev)
        self.pad_id = tok.pad_token_id if tok.pad_token_id is not None else 0
        self.cap = {"on": False, "rows": None, "idx": None, "h": {}, "n": 0}
        cap = self.cap

        def hook_for(k):
            def h(mod, inp, outp):
                if cap["on"]:
                    o = outp[0] if isinstance(outp, tuple) else outp
                    cap["h"][k] = o[cap["rows"], cap["idx"]].detach()
            return h

        def count(mod, inp, outp):
            if cap["on"]:
                cap["n"] += 1

        self.hooks = [self.inner.layers[k - 1].register_forward_hook(hook_for(k)) for k in self.layers]
        self.hooks += [layer.register_forward_hook(count) for layer in self.inner.layers]
        self.manual_crop = None

    def close(self) -> None:
        for h in self.hooks:
            h.remove()

    def new_cache(self):
        from transformers import DynamicCache
        try:
            return DynamicCache(config=self.model.config)
        except TypeError:
            return DynamicCache()

    def prefill(self, cache, ids: list[int]) -> None:
        torch = self.torch
        for s in range(0, len(ids), PREFILL_CHUNK):
            x = torch.tensor([ids[s:s + PREFILL_CHUNK]], dtype=torch.long, device=self.dev)
            self.inner(input_ids=x, past_key_values=cache, use_cache=True)
        if cache.get_seq_length() != len(ids):
            raise RuntimeError(f"cache length {cache.get_seq_length()} != prefix length {len(ids)}")

    def _layers_of(self, cache):
        ls = getattr(cache, "layers", None)
        if ls and all(type(x).__name__ == "DynamicLayer" and hasattr(x, "keys") and hasattr(x, "values") for x in ls):
            return ls
        return None

    def crop(self, cache, n: int) -> None:
        """Cut the cache back to n tokens. DynamicLayer (transformers 5.x): the key and value tensors are cut
        directly (the meaning of Cache.crop changed between 5.8, 5.18 and later versions). Else Cache.crop with a
        negative value (remove that many tokens; the same meaning in 4.x and 5.x). The length is examined."""
        cur = cache.get_seq_length()
        if cur > n:
            ls = self._layers_of(cache)
            if ls is not None:
                for x in ls:
                    x.keys = x.keys[..., :n, :]
                    x.values = x.values[..., :n, :]
                self.manual_crop = True
            else:
                cache.crop(-(cur - n))
                self.manual_crop = False
        if cache.get_seq_length() != n:
            raise RuntimeError(f"crop: cache length {cache.get_seq_length()} != {n}")

    def repeat_rows(self, cache, b: int) -> None:
        """Batch mode: the prefix cache (batch 1) gets b rows (copies)."""
        ls = self._layers_of(cache)
        if ls is None:
            raise SystemExit("--batch > 1 needs a DynamicCache with DynamicLayer layers")
        for x in ls:
            x.keys = x.keys.repeat(b, 1, 1, 1)
            x.values = x.values.repeat(b, 1, 1, 1)

    def keep_rows(self, cache, b: int) -> None:
        for x in self._layers_of(cache):
            x.keys = x.keys[:b]
            x.values = x.values[:b]

    def suffix_pass(self, cache, seqs: list[list[int]]):
        """One forward pass of len(seqs) suffixes on top of the cache (cache batch = len(seqs)).
        Returns states float32 [B, n_layers_readout, hidden] and letter log-probs float32 [B, 6] (numpy)."""
        torch = self.torch
        b = len(seqs)
        L = max(len(s) for s in seqs)
        x = torch.full((b, L), int(self.pad_id), dtype=torch.long)
        for i, s in enumerate(seqs):
            x[i, :len(s)] = torch.tensor(s, dtype=torch.long)
        rows = torch.arange(b, device=self.dev)
        idx = torch.tensor([len(s) - 1 for s in seqs], dtype=torch.long, device=self.dev)
        cap = self.cap
        cap["rows"], cap["idx"], cap["h"], cap["n"] = rows, idx, {}, 0
        cap["on"] = True
        try:
            o = self.inner(input_ids=x.to(self.dev), past_key_values=cache, use_cache=True)
        finally:
            cap["on"] = False
        if cap["n"] != self.n_layers:
            raise RuntimeError(f"not all decoder layers ran ({cap['n']} of {self.n_layers})")
        hn = o.last_hidden_state[rows, idx]
        lg = self.model.lm_head(hn).float()
        lp = lg - torch.logsumexp(lg, dim=-1, keepdim=True)
        let = lp.index_select(1, self.letter_ix)
        st = torch.stack([cap["h"][k] for k in self.layers], dim=1).float()
        cap["h"] = {}
        return st.cpu().numpy(), let.cpu().numpy()

    def fresh_prefix_then_suffix(self, pre: list[int], suf: list[int]):
        cache = self.new_cache()
        self.prefill(cache, pre)
        st, let = self.suffix_pass(cache, [suf])
        del cache
        return st[0], let[0]

    def fresh_m07_rule(self, pre: list[int], suf: list[int]):
        ids = pre + suf
        cache = self.new_cache()
        self.prefill(cache, ids[:-1])
        st, let = self.suffix_pass(cache, [ids[-1:]])
        del cache
        return st[0], let[0]


def to_f16(a, what: str):
    import numpy as np
    b = a.astype(np.float16)
    if not np.isfinite(b).all():
        raise FloatingPointError(f"{what}: value not finite in float16 (max abs {float(np.abs(a).max())})")
    return b


def diff_stats(a, b, layers) -> dict:
    import numpy as np
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    d = np.abs(a - b)
    per = {str(k): round(float(d[j].max()), 8) for j, k in enumerate(layers)} if a.ndim == 2 else None
    cosv = []
    if a.ndim == 2:
        for j in range(a.shape[0]):
            na, nb = np.linalg.norm(a[j]), np.linalg.norm(b[j])
            cosv.append(float(a[j] @ b[j] / (na * nb)) if na > 0 and nb > 0 else 1.0)
    return {"max_abs_diff": round(float(d.max()), 8), "max_abs_value": round(float(np.abs(a).max()), 6),
            "per_layer_max_abs_diff": per, "min_cosine": round(min(cosv), 10) if cosv else None}


# ---------------------------------------------------------------- command run (one attempt)

def quantiles(ms: list[float]) -> dict | None:
    """Mean, p50, p95 and max of sorted values (ms of the suffix passes, crop included)."""
    if not ms:
        return None
    return {"mean": round(sum(ms) / len(ms), 3), "p50": round(ms[len(ms) // 2], 3),
            "p95": round(ms[min(len(ms) - 1, int(0.95 * len(ms)))], 3), "max": round(ms[-1], 3), "n": len(ms)}


def set_sdpa(torch, policy: str) -> None:
    """Attention kernels (scaled dot-product attention) on CUDA. no-cudnn (default): flash, memory-efficient and
    math on, cuDNN off. Reason: cuDNN attention builds a new kernel plan for each new sequence length (about 1.2 s,
    src/m07_lora_train.py), and each suffix pass has a new length. In the H7k records of src/m07_h_vm_states.py
    (cuDNN on), all 474 of 7,000 documents under 0.3 s had a prefill length that the same process had seen before;
    the median document took 0.98 s. auto: the torch default (as m07). flash-mem: cuDNN and math off (a missing
    kernel stops the pass)."""
    if policy == "auto":
        return
    torch.backends.cuda.enable_cudnn_sdp(False)
    if policy == "flash-mem":
        torch.backends.cuda.enable_math_sdp(False)


def next_attempt(out: Path) -> int:
    ns = [int(m.group(1)) for p in out.glob("run_a*.json") if (m := re.match(r"run_a(\d+)\.json$", p.name))]
    return max(ns, default=0) + 1


def cmd_run(a) -> int:
    t_start = time.time()
    job, out = Path(a.job), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "states").mkdir(exist_ok=True)
    layers = parse_layers(a.layers)
    attempt = a.attempt or next_attempt(out)
    run_p = out / f"run_a{attempt:02d}.json"
    if run_p.exists():
        raise SystemExit(f"{run_p} exists")
    model_dir = Path(a.model_dir)
    rec = {"command": "run", "version": VERSION, "attempt": attempt, "start": now(), "argv": sys.argv[1:],
           "code_sha256": code_sha(), "host": socket.gethostname(), "pid": os.getpid(),
           "job_dir": str(job), "out_dir": str(out), "model_dir": str(model_dir),
           "settings": {"layers": list(layers), "prefill_chunk": PREFILL_CHUNK, "dtype": a.dtype, "attn": a.attn,
                        "sdpa": a.sdpa,
                        "device": a.device, "batch": a.batch, "batch_token_budget": a.batch_token_budget,
                        "max_prefix_tokens": a.max_prefix_tokens, "doc_timeout_s": a.doc_timeout,
                        "total_timeout_s": a.total_timeout, "check_fresh": a.check_fresh,
                        "retry_skipped": bool(a.retry_skipped), "letters": list(LETTERS),
                        "letter_form": LETTER_FORM},
           "readout": "forward hook output of model.model.layers[k-1] (residual stream after decoder layer k, "
                      "before the final norm) at the last suffix token; the same unit as src/m07_h_vm_states.py",
           "token_rule": "prefix ids = tok(prefix, add_special_tokens=False); suffix ids = tok(suffix text, "
                         "add_special_tokens=False); model input = prefix ids + suffix ids",
           "pass_rule": f"prefix ids in chunks of {PREFILL_CHUNK} tokens from position 0 into one DynamicCache; each "
                        "suffix in one forward pass on top of the cache; then the cache is cropped back to the "
                        "prefix length", "disk_free_bytes_start": free_bytes(out), "documents": [], "check_fresh": []}
    state = {"rec": rec, "written": False}

    def write_record(stopped: str | None = None) -> None:
        if state["written"]:
            return
        state["written"] = True
        if stopped:
            rec["stopped"] = stopped
        rec["end"] = now()
        rec["wall_seconds"] = round(time.time() - t_start, 2)
        rec["disk_free_bytes_end"] = free_bytes(out)
        if "mem" in state:
            state["mem"].stop_ev.set()
            rec["memory_guest"] = state["mem"].result()
        if "torch" in state and state.get("cuda"):
            torch = state["torch"]
            with contextlib.suppress(Exception):
                rec["gpu_peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated())
                rec["gpu_peak_reserved_bytes"] = int(torch.cuda.max_memory_reserved())
        docs = rec["documents"]
        ms = sorted(m for d in docs for m in d.get("_pass_ms", []))
        ms_first = sorted(d["_pass_ms"][0] for d in docs if d.get("_pass_ms"))
        ms_rest = sorted(m for d in docs for m in d.get("_pass_ms", [])[1:])
        for d in docs:
            d.pop("_pass_ms", None)
        rec["counts"] = {"docs_in_job": rec.get("job", {}).get("docs"),
                         "docs_valid_before": rec.get("resume", {}).get("valid_before"),
                         "docs_done": sum(1 for d in docs if d.get("file_sha256")),
                         "docs_skipped": {r: sum(1 for d in docs if d.get("skip") == r) for r in SKIP_REASONS_FINAL},
                         "suffix_passes": sum(d.get("n_passes", 0) for d in docs),
                         "suffixes": sum(d.get("n_suffix", 0) for d in docs if d.get("file_sha256")),
                         "prefix_tokens": sum(d.get("n_prefix_tokens", 0) for d in docs if d.get("file_sha256")),
                         "suffix_tokens": sum(d.get("n_suffix_tokens", 0) for d in docs if d.get("file_sha256"))}
        pre_s = sum(d.get("prefill_s", 0.0) for d in docs)
        suf_s = sum(d.get("suffix_s", 0.0) for d in docs)
        rec["timing"] = {"prefill_seconds": round(pre_s, 3), "suffix_seconds": round(suf_s, 3),
                         "prefill_tokens_per_second": round(rec["counts"]["prefix_tokens"] / pre_s, 1) if pre_s else None,
                         "ms_per_suffix_pass": quantiles(ms), "ms_first_pass_of_document": quantiles(ms_first),
                         "ms_other_passes": quantiles(ms_rest)}
        rec["files_sha256"] = {f"states/{d['doc_id']}.npz": d["file_sha256"] for d in docs if d.get("file_sha256")}
        write_json(run_p, rec)
        with contextlib.suppress(Exception):
            rec["outputs_json_sha256"] = write_outputs_json(out, {"last_attempt": attempt})

    def on_expire(kind: str, doc: str | None) -> None:
        msg = f"self-timeout ({kind}{'' if doc is None else ', document ' + doc})"
        print(f"[{now()}] {msg}: stop", flush=True)
        with contextlib.suppress(Exception):
            if kind == "doc" and doc is not None:
                append_jsonl(out / "skips.jsonl", {"doc_id": doc, "reason": "doc_timeout", "time": now(),
                                                   "attempt": attempt, "seconds": a.doc_timeout})
                rec["documents"].append({"doc_id": doc, "skip": "doc_timeout"})
            write_record(msg)
        os._exit(RC_DOC_TIMEOUT if kind == "doc" else RC_TOTAL_TIMEOUT)

    wd = Watchdog(a.total_timeout, a.doc_timeout, on_expire, tick=a.watchdog_tick)
    wd.start()
    try:
        files = job_files_sha(job)
        man = check_manifest(job, files)
        template = read_template(job)
        index, counts = scan_items(job)
        tcalc = sha256_json({k: v for k, v in template.items() if k != "sha256"})
        rec["job"] = {"files_sha256": files, "template_id": template["template_id"],
                      "template_sha256": template["sha256"], "template_sha256_equal_content": tcalc == template["sha256"],
                      **counts, "manifest": man is not None}
        if tcalc != template["sha256"]:
            rec["stopped"] = ("template.json: the key sha256 is not the SHA-256 of the canonical JSON of the other keys "
                              f"({tcalc}): no model load")
            raise SystemExit(rec["stopped"])
        mfp = model_fingerprint(model_dir)
        rec["model_fingerprint"] = mfp
        want_fp = (man or {}).get("model_fingerprint")
        rec["model_fingerprint_job"] = want_fp
        if want_fp and want_fp != mfp and not a.allow_other_model:
            rec["stopped"] = "model fingerprint differs from the job manifest: no model load"
            raise SystemExit(rec["stopped"])
        ctx = {"layers": layers, "template_json_sha256": files["template.json"], "model_fingerprint": mfp,
               "code_sha256": rec["code_sha256"], "hidden": None, "dtype": a.dtype, "sdpa": a.sdpa,
               "batch_setting": a.batch}
        skipped = {} if a.retry_skipped else {s["doc_id"]: s["reason"] for s in read_jsonl(out / "skips.jsonl")
                                              if s.get("reason") in SKIP_REASONS_FINAL}
        todo, valid, invalid = [], 0, {}
        for e in index:
            ok, why = valid_output(out / "states" / f"{e['doc_id']}.npz", e, ctx)
            if ok:
                valid += 1
            elif e["doc_id"] in skipped:
                continue
            else:
                if why != "absent":
                    invalid[why] = invalid.get(why, 0) + 1
                todo.append(e)
        in_job = {e["doc_id"] for e in index}
        rec["resume"] = {"valid_before": valid, "skipped_before": sum(1 for d in skipped if d in in_job),
                         "invalid_before": invalid, "todo": len(todo)}
        print(f"[{now()}] job: {counts['docs']} documents, {counts['suffixes']} suffixes; valid outputs {valid}; "
              f"skipped before {rec['resume']['skipped_before']}; to do {len(todo)}", flush=True)
        if not todo:
            wd.stop_ev.set()
            write_record(None)
            return 0
        network_guard()
        with gpu_lock(a.lock, a.wait_lock, rec):
            print(f"[{now()}] GPU lock taken after {rec['lock_wait_seconds']} s", flush=True)
            mem = MemSampler()
            mem.start()
            state["mem"] = mem
            import numpy as np
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer
            state["torch"] = torch
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            set_sdpa(torch, a.sdpa)
            dev = torch.device(a.device)
            cuda = dev.type == "cuda"
            state["cuda"] = cuda
            try:
                import tokenizers
                tv = tokenizers.__version__
            except ImportError:
                tv = None
            rec["versions"] = {"python": sys.version.split()[0], "torch": torch.__version__,
                               "transformers": transformers.__version__, "numpy": np.__version__, "tokenizers": tv,
                               "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(dev) if cuda else a.device}
            rec["sdpa_policy"] = a.sdpa
            if cuda:
                rec["sdpa_backends_enabled"] = {"flash": torch.backends.cuda.flash_sdp_enabled(),
                                                "mem_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                                                "math": torch.backends.cuda.math_sdp_enabled(),
                                                "cudnn": torch.backends.cuda.cudnn_sdp_enabled()}
                free_b, total_b = torch.cuda.mem_get_info(dev)
                rec["gpu_memory_at_start"] = {"free_bytes": int(free_b), "total_bytes": int(total_b)}
            tok = AutoTokenizer.from_pretrained(str(model_dir))
            lids = letter_ids(tok)
            rec["tokenizer"] = {"class": type(tok).__name__, "bos_token_id": tok.bos_token_id,
                                "pad_token_id": tok.pad_token_id, "letter_token_ids": lids}
            if str(model_dir) == VM_MODEL_DIR and tuple(lids) != APERTUS_LETTER_IDS:
                rec["stopped"] = f"letter token ids {lids} differ from {list(APERTUS_LETTER_IDS)}: no model load"
                raise SystemExit(rec["stopped"])
            first = read_item(job, todo[0])
            pre0, suf0 = tokenize_item(tok, first)
            probs = token_problems(tok, pre0, suf0)
            del first
            if probs:
                rec["stopped"] = f"token check of the first document: {probs}: no model load"
                raise SystemExit(rec["stopped"])
            t0 = time.time()
            rec["model_load_start"] = now()
            dtype = {"bfloat16": torch.bfloat16, "float32": torch.float32, "float16": torch.float16}[a.dtype]
            kw = {"dtype": dtype, "attn_implementation": a.attn}
            if cuda:
                kw["device_map"] = a.device
            model = AutoModelForCausalLM.from_pretrained(str(model_dir), **kw)
            if not cuda:
                model = model.to(dev)
            model.eval()
            rec["model_load_seconds"] = round(time.time() - t0, 2)
            rec["attn_implementation"] = model.config._attn_implementation
            nl = model.config.num_hidden_layers
            hidden = model.config.hidden_size
            rec["model_config"] = {"model_type": model.config.model_type, "num_hidden_layers": nl,
                                   "hidden_size": hidden, "num_key_value_heads": getattr(model.config, "num_key_value_heads", None)}
            if str(model_dir) == VM_MODEL_DIR and (nl != APERTUS_N_LAYERS or hidden != APERTUS_HIDDEN):
                raise SystemExit(f"model has {nl} layers and hidden size {hidden}")
            if max(layers) > nl:
                raise SystemExit(f"--layers {list(layers)}: the model has {nl} decoder layers")
            ctx["hidden"] = hidden
            eng = Engine(model, tok, layers, a.device)
            if cuda:
                torch.cuda.reset_peak_memory_stats()
            rec["passes_start"] = now()
            t_pass = time.time()
            n_check = int(a.check_fresh)
            with torch.inference_mode():
                for e in todo:
                    if n_check > 0:
                        n = len(e["suffix_ids"])
                        want = [n - 1] + ([n // 2] if n >= 3 and n_check > 1 else [])
                        check_ix = want[:n_check]
                    else:
                        check_ix = []
                    drec = run_doc(eng, job, e, out, ctx, a, attempt, wd, check_ix, rec)
                    n_check -= len(drec.get("_checked", []))
                    drec.pop("_checked", None)
                    rec["documents"].append(drec)
            rec["passes_end"] = now()
            rec["passes_seconds"] = round(time.time() - t_pass, 2)
            rec["crop_mode"] = ("manual DynamicLayer cut" if eng.manual_crop else
                                "Cache.crop(negative)" if eng.manual_crop is False else "no crop")
            eng.close()
            del eng, model
            gc.collect()
            if cuda:
                rec["gpu_peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated())
                rec["gpu_peak_reserved_bytes"] = int(torch.cuda.max_memory_reserved())
                torch.cuda.empty_cache()
        wd.stop_ev.set()
        write_record(None)
        print(json.dumps({k: rec.get(k) for k in ("start", "end", "lock_wait_seconds", "model_load_seconds",
                                                  "passes_seconds", "counts", "timing", "gpu_peak_allocated_bytes")}),
              flush=True)
        return 0
    except SystemExit as e:
        wd.stop_ev.set()
        write_record(rec.get("stopped") or str(e))
        raise
    except BaseException as e:
        wd.stop_ev.set()
        write_record(f"{type(e).__name__}: {str(e)[:300]}")
        raise


def run_doc(eng: Engine, job: Path, e: dict, out: Path, ctx: dict, a, attempt: int, wd: Watchdog,
            check_ix: list[int], rec: dict) -> dict:
    """All suffixes of one document. Returns the document record (no text)."""
    import numpy as np
    torch = eng.torch
    d = e["doc_id"]
    drec = {"doc_id": d, "n_suffix": len(e["suffix_ids"])}
    wd.doc_start(d)
    t0 = time.time()
    cache = None

    def skip(reason: str, detail: str = "") -> dict:
        append_jsonl(out / "skips.jsonl", {"doc_id": d, "reason": reason, "time": now(), "attempt": attempt,
                                           "detail": detail[:300]})
        drec["skip"] = reason
        if detail:
            drec["skip_detail"] = detail[:300]
        print(f"[{now()}] {d}: no output ({reason})", flush=True)
        return drec

    try:
        x = read_item(job, e)
        pre, suf = tokenize_item(eng.tok, x)
        drec["n_prefix_tokens"] = len(pre)
        drec["n_suffix_tokens"] = sum(len(s) for s in suf)
        drec["max_suffix_tokens"] = max(len(s) for s in suf)
        probs = token_problems(eng.tok, pre, suf)
        if probs:
            return skip("error", f"token check: {probs}")
        if len(pre) > a.max_prefix_tokens:
            return skip("too_long", f"{len(pre)} prefix tokens > {a.max_prefix_tokens}")
        joint = [int(i) for i in eng.tok(x["prefix"] + x["suffixes"][0]["text"], add_special_tokens=False)["input_ids"]]
        boundary_equal = joint == pre + suf[0]
        drec["boundary_equal_first_suffix"] = boundary_equal
        del x, joint
        n = len(suf)
        b_eff = max(1, min(int(a.batch), n, int(a.batch_token_budget) // max(1, len(pre))))
        drec["batch"] = b_eff
        t1 = time.time()
        cache = eng.new_cache()
        eng.prefill(cache, pre)
        if eng.cuda:
            torch.cuda.synchronize()
        drec["prefill_s"] = round(time.time() - t1, 4)
        if b_eff > 1:
            eng.repeat_rows(cache, b_eff)
        states = np.zeros((n, len(eng.layers), ctx["hidden"]), dtype=np.float32)
        lets = np.zeros((n, len(LETTERS)), dtype=np.float32)
        pass_ms = []
        t2 = time.time()
        for g in range(0, n, b_eff):
            grp = list(range(g, min(n, g + b_eff)))
            if len(grp) < b_eff:
                eng.keep_rows(cache, len(grp))
            tp = time.perf_counter()
            st, lt = eng.suffix_pass(cache, [suf[j] for j in grp])
            eng.crop(cache, len(pre))
            pass_ms.append((time.perf_counter() - tp) * 1000.0)
            states[grp] = st
            lets[grp] = lt
        drec["suffix_s"] = round(time.time() - t2, 4)
        drec["n_passes"] = len(pass_ms)
        drec["ms_per_pass"] = round(sum(pass_ms) / len(pass_ms), 3)
        drec["ms_first_pass"] = round(pass_ms[0], 3)
        drec["_pass_ms"] = pass_ms
        del cache
        cache = None
        try:
            s16 = to_f16(states, d)
        except FloatingPointError as fe:
            return skip("not_finite", str(fe))
        arrays = {
            "doc_id": np.array(d), "suffix_ids": np.array(e["suffix_ids"]),
            "layers": np.array(eng.layers, dtype=np.int16), "states": s16,
            "letter_logprobs": lets.astype(np.float32), "n_prefix_tokens": np.int64(len(pre)),
            "n_suffix_tokens": np.array([len(s) for s in suf], dtype=np.int64),
            "letters": np.array(LETTERS), "letter_token_ids": np.array(eng.letter_ids, dtype=np.int64),
            "prefix_text_sha256": np.array(e["prefix_text_sha256"]),
            "suffix_text_sha256": np.array(e["suffix_text_sha256"]),
            "prefix_tokens_sha256": np.array(sha256_json(pre)),
            "suffix_tokens_sha256": np.array([sha256_json(s) for s in suf]),
            "boundary_equal_first_suffix": np.bool_(boundary_equal),
            "template_id": np.array(str(rec["job"]["template_id"])),
            "template_sha256": np.array(str(rec["job"]["template_sha256"])),
            "template_json_sha256": np.array(ctx["template_json_sha256"]),
            "model": np.array(rec["model_dir"]), "model_fingerprint": np.array(ctx["model_fingerprint"]),
            "code_sha256": np.array(ctx["code_sha256"]), "version": np.array(VERSION),
            "dtype": np.array(a.dtype), "attn": np.array(rec.get("attn_implementation") or a.attn),
            "sdpa": np.array(a.sdpa), "batch": np.int64(b_eff), "batch_setting": np.int64(a.batch),
            "prefill_chunk": np.int64(PREFILL_CHUNK), "made": np.array(now())}
        p = out / "states" / f"{d}.npz"
        tw = time.time()
        write_npz(p, arrays)
        drec["write_s"] = round(time.time() - tw, 4)
        drec["file_sha256"] = sha256_file(p)
        drec["seconds"] = round(time.time() - t0, 4)
        checked = []
        for j in check_ix:
            checked.append(fresh_check(eng, d, e["suffix_ids"][j], j, pre, suf[j], states[j], lets[j], b_eff))
        if checked:
            rec["check_fresh"] += checked
            drec["_checked"] = checked
        print(f"[{now()}] {d}: {len(pre)} prefix tokens, {n} suffixes, {drec['ms_per_pass']} ms per pass, "
              f"prefill {drec['prefill_s']} s, total {drec['seconds']} s", flush=True)
        return drec
    except Exception as ex:  # noqa: BLE001
        oom = isinstance(ex, getattr(torch, "OutOfMemoryError", ())) or "out of memory" in str(ex).lower()
        cache = None
        gc.collect()
        if eng.cuda:
            with contextlib.suppress(Exception):
                torch.cuda.empty_cache()
        return skip("oom" if oom else "error", f"{type(ex).__name__}: {str(ex)[:250]}")
    finally:
        wd.doc_done()


def fresh_check(eng: Engine, d: str, sid: str, j: int, pre: list[int], suf: list[int], st, lt, b_eff: int) -> dict:
    t = time.time()
    s1, l1 = eng.fresh_prefix_then_suffix(pre, suf)
    s2, l2 = eng.fresh_m07_rule(pre, suf)
    r = {"doc_id": d, "suffix_id": sid, "suffix_index": j, "crops_before": j // max(1, b_eff), "batch": b_eff,
         "n_prefix_tokens": len(pre), "n_suffix_tokens": len(suf),
         "fresh_prefix_then_suffix": {"states": diff_stats(st, s1, eng.layers), "letter_logprobs": diff_stats(lt, l1, ())},
         "fresh_m07_rule_joined": {"states": diff_stats(st, s2, eng.layers), "letter_logprobs": diff_stats(lt, l2, ())},
         "seconds": round(time.time() - t, 3)}
    print(f"[{now()}] check-fresh {d}/{sid}: crop vs fresh max abs diff "
          f"{r['fresh_prefix_then_suffix']['states']['max_abs_diff']}; vs m07 rule "
          f"{r['fresh_m07_rule_joined']['states']['max_abs_diff']}", flush=True)
    return r


# ---------------------------------------------------------------- command drive (VM driver; standard library only)

def count_states(out: Path) -> int:
    return sum(1 for _ in (out / "states").glob("*.npz")) if (out / "states").exists() else 0


def log_tail(p: Path, n: int = 20000) -> str:
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - n))
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def checks_done(out: Path) -> int:
    n = 0
    for p in out.glob("run_a*.json"):
        with contextlib.suppress(Exception):
            n += len(json.loads(p.read_text(encoding="utf-8")).get("check_fresh") or [])
    return n


def run_argv(a, attempt: int, remaining: float, check_n: int) -> list[str]:
    cmd = [sys.executable, "-I", os.path.abspath(__file__), "run", "--job", str(a.job), "--out", str(a.out),
           "--layers", a.layers, "--model-dir", a.model_dir, "--lock", a.lock, "--device", a.device,
           "--dtype", a.dtype, "--attn", a.attn, "--sdpa", a.sdpa, "--batch", str(a.batch), "--batch-token-budget",
           str(a.batch_token_budget), "--max-prefix-tokens", str(a.max_prefix_tokens), "--doc-timeout",
           str(a.doc_timeout), "--total-timeout", str(int(remaining)), "--check-fresh", str(check_n),
           "--watchdog-tick", str(a.watchdog_tick), "--attempt", str(attempt)]
    if a.wait_lock:
        cmd.append("--wait-lock")
    if a.allow_other_model:
        cmd.append("--allow-other-model")
    return cmd


def cmd_drive(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t_end = time.time() + float(a.total_timeout)
    pidf = out / "driver.pid"
    pidf.write_text(f"{os.getpid()} {now()}\n")
    dp = out / "drive.json"
    drive = json.loads(dp.read_text(encoding="utf-8")) if dp.exists() else {
        "version": VERSION, "start": now(), "job": str(a.job), "out": str(out), "attempts": [], "driver_starts": []}
    drive["driver_starts"].append(now())
    drive.pop("failed", None)
    drive["code_sha256"] = code_sha()
    _, counts = scan_items(Path(a.job))
    total = counts["docs"]

    def save() -> None:
        write_json(dp, drive)

    def status(**kw) -> None:
        write_json(out / "status.json", {**kw, "docs_total": total, "states_done": count_states(out),
                                         "skips": len(read_jsonl(out / "skips.jsonl")), "updated": now()})

    def fail(msg: str) -> int:
        drive["failed"] = msg
        drive.setdefault("failures", []).append({"time": now(), "error": msg})
        save()
        status(phase="failed", error=msg)
        print(f"[{now()}] driver: {msg}", flush=True)
        return 1

    try:
        save()
        while True:
            k = next_attempt(out)
            if k > a.max_attempts:
                return fail(f"attempt limit {a.max_attempts} reached")
            remaining = t_end - time.time()
            if remaining < 60:
                return fail("total timeout of the driver")
            check_n = max(0, int(a.check_fresh) - checks_done(out))
            before = count_states(out)
            lf = out / "logs" / f"run_a{k:02d}.log"
            lf.parent.mkdir(parents=True, exist_ok=True)
            att = {"attempt": k, "start": now(), "log": str(lf.relative_to(out)), "states_before": before,
                   "check_fresh": check_n}
            drive["attempts"].append(att)
            save()
            with open(lf, "w", encoding="utf-8") as log:
                proc = subprocess.Popen(run_argv(a, k, remaining, check_n), stdout=log, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL)
                while proc.poll() is None:
                    lock = "taken" if "GPU lock taken" in log_tail(lf) else "waiting"
                    status(phase="running", attempt=k, lock=lock)
                    for _ in range(int(a.poll)):
                        if proc.poll() is not None:
                            break
                        time.sleep(1)
            att["rc"] = proc.returncode
            att["end"] = now()
            att["states_after"] = count_states(out)
            rp = out / f"run_a{k:02d}.json"
            r = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {}
            att["run_json_sha256"] = sha256_file(rp) if rp.exists() else None
            att["stopped"] = r.get("stopped")
            att["counts"] = r.get("counts")
            save()
            if att["rc"] == 0:
                break
            if att["rc"] == RC_TOTAL_TIMEOUT:
                return fail(f"attempt {k}: total self-timeout")
            if att["rc"] == RC_DOC_TIMEOUT:
                continue
            if att["states_after"] <= before:
                return fail(f"attempt {k}: rc {att['rc']} without a new output ({att['stopped']})")
        osha = write_outputs_json(out, {"last_attempt": next_attempt(out) - 1, "driver": True})
        drive["end"] = now()
        drive["outputs_json_sha256"] = osha
        save()
        status(phase="done", outputs_json_sha256=osha, drive_json_sha256=sha256_file(dp))
        print(f"[{now()}] driver: done; outputs.json {osha}", flush=True)
        return 0
    except Exception as e:  # noqa: BLE001
        return fail(f"{type(e).__name__}: {str(e)[:300]}")
    finally:
        with contextlib.suppress(Exception):
            pidf.unlink()


# ---------------------------------------------------------------- command compare (numpy only)

def cmd_compare(a) -> int:
    import numpy as np
    A, B = Path(a.a), Path(a.b)
    fa = {p.stem: p for p in (A / "states").glob("*.npz")}
    fb = {p.stem: p for p in (B / "states").glob("*.npz")}
    common = sorted(set(fa) & set(fb))
    rows = []
    for d in common:
        with np.load(fa[d], allow_pickle=False) as za, np.load(fb[d], allow_pickle=False) as zb:
            if [str(s) for s in za["suffix_ids"]] != [str(s) for s in zb["suffix_ids"]]:
                rows.append({"doc_id": d, "error": "suffix_ids differ"})
                continue
            la, lb = [int(k) for k in za["layers"]], [int(k) for k in zb["layers"]]
            ks = [k for k in la if k in lb]
            sa = za["states"][:, [la.index(k) for k in ks]].astype(np.float32)
            sb = zb["states"][:, [lb.index(k) for k in ks]].astype(np.float32)
            dl = np.abs(za["letter_logprobs"] - zb["letter_logprobs"])
            rows.append({"doc_id": d, "n_suffix": int(sa.shape[0]), "layers": ks,
                         "max_abs_diff_states": float(np.abs(sa - sb).max()),
                         "per_layer": {str(k): float(np.abs(sa[:, j] - sb[:, j]).max()) for j, k in enumerate(ks)},
                         "max_abs_diff_letter_logprobs": float(dl.max()),
                         "same_argmax_letter": int((za["letter_logprobs"].argmax(1) == zb["letter_logprobs"].argmax(1)).sum()),
                         "prefix_tokens_equal": str(za["prefix_tokens_sha256"]) == str(zb["prefix_tokens_sha256"])})
    ok = [r for r in rows if "error" not in r]
    res = {"made": now(), "a": str(A), "b": str(B), "docs_a": len(fa), "docs_b": len(fb), "common": len(common),
           "max_abs_diff_states": max((r["max_abs_diff_states"] for r in ok), default=None),
           "max_abs_diff_letter_logprobs": max((r["max_abs_diff_letter_logprobs"] for r in ok), default=None),
           "errors": [r for r in rows if "error" in r], "documents": rows}
    txt = json.dumps(res, indent=1)
    if a.out_json:
        write_json(Path(a.out_json), res)
    print(json.dumps({k: res[k] for k in ("docs_a", "docs_b", "common", "max_abs_diff_states",
                                           "max_abs_diff_letter_logprobs")}, indent=1) if a.out_json else txt)
    return 0


# ---------------------------------------------------------------- main

def add_run_args(p) -> None:
    p.add_argument("--job", required=True, help="job folder (template.json, items.jsonl, manifest.json)")
    p.add_argument("--out", required=True, help="output folder (states/, run_aNN.json, skips.jsonl, outputs.json)")
    p.add_argument("--layers", default=",".join(str(k) for k in DEFAULT_LAYERS),
                   help="decoder layers k (1-based; residual stream after layer k)")
    p.add_argument("--model-dir", default=VM_MODEL_DIR)
    p.add_argument("--lock", default=VM_GPU_LOCK)
    p.add_argument("--wait-lock", action="store_true")
    p.add_argument("--device", default="cuda:0", help="torch device (cpu only for a code test with a small model)")
    p.add_argument("--dtype", choices=["bfloat16", "float32", "float16"], default="bfloat16")
    p.add_argument("--attn", choices=["sdpa", "eager", "flash_attention_2"], default="sdpa")
    p.add_argument("--sdpa", choices=["no-cudnn", "auto", "flash-mem"], default="no-cudnn",
                   help="SDPA kernels on CUDA (see set_sdpa)")
    p.add_argument("--batch", type=int, default=1, help="suffixes in one forward pass (1 = plan layout)")
    p.add_argument("--batch-token-budget", type=int, default=BATCH_TOKEN_BUDGET)
    p.add_argument("--max-prefix-tokens", type=int, default=MAX_PREFIX_TOKENS)
    p.add_argument("--doc-timeout", type=float, default=DOC_TIMEOUT_S)
    p.add_argument("--total-timeout", type=float, default=TOTAL_TIMEOUT_S)
    p.add_argument("--check-fresh", type=int, default=0,
                   help="N suffixes: state again with a fresh prefill (crop check) and with the m07 prefill rule")
    p.add_argument("--watchdog-tick", type=float, default=1.0, help="seconds between two deadline checks")
    p.add_argument("--allow-other-model", action="store_true",
                   help="test only: accept a model fingerprint that differs from the job manifest")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run", help="one attempt in this process (resume: valid outputs are not done again)")
    add_run_args(pr)
    pr.add_argument("--attempt", type=int, default=0)
    pr.add_argument("--retry-skipped", action="store_true")
    pd = sub.add_parser("drive", help="the VM driver: attempts of run until done (start with setsid nohup)")
    add_run_args(pd)
    pd.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    pd.add_argument("--poll", type=float, default=15.0)
    pc = sub.add_parser("compare", help="largest differences of two output folders (numpy only)")
    pc.add_argument("--a", required=True)
    pc.add_argument("--b", required=True)
    pc.add_argument("--out-json")
    a = ap.parse_args()
    if a.cmd in ("run", "drive") and a.batch < 1:
        raise SystemExit("--batch must be >= 1")
    if a.cmd == "run":
        sys.exit(cmd_run(a))
    elif a.cmd == "drive":
        a.retry_skipped = False
        sys.exit(cmd_drive(a))
    else:
        sys.exit(cmd_compare(a))


if __name__ == "__main__":
    main()
