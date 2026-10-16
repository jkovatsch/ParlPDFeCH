#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the Apertus read-out (states) of one block file, as a subprocess.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude
Opus 5.5), 15./16.10.2026, for the main agent of session ad54858c.

Task
  The value heads (daten/gj_values/heads2/heads2.npz) read the hidden state of Apertus-v1.5-8B (text branch, bf16)
  after decoder layer 20 at the last token of each question (suffix) of the template gj_values_v1_de. This file
  makes these states for ONE block file and writes them as one npz file with the keys of the stored states of the
  fixed run (daten/gj/states/values_dev/states/<id>.npz, keys m10_vm_states.NPZ_KEYS). It writes no document text.

  It is a subprocess of the worker (worker/apertus_provider.py starts it), so that the 16 GB model leaves the
  memory of the computer when the process ends, and so that the worker process never imports torch or MLX.

The recipe (the same as the fixed run of 13.10.2026; not changed)
  - prompt texts: m11_prompts_values.item(block file, "all") (prefix = all blocks of the document, rule E18; the
    suffixes Q0, Q1 and one Q2.B<n> for each block);
  - token ids: m10_vm_states.tokenize_item with the Hugging Face tokenizer of the model folder (never the MLX
    tokenizer wrapper, never apply_chat_template); the token checks of the fixed run (one BOS, no BOS in a suffix,
    no empty suffix, at most 32,768 prefix tokens with no cut);
  - passes: prefill of the prefix in chunks of 2,048 tokens into one cache, one forward pass for each suffix on the
    cache, the cache is cut back to the prefix after each pass; batch 1;
  - read-out: the residual stream after decoder layer k (before the final norm) at the last suffix token, for the
    layers 8, 12, ..., 32; float16 with a finite check (m10_vm_states.to_f16).

Backends (the interface: class Backend)
  A backend is a function from the prompt texts of one document (an item of m11_prompts_values.item: prefix and
  suffixes) to the float16 states of the asked layers (layer 20 is the layer of the heads), plus its name, the
  model fingerprint and the library versions. The callers (cmd_run here, and a service on a GPU computer) use only
  this interface:

      b = open_backend(name, model_dir)     # no model load; b.describe() has name, fingerprint, versions
      b.load()                              # loads the model (seconds, memory)
      r = b.readout(item, layers)           # dict: suffix_ids, layers, states float16 [n, len(layers), 4096], ...
      b.close()

  mlx   Apple silicon, MLX (mlx-lm 0.32.0): a manual loop over the decoder layers of mlx_lm, as the scout script of
        15.10.2026 (the closest result to the H100 states: 19 of 20 Apertus values equal). Memory limits of MLX as
        in every MLX run of the project since 04.10.2026: wired 10 GiB, memory 27 GiB, cache 1 GiB.
  cuda  NVIDIA GPU, torch CUDA bf16: the frozen engine of the fixed run (m10_vm_states.Engine, sdpa with cuDNN
        attention off, no TF32), as on the H100 of the fixed run.
  mps   Apple silicon without MLX: the same frozen engine on torch MPS (device_map 'mps').
  cpu   torch CPU bf16: the same frozen engine. Very slow. Only when forced (APERTUS_BACKEND=cpu), for checks.
  remote  a GPU of another computer (worker/apertus_backend_remote.py, the client of the read-out service
        worker/apertus_serve.py, 'make serve-apertus'): the first choice of 'auto' when APERTUS_URL is set.
  A file apertus_backend_<name>.py in the folder of this file can add a backend (function register(api), which
  calls api.register_backend). Such a backend can also be the first choice of 'auto' (argument auto_when).

  The choice 'auto': a registered backend whose auto_when is true; else mlx, cuda, mps (the first that is
  available). The choice 'auto' never takes the CPU. With no GPU, 'auto' stops with the reason no_gpu and a text
  that names the 2 ways out: a GPU in the cloud (docs/apertus-gpu.md) or APERTUS=0 (code rules only).

Tested: only on one Mac (Apple M4, 32 GB, macOS), 15./16.10.2026: mlx, mps and cpu. cuda, Linux and Windows are
NOT tested (no such computer on that night). On Windows, m10_vm_states imports fcntl; this file puts an empty
module fcntl in its place (the engine does not call it).

Commands (python -I: the file puts ROOT/src at the start of the module search path itself)
  python -I -B apertus_states.py run   --root ROOT --block-file F --model-dir D --out NPZ --record JSON
                                       [--backend auto|mlx|cuda|mps|cpu] [--layers 8,12,16,20,24,28,32]
  python -I -B apertus_states.py check --root ROOT --model-dir D [--backend auto|...]
  ROOT is a folder with the converter files below src/ (the scratch root of the worker, or app/layout/).
  'check' loads no model: it prints one JSON line (backend, reason, message, fingerprint, memory) for
  'make setup-apertus' and 'make convert'.

Environment: APERTUS_MEMORY_CHECK=0 switches the memory check off (the record says so). The file sets
HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 for the local backends, and for torch MPS
PYTORCH_MPS_HIGH_WATERMARK_RATIO=1.0 with PYTORCH_MPS_LOW_WATERMARK_RATIO=0.9 (torch 2.14.1 stops without the low
ratio), and it removes PYTORCH_ENABLE_MPS_FALLBACK (no silent CPU fallback).

Exit codes (the record JSON always has the key 'exit' with the reason)
  0 ok; 1 error; 3 input refused (prefix_too_long, token_problems, template_differs, block_file_bad);
  4 model_absent, fingerprint_differs; 5 no_gpu, backend_absent; 6 memory_too_small (the computer or the GPU has
  less memory in total than the model needs: a Mac below 32 GB, an NVIDIA GPU below 20 GiB), memory_low (too
  little memory is free now); 7 not_finite; 8 reserved for the reasons of a remote backend (for example
  remote_unreachable, remote_busy).
  No message of this file holds the value of APERTUS_TOKEN (function scrub: a second guard after the token check
  of the backend remote).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import time
import types
from pathlib import Path

VERSION = "m12-apertus-states-1"
MODEL_NAME = "swiss-ai/Apertus-v1.5-8B, text branch, bf16"
WANT_FP = "apertus-v1.5-8b-text-bf16:c10cd28db5bd3adf6043a5047a1435dedc5c3e55c45d5abc2ca82baf2a7786c3"
TEMPLATE_ID = "gj_values_v1_de"
TEMPLATE_SHA256 = "54abf49ab788b2779b7bd00d8ebfb99abb3daf0fbe076e274fec30851dca81f6"   # m11_value_heads2_data
HEADS_LAYER = 20
# The 4 converter files that build the prompt texts (frozen since the fixed run of 13.10.2026). The template
# record (m11_prompts_values.template) also hashes the chat template file of the model folder below the root;
# a scratch root has no such file, so the check is the SHA-256 of the code that makes the texts.
PROMPT_CODE_SHA256 = {
    "src/m11_prompts_values.py": "c32896531bb8ee6f361171201a33b8336338a16da3d01a20301cc790da5723e9",
    "src/m10_prompts.py": "afa15e27806eb32dbf92f8e40886193f7cba598684de39e80229edae00c8b6e8",
    "src/m05_cls_apertus.py": "f3677338ec95a2c53ad0254655cc4438d15ac722e3b446769f5ff3498191a8a2",
    "src/m05_cls_data.py": "88a0207465bd6e6d704a82b138752a1e0caf0059cb7f8795040582fee1ebe4ae",
}
CHAT_TEMPLATE_REL = "daten/modelle/apertus-v1.5-8b-text-bf16/chat_template.jinja"
HIDDEN = 4096
# MLX memory limits (GiB) of src/m04_kern.py (kernel panic of the GPU driver on 04.10.2026).
MLX_LIMITS_GIB = {"wired": 10.0, "memory": 27.0, "cache": 1.0}
# Memory rules before a load (bytes). The model needs 16.1 GB; the peak of the measured runs was 17.2 to 18.7 GB.
MIN_RAM_TOTAL_APPLE = 32 * 1024 ** 3        # a Mac with less memory cannot hold the model and the system
MIN_FREE_BYTES = 18 * 10 ** 9               # free memory before the load (Apple, Linux CPU, Windows)
MIN_VRAM_TOTAL = 20 * 1024 ** 3             # an NVIDIA GPU with 24 GB passes, one with 16 GB does not
MIN_VRAM_FREE = 18 * 10 ** 9
AUTO_ORDER = ("mlx", "cuda", "mps")         # the choice 'auto' never takes the CPU
LOCAL_BACKENDS = ("mlx", "cuda", "mps", "cpu")
GPU_DOC = "docs/apertus-gpu.md"
WAYS_OUT = (f"Use a GPU in the cloud (see {GPU_DOC}), or APERTUS=0 for code rules only.")
EXIT_CODES = {"ok": 0, "error": 1, "prefix_too_long": 3, "token_problems": 3, "template_differs": 3,
              "block_file_bad": 3, "model_absent": 4, "fingerprint_differs": 4, "no_gpu": 5, "backend_absent": 5,
              "memory_too_small": 6, "memory_low": 6, "not_finite": 7}
REMOTE_EXIT = 8
HERE = Path(__file__).resolve().parent


class Refused(Exception):
    """A stop with a reason code (the key 'exit' of the record) and a text for the user."""

    def __init__(self, code: str, message: str, exit_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = EXIT_CODES.get(code, REMOTE_EXIT) if exit_code is None else exit_code


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def scrub(text) -> str:
    """The text with each copy of the value of APERTUS_TOKEN replaced by <APERTUS_TOKEN>. No code path of the
    read-out puts the token in a message (the backend remote checks it before any request); this is a second guard
    for each message, record and JSON line of this file."""
    out = str(text if text is not None else "")
    raw = os.environ.get("APERTUS_TOKEN") or ""
    for t in sorted({raw, raw.strip(), json.dumps(raw.strip())[1:-1]}, key=len, reverse=True):
        if len(t) >= 8 and t in out:
            out = out.replace(t, "<APERTUS_TOKEN>")
    return out


def log(msg: str) -> None:
    """A progress line on standard output (numbers only, never document text)."""
    print(f"[{now()}] {scrub(msg)}", flush=True)


# ---------------------------------------------------------------------------------------------- converter modules

def converter_modules(root: Path):
    """(m10_vm_states, m11_prompts_values) of ROOT/src. Windows: an empty module fcntl first (the frozen
    m10_vm_states imports it at the top; the engine does not call it)."""
    src = str(Path(root).resolve() / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    if sys.platform == "win32":
        sys.modules.setdefault("fcntl", types.ModuleType("fcntl"))
    import m10_vm_states as vm  # noqa: PLC0415
    import m11_prompts_values as pv  # noqa: PLC0415
    return vm, pv


def check_block_doc(root: Path, doc: dict) -> None:
    """The block file must give each block text from its spans (m10_docs.check_doc), and each block needs an id
    B<n>. A block file of another form gives other prompts than the fit."""
    import m10_docs as docs  # noqa: PLC0415  (ROOT/src is in the search path)
    try:
        docs.check_doc(doc)
    except (KeyError, TypeError, ValueError) as e:
        raise Refused("block_file_bad", f"the block file is not in the form of the converter ({str(e)[:120]})") from e
    if any(not re.fullmatch(r"B[0-9]{1,5}", str(b.get("block", ""))) for b in doc["blocks"]):
        raise Refused("block_file_bad", "a block of the block file has no id B<n>")


def template_check(root: Path, pv, vm) -> dict:
    """The prompt texts must be those of the template of the heads (gj_values_v1_de, 54abf49a...). The 4 code files
    that make them must have their pinned SHA-256. If the chat template file of the template record is below the
    root (the project folder), the template SHA-256 itself is computed and compared too."""
    root = Path(root)
    bad = [p for p, want in PROMPT_CODE_SHA256.items() if not (root / p).is_file() or sha256_file(root / p) != want]
    if bad:
        raise Refused("template_differs", f"the prompt code differs from the code of the heads: {', '.join(bad)}")
    if not (root / CHAT_TEMPLATE_REL).is_file():
        return {"check": "SHA-256 of the 4 prompt code files", "template_json_sha256": "not computed"}
    t = pv.template()
    if t["template_id"] != TEMPLATE_ID or t["sha256"] != TEMPLATE_SHA256:
        raise Refused("template_differs", f"the template of the converter is {t['template_id']} {t['sha256'][:12]}, "
                                          f"not {TEMPLATE_ID} {TEMPLATE_SHA256[:12]} (the template of the heads)")
    return {"check": "SHA-256 of the 4 prompt code files and of the template record",
            "template_json_sha256": vm.sha256_json(t)}


def prepare_item(root: Path, doc: dict) -> dict:
    """The prompt texts of one document (m11_prompts_values.item with all blocks) after the checks of the template
    and of the suffix ids: Q0, Q1, then one Q2.B<n> for every block (also a block with no text)."""
    vm, pv = converter_modules(root)
    check_block_doc(root, doc)
    tc = template_check(root, pv, vm)
    x = pv.item(doc, "all")
    want = ["Q0", "Q1"] + [f"Q2.{b['block']}" for b in doc["blocks"]]
    if [s["id"] for s in x["suffixes"]] != want:
        raise Refused("block_file_bad", "the suffix ids are not Q0, Q1 and one Q2.B<n> for each block")
    x["template_id"], x["template_sha256"] = TEMPLATE_ID, TEMPLATE_SHA256
    x["template_json_sha256"] = tc["template_json_sha256"]
    x["template_check"] = tc["check"]
    x["prefix_text_sha256"] = vm.sha256_text(x["prefix"])
    x["suffix_text_sha256"] = [vm.sha256_text(s["text"]) for s in x["suffixes"]]
    return x


# ---------------------------------------------------------------------------------------------- memory

def _memory_pressure_free_percent() -> int | None:
    try:
        out = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", out)
    return int(m.group(1)) if m else None


def _darwin_memsize() -> int | None:
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=10).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _linux_meminfo() -> dict:
    out = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            if v.strip().endswith("kB"):
                out[k] = int(v.split()[0]) * 1024
    except OSError:
        pass
    return out


def _windows_memory() -> dict:
    import ctypes  # noqa: PLC0415

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    s = MS()
    s.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))  # type: ignore[attr-defined]
    return {"total": int(s.ullTotalPhys), "available": int(s.ullAvailPhys)}


def memory_facts(backend: str) -> dict:
    """The memory figures that the rule of memory_check reads (no model is loaded)."""
    f = {"time": now(), "platform": sys.platform}
    if backend == "cuda":
        import torch  # noqa: PLC0415
        free_b, total_b = torch.cuda.mem_get_info(0)
        f.update(kind="cuda", total_bytes=int(total_b), free_bytes=int(free_b))
    elif sys.platform == "darwin":
        total = _darwin_memsize()
        pct = _memory_pressure_free_percent()
        f.update(kind="memory_pressure", total_bytes=total, free_percent=pct,
                 free_bytes=int(pct / 100 * total) if (pct is not None and total) else None)
    elif sys.platform.startswith("linux"):
        mi = _linux_meminfo()
        f.update(kind="proc_meminfo", total_bytes=mi.get("MemTotal"), free_bytes=mi.get("MemAvailable"))
    elif sys.platform == "win32":
        try:
            w = _windows_memory()
            f.update(kind="GlobalMemoryStatusEx", total_bytes=w["total"], free_bytes=w["available"])
        except Exception as e:  # noqa: BLE001
            f.update(kind="unknown", error=str(e)[:100])
    else:
        f["kind"] = "unknown"
    return f


def memory_check(backend: str) -> dict:
    """Stop before a load that does not fit (exit 6): memory_too_small if the computer (a Mac) or the NVIDIA GPU
    has less memory in total than the model needs (a fact of the computer: setup-apertus stops for it), memory_low
    if too little memory is free now (close other programs and try again). APERTUS_MEMORY_CHECK=0 switches it off."""
    f = memory_facts(backend)
    if os.environ.get("APERTUS_MEMORY_CHECK") == "0":
        f["check"] = "off (APERTUS_MEMORY_CHECK=0)"
        return f
    gb = lambda b: f"{b / 1e9:.1f} GB" if b else "unknown"  # noqa: E731
    total, free = f.get("total_bytes"), f.get("free_bytes")
    if backend == "cuda":
        if total is None or total < MIN_VRAM_TOTAL:
            raise Refused("memory_too_small", f"the NVIDIA GPU has {gb(total)} memory; Apertus bf16 needs a GPU "
                                              f"with 24 GB. {WAYS_OUT}")
        if free is None or free < MIN_VRAM_FREE:
            raise Refused("memory_low", f"the NVIDIA GPU has {gb(total)} memory, {gb(free)} free; Apertus bf16 "
                                        f"needs {MIN_VRAM_FREE / 1e9:.0f} GB free (end other programs on the GPU and "
                                        f"try again). {WAYS_OUT}")
    else:
        if sys.platform == "darwin" and backend in ("mlx", "mps") and (total or 0) < MIN_RAM_TOTAL_APPLE:
            raise Refused("memory_too_small", f"this Mac has {gb(total)} memory; Apertus bf16 needs a Mac with "
                                              f"32 GB. {WAYS_OUT}")
        if free is not None and free < MIN_FREE_BYTES:
            raise Refused("memory_low", f"only {gb(free)} of memory are free now; Apertus bf16 needs "
                                        f"{MIN_FREE_BYTES / 1e9:.0f} GB free (close other programs and try again). "
                                        f"{WAYS_OUT}")
    f["check"] = "pass"
    return f


# ---------------------------------------------------------------------------------------------- backend registry

def _have(*mods: str) -> list[str]:
    """The names of the modules that are absent."""
    out = []
    for m in mods:
        try:
            if importlib.util.find_spec(m) is None:
                out.append(m)
        except (ImportError, ValueError):
            out.append(m)
    return out


def probe_mlx() -> dict:
    if sys.platform != "darwin" or platform.machine() != "arm64":
        return {"available": False, "why": "not a Mac with Apple silicon"}
    absent = _have("mlx", "mlx_lm", "transformers", "tokenizers", "numpy")
    if absent:
        return {"available": False, "why": f"Python package absent: {', '.join(absent)} (make setup-apertus)"}
    try:
        import mlx.core as mx  # noqa: PLC0415
        ok = bool(mx.metal.is_available())
    except Exception as e:  # noqa: BLE001
        return {"available": False, "why": f"mlx does not start ({type(e).__name__})"}
    return {"available": ok, "why": None if ok else "MLX finds no Metal GPU", "device": "metal"}


def _torch_probe() -> tuple[object | None, str | None]:
    absent = _have("torch", "transformers", "tokenizers", "numpy")
    if absent:
        return None, f"Python package absent: {', '.join(absent)} (make setup-pdf)"
    try:
        import torch  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return None, f"torch does not start ({type(e).__name__})"
    return torch, None


def probe_cuda() -> dict:
    torch, why = _torch_probe()
    if torch is None:
        return {"available": False, "why": why}
    if not torch.cuda.is_available():
        return {"available": False, "why": "torch finds no NVIDIA GPU (CUDA)"}
    try:
        props = torch.cuda.get_device_properties(0)
        total, name, bf16 = int(props.total_memory), str(props.name), bool(torch.cuda.is_bf16_supported())
    except Exception as e:  # noqa: BLE001
        return {"available": False, "why": f"CUDA device 0 does not answer ({type(e).__name__})"}
    if not bf16:
        return {"available": False, "why": f"the GPU {name} has no bf16", "gpu": name}
    if total < MIN_VRAM_TOTAL:
        return {"available": False, "why": f"the GPU {name} has {total / 1e9:.1f} GB; Apertus bf16 needs 24 GB",
                "gpu": name}
    return {"available": True, "why": None, "device": "cuda:0", "gpu": name, "total_bytes": total,
            "cuda": torch.version.cuda}


def probe_mps() -> dict:
    if sys.platform != "darwin":
        return {"available": False, "why": "not a Mac"}
    torch, why = _torch_probe()
    if torch is None:
        return {"available": False, "why": why}
    if not torch.backends.mps.is_available():
        return {"available": False, "why": "torch finds no MPS device"}
    return {"available": True, "why": None, "device": "mps"}


def probe_cpu() -> dict:
    torch, why = _torch_probe()
    if torch is None:
        return {"available": False, "why": why}
    return {"available": True, "why": None, "device": "cpu",
            "note": "torch CPU bf16 is very slow (many minutes for one page); use it only for checks"}


# name -> {"probe": callable() -> dict, "open": callable(model_dir, facts) -> Backend, "auto_when": callable(env)}
BACKENDS: dict[str, dict] = {}


def register_backend(name: str, probe, opener, auto_when=None) -> None:
    """Add a backend (for example 'remote' of a file apertus_backend_remote.py). auto_when(env) -> bool: the
    choice 'auto' takes this backend first when it is true (for example when APERTUS_URL is set)."""
    BACKENDS[name] = {"probe": probe, "open": opener, "auto_when": auto_when}


def load_extra_backends() -> list[str]:
    """Each file apertus_backend_<name>.py in the folder of this file: its function register(api) is called with
    this module as api. The files are imported from this folder only."""
    done = []
    me = sys.modules[__name__]
    for p in sorted(HERE.glob("apertus_backend_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "register"):
            mod.register(me)
            done.append(p.stem)
    return done


def choose_backend(requested: str, env=None) -> tuple[str, dict]:
    """(backend name, facts of each probe). 'auto': a registered backend with auto_when true, else the first
    available of mlx, cuda, mps; never cpu. A forced backend that is not available: backend_absent."""
    env = os.environ if env is None else env
    tests: dict[str, dict] = {}
    if requested == "auto":
        for name, b in BACKENDS.items():
            if b.get("auto_when") and b["auto_when"](env):
                tests[name] = b["probe"]()
                if tests[name].get("available"):
                    return name, tests
                # a probe can give its own reason code (for example remote_unreachable of the backend remote)
                raise Refused(tests[name].get("code") or "backend_absent",
                              f"backend {name}: {tests[name].get('why')}. {WAYS_OUT}", tests[name].get("exit_code"))
        for name in AUTO_ORDER:
            tests[name] = BACKENDS[name]["probe"]()
            if tests[name]["available"]:
                return name, tests
        whys = "; ".join(f"{n}: {tests[n]['why']}" for n in AUTO_ORDER)
        raise Refused("no_gpu", f"no GPU for Apertus on this computer ({whys}). {WAYS_OUT} "
                                f"APERTUS_BACKEND=cpu forces the CPU (very slow, for checks only).")
    if requested not in BACKENDS:
        raise Refused("backend_absent", f"APERTUS_BACKEND={requested}: not one of auto, {', '.join(BACKENDS)}")
    tests[requested] = BACKENDS[requested]["probe"]()
    if not tests[requested].get("available"):
        raise Refused(tests[requested].get("code") or "backend_absent",
                      f"APERTUS_BACKEND={requested}: not available on this computer "
                      f"({tests[requested].get('why')}). {WAYS_OUT}", tests[requested].get("exit_code"))
    return requested, tests


def open_backend(name: str, model_dir: Path | None, root: Path, facts: dict | None = None) -> "Backend":
    return BACKENDS[name]["open"](model_dir, root, facts or {})


def local_environment(backend: str) -> None:
    """The environment of a local backend, set before torch or MLX is imported."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    if backend == "mps":
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "1.0"
        os.environ["PYTORCH_MPS_LOW_WATERMARK_RATIO"] = "0.9"
        os.environ.pop("PYTORCH_ENABLE_MPS_FALLBACK", None)


# ---------------------------------------------------------------------------------------------- backends

class Backend:
    """The interface. readout(item, layers) -> dict (a backend may give a part of the asked layers; the layer 20 of
    the heads must be in it):
      suffix_ids [str], layers [int], states float16 [n, len(layers), 4096] (finite), letter_logprobs float32
      [n, 6] or None, n_prefix_tokens int, n_suffix_tokens [int], prefix_tokens_sha256, suffix_tokens_sha256 [str],
      boundary_equal_first_suffix bool or None, timing {prefill_seconds, suffix_seconds, seconds}, peak_bytes,
      peak_kind.
    describe() -> dict: backend, device, dtype, attn, sdpa, versions, model_fingerprint, model (no user path)."""

    name = "none"
    remote = False

    def describe(self) -> dict:
        raise NotImplementedError

    def load(self) -> dict:
        raise NotImplementedError

    def readout(self, item: dict, layers: tuple[int, ...]) -> dict:
        raise NotImplementedError

    def close(self) -> None:
        return None


class LocalBackend(Backend):
    """The common part of the local backends: model folder, fingerprint, tokenizer and token checks."""

    def __init__(self, model_dir: Path | None, root: Path, facts: dict):
        if model_dir is None or not (Path(model_dir) / "config.json").is_file():
            raise Refused("model_absent", f"no model folder with config.json at {model_dir}: run 'make setup-apertus'")
        self.model_dir = Path(model_dir)
        self.root = Path(root)
        self.facts = dict(facts)
        self.vm, self.pv = converter_modules(root)
        self.fp = self.vm.model_fingerprint(self.model_dir)
        self.tok = None

    def tokenizer(self):
        if self.tok is None:
            from transformers import AutoTokenizer  # noqa: PLC0415
            self.tok = AutoTokenizer.from_pretrained(str(self.model_dir))
            if self.vm.letter_ids(self.tok) != list(self.vm.APERTUS_LETTER_IDS):
                raise Refused("token_problems", "the letter tokens of the tokenizer are not those of Apertus")
        return self.tok

    def tokens(self, item: dict) -> dict:
        """Token ids with the one rule of the fixed run, and the checks before any pass."""
        vm, tok = self.vm, self.tokenizer()
        pre, suf = vm.tokenize_item(tok, item)
        probs = vm.token_problems(tok, pre, suf)
        if probs:
            raise Refused("token_problems", f"token check: {'; '.join(probs)}")
        if len(pre) > vm.MAX_PREFIX_TOKENS:
            raise Refused("prefix_too_long", f"the document has {len(pre)} prefix tokens; the limit is "
                                             f"{vm.MAX_PREFIX_TOKENS} (rule E18: no cut, no states)")
        joint = [int(i) for i in tok(item["prefix"] + item["suffixes"][0]["text"], add_special_tokens=False)["input_ids"]]
        return {"pre": pre, "suf": suf, "boundary_equal": joint == pre + suf[0]}

    def versions(self) -> dict:
        from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415
        out = {"python": sys.version.split()[0]}
        for p in ("torch", "transformers", "tokenizers", "numpy", "mlx", "mlx-lm", "accelerate"):
            try:
                out[p] = version(p)
            except PackageNotFoundError:
                out[p] = None
        return out

    def check_layers(self, layers) -> tuple[int, ...]:
        layers = tuple(int(k) for k in layers)
        if not layers or any(k not in self.vm.DEFAULT_LAYERS for k in layers):
            raise Refused("error", f"layers {list(layers)}: each must be one of {list(self.vm.DEFAULT_LAYERS)}")
        return layers

    def result(self, item, tk, states, lets, layers, t_pre, t_suf, t_all, peak, peak_kind) -> dict:
        vm = self.vm
        idx = [vm.DEFAULT_LAYERS.index(k) for k in layers]
        try:
            s16 = vm.to_f16(states[:, idx, :], str(item["doc_id"]))
        except FloatingPointError as e:
            raise Refused("not_finite", str(e)[:200]) from e
        return {"suffix_ids": [s["id"] for s in item["suffixes"]], "layers": list(layers), "states": s16,
                "letter_logprobs": lets, "n_prefix_tokens": len(tk["pre"]),
                "n_suffix_tokens": [len(s) for s in tk["suf"]],
                "prefix_tokens_sha256": vm.sha256_json(tk["pre"]),
                "suffix_tokens_sha256": [vm.sha256_json(s) for s in tk["suf"]],
                "boundary_equal_first_suffix": bool(tk["boundary_equal"]),
                "timing": {"prefill_seconds": round(t_pre, 3), "suffix_seconds": round(t_suf, 3),
                           "seconds": round(t_all, 3)},
                "peak_bytes": peak, "peak_kind": peak_kind}


class TorchBackend(LocalBackend):
    """cuda, mps, cpu: the frozen engine of the fixed run (m10_vm_states.Engine), batch 1."""

    def __init__(self, model_dir, root, facts, device_kind: str):
        super().__init__(model_dir, root, facts)
        self.name = device_kind
        self.device = {"cuda": "cuda:0", "mps": "mps", "cpu": "cpu"}[device_kind]
        self.model = self.eng = None
        self.torch = None

    def describe(self) -> dict:
        return {"backend": self.name, "device": self.device, "dtype": "bfloat16", "attn": "sdpa",
                "sdpa": {"cuda": "no-cudnn", "mps": "mps-default", "cpu": "cpu-default"}[self.name],
                "versions": self.versions(), "model_fingerprint": self.fp, "model": self.model_dir.name,
                "engine": "m10_vm_states.Engine (frozen engine of the fixed run)"}

    def load(self) -> dict:
        local_environment(self.name)
        import torch  # noqa: PLC0415
        from transformers import AutoModelForCausalLM  # noqa: PLC0415
        self.torch = torch
        self.tokenizer()
        if self.name == "cuda":
            # the settings of the fixed run (m10_vm_states.cmd_run): no TF32, cuDNN attention off
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            self.vm.set_sdpa(torch, "no-cudnn")
        t0 = time.time()
        kw = {"dtype": torch.bfloat16, "attn_implementation": "sdpa"}
        if self.name in ("cuda", "mps"):
            kw["device_map"] = self.device      # loads each tensor to the device (no full copy on the CPU first)
        model = AutoModelForCausalLM.from_pretrained(str(self.model_dir), **kw)
        model.eval()
        devs = sorted({str(p.device) for p in model.parameters()})
        dts = sorted({str(p.dtype) for p in model.parameters()})
        want = {"cuda": "cuda", "mps": "mps", "cpu": "cpu"}[self.name]
        if any(not d.startswith(want) for d in devs) or dts != ["torch.bfloat16"]:
            raise Refused("error", f"the parameters are on {devs} in {dts}, not all on {want} in bf16")
        if model.config.num_hidden_layers != self.vm.APERTUS_N_LAYERS or model.config.hidden_size != HIDDEN:
            raise Refused("error", "the model does not have 32 layers and the hidden size 4096")
        self.model = model
        self.eng = self.vm.Engine(model, self.tok, self.vm.DEFAULT_LAYERS, self.device)
        out = {"load_seconds": round(time.time() - t0, 2), "attn_implementation": model.config._attn_implementation,
               "parameter_devices": devs}
        if self.name == "mps":
            out["mps_driver_allocated_bytes"] = int(torch.mps.driver_allocated_memory())
        if self.name == "cuda":
            torch.cuda.reset_peak_memory_stats()
        return out

    def _peak_now(self) -> int | None:
        torch = self.torch
        if self.name == "mps":
            return int(torch.mps.driver_allocated_memory())
        if self.name == "cuda":
            return int(torch.cuda.max_memory_allocated())
        try:
            import resource  # noqa: PLC0415  (not on Windows)
        except ImportError:
            return None
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss if sys.platform == "darwin" else rss * 1024)

    def _sync(self) -> None:
        if self.name == "mps":
            self.torch.mps.synchronize()
        elif self.name == "cuda":
            self.torch.cuda.synchronize()

    def readout(self, item: dict, layers=None) -> dict:
        import numpy as np  # noqa: PLC0415
        layers = self.check_layers(layers or self.vm.DEFAULT_LAYERS)
        tk = self.tokens(item)
        pre, suf = tk["pre"], tk["suf"]
        eng, torch = self.eng, self.torch
        n = len(suf)
        states = np.zeros((n, len(eng.layers), HIDDEN), dtype=np.float32)
        lets = np.zeros((n, len(self.vm.LETTERS)), dtype=np.float32)
        peak = self._peak_now()
        t_all = time.time()
        with torch.inference_mode():
            cache = eng.new_cache()
            t1 = time.time()
            eng.prefill(cache, pre)
            self._sync()
            t_pre = time.time() - t1
            peak = max(peak or 0, self._peak_now() or 0)
            t2 = time.time()
            for j in range(n):
                st, lt = eng.suffix_pass(cache, [suf[j]])
                eng.crop(cache, len(pre))
                states[j], lets[j] = st[0], lt[0]
                if self.name == "mps":
                    peak = max(peak, self._peak_now() or 0)
                if (j + 1) % 25 == 0:
                    log(f"{self.name}: {j + 1} of {n} passes")
            t_suf = time.time() - t2
            del cache
        peak = max(peak or 0, self._peak_now() or 0)
        kind = {"mps": "torch.mps.driver_allocated_memory", "cuda": "torch.cuda.max_memory_allocated",
                "cpu": "ru_maxrss"}[self.name]
        if self.name == "mps":
            torch.mps.empty_cache()
        return self.result(item, tk, states, lets, layers, t_pre, t_suf, time.time() - t_all, peak, kind)

    def close(self) -> None:
        if self.eng is not None:
            self.eng.close()
        self.eng = self.model = None


class MlxBackend(LocalBackend):
    """mlx: a port of the scout script mlx_states.py of 15.10.2026 (no change of the math)."""

    name = "mlx"

    def __init__(self, model_dir, root, facts):
        super().__init__(model_dir, root, facts)
        self.model = None

    def describe(self) -> dict:
        return {"backend": "mlx", "device": "metal", "dtype": "bfloat16", "attn": "mlx-fast-sdpa", "sdpa": "mlx",
                "versions": self.versions(), "model_fingerprint": self.fp, "model": self.model_dir.name,
                "engine": "mlx_lm model with a manual loop over the decoder layers (residual stream after layer k)",
                "mlx_limits_gib": MLX_LIMITS_GIB}

    def load(self) -> dict:
        local_environment("mlx")
        import mlx.core as mx  # noqa: PLC0415
        import mlx_lm  # noqa: PLC0415
        import mlx_lm.generate as generate  # noqa: PLC0415
        from mlx_lm.models.base import create_attention_mask  # noqa: PLC0415
        from mlx_lm.models.cache import make_prompt_cache, trim_prompt_cache  # noqa: PLC0415
        self.tokenizer()
        gib = 1024 ** 3
        mx.set_wired_limit(int(MLX_LIMITS_GIB["wired"] * gib))
        mx.set_memory_limit(int(MLX_LIMITS_GIB["memory"] * gib))
        mx.set_cache_limit(int(MLX_LIMITS_GIB["cache"] * gib))
        # mlx-lm raises the wired limit again in these 2 places (src/m04_kern.speicher_begrenzen): no effect
        mods = [generate]
        try:
            import mlx_lm.tuner.trainer as trainer  # noqa: PLC0415
            mods.append(trainer)
        except Exception:  # noqa: BLE001  (the trainer is not needed for a read-out)
            pass
        for m in mods:
            if hasattr(m, "maybe_set_recommended_wired_limit"):
                m.maybe_set_recommended_wired_limit = lambda *a, **k: None
        self.mx, self.mask_of, self.make_cache, self.trim = mx, create_attention_mask, make_prompt_cache, trim_prompt_cache
        t0 = time.time()
        model, _ = mlx_lm.load(str(self.model_dir))
        model.eval()
        mx.eval(model.parameters())
        self.model = model
        self.inner = model.model
        self.letter_ix = mx.array(self.vm.letter_ids(self.tok))
        return {"load_seconds": round(time.time() - t0, 2), "mlx_active_after_load_bytes": int(mx.get_active_memory())}

    def _head(self, h):
        m = self.model
        return m.lm_head(h) if hasattr(m, "lm_head") else self.inner.embed_tokens.as_linear(h)

    def _prefill(self, cache, ids) -> None:
        mx, chunk = self.mx, self.vm.PREFILL_CHUNK
        for s in range(0, len(ids), chunk):
            self.inner(mx.array([ids[s:s + chunk]]), cache=cache)
            mx.eval([c.state for c in cache])
        if cache[0].offset != len(ids):
            raise Refused("error", f"MLX cache offset {cache[0].offset} != {len(ids)}")

    def _suffix_pass(self, cache, suf):
        import numpy as np  # noqa: PLC0415
        mx, inner, layers = self.mx, self.inner, self.vm.DEFAULT_LAYERS
        x = inner.embed_tokens(mx.array([suf]))
        mask = self.mask_of(x, cache[0])
        keep = {}
        k = 0
        for k, (layer, c) in enumerate(zip(inner.layers, cache), start=1):
            x = layer(x, mask=mask, cache=c)
            if k in layers:
                keep[k] = x[0, -1]
        if k != len(inner.layers):
            raise Refused("error", "not all decoder layers ran")
        hn = inner.norm(x[:, -1:, :])
        lg = self._head(hn[0]).astype(mx.float32)
        lp = lg - mx.logsumexp(lg, axis=-1, keepdims=True)
        let = lp[0][self.letter_ix]
        st = mx.stack([keep[k].astype(mx.float32) for k in layers])
        mx.eval(st, let, [c.state for c in cache])
        return np.array(st), np.array(let)

    def readout(self, item: dict, layers=None) -> dict:
        import numpy as np  # noqa: PLC0415
        mx = self.mx
        layers = self.check_layers(layers or self.vm.DEFAULT_LAYERS)
        tk = self.tokens(item)
        pre, suf = tk["pre"], tk["suf"]
        n = len(suf)
        states = np.zeros((n, len(self.vm.DEFAULT_LAYERS), HIDDEN), dtype=np.float32)
        lets = np.zeros((n, len(self.vm.LETTERS)), dtype=np.float32)
        mx.reset_peak_memory()
        t_all = time.time()
        cache = self.make_cache(self.model)
        t1 = time.time()
        self._prefill(cache, pre)
        t_pre = time.time() - t1
        t2 = time.time()
        for j in range(n):
            st, lt = self._suffix_pass(cache, suf[j])
            self.trim(cache, len(suf[j]))
            if cache[0].offset != len(pre):
                raise Refused("error", "MLX cache: the cut back to the prefix failed")
            states[j], lets[j] = st, lt
            if (j + 1) % 25 == 0:
                log(f"mlx: {j + 1} of {n} passes")
        t_suf = time.time() - t2
        del cache
        peak = int(mx.get_peak_memory())
        mx.clear_cache()
        return self.result(item, tk, states, lets, layers, t_pre, t_suf, time.time() - t_all, peak,
                           "mlx.get_peak_memory (active memory)")

    def close(self) -> None:
        self.model = self.inner = None
        try:
            self.mx.clear_cache()
        except Exception:  # noqa: BLE001
            pass


register_backend("mlx", probe_mlx, lambda d, r, f: MlxBackend(d, r, f))
register_backend("cuda", probe_cuda, lambda d, r, f: TorchBackend(d, r, f, "cuda"))
register_backend("mps", probe_mps, lambda d, r, f: TorchBackend(d, r, f, "mps"))
register_backend("cpu", probe_cpu, lambda d, r, f: TorchBackend(d, r, f, "cpu"))


# ---------------------------------------------------------------------------------------------- npz and commands

def npz_arrays(item: dict, r: dict, desc: dict, code_sha: str, vm) -> dict:
    """The keys of daten/gj/states/values_dev/states/<id>.npz (m10_vm_states.NPZ_KEYS). The key model holds the
    name of the model folder only (no path of the user). letter_logprobs: NaN if the backend gives none."""
    import numpy as np  # noqa: PLC0415
    n = len(r["suffix_ids"])
    lets = r.get("letter_logprobs")
    lets = np.full((n, len(vm.LETTERS)), np.nan, dtype=np.float32) if lets is None else np.asarray(lets, np.float32)
    return {
        "doc_id": np.array(str(item["doc_id"])), "suffix_ids": np.array(r["suffix_ids"]),
        "layers": np.array(r["layers"], dtype=np.int16), "states": r["states"],
        "letter_logprobs": lets, "n_prefix_tokens": np.int64(r["n_prefix_tokens"]),
        "n_suffix_tokens": np.array(r["n_suffix_tokens"], dtype=np.int64),
        "letters": np.array(vm.LETTERS), "letter_token_ids": np.array(list(vm.APERTUS_LETTER_IDS), dtype=np.int64),
        "prefix_text_sha256": np.array(item["prefix_text_sha256"]),
        "suffix_text_sha256": np.array(item["suffix_text_sha256"]),
        "prefix_tokens_sha256": np.array(r["prefix_tokens_sha256"]),
        "suffix_tokens_sha256": np.array(r["suffix_tokens_sha256"]),
        "boundary_equal_first_suffix": np.bool_(bool(r.get("boundary_equal_first_suffix"))),
        "template_id": np.array(item["template_id"]), "template_sha256": np.array(item["template_sha256"]),
        "template_json_sha256": np.array(item["template_json_sha256"]),
        "model": np.array(str(desc.get("model", ""))), "model_fingerprint": np.array(str(desc["model_fingerprint"])),
        "code_sha256": np.array(code_sha), "version": np.array(f"{VERSION}+{desc['backend']}"),
        "dtype": np.array(str(desc.get("dtype", "bfloat16"))), "attn": np.array(str(desc.get("attn", ""))),
        "sdpa": np.array(str(desc.get("sdpa", ""))), "batch": np.int64(1), "batch_setting": np.int64(1),
        "prefill_chunk": np.int64(vm.PREFILL_CHUNK), "made": np.array(now())}


def parse_layers(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in str(s).split(",") if x.strip())


def write_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    tmp.write_text(scrub(json.dumps(obj, indent=1, ensure_ascii=False)) + "\n", encoding="utf-8")
    tmp.replace(p)


def cmd_run(a) -> int:
    t_start = time.time()
    root = Path(a.root).resolve()
    rec_p = Path(a.record)
    code_sha = sha256_file(Path(__file__))
    rec: dict = {"version": VERSION, "code_sha256": code_sha, "started": now(), "requested_backend": a.backend,
                 "model": MODEL_NAME, "exit": None}

    def finish(code: str, message: str | None = None, rc: int | None = None) -> int:
        rec["exit"], rec["message"] = code, message
        rec["ended"] = now()
        rec["seconds"] = round(time.time() - t_start, 2)
        write_json(rec_p, rec)
        log(f"end: {code}" + (f" ({message})" if message else ""))
        return EXIT_CODES.get(code, 1) if rc is None else rc

    backend = None
    try:
        rec["extra_backends"] = load_extra_backends()
        block_file = Path(a.block_file)
        raw = block_file.read_bytes()
        rec["block_file_sha256"] = hashlib.sha256(raw).hexdigest()
        doc = json.loads(raw)
        item = prepare_item(root, doc)
        rec.update(doc_id=str(item["doc_id"]), n_passes=len(item["suffixes"]), template_sha256=item["template_sha256"],
                   template_check=item["template_check"])
        name, tests = choose_backend(a.backend)
        rec["backend"], rec["backend_facts"] = name, tests
        if name in LOCAL_BACKENDS:
            local_environment(name)
        backend = open_backend(name, Path(a.model_dir) if a.model_dir else None, root, tests.get(name))
        desc = backend.describe()
        rec["describe"] = desc
        # the name for the record: a local backend gives its name; a remote backend gives "remote:<the backend of
        # the service>" (for example remote:cuda)
        rec["backend_choice"], rec["backend"] = name, str(desc.get("backend") or name)
        if backend.remote and desc.get("host"):
            rec["host"] = desc["host"]          # a remote backend: the host of its URL only (no path, no port)
        rec["model_fingerprint"] = desc["model_fingerprint"]
        if desc["model_fingerprint"] != WANT_FP:
            raise Refused("fingerprint_differs", f"the model fingerprint is {desc['model_fingerprint']}, not {WANT_FP} "
                                                 f"(the heads are valid for that model only): run 'make setup-apertus'")
        if not backend.remote:
            rec["memory_before"] = memory_check(name)
        log(f"backend {name}: load")
        rec["load"] = backend.load()
        log(f"backend {name}: loaded in {rec['load'].get('load_seconds')} s; {len(item['suffixes'])} passes")
        r = backend.readout(item, parse_layers(a.layers))
        if r["suffix_ids"] != [s["id"] for s in item["suffixes"]]:
            raise Refused("error", "the read-out has other suffix ids than the prompt item")
        if r["states"].shape != (len(item["suffixes"]), len(r["layers"]), HIDDEN) or HEADS_LAYER not in r["layers"]:
            raise Refused("error", f"the read-out has the form {tuple(r['states'].shape)} with layers {r['layers']}")
        import numpy as np  # noqa: PLC0415
        if r["states"].dtype != np.float16 or not np.isfinite(r["states"]).all():
            raise Refused("not_finite", "the states are not finite float16 values")
        vm = backend.vm if hasattr(backend, "vm") else converter_modules(root)[0]
        out = Path(a.out)
        vm.write_npz(out, npz_arrays(item, r, desc, code_sha, vm))
        tokens = r["n_prefix_tokens"] + sum(r["n_suffix_tokens"])
        tm = r["timing"]
        rec.update(device=desc.get("device"), dtype=desc.get("dtype"), attn=desc.get("attn"),
                   versions=desc.get("versions"), layers=r["layers"],
                   load_seconds=rec["load"].get("load_seconds"), prefill_seconds=tm["prefill_seconds"],
                   suffix_seconds=tm["suffix_seconds"], readout_seconds=tm["seconds"],
                   n_prefix_tokens=r["n_prefix_tokens"], n_suffix_tokens=int(sum(r["n_suffix_tokens"])),
                   tokens_per_s=round(tokens / max(tm["prefill_seconds"] + tm["suffix_seconds"], 1e-9), 1),
                   peak_bytes=r.get("peak_bytes"), peak_kind=r.get("peak_kind"), finite=True,
                   boundary_equal_first_suffix=r.get("boundary_equal_first_suffix"),
                   npz_sha256=sha256_file(out), npz_bytes=out.stat().st_size,
                   remote=r.get("remote"))
        return finish("ok")
    except Refused as e:
        return finish(e.code, e.message, e.exit_code)
    except FileNotFoundError as e:
        return finish("error", f"file absent: {Path(str(e.filename or '')).name}")
    except json.JSONDecodeError:
        return finish("block_file_bad", "the block file is not JSON")
    except Exception as e:  # noqa: BLE001
        return finish("error", f"{type(e).__name__}: {str(e)[:300]}")
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:  # noqa: BLE001
                pass


def cmd_check(a) -> int:
    """One JSON line: the backend that 'run' would take, the model fingerprint and the memory (no model load)."""
    out: dict = {"version": VERSION, "requested_backend": a.backend, "backend": None, "reason": None,
                 "message": None, "model_fingerprint": None, "fingerprint_ok": None, "memory": None,
                 "tested_on": "only macOS arm64 (Apple M4, 32 GB) on 15./16.10.2026: mlx, mps, cpu; "
                              "cuda, Linux and Windows not tested"}
    rc = 0
    try:
        out["extra_backends"] = load_extra_backends()
        name, tests = choose_backend(a.backend)
        out["backend"], out["tests"] = name, tests
        if name in LOCAL_BACKENDS:
            local_environment(name)
        if tests.get(name, {}).get("note"):
            out["note"] = tests[name]["note"]
        if not a.no_model or name not in LOCAL_BACKENDS:
            # a local backend reads the model folder (no load); another backend (for example remote) asks its
            # service for the fingerprint
            b = open_backend(name, Path(a.model_dir) if a.model_dir else None, Path(a.root).resolve(), tests.get(name))
            fp = b.describe()["model_fingerprint"]
            out["model_fingerprint"], out["fingerprint_ok"] = fp, fp == WANT_FP
            if fp != WANT_FP:
                raise Refused("fingerprint_differs", f"the model folder has the fingerprint {fp}, not {WANT_FP}: "
                                                     f"run 'make setup-apertus'")
        if name in LOCAL_BACKENDS:
            out["memory"] = memory_check(name)
    except Refused as e:
        out["reason"], out["message"] = e.code, e.message
        rc = e.exit_code
    except Exception as e:  # noqa: BLE001
        out["reason"], out["message"] = "error", f"{type(e).__name__}: {str(e)[:300]}"
        rc = 1
    print(scrub(json.dumps(out, ensure_ascii=False)), flush=True)
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Apertus read-out states of one block file (worker subprocess)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--root", required=True, help="folder with the converter files below src/")
    r.add_argument("--block-file", required=True)
    r.add_argument("--model-dir", default=None, help="the text branch folder (not needed by a remote backend)")
    r.add_argument("--out", required=True, help="the states file (npz)")
    r.add_argument("--record", required=True, help="the record of the run (JSON)")
    r.add_argument("--backend", default="auto")
    r.add_argument("--layers", default="8,12,16,20,24,28,32")
    c = sub.add_parser("check")
    c.add_argument("--root", required=True)
    c.add_argument("--model-dir", default=None)
    c.add_argument("--backend", default="auto")
    c.add_argument("--no-model", action="store_true", help="do not read the model folder (only the backend)")
    a = ap.parse_args(argv)
    if sys.platform == "darwin":
        # torch MPS reads these at its first allocation; set them before any probe imports torch
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "1.0"
        os.environ["PYTORCH_MPS_LOW_WATERMARK_RATIO"] = "0.9"
        os.environ.pop("PYTORCH_ENABLE_MPS_FALLBACK", None)
    return cmd_run(a) if a.cmd == "run" else cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
