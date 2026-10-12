# SPDX-License-Identifier: Apache-2.0
"""Path 2 iteration 2 (E35, E37 item 6): equality check of the hidden states of candidate H (VM against Mac).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5).
This file does not change an existing file. It does not write into daten/cls/it2/states or
daten/cls/it2/heads. Outputs: daten/cls/it2/vm_equality/ only.

1 Rule (protocol, 12.10.2026, 01:37; decisions, E37 item 6)
  Rows: 10 R1 rows of C1 and 10 R2 rows of C2 (addendum L, chapter 4.1). C1 = the rows of train_r1.csv with
  use 1 and the label recommended_for or recommended_against (279). C2 = the 800 rows of
  extract_r2_sample.csv. For each task: sort the rows by the SHA-256 hex of "cls-it2-eq|" + doc_id
  (ascending) and take the first 10. The VM makes their states with the frozen template and the frozen
  prefill rule of H. The frozen heads give q from the Mac states and from the VM states.
  PASS for a task: the same decision on 10 of 10 rows and the largest absolute difference of q at most
  0.02. Else FAIL for that task.

2 Tensor (same on both sides)
  Mac (src/m05_cls_it2_states.py, MLX): StateEngine.pass_one keeps x = layer(x) for the decoder layers
  2, 4, ..., 32 at the last prompt token. This is the residual stream after decoder layer k, BEFORE the
  final norm. final_norm is the output of the final norm at the same token.
  VM (this script, PyTorch): a forward hook on model.model.layers[k - 1] (ApertusDecoderLayer, the output is
  the residual stream hidden_states after attention and MLP) keeps output[0, -1] for the same layers. The
  final norm output is last_hidden_state[0, -1] of model.model. The HF hidden_states tuple is not used.
  Both sides: bf16 model weights and activations; the file value is float16 (exact copy of the float32
  value of the bf16 tensor, cast to float16; a value that is not finite in float16 stops the script).

3 Prompt and prefill (same on both sides)
  Prompt: m05_cls_apertus.build(task, frozen variant, doc_id) on the Mac (MLX tokenizer wrapper). The VM
  builds the ids again with the transformers tokenizer of the VM model (chat template with
  add_generation_prompt True and enable_thinking False, then the ids of the prefix "Antwort:") and
  compares them with the Mac ids. A difference stops the run before the model load.
  Prefill: ids[:-1] in chunks of 2048 tokens from position 0 into one KV cache (DynamicCache), then the
  last prompt token alone through all 32 decoder layers, the final norm and the language model head.
  Option values: the constrained readout of iteration 1 (m05_cls_apertus.constrained, copy below).

4 Output files (same keys and dtypes as the Mac state files)
  states float16 [16, 4096], layers int16 [16], final_norm float16 [4096], probs float64, option_logprobs
  float64, mass float64, n_prompt_tokens int64, and the texts doc_id, state_id, task, variant,
  prompt_sha256, text_sha256, template_sha256, cache_key, model, model_fingerprint, code_sha256,
  engine_code_sha256 (here: SHA-256 of this script), version, made.

5 Rules of the process
  Mac: m05_cls_data.assert_allowed(ids, ("dev",)) before the job file is written. No local model run.
  VM: no network (socket connections refused), GPU lock /opt/apertus/runs/gpu.lock (flock, the same
  protocol as m07_lora_train.py --wait-lock). The script takes the lock BEFORE torch and the model load
  and releases it after the last pass. The VM writes no document text to an output.

Usage:
  .venv/bin/python src/m07_h_vm_states.py select        (Mac: rows.json)
  .venv/bin/python src/m07_h_vm_states.py prepare       (Mac: job.json with texts and Mac prompt ids)
  /opt/apertus/venv/bin/python -I m07_h_vm_states.py run --job JOB.json --out DIR [--wait-lock]   (VM)
  .venv/bin/python src/m07_h_vm_states.py compare       (Mac: equality.json and equality.md)
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import fcntl
import hashlib
import io
import json
import math
import os
import socket
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

VERSION = "m07-h-vm-states-1"
SALT = "cls-it2-eq|"
N_ROWS = 10
LAYERS = tuple(range(2, 33, 2))            # same layers as the Mac state files (m05_cls_it2_states.LAYERS)
N_LAYERS = 32
PREFILL_CHUNK = 2048
MAX_DQ = 0.02
VARIANT = {"r1": "r1_v1_i95_de", "r2": "r2_v1_de"}
TEMPLATE_SHA = {"r1": "1f507fa222971beff705bc3c76dce8082fd6f5c7dd9153621e6328ce15847547",
                "r2": "2a48e04bb8996dd331df38c79fa3121db63420b9c2e3eb5c8afaf053b8e5872e"}
FROZEN_SHA = "9517c31d99327a99de3c259537ddefd42ca6140b5524d0668dd018d4be693ab5"
VM_MODEL_DIR = "/opt/apertus/models/apertus-v1.5-8b-text-bf16"
VM_GPU_LOCK = "/opt/apertus/runs/gpu.lock"

# Mac paths (relative to the project folder)
ROOT = Path(__file__).resolve().parents[1]
EQ = ROOT / "daten/cls/it2/vm_equality"
ROWS_JSON = EQ / "rows.json"
JOB_JSON = EQ / "job.json"
VM_STATES = EQ / "vm_states"
EQ_JSON = EQ / "equality.json"
EQ_MD = EQ / "equality.md"
MAC_STATES = ROOT / "daten/cls/it2/states"
TRAIN_R1 = ROOT / "daten/cls/it2/train_r1.csv"
R2_SAMPLE = ROOT / "daten/cls/it2/extract_r2_sample.csv"
FROZEN = ROOT / "daten/cls/it2/frozen_it2.json"


# ---------------------------------------------------------------- helpers (both sides)

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


def order_key(doc_id: str) -> str:
    return hashlib.sha256((SALT + str(doc_id)).encode("utf-8")).hexdigest()


def constrained(choice_ids: list[list[int]], lps: dict) -> tuple[list[float], float]:
    """Exact copy of m05_cls_apertus.constrained (SHA-256 f3677338...a2b)."""
    logp, raw = [], []
    for c in choice_ids:
        s, r = 0.0, 0.0
        for j, t in enumerate(c):
            node = tuple(c[:j])
            allowed = sorted({d[j] for d in choice_ids if len(d) > j and tuple(d[:j]) == node})
            la = [lps[node][a] for a in allowed]
            m = max(la)
            z = m + math.log(sum(math.exp(x - m) for x in la))
            s += lps[node][t] - z
            r += lps[node][t]
        logp.append(s)
        raw.append(r)
    m = max(logp)
    e = [math.exp(x - m) for x in logp]
    return [x / sum(e) for x in e], sum(math.exp(x) for x in raw)


def template_sha(spec: dict, task: str) -> str:
    """Template SHA-256 with the definition of m05_cls_apertus.build() (zero-shot, language key '*')."""
    options = {"r1": ["recommended_for", "recommended_against"], "r2": ["yes", "no"]}[task]
    tmpl = {"system": spec["system"], "doc_head": spec["doc_head"], "sep": spec["sep"],
            "spec": {"question": spec["question"], "prefix": spec["prefix"], "choices": list(spec["choices"])},
            "lang_key": "*", "shots": [], "options": options}
    return sha256_json(tmpl)


def model_fingerprint(model_dir: Path) -> str:
    """Same definition as m05_cls_apertus.model_fingerprint (small files, names and sizes of the weights)."""
    h = hashlib.sha256()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                 "model.safetensors.index.json"):
        p = model_dir / name
        if p.exists():
            h.update(name.encode() + b"\0" + p.read_bytes())
    for p in sorted(model_dir.glob("*.safetensors")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    return "apertus-v1.5-8b-text-bf16:" + h.hexdigest()


# ---------------------------------------------------------------- Mac: select and prepare

def select_rows() -> dict:
    with open(TRAIN_R1, encoding="utf-8", newline="") as f:
        r1 = [r for r in csv.DictReader(f) if r["use"] == "1" and r["label"] in ("recommended_for", "recommended_against")]
    with open(R2_SAMPLE, encoding="utf-8", newline="") as f:
        r2 = list(csv.DictReader(f))
    assert len(r1) == 279 and len({r["doc_id"] for r in r1}) == 279, len(r1)
    assert len(r2) == 800 and len({r["doc_id"] for r in r2}) == 800, len(r2)
    out = {}
    for task, rs in (("r1", r1), ("r2", r2)):
        keyed = sorted(((order_key(r["doc_id"]), r["doc_id"]) for r in rs))
        out[task] = [{"task": task, "doc_id": d, "order_sha256": k, "position": i + 1}
                     for i, (k, d) in enumerate(keyed[:N_ROWS])]
    return out


def cmd_select() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import m05_cls_data as cd
    if ROWS_JSON.exists():
        raise SystemExit(f"{ROWS_JSON} exists")
    sel = select_rows()
    ids = [x["doc_id"] for t in sel for x in sel[t]]
    cd.assert_allowed(ids, ("dev",))
    for t in sel:
        for x in sel[t]:
            p = MAC_STATES / t / f"{x['doc_id']}.npz"
            assert p.exists(), p
    rec = {"version": VERSION, "made": now(), "time_source": "date (clock of the Mac)",
           "rule": "protocol 12.10.2026 01:37 (E37 item 6): C1 = train_r1.csv rows with use 1 and label "
                   "recommended_for or recommended_against (279); C2 = the 800 rows of extract_r2_sample.csv; "
                   "for each task the first 10 rows by the SHA-256 hex of 'cls-it2-eq|' + doc_id (ascending)",
           "inputs_sha256": {"daten/cls/it2/train_r1.csv": sha256_file(TRAIN_R1),
                             "daten/cls/it2/extract_r2_sample.csv": sha256_file(R2_SAMPLE)},
           "split_check": "m05_cls_data.assert_allowed(20 doc_ids, ('dev',)): passed",
           "script_sha256": code_sha(), "rows": sel}
    EQ.mkdir(parents=True, exist_ok=True)
    ROWS_JSON.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(sel, indent=1))
    print("written", ROWS_JSON.relative_to(ROOT), sha256_file(ROWS_JSON))


def cmd_prepare() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import m05_cls_data as cd
    import m05_cls_apertus as ap
    if JOB_JSON.exists():
        raise SystemExit(f"{JOB_JSON} exists")
    rows = json.loads(ROWS_JSON.read_text(encoding="utf-8"))
    assert rows["rows"] == select_rows(), "rows.json differs from the rule"
    fr = json.loads(FROZEN.read_text(encoding="utf-8"))
    assert sha256_file(FROZEN) == FROZEN_SHA
    mfp = ap.model_fingerprint()
    assert mfp == fr["model_fingerprint"], mfp
    items = []
    for t in ("r1", "r2"):
        v = fr["tasks"][t]["prompt_variant"]
        assert v == VARIANT[t]
        ids_t = [x["doc_id"] for x in rows["rows"][t]]
        cd.assert_allowed(ids_t, ("dev",))
        for x in rows["rows"][t]:
            d = x["doc_id"]
            text = cd.text(d)
            b = ap.build(t, v, d)
            assert b["template_sha256"] == fr["tasks"][t]["template_sha256"] == TEMPLATE_SHA[t]
            assert b["text_sha256"] == hashlib.sha256(text.encode()).hexdigest()
            sp = ap.VARIANTS[t][v]["lang"]["*"]
            spec = {"system": ap.SYSTEM, "doc_head": ap.DOC_HEAD, "sep": ap.SEP, "question": sp["question"],
                    "prefix": sp["prefix"], "choices": list(sp["choices"])}
            assert template_sha(spec, t) == b["template_sha256"]
            mac_file = MAC_STATES / t / f"{d}.npz"
            import numpy as np
            with np.load(mac_file, allow_pickle=False) as z:
                assert str(z["prompt_sha256"]) == b["prompt_sha256"], f"{t}/{d}: Mac state file has another prompt"
                assert tuple(int(k) for k in z["layers"]) == LAYERS
            items.append({"task": t, "doc_id": d, "state_id": d, "variant": v, "spec": spec,
                          "template_sha256": b["template_sha256"], "text": text, "text_sha256": b["text_sha256"],
                          "ids_mac": b["ids"], "prompt_sha256_mac": b["prompt_sha256"], "choice_ids": b["choice_ids"],
                          "cache_key_mac": ap.cache_key(mfp, b["ids"], b["choice_ids"]),
                          "mac_state_file": str(mac_file.relative_to(ROOT)), "mac_state_sha256": sha256_file(mac_file)})
    job = {"version": VERSION, "made": now(), "script_sha256": code_sha(), "rows_json_sha256": sha256_file(ROWS_JSON),
           "frozen_sha256": FROZEN_SHA, "model_fingerprint_mac": mfp, "layers": list(LAYERS),
           "prefill_chunk": PREFILL_CHUNK, "split": "dev", "items": items}
    JOB_JSON.write_text(json.dumps(job, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(items)} items, prompt tokens {sum(len(i['ids_mac']) for i in items)}, "
          f"max {max(len(i['ids_mac']) for i in items)}")
    print("written", JOB_JSON.relative_to(ROOT), sha256_file(JOB_JSON))


# ---------------------------------------------------------------- VM: run

def network_guard() -> None:
    orig = socket.socket.connect

    def deny(self, addr, *a, **k):
        if self.family == getattr(socket, "AF_UNIX", None):
            return orig(self, addr, *a, **k)
        raise RuntimeError(f"m07_h_vm_states: network connection refused ({addr})")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = lambda *a, **k: deny(socket.socket(), a[0] if a else None)


@contextlib.contextmanager
def gpu_lock(path: str, wait: bool, rec: dict):
    """Same protocol as m07_lora_train.gpu_lock: flock, then one line 'pid N since T'."""
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
        f.write(f"pid {os.getpid()} since {now()}\n")
        f.flush()
        yield
    finally:
        with contextlib.suppress(Exception):
            f.seek(0)
            f.truncate()
            f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        rec["lock_released"] = now()


def vm_prompt_ids(tok, it: dict) -> list[int]:
    sp = it["spec"]
    msgs = [{"role": "system", "content": sp["system"]},
            {"role": "user", "content": sp["doc_head"] + it["text"] + sp["sep"] + sp["question"]}]
    x = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, tokenize=True,
                                return_dict=False)
    if hasattr(x, "keys"):
        x = x["input_ids"]
    ids = [int(i) for i in x]
    ids += [int(i) for i in tok.encode(sp["prefix"], add_special_tokens=False)]
    return ids


def to_f16(a, what: str):
    import numpy as np
    b = a.astype(np.float16)
    if not np.isfinite(b).all():
        raise ValueError(f"{what}: value not finite in float16 (max abs {float(np.abs(a).max())})")
    return b


def write_npz(p: Path, arrays: dict) -> None:
    import numpy as np
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    tmp = p.with_name(f"{p.stem}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(p)


def cmd_run(a) -> None:
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    out.mkdir(parents=True, exist_ok=True)
    job = json.load(open(a.job, encoding="utf-8"))
    items = job["items"]
    assert tuple(job["layers"]) == LAYERS and job["prefill_chunk"] == PREFILL_CHUNK
    assert all(it["template_sha256"] == TEMPLATE_SHA[it["task"]] == template_sha(it["spec"], it["task"]) for it in items)
    assert all(it["variant"] == VARIANT[it["task"]] for it in items)
    assert all(hashlib.sha256(it["text"].encode()).hexdigest() == it["text_sha256"] for it in items)
    model_dir = Path(a.model_dir)
    rec = {"command": "run", "version": VERSION, "start": now(), "argv": sys.argv[1:], "code_sha256": code_sha(),
           "job_sha256": sha256_file(a.job), "items": len(items), "model_dir": str(model_dir),
           "prefill_rule": f"ids[:-1] in chunks of {PREFILL_CHUNK} tokens from position 0 (DynamicCache), "
                           "then the last prompt token alone",
           "tensor": "forward hook output of model.model.layers[k-1] (residual stream after decoder layer k, "
                     "before the final norm) at the last prompt token; final_norm = last_hidden_state[0, -1]",
           "layers": list(LAYERS)}
    mfp = model_fingerprint(model_dir)
    rec["model_fingerprint"] = mfp
    rec["model_fingerprint_equal_mac"] = mfp == job["model_fingerprint_mac"]
    if not rec["model_fingerprint_equal_mac"]:
        raise SystemExit(f"model fingerprint differs from the Mac: {mfp}")
    network_guard()
    per = []
    try:
        with gpu_lock(a.lock, a.wait_lock, rec):
            print(f"[{now()}] GPU lock taken after {rec['lock_wait_seconds']} s", flush=True)
            import numpy as np
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            dev = torch.device(a.device)
            cuda = dev.type == "cuda"
            rec["versions"] = {"python": sys.version.split()[0], "torch": torch.__version__,
                               "transformers": transformers.__version__, "numpy": np.__version__,
                               "gpu": torch.cuda.get_device_name(dev) if cuda else a.device}
            rec["sdpa_backends_enabled"] = {"flash": torch.backends.cuda.flash_sdp_enabled(),
                                            "mem_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                                            "math": torch.backends.cuda.math_sdp_enabled(),
                                            "cudnn": torch.backends.cuda.cudnn_sdp_enabled()}
            tok = AutoTokenizer.from_pretrained(str(model_dir))
            for it in items:
                ids = vm_prompt_ids(tok, it)
                ch = [[int(i) for i in tok.encode(c, add_special_tokens=False)] for c in it["spec"]["choices"]]
                it["_ids"] = ids
                it["_ids_equal"] = ids == it["ids_mac"]
                it["_choice_equal"] = ch == it["choice_ids"]
            rec["prompt_ids_equal"] = sum(it["_ids_equal"] for it in items)
            rec["choice_ids_equal"] = sum(it["_choice_equal"] for it in items)
            print(f"[{now()}] prompt ids equal to the Mac: {rec['prompt_ids_equal']}/{len(items)}; "
                  f"option ids equal: {rec['choice_ids_equal']}/{len(items)}", flush=True)
            if rec["prompt_ids_equal"] != len(items) or rec["choice_ids_equal"] != len(items):
                rec["stopped"] = "prompt or option token ids differ from the Mac: no model load"
                raise SystemExit(rec["stopped"])
            t0 = time.time()
            rec["model_load_start"] = now()
            model = AutoModelForCausalLM.from_pretrained(str(model_dir), dtype=torch.bfloat16, device_map=a.device,
                                                         attn_implementation=a.attn)
            model.eval()
            assert model.config.num_hidden_layers == N_LAYERS
            rec["model_load_seconds"] = round(time.time() - t0, 2)
            rec["attn_implementation"] = model.config._attn_implementation
            inner = model.model
            cap = {"on": False, "h": {}}

            def hook_for(k):
                def h(mod, inp, outp):
                    if cap["on"]:
                        o = outp[0] if isinstance(outp, tuple) else outp
                        cap["h"][k] = o[0, -1].detach().float().cpu().numpy()
                return h

            hooks = [inner.layers[k - 1].register_forward_hook(hook_for(k)) for k in LAYERS]
            n_run = {"n": 0}

            def count(mod, inp, outp):
                if cap["on"]:
                    n_run["n"] += 1
            hooks += [layer.register_forward_hook(count) for layer in inner.layers]
            if cuda:
                torch.cuda.reset_peak_memory_stats()
            t_gpu = time.time()
            rec["passes_start"] = now()
            with torch.inference_mode():
                for it in items:
                    ids = it["_ids"]
                    t1 = time.time()
                    try:
                        cache = DynamicCache(config=model.config)
                    except TypeError:
                        cache = DynamicCache()
                    pre = ids[:-1]
                    for s in range(0, len(pre), PREFILL_CHUNK):
                        x = torch.tensor([pre[s:s + PREFILL_CHUNK]], dtype=torch.long, device=dev)
                        inner(input_ids=x, past_key_values=cache, use_cache=True)
                    assert cache.get_seq_length() == len(pre)
                    cap["on"], cap["h"], n_run["n"] = True, {}, 0
                    o = inner(input_ids=torch.tensor([ids[-1:]], dtype=torch.long, device=dev),
                              past_key_values=cache, use_cache=True)
                    cap["on"] = False
                    assert n_run["n"] == N_LAYERS, "not all decoder layers ran"
                    hn = o.last_hidden_state[0, -1:]
                    lg = model.lm_head(hn).float()
                    lp = (lg - torch.logsumexp(lg, dim=-1, keepdim=True))[0]
                    if cuda:
                        torch.cuda.synchronize()
                    root = lp.cpu().numpy()
                    ch = it["choice_ids"]
                    assert all(len(c) == 1 for c in ch), "frozen variants have options of one token"
                    small = {(): {int(c[0]): float(root[c[0]]) for c in ch}}
                    probs, mass = constrained(ch, small)
                    opt_lp = [small[()][c[0]] for c in ch]
                    states = np.stack([cap["h"][k] for k in LAYERS])
                    final = hn[0].float().cpu().numpy()
                    sec = time.time() - t1
                    arrays = {
                        "states": to_f16(states, it["state_id"]), "layers": np.array(LAYERS, dtype=np.int16),
                        "final_norm": to_f16(final, it["state_id"]),
                        "probs": np.array(probs, dtype=np.float64),
                        "option_logprobs": np.array(opt_lp, dtype=np.float64),
                        "mass": np.float64(mass), "n_prompt_tokens": np.int64(len(ids)),
                        "doc_id": np.array(it["doc_id"]), "state_id": np.array(it["state_id"]),
                        "task": np.array(it["task"]), "variant": np.array(it["variant"]),
                        "prompt_sha256": np.array(sha256_json(ids)), "text_sha256": np.array(it["text_sha256"]),
                        "template_sha256": np.array(it["template_sha256"]),
                        "cache_key": np.array(sha256_json({"model": mfp, "prompt": ids, "choices": ch})),
                        "model": np.array(str(model_dir)), "model_fingerprint": np.array(mfp),
                        "code_sha256": np.array(rec["code_sha256"]), "engine_code_sha256": np.array(rec["code_sha256"]),
                        "version": np.array(VERSION), "made": np.array(now())}
                    write_npz(out / it["task"] / f"{it['state_id']}.npz", arrays)
                    per.append({"task": it["task"], "doc_id": it["doc_id"], "n_prompt_tokens": len(ids),
                                "prefill_chunks": -(-len(pre) // PREFILL_CHUNK), "prompt_ids_equal_mac": it["_ids_equal"],
                                "prompt_sha256": sha256_json(ids), "probs": probs, "mass": mass,
                                "seconds": round(sec, 3)})
                    del cache, o
                    print(f"[{now()}] {it['task']} {it['doc_id']}: {len(ids)} tokens, {round(sec, 2)} s", flush=True)
            rec["passes_end"] = now()
            rec["passes_seconds"] = round(time.time() - t_gpu, 2)
            rec["gpu_peak_bytes"] = int(torch.cuda.max_memory_allocated()) if cuda else None
            for h in hooks:
                h.remove()
            del model
            if cuda:
                torch.cuda.empty_cache()
    finally:
        rec["end"] = now()
        rec["documents"] = per
        rec["prompt_tokens"] = sum(p["n_prompt_tokens"] for p in per)
        files = sorted(out.rglob("*.npz"))
        rec["files_sha256"] = {str(p.relative_to(out)): sha256_file(p) for p in files}
        (out / "run.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: rec.get(k) for k in ("start", "lock_wait_seconds", "lock_taken", "lock_released", "end",
                                                  "model_load_seconds", "passes_seconds", "prompt_tokens",
                                                  "prompt_ids_equal", "stopped")}), flush=True)


# ---------------------------------------------------------------- Mac: compare

def cos(a, b) -> float:
    import numpy as np
    a, b = np.asarray(a, dtype=np.float64).ravel(), np.asarray(b, dtype=np.float64).ravel()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def r(x, n=8):
    return None if x is None else round(float(x), n)


def cmd_compare() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import numpy as np
    import m05_cls_data as cd
    import m05_cls_it2_head as hd
    assert sha256_file(FROZEN) == FROZEN_SHA
    fr = json.loads(FROZEN.read_text(encoding="utf-8"))
    assert fr["code"]["src/m05_cls_it2_head.py"] == sha256_file(ROOT / "src/m05_cls_it2_head.py")
    rows = json.loads(ROWS_JSON.read_text(encoding="utf-8"))
    assert rows["rows"] == select_rows()
    job = json.loads(JOB_JSON.read_text(encoding="utf-8"))
    run = json.loads((VM_STATES / "run.json").read_text(encoding="utf-8"))
    res_tasks, row_out = {}, []
    for t in ("r1", "r2"):
        f = fr["tasks"][t]
        head, meta = hd.load_head(ROOT / f["weights_file"])
        assert sha256_file(ROOT / f["weights_file"]) == f["weights_sha256"]
        feat = tuple(f["layers"])
        ids = [x["doc_id"] for x in rows["rows"][t]]
        cd.assert_allowed(ids, ("dev",))
        dq_all, eq_n, out_t = [], 0, []
        for x in rows["rows"][t]:
            d = x["doc_id"]
            pm = MAC_STATES / t / f"{d}.npz"
            pv = VM_STATES / t / f"{d}.npz"
            zm, zv = hd.load_npz(pm), hd.load_npz(pv)
            assert zm["prompt_sha256"] == zv["prompt_sha256"], f"{t}/{d}: prompt differs"
            assert zm["template_sha256"] == zv["template_sha256"] == f["template_sha256"]
            assert int(zm["n_prompt_tokens"]) == int(zv["n_prompt_tokens"])
            assert tuple(int(k) for k in zm["layers"]) == tuple(int(k) for k in zv["layers"]) == LAYERS
            vm_ = hd.predict_state(t, pv, fr, head)
            mm_ = hd.predict_state(t, pm, fr, head)
            dq = max(abs(mm_["q"][o] - vm_["q"][o]) for o in f["options"])
            same = mm_["decision"] == vm_["decision"]
            eq_n += same
            dq_all.append(dq)
            fm = hd.features_from_state(zm, feat)[0].astype(np.float64)
            fv = hd.features_from_state(zv, feat)[0].astype(np.float64)
            per_layer = {}
            for j, k in enumerate(LAYERS):
                a_, b_ = zm["states"][j].astype(np.float64), zv["states"][j].astype(np.float64)
                per_layer[str(k)] = {"cosine": r(cos(a_, b_)), "max_abs_diff": r(np.abs(a_ - b_).max(), 6),
                                     "max_abs_mac": r(np.abs(a_).max(), 4)}
            fn_m, fn_v = zm["final_norm"].astype(np.float64), zv["final_norm"].astype(np.float64)
            out_t.append({
                "task": t, "doc_id": d, "order_sha256": x["order_sha256"], "n_prompt_tokens": int(zm["n_prompt_tokens"]),
                "prompt_sha256_equal": True, "decision_mac": mm_["decision"], "decision_vm": vm_["decision"],
                "decision_equal": same, "q_mac": {k: r(v) for k, v in mm_["q"].items()},
                "q_vm": {k: r(v) for k, v in vm_["q"].items()}, "abs_diff_q": r(dq),
                "feature_layers": list(feat), "feature_cosine": r(cos(fm, fv)),
                "feature_max_abs_diff": r(np.abs(fm - fv).max(), 6), "feature_max_abs_mac": r(np.abs(fm).max(), 4),
                "final_norm_cosine": r(cos(fn_m, fn_v)), "final_norm_max_abs_diff": r(np.abs(fn_m - fn_v).max(), 6),
                "zero_shot_p_first_mac": r(float(zm["probs"][0])), "zero_shot_p_first_vm": r(float(zv["probs"][0])),
                "zero_shot_abs_diff": r(abs(float(zm["probs"][0]) - float(zv["probs"][0]))),
                "layers": per_layer})
        max_dq = max(dq_all)
        ok = eq_n == N_ROWS and max_dq <= MAX_DQ
        res_tasks[t] = {"rows": N_ROWS, "decision_equal": eq_n, "max_abs_diff_q": r(max_dq),
                        "mean_abs_diff_q": r(sum(dq_all) / len(dq_all)),
                        "feature_layers": list(feat),
                        "min_feature_cosine": min(o["feature_cosine"] for o in out_t),
                        "max_feature_abs_diff": max(o["feature_max_abs_diff"] for o in out_t),
                        "min_cosine_all_layers": min(v["cosine"] for o in out_t for v in o["layers"].values()),
                        "max_zero_shot_abs_diff": max(o["zero_shot_abs_diff"] for o in out_t),
                        "result": "PASS" if ok else "FAIL"}
        row_out += out_t
    rec = {"version": VERSION, "made": now(), "time_source": "date (clock of the Mac)",
           "actor": "workflow sub-agent (Claude Opus 5.5) for the main agent",
           "rule": "protocol 12.10.2026 01:37 (E37 item 6): PASS for a task if the decision is the same on 10 of 10 "
                   "rows and the largest absolute difference of q is at most 0.02; else FAIL",
           "results": res_tasks, "rows": row_out,
           "tensor_mac": "src/m05_cls_it2_states.py StateEngine.pass_one (MLX, bf16): x = layer(x) for decoder "
                         "layers 2, 4, ..., 32 at the last prompt token (residual stream after layer k, before the "
                         "final norm); file value float16",
           "tensor_vm": "src/m07_h_vm_states.py run (PyTorch, bf16, CUDA): forward hook output of "
                        "model.model.layers[k-1] at the last prompt token (residual stream after layer k, before "
                        "the final norm); file value float16",
           "prefill_rule_both": "ids[:-1] in chunks of 2048 tokens from position 0 into one KV cache, then the "
                                "last prompt token alone through all 32 decoder layers",
           "head_application": "m05_cls_it2_head.predict_state (frozen heads, z-score with mu and sd of the head "
                               "file, lr softmax; decision: first option if q(first) >= 0.5)",
           "vm_run": {k: run.get(k) for k in ("start", "end", "lock_wait_seconds", "lock_taken", "lock_released",
                                              "model_load_start", "model_load_seconds", "passes_start", "passes_end",
                                              "passes_seconds", "prompt_tokens", "prompt_ids_equal",
                                              "choice_ids_equal", "model_fingerprint", "model_fingerprint_equal_mac",
                                              "versions", "attn_implementation", "sdpa_backends_enabled",
                                              "gpu_peak_bytes", "argv", "code_sha256", "job_sha256")},
           "inputs_sha256": {
               "daten/cls/it2/frozen_it2.json": FROZEN_SHA,
               "daten/cls/it2/heads/r1_head.npz": sha256_file(ROOT / fr["tasks"]["r1"]["weights_file"]),
               "daten/cls/it2/heads/r2_head.npz": sha256_file(ROOT / fr["tasks"]["r2"]["weights_file"]),
               "src/m05_cls_it2_head.py": sha256_file(ROOT / "src/m05_cls_it2_head.py"),
               "src/m05_cls_it2_states.py": sha256_file(ROOT / "src/m05_cls_it2_states.py"),
               "src/m05_cls_apertus.py": sha256_file(ROOT / "src/m05_cls_apertus.py"),
               "src/m07_h_vm_states.py": code_sha(),
               "daten/cls/it2/vm_equality/rows.json": sha256_file(ROWS_JSON),
               "daten/cls/it2/vm_equality/job.json": sha256_file(JOB_JSON),
               "daten/cls/it2/vm_equality/vm_states/run.json": sha256_file(VM_STATES / "run.json")},
           "mac_state_files_sha256": {f"{o['task']}/{o['doc_id']}.npz": sha256_file(MAC_STATES / o["task"] / f"{o['doc_id']}.npz")
                                      for o in row_out},
           "vm_state_files_sha256": {f"{o['task']}/{o['doc_id']}.npz": sha256_file(VM_STATES / o["task"] / f"{o['doc_id']}.npz")
                                     for o in row_out}}
    EQ_JSON.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(res_tasks, indent=1))
    print("written", EQ_JSON.relative_to(ROOT), sha256_file(EQ_JSON))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["select", "prepare", "run", "compare"])
    p.add_argument("--job")
    p.add_argument("--out")
    p.add_argument("--model-dir", default=VM_MODEL_DIR)
    p.add_argument("--lock", default=VM_GPU_LOCK)
    p.add_argument("--wait-lock", action="store_true")
    p.add_argument("--attn", choices=["sdpa", "flash_attention_2"], default="sdpa")
    p.add_argument("--device", default="cuda:0", help="torch device (cpu only for a code test with a small model)")
    a = p.parse_args()
    if a.cmd == "select":
        cmd_select()
    elif a.cmd == "prepare":
        cmd_prepare()
    elif a.cmd == "run":
        if not (a.job and a.out):
            raise SystemExit("--job and --out are necessary")
        cmd_run(a)
    else:
        cmd_compare()


if __name__ == "__main__":
    main()
