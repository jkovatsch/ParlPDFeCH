# SPDX-License-Identifier: Apache-2.0
"""Path 2 iteration 2 (E35), step 1: hidden states of the local Apertus-v1.5-8B (bf16, MLX) for R1 and R2.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5).
This file does not change an existing file. It uses src/m05_cls_data.py (rows, text,
lock, assert_allowed) and src/m05_cls_apertus.py (prompt build, Engine, constrained readout, cache key).

1 What the script does
  For each document, the script builds the prompt of iteration 1 (m05_cls_apertus.build(): system text,
  user turn "Dokument:\n" + whole document text + "\n\n" + question, then the assistant prefix; whole
  document first, question last). The default prompt variant is the frozen variant of iteration 1
  (VARIANT). The model input is the document text only: no export field, category, file name or URL.
  The script runs the full model (all 32 decoder layers, bf16, no truncation, no quantization):
    a) prefill of the prompt tokens without the last token, in chunks of PREFILL_CHUNK tokens (the same
       chunks as the iteration-1 engine for one variant: m05_cls_apertus.Engine.run_group, L = n - 1);
    b) the last prompt token alone, layer by layer. The script keeps the output of the decoder layers in
       LAYERS (residual stream, before the final norm) and the output of the final norm (input of the
       language model head) at this token;
    c) the readout of the option tokens from the same logits (constrained choice of iteration 1).
  Thus the last-layer state gives the same option values as the iteration-1 engine (check command).

2 Output (one file for each document)
  daten/cls/it2/states/<task>/<doc_id>.npz            dev documents
  daten/cls/it2/states_pairs/<task>/<state_id>.npz    synthetic texts (counterfactual pairs, dev only)
  daten/cls/it2/states_validation/<task>/<doc_id>.npz the one validation run (flag --allow-validation)
  Arrays in the file:
    states       float16 [len(layers), 4096]   output of decoder layer k at the last prompt token
    layers       int16   [len(layers)]         k (1 to 32; 32 = last layer, before the final norm)
    final_norm   float16 [4096]                output of the final norm at the last prompt token
    probs        float64 [options]             constrained option probabilities (p = probs[0])
    option_logprobs float64 [options]          unconstrained log-probability of each option
    mass         float64                       unconstrained probability mass of the options
    n_prompt_tokens int64
    texts: doc_id, state_id, task, variant, prompt_sha256 (SHA-256 of the prompt token ids, as in
    iteration 1), text_sha256, template_sha256, cache_key (key of the iteration-1 cache), model,
    model_fingerprint, code_sha256, engine_code_sha256, version, made.
  The script refuses a value that is not finite in float16 (no silent overflow).
  A document with more than MAX_TEXT_TOKENS text tokens gets no file (memory limit of iteration 1);
  the run record counts it (no_state_length).

3 Rules of the process
  Local model only (daten/modelle/apertus-v1.5-8b-text-bf16), memory limits of m04_kern, lock
  daten/cls/model.lock (m05_cls_data.model_lock), socket connections refused in the process, no Docling
  process at the same time (process rule 7.4). m05_cls_data.assert_allowed() before each model run:
  dev only, except the validation run with --allow-validation (only after the freeze of the head).
  Each model run writes one line to daten/cls/it2/runs.jsonl (start, end, documents, tokens, seconds).
  A file that exists with the same prompt SHA-256, model fingerprint and layers is not made again.

4 Check (command check, dev only)
  CHECK_DOCS: 3 dev check documents for each task (iteration-1 values in daten/cls/cache, made by the
  check run with one variant, thus with the same chunks) and 1 long R2 document for the speed.
  a) Deterministic: 2 passes for each document; the states, final norm and log-probabilities must be
     bit-equal.
  b) Same values as iteration 1: the probabilities (6 decimals) and the mass must be equal to the
     cache value of the same cache key (same model fingerprint, prompt token ids, option token ids).
  c) The stored float16 state of layer 32, through the final norm and the head (bf16), must give the
     same probabilities.
  d) Speed: seconds for each 1,000 prompt tokens (prefill and last token).
  Output: daten/cls/it2/states_check.json.

Usage:
  .venv/bin/python src/m05_cls_it2_states.py check
  .venv/bin/python src/m05_cls_it2_states.py run --task r1|r2 [--subset design,check] [--ids FILE]
         [--limit N] [--budget-seconds S] [--variant V]
  .venv/bin/python src/m05_cls_it2_states.py run-texts --task r1|r2 --texts FILE.jsonl [--budget-seconds S]
         (FILE.jsonl: one line {"state_id", "doc_id", "text_path"} for each synthetic text; text_path
         inside daten/cls/it2/; doc_id = the dev source document)
  .venv/bin/python src/m05_cls_it2_states.py run --task r1|r2 --split validation --allow-validation
  .venv/bin/python src/m05_cls_it2_states.py plan --task r1|r2 [--subset ...] [--ids FILE] [--limit N]
         (no model: number of documents and tokens, time estimate from SPEED_S_PER_1K)
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m05_cls_data as cd  # noqa: E402
import m05_cls_apertus as ap  # noqa: E402

ROOT = cd.ROOT
OUT = cd.OUT / "it2"
STATES = OUT / "states"
STATES_PAIRS = OUT / "states_pairs"
STATES_VAL = OUT / "states_validation"
RUNS = OUT / "runs.jsonl"
CHECK_FILE = OUT / "states_check.json"
VERSION = "cls-it2-states-1"
LAYERS = tuple(range(2, 33, 2))          # every 2nd decoder layer: holds every 4th layer and the last layer
N_LAYERS = 32
MAX_TEXT_TOKENS = ap.MAX_TEXT_TOKENS
PREFILL_CHUNK = ap.PREFILL_CHUNK
DOCLING_CHECK_EVERY = 20
VARIANT = {"r1": "r1_v1_i95_de", "r2": "r2_v1_de"}
# dev check documents with an iteration-1 value from the check run (one variant) and p not near 0 or 1,
# prompt lengths in 1, 2 and 3 or more prefill chunks; R2 132948 (13,643 tokens) is the long speed point
CHECK_DOCS = {"r1": ("233117", "178623", "556625"), "r2": ("76383", "887818", "655804", "132948")}
SPEED_S_PER_1K = 5.4                     # planning value: check of 11.10.2026 (5.27 to 5.45; iteration 1: 4.29 to 4.62)


# ---------------------------------------------------------------- helpers

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_sha() -> str:
    return sha256_file(Path(__file__))


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def out_dir(kind: str, task: str) -> Path:
    return {"dev": STATES, "pairs": STATES_PAIRS, "validation": STATES_VAL}[kind] / task


def append_run(rec: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_state(p: Path) -> dict:
    with np().load(p, allow_pickle=False) as z:
        return {k: (z[k].item() if z[k].ndim == 0 else z[k]) for k in z.files}


def np():
    import numpy
    return numpy


def write_state(p: Path, arrays: dict) -> None:
    """Write the npz file through a temporary file (atomic replace)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    np().savez(buf, **arrays)
    tmp = p.with_name(f"{p.stem}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(p)


def is_done(p: Path, prompt_sha: str, mfp: str, layers: tuple[int, ...]) -> bool:
    if not p.exists():
        return False
    try:
        z = read_state(p)
    except Exception:  # noqa: BLE001
        return False
    return (z.get("prompt_sha256") == prompt_sha and z.get("model_fingerprint") == mfp
            and tuple(int(x) for x in z["layers"]) == tuple(layers))


# ---------------------------------------------------------------- items (what to run)

def dev_rows(task: str, subsets: tuple[str, ...]) -> list[dict]:
    """Dev rows of the subsets in rank order, without text duplicates and without the documents that the
    protected lists hold now (m05_cls_data.protected_doc_ids())."""
    prot = cd.protected_doc_ids()
    rs = [r for r in cd.rows(task) if r["split"] == "dev" and r["subset"] in subsets and r["doc_id"] not in prot]
    return sorted(rs, key=lambda r: r["rank"])


def validation_rows(task: str) -> list[dict]:
    prot = cd.protected_doc_ids()
    rs = [r for r in cd.rows(task) if r["split"] == "validation" and r["subset"] == "validation"
          and r["doc_id"] not in prot]
    return sorted(rs, key=lambda r: r["rank"])


def read_ids(p: Path) -> list[str]:
    return [x.strip().split(",")[0] for x in Path(p).read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.startswith("#") and x.strip() != "doc_id"]


def doc_items(task: str, split: str, subsets: tuple[str, ...], ids_file: str | None, limit: int | None) -> list[dict]:
    rs = validation_rows(task) if split == "validation" else dev_rows(task, subsets)
    if ids_file:
        want = read_ids(Path(ids_file))
        by = {r["doc_id"]: r for r in rs}
        miss = [d for d in want if d not in by]
        if miss:
            raise SystemExit(f"{len(miss)} ids are not in the {split} rows of {task} {subsets}: {miss[:5]}")
        rs = [by[d] for d in want]
    rs = rs[:limit] if limit else rs
    return [{"state_id": r["doc_id"], "doc_id": r["doc_id"], "text": None, "n_text_tokens": int(r["n_tokens"]),
             "text_path": f"daten/cls/text/{r['doc_id']}.txt"} for r in rs]


def text_items(task: str, texts_file: str) -> list[dict]:
    """Synthetic texts (counterfactual pairs): text file inside daten/cls/it2/, source document in dev."""
    tok = cd.tokenizer()
    out = []
    for line in Path(texts_file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        x = json.loads(line)
        tp = (ROOT / x["text_path"]).resolve()
        if OUT.resolve() not in tp.parents:
            raise SystemExit(f"{x['text_path']}: a synthetic text must be inside daten/cls/it2/")
        t = tp.read_text(encoding="utf-8")
        out.append({"state_id": str(x["state_id"]), "doc_id": str(x["doc_id"]), "text": t,
                    "n_text_tokens": len(tok.encode(t, add_special_tokens=False).ids), "text_path": rel(tp)})
    ids = [o["state_id"] for o in out]
    assert len(ids) == len(set(ids)), "repeated state_id"
    return out


# ---------------------------------------------------------------- model

class StateEngine:
    """The iteration-1 engine (same load, memory limits, warm-up) and a last-token pass that keeps the
    layer outputs."""

    def __init__(self):
        self.eng = ap.Engine()
        from mlx_lm.models.base import create_attention_mask
        self.mask_fn = create_attention_mask
        self.mx = self.eng.mx

    def pass_one(self, ids: list[int], choice_ids: list[list[int]], layers: tuple[int, ...]) -> dict:
        """Full forward pass of the prompt. Return the states (float32 numpy, exact bf16 values), the final
        norm, the root log-probabilities of the option tokens, the option values and the times."""
        mx, e = self.mx, self.eng
        numpy = np()
        cache = e.make(e.model)
        t0 = time.perf_counter()
        e.feed(cache, ids[:-1])                               # same chunks as Engine.run_group with one item
        t1 = time.perf_counter()
        inner = e.model.model
        x = inner.embed_tokens(mx.array([ids[-1:]]))
        mask = self.mask_fn(x, cache[0])
        keep = {}
        for k, (layer, c) in enumerate(zip(inner.layers, cache), start=1):
            x = layer(x, mask=mask, cache=c)
            if k in layers:
                keep[k] = x[0, -1:]
        assert k == N_LAYERS, "not all decoder layers ran"
        hn = inner.norm(x)
        lg = e.head(hn[0, -1:]).astype(mx.float32)
        lp = lg - mx.logsumexp(lg, axis=-1, keepdims=True)
        mx.eval(lp, hn, list(keep.values()), [c.state for c in cache])
        root = numpy.array(lp)[0]
        states = numpy.stack([numpy.array(keep[k].astype(mx.float32))[0] for k in layers])
        final = numpy.array(hn[0, -1].astype(mx.float32))
        lps = {(): root}
        for c in choice_ids:                                  # options with more than one token (as Engine.score)
            if len(c) > 1 and any(tuple(c[:j]) not in lps for j in range(1, len(c))):
                lpc = e.feed(cache, c[:-1], len(c) - 1)
                for j in range(1, len(c)):
                    lps[tuple(c[:j])] = lpc[j - 1]
                e.trim(cache, len(c) - 1)
        small = {node: {int(t): float(v[t]) for t in {d[len(node)] for d in choice_ids
                                                      if len(d) > len(node) and tuple(d[:len(node)]) == node}}
                 for node, v in lps.items()}
        probs, mass = ap.constrained(choice_ids, small)
        opt_lp = [sum(small[tuple(c[:j])][c[j]] for j in range(len(c))) for c in choice_ids]
        t2 = time.perf_counter()
        del cache
        mx.clear_cache()
        return {"states": states, "final_norm": final, "root_logprobs": root, "probs": probs, "mass": mass,
                "option_logprobs": opt_lp, "prefill_seconds": t1 - t0, "seconds": t2 - t0}

    def readout_from_state(self, state_f16, choice_ids: list[list[int]]) -> tuple[list[float], float]:
        """Option values from a stored float16 state of layer 32 (final norm and head in bf16).
        Only for options of one token (the frozen variants)."""
        mx, e = self.mx, self.eng
        assert all(len(c) == 1 for c in choice_ids)
        h = mx.array(np().asarray(state_f16, dtype=np().float32)).astype(mx.bfloat16)[None, None, :]
        hn = e.model.model.norm(h)
        lg = e.head(hn[0, -1:]).astype(mx.float32)
        lp = lg - mx.logsumexp(lg, axis=-1, keepdims=True)
        mx.eval(lp)
        root = np().array(lp)[0]
        return ap.constrained(choice_ids, {(): {int(c[0]): float(root[c[0]]) for c in choice_ids}})


def to_f16(a, what: str):
    numpy = np()
    b = a.astype(numpy.float16)
    if not numpy.isfinite(b).all():
        raise ValueError(f"{what}: value not finite in float16 (max abs {float(numpy.abs(a).max())})")
    return b


def arrays_for(item: dict, task: str, variant: str, b: dict, r: dict, layers: tuple[int, ...], mfp: str) -> dict:
    numpy = np()
    return {
        "states": to_f16(r["states"], item["state_id"]), "layers": numpy.array(layers, dtype=numpy.int16),
        "final_norm": to_f16(r["final_norm"], item["state_id"]),
        "probs": numpy.array(r["probs"], dtype=numpy.float64),
        "option_logprobs": numpy.array(r["option_logprobs"], dtype=numpy.float64),
        "mass": numpy.float64(r["mass"]), "n_prompt_tokens": numpy.int64(len(b["ids"])),
        "doc_id": numpy.array(item["doc_id"]), "state_id": numpy.array(item["state_id"]),
        "task": numpy.array(task), "variant": numpy.array(variant),
        "prompt_sha256": numpy.array(b["prompt_sha256"]), "text_sha256": numpy.array(b["text_sha256"]),
        "template_sha256": numpy.array(b["template_sha256"]),
        "cache_key": numpy.array(ap.cache_key(mfp, b["ids"], b["choice_ids"])),
        "model": numpy.array(rel(cd.MODEL_DIR)), "model_fingerprint": numpy.array(mfp),
        "code_sha256": numpy.array(code_sha()), "engine_code_sha256": numpy.array(ap.code_sha()),
        "version": numpy.array(VERSION), "made": numpy.array(now()),
    }


# ---------------------------------------------------------------- runs

class ModelRun:
    """Context: Docling check, network guard, lock, engine, run record in daten/cls/it2/runs.jsonl."""

    def __init__(self, name: str, purpose: str, rec: dict):
        self.name, self.purpose = name, purpose
        self.rec = {"run": name, "purpose": purpose, "start": None, "end": None, **rec,
                    "model": rel(cd.MODEL_DIR), "model_fingerprint": ap.model_fingerprint(), "precision": "bf16",
                    "all_layers_run": True, "code_sha256": code_sha(), "engine_code_sha256": ap.code_sha(),
                    "network_guard": True, "documents": [], "documents_done": 0, "documents_skipped_exist": 0,
                    "no_state_length": [], "prompt_tokens": 0, "model_seconds": 0.0}
        self.cm = None
        self.t0 = 0.0

    def __enter__(self):
        if ap.docling_running():
            raise SystemExit(f"a Docling process runs (process rule 7.4): {ap.docling_running()}")
        ap.network_guard()
        self.cm = cd.model_lock(f"m05_cls_it2_states {self.name}: {self.purpose}")
        self.rec["lock"] = self.cm.__enter__()
        self.rec["start"] = now()
        self.t0 = time.perf_counter()
        try:
            self.se = StateEngine()
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise
        self.rec.update(model_load_seconds=self.se.eng.load_s, memory_after_load_gb=self.se.eng.mem_after_load_gb,
                        memory_limits=self.se.eng.limits)
        return self

    def __exit__(self, et, ev, tb):
        try:
            if hasattr(self, "se"):
                self.rec["peak_memory_gb"] = round(self.se.mx.get_peak_memory() / 1e9, 2)
        finally:
            self.cm.__exit__(None, None, None)
            self.rec["end"] = now()
            self.rec["seconds"] = round(time.perf_counter() - self.t0, 1)
            self.rec["model_seconds"] = round(self.rec["model_seconds"], 1)
            if self.rec["prompt_tokens"]:
                self.rec["seconds_per_1k_prompt_tokens"] = round(1000 * self.rec["model_seconds"]
                                                                 / self.rec["prompt_tokens"], 3)
            self.rec["error"] = None if et is None else f"{et.__name__}: {ev}"
            append_run(self.rec)
        return False


def run_items(task: str, kind: str, items: list[dict], variant: str, layers: tuple[int, ...],
              budget_s: float | None, name: str, extra: dict) -> dict:
    allowed = ("validation",) if kind == "validation" else ("dev",)
    cd.assert_allowed(sorted({it["doc_id"] for it in items}), allowed)
    mfp = ap.model_fingerprint()
    od = out_dir(kind, task)
    plan, skip_len, skip_done = [], [], 0
    for it in items:
        if it["n_text_tokens"] > MAX_TEXT_TOKENS:
            skip_len.append(it["state_id"])
            continue
        b = ap.build(task, variant, it["doc_id"], it["text"])
        if is_done(od / f"{it['state_id']}.npz", b["prompt_sha256"], mfp, layers):
            skip_done += 1
            continue
        plan.append((it, b))
    tokens = sum(len(b["ids"]) for _, b in plan)
    print(f"{task} {kind}: {len(plan)} to run, {skip_done} exist, {len(skip_len)} too long, {tokens} prompt tokens, "
          f"estimate {round(tokens / 1000 * SPEED_S_PER_1K / 60)} min", flush=True)
    rec = {"task": task, "kind": kind, "variant": variant, "layers": list(layers), "budget_seconds": budget_s,
           "documents_planned": len(plan), **extra}
    if not plan:
        return rec | {"documents_skipped_exist": skip_done, "no_state_length": skip_len}
    with ModelRun(name, f"{task} {kind} {variant}", rec) as mr:
        mr.rec["documents_skipped_exist"] = skip_done
        mr.rec["no_state_length"] = skip_len
        t_run = time.perf_counter()
        for i, (it, b) in enumerate(plan, start=1):
            if budget_s and time.perf_counter() - t_run > budget_s:
                mr.rec["stopped"] = f"budget of {budget_s} s reached"
                print(mr.rec["stopped"], flush=True)
                break
            r = mr.se.pass_one(b["ids"], b["choice_ids"], layers)
            write_state(od / f"{it['state_id']}.npz", arrays_for(it, task, variant, b, r, layers, mfp))
            mr.rec["documents"].append(it["state_id"])
            mr.rec["documents_done"] += 1
            mr.rec["prompt_tokens"] += len(b["ids"])
            mr.rec["model_seconds"] += r["seconds"]
            if i % DOCLING_CHECK_EVERY == 0:
                if ap.docling_running():
                    raise SystemExit("a Docling process started: run stopped (process rule 7.4); the files "
                                     "written stay, a new run continues")
                el = time.perf_counter() - t_run
                print(f"{task} {kind}: {i}/{len(plan)} documents, {round(el)} s, "
                      f"{round(1000 * mr.rec['model_seconds'] / mr.rec['prompt_tokens'], 2)} s/1k tokens", flush=True)
    return mr.rec


# ---------------------------------------------------------------- check

def cmd_check() -> None:
    numpy = np()
    items = {t: doc_items(t, "dev", ("check",), None, None) for t in CHECK_DOCS}
    sel = {t: [x for x in items[t] if x["doc_id"] in CHECK_DOCS[t]] for t in CHECK_DOCS}
    for t in CHECK_DOCS:
        assert sorted(x["doc_id"] for x in sel[t]) == sorted(CHECK_DOCS[t]), f"{t}: check documents not in dev check"
        cd.assert_allowed(CHECK_DOCS[t], ("dev",))
    mfp = ap.model_fingerprint()
    res = {"made": now(), "version": VERSION, "code_sha256": code_sha(), "engine_code_sha256": ap.code_sha(),
           "model_fingerprint": mfp, "layers": list(LAYERS), "documents": {}}
    all_ok = True
    with ModelRun("check", "states check: determinism, iteration-1 values, speed",
                  {"task": "r1,r2", "kind": "dev", "variant": VARIANT, "layers": list(LAYERS),
                   "documents_planned": sum(len(v) for v in CHECK_DOCS.values()), "passes_per_document": 2}) as mr:
        se = mr.se
        res["model_load_seconds"] = se.eng.load_s
        for task in CHECK_DOCS:
            v = VARIANT[task]
            for it in sel[task]:
                d = it["doc_id"]
                b = ap.build(task, v, d)
                key = ap.cache_key(mfp, b["ids"], b["choice_ids"])
                hit = ap.cache_get(key)
                r1 = se.pass_one(b["ids"], b["choice_ids"], LAYERS)
                r2 = se.pass_one(b["ids"], b["choice_ids"], LAYERS)
                same = {k: bool(numpy.array_equal(r1[k], r2[k])) for k in ("states", "final_norm", "root_logprobs")}
                same["probs"] = r1["probs"] == r2["probs"]
                od = out_dir("dev", task) / f"{d}.npz"
                write_state(od, arrays_for(it, task, v, b, r1, LAYERS, mfp))
                z = read_state(od)
                i32 = list(LAYERS).index(N_LAYERS)
                f16_exact = float((z["states"].astype(numpy.float32) == r1["states"]).mean())
                p_stored, mass_stored = se.readout_from_state(z["states"][i32], b["choice_ids"])
                cache_cmp = None
                if hit is not None:
                    cache_cmp = {
                        "cache_probs": hit["probs"], "cache_mass": hit["mass"],
                        "probs_6dp": [round(x, 6) for x in r1["probs"]], "mass_6dp": round(r1["mass"], 6),
                        "probs_equal_6dp": [round(x, 6) for x in r1["probs"]] == hit["probs"],
                        "mass_equal_6dp": round(r1["mass"], 6) == hit["mass"],
                        "max_abs_diff_probs": max(abs(a - c) for a, c in zip(r1["probs"], hit["probs"])),
                        "cache_prefill_tokens": hit.get("prefill_tokens"), "cache_version": hit.get("version")}
                stored_cmp = {"probs": p_stored, "max_abs_diff_to_pass": max(abs(a - c) for a, c in
                                                                           zip(p_stored, r1["probs"]))}
                ok = all(same.values()) and cache_cmp is not None and cache_cmp["probs_equal_6dp"] \
                    and cache_cmp["mass_equal_6dp"] and stored_cmp["max_abs_diff_to_pass"] < 1e-6
                all_ok &= ok
                n = len(b["ids"])
                res["documents"][f"{task}/{d}"] = {
                    "task": task, "variant": v, "n_prompt_tokens": n,
                    "prefill_chunks": -(-(n - 1) // PREFILL_CHUNK), "prompt_sha256": b["prompt_sha256"],
                    "cache_key": key, "deterministic": same, "iteration1_cache": cache_cmp,
                    "stored_layer32_readout": stored_cmp, "float16_exact_share": f16_exact,
                    "max_abs_state_by_layer": {str(k): float(numpy.abs(r1["states"][j]).max())
                                               for j, k in enumerate(LAYERS)},
                    "max_abs_final_norm": float(numpy.abs(r1["final_norm"]).max()),
                    "seconds_pass1": round(r1["seconds"], 3), "seconds_pass2": round(r2["seconds"], 3),
                    "s_per_1k_pass1": round(1000 * r1["seconds"] / n, 3),
                    "s_per_1k_pass2": round(1000 * r2["seconds"] / n, 3),
                    "file": rel(od), "file_bytes": od.stat().st_size, "ok": ok}
                mr.rec["documents"].append(f"{task}/{d}")
                mr.rec["documents_done"] += 1
                mr.rec["prompt_tokens"] += 2 * n
                mr.rec["model_seconds"] += r1["seconds"] + r2["seconds"]
                print(f"{task} {d}: {n} tokens, {round(r1['seconds'], 1)} s / {round(r2['seconds'], 1)} s, "
                      f"deterministic {all(same.values())}, cache equal "
                      f"{cache_cmp and cache_cmp['probs_equal_6dp'] and cache_cmp['mass_equal_6dp']}, "
                      f"stored diff {stored_cmp['max_abs_diff_to_pass']:.2e}", flush=True)
        res["peak_memory_gb"] = round(se.mx.get_peak_memory() / 1e9, 2)
    docs = res["documents"].values()
    tok = sum(x["n_prompt_tokens"] for x in docs)
    s1 = sum(x["seconds_pass1"] for x in docs)
    s2 = sum(x["seconds_pass2"] for x in docs)
    short = [x for x in docs if x["n_prompt_tokens"] <= 8192]
    res["speed"] = {
        "prompt_tokens_per_pass": tok,
        "s_per_1k_tokens_pass1": round(1000 * s1 / tok, 3), "s_per_1k_tokens_pass2": round(1000 * s2 / tok, 3),
        "s_per_1k_tokens_all_passes": round(1000 * (s1 + s2) / (2 * tok), 3),
        "s_per_1k_tokens_le8192": round(1000 * sum(x["seconds_pass1"] + x["seconds_pass2"] for x in short)
                                        / (2 * sum(x["n_prompt_tokens"] for x in short)), 3),
        "iteration1_reference_s_per_1k": "4.29 to 4.62 (daten/cls/apertus/runs.jsonl, prefill seconds / prefill tokens)",
    }
    res["all_ok"] = all_ok
    res["end"] = now()
    CHECK_FILE.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"all_ok": all_ok, "speed": res["speed"], "peak_memory_gb": res["peak_memory_gb"]}, indent=1))
    print("written", rel(CHECK_FILE))


# ---------------------------------------------------------------- commands

def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["check", "run", "run-texts", "plan"])
    a.add_argument("--task", choices=["r1", "r2"])
    a.add_argument("--split", choices=["dev", "validation"], default="dev")
    a.add_argument("--subset", default="design,check")
    a.add_argument("--ids")
    a.add_argument("--texts")
    a.add_argument("--limit", type=int)
    a.add_argument("--budget-seconds", type=float)
    a.add_argument("--variant")
    a.add_argument("--layers", help="comma list of decoder layers (default: every 2nd layer, 2 to 32)")
    a.add_argument("--allow-validation", action="store_true")
    x = a.parse_args()
    if x.cmd == "check":
        cmd_check()
        return
    if not x.task:
        raise SystemExit("--task is necessary")
    variant = x.variant or VARIANT[x.task]
    assert variant in ap.VARIANTS[x.task], variant
    layers = tuple(sorted({int(k) for k in x.layers.split(",")})) if x.layers else LAYERS
    assert all(1 <= k <= N_LAYERS for k in layers), layers
    subsets = tuple(s.strip() for s in x.subset.split(",") if s.strip())
    assert set(subsets) <= {"design", "check"}, subsets
    if x.split == "validation" and not x.allow_validation:
        raise SystemExit("validation: only the one run after the freeze of the head (flag --allow-validation)")
    extra = {"subsets": list(subsets) if x.split == "dev" else ["validation"], "limit": x.limit,
             "ids_file": x.ids, "ids_file_sha256": sha256_file(Path(x.ids)) if x.ids else None}
    if x.cmd == "run-texts":
        if not x.texts:
            raise SystemExit("--texts is necessary")
        items = text_items(x.task, x.texts)
        extra = {"texts_file": x.texts, "texts_file_sha256": sha256_file(Path(x.texts))}
        kind = "pairs"
    else:
        items = doc_items(x.task, x.split, subsets, x.ids, x.limit)
        kind = "validation" if x.split == "validation" else "dev"
    if x.cmd == "plan":
        n_tok = [it["n_text_tokens"] for it in items]
        ok = [n for n in n_tok if n <= MAX_TEXT_TOKENS]
        first = next((it for it in items if it["n_text_tokens"] <= MAX_TEXT_TOKENS), None)
        over = (len(ap.build(x.task, variant, first["doc_id"], first["text"])["ids"]) - first["n_text_tokens"]
                if first else 0)                       # prompt tokens that are not document text
        tot = sum(ok) + over * len(ok)
        print(json.dumps({"task": x.task, "kind": kind, "documents": len(items), "too_long": len(n_tok) - len(ok),
                          "text_tokens": sum(ok), "prompt_overhead_tokens_per_document": over,
                          "prompt_tokens_estimate": tot, "estimate_hours": round(tot / 1000 * SPEED_S_PER_1K / 3600, 2),
                          "s_per_1k_used": SPEED_S_PER_1K}, indent=1))
        return
    name = f"{x.cmd}-{x.task}-{kind}-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    rec = run_items(x.task, kind, items, variant, layers, x.budget_seconds, name, extra)
    print(json.dumps({k: rec.get(k) for k in ("run", "documents_done", "documents_skipped_exist", "prompt_tokens",
                                              "model_seconds", "seconds_per_1k_prompt_tokens", "stopped")}
                     | {"no_state_length": len(rec.get("no_state_length", []))}, indent=1))


if __name__ == "__main__":
    main()
