#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""ParlPDFeCH, track_2a: the text branch of swiss-ai/Apertus-v1.5-8B, made without MLX ('make setup-apertus').

Status: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude Opus 5.5),
15./16.10.2026, for the main agent of session ad54858c.

Why this file
  Apertus-v1.5-8B is an omni model (text, image, sound). The heads of ParlPDFeCH read its TEXT branch only. The
  project made that folder on 04.10.2026 with the MLX tool src/m04_text_branch_extrahieren.py (Apple only): the
  tensors model.language_model.* (renamed to model.*) and lm_head.weight, the embedding cut to the first 131,072
  rows (the text tokens), bf16 with no change of a value, and a config with model_type "apertus". The read-out
  code checks the model fingerprint (m10_vm_states.model_fingerprint): the bytes of config.json,
  tokenizer.json, tokenizer_config.json, chat_template.jinja and model.safetensors.index.json, and the NAME and
  the SIZE of each shard. The MLX tool writes the tensor data in its own order, and the safetensors package
  cannot write the same bytes. So this file writes the same bytes from a pinned layout
  (tools/apertus/text_branch_layout.json: the 4 shard headers, config.json, the index and the SHA-256 of each
  output file; names, shapes and offsets only, no weight). Each byte of a weight comes from the downloaded shard.

Standard library only (struct, json, hashlib): it runs with any Python 3.9 or later, on each system, with no
MLX, no torch and no safetensors package.

Commands
  python -I text_branch.py extract --source SNAPSHOT --target DIR --layout LAYOUT   write the text branch
  python -I text_branch.py verify  --source SNAPSHOT --layout LAYOUT                write nothing: hash the bytes
                                                                                    that extract would write
  python -I text_branch.py fingerprint --model-dir DIR                              print the model fingerprint
  python -I text_branch.py check-dir --model-dir DIR --layout LAYOUT                write nothing: the full SHA-256
                                                    of each file of a present text branch against the layout (the
                                                    fingerprint has only the name and the size of each shard)
  python -I text_branch.py layout --model-dir DIR --source SNAPSHOT --sha-list FILE --out LAYOUT
                                                    make the layout file from a text branch of the MLX tool (once)
SNAPSHOT is the folder that 'hf download swiss-ai/Apertus-v1.5-8B --revision <rev>' prints.
Exit code: 0 pass; 1 a check failed; 2 a file is absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import time
from pathlib import Path

LAYOUT_SCHEMA = "parlpdfech-text-branch-layout/1"
WANT_FP = "apertus-v1.5-8b-text-bf16:c10cd28db5bd3adf6043a5047a1435dedc5c3e55c45d5abc2ca82baf2a7786c3"
SOURCE_PREFIX = "model.language_model."
TEXT_ROWS = 131072
CHUNK = 64 << 20
COPIED = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja",
          "generation_config.json", "LICENSE.txt")
OPTIONAL = ("USAGE_POLICY.pdf", "PRIVACY_POLICY.pdf")        # not in the fingerprint; copied if present
WRITTEN = ("config.json", "model.safetensors.index.json")    # bytes from the layout file
DTYPE_BYTES = {"BF16": 2, "F16": 2, "F32": 4}


def say(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(CHUNK), b""):
            h.update(ch)
    return h.hexdigest()


def fingerprint(model_dir: Path) -> str:
    """The same definition as m10_vm_states.model_fingerprint (frozen, 13.10.2026)."""
    h = hashlib.sha256()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                 "model.safetensors.index.json"):
        p = model_dir / name
        if p.exists():
            h.update(name.encode() + b"\0" + p.read_bytes())
    for p in sorted(model_dir.glob("*.safetensors")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    return "apertus-v1.5-8b-text-bf16:" + h.hexdigest()


def read_header(p: Path) -> tuple[int, bytes, dict]:
    """(length, bytes, parsed) of the header of one safetensors file."""
    with open(p, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        if n <= 0 or n > 100 << 20:
            raise SystemExit(f"FAIL: {p.name}: the header length {n} is not plausible")
        raw = f.read(n)
    return n, raw, json.loads(raw)


def source_name(out_name: str) -> str:
    """The name of a tensor in the omni model (the inverse of the rename of the MLX tool)."""
    if out_name == "lm_head.weight":
        return out_name
    if out_name.startswith("model."):
        return SOURCE_PREFIX + out_name[len("model."):]
    raise SystemExit(f"FAIL: the tensor {out_name} has no rule of the rename")


def numel(shape) -> int:
    n = 1
    for s in shape:
        n *= int(s)
    return n


class Source:
    """The downloaded omni model: its index and the headers of its shards."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        ip = self.folder / "model.safetensors.index.json"
        if not ip.is_file():
            raise SystemExit(f"FAIL: no model.safetensors.index.json in the source folder {self.folder}")
        self.weight_map = json.loads(ip.read_text(encoding="utf-8"))["weight_map"]
        self.headers: dict[str, tuple[int, dict]] = {}

    def tensor(self, out_name: str) -> tuple[Path, int, dict]:
        """(shard path, absolute byte offset of the tensor data, header entry) of one output tensor."""
        sn = source_name(out_name)
        shard = self.weight_map.get(sn)
        if shard is None:
            raise SystemExit(f"FAIL: the source index has no tensor {sn}")
        p = self.folder / shard
        if not p.is_file():
            raise SystemExit(f"FAIL: the source shard {shard} is absent (hf download)")
        if shard not in self.headers:
            n, _raw, h = read_header(p)
            self.headers[shard] = (n, h)
        n, h = self.headers[shard]
        e = h.get(sn)
        if e is None:
            raise SystemExit(f"FAIL: the shard {shard} has no tensor {sn}")
        return p, 8 + n + int(e["data_offsets"][0]), e


def plan_shard(shard: dict, src: Source) -> list[tuple[str, int, int, Path, int]]:
    """For one output shard: (name, start, length, source path, source offset) of each tensor in the order of the
    data. The offsets must cover the data region with no gap and no overlap."""
    h = json.loads(shard["header"])
    rows = []
    for name, e in h.items():
        if name == "__metadata__":
            continue
        start, end = (int(x) for x in e["data_offsets"])
        p, off, se = src.tensor(name)
        if se["dtype"] != e["dtype"] or e["dtype"] not in DTYPE_BYTES:
            raise SystemExit(f"FAIL: {name}: dtype {se['dtype']} in the source, {e['dtype']} in the layout")
        if end - start != numel(e["shape"]) * DTYPE_BYTES[e["dtype"]]:
            raise SystemExit(f"FAIL: {name}: the byte length does not fit the shape {e['shape']}")
        if list(se["shape"]) != list(e["shape"]):
            # only the embedding is cut: the first TEXT_ROWS rows (row-major, so the first bytes of the tensor)
            cut = (name == "model.embed_tokens.weight" and len(se["shape"]) == 2 and se["shape"][1] == e["shape"][1]
                   and e["shape"][0] == TEXT_ROWS and se["shape"][0] >= TEXT_ROWS)
            if not cut:
                raise SystemExit(f"FAIL: {name}: shape {se['shape']} in the source, {e['shape']} in the layout")
        rows.append((name, start, end - start, p, off))
    rows.sort(key=lambda r: r[1])
    pos = 0
    for name, start, length, _p, _o in rows:
        if start != pos:
            raise SystemExit(f"FAIL: {shard['name']}: the data of {name} starts at {start}, not at {pos}")
        pos += length
    if 8 + len(shard["header"].encode("utf-8")) + pos != int(shard["bytes"]):
        raise SystemExit(f"FAIL: {shard['name']}: the layout gives {shard['bytes']} bytes, the plan {8 + pos} + header")
    return rows


def stream_shard(shard: dict, src: Source, out_path: Path | None) -> str:
    """Write (or, with out_path None, only hash) the bytes of one output shard. Returns the SHA-256."""
    rows = plan_shard(shard, src)
    hb = shard["header"].encode("utf-8")
    h = hashlib.sha256()
    out = open(out_path, "wb") if out_path is not None else None
    try:
        head = struct.pack("<Q", len(hb)) + hb
        h.update(head)
        if out:
            out.write(head)
        for _name, _start, length, p, off in rows:
            with open(p, "rb") as f:
                f.seek(off)
                left = length
                while left:
                    b = f.read(min(CHUNK, left))
                    if not b:
                        raise SystemExit(f"FAIL: the source shard {p.name} ends early")
                    h.update(b)
                    if out:
                        out.write(b)
                    left -= len(b)
    finally:
        if out:
            out.close()
    return h.hexdigest()


def load_layout(p: Path) -> dict:
    lay = json.loads(Path(p).read_text(encoding="utf-8"))
    if lay.get("schema") != LAYOUT_SCHEMA:
        raise SystemExit(f"FAIL: {p} is not a layout file of the form {LAYOUT_SCHEMA}")
    return lay


def check_copied(src: Path, lay: dict) -> list[str]:
    bad = []
    for name in COPIED:
        p = src / name
        if not p.is_file():
            bad.append(f"{name} absent")
        elif sha256_file(p) != lay["copied"][name]:
            bad.append(f"{name} has another SHA-256")
    return bad


def cmd_verify(a) -> int:
    lay = load_layout(Path(a.layout))
    src = Source(Path(a.source))
    bad = check_copied(Path(a.source), lay)
    for sh in lay["shards"]:
        t0 = time.time()
        got = stream_shard(sh, src, None)
        ok = got == sh["sha256"]
        say(f"{'PASS' if ok else 'FAIL'}: {sh['name']} {got[:16]}... ({time.time() - t0:.0f} s)")
        if not ok:
            bad.append(sh["name"])
    for name in WRITTEN:
        if hashlib.sha256(lay["files"][name]["text"].encode("utf-8")).hexdigest() != lay["files"][name]["sha256"]:
            bad.append(name)
    if bad:
        say("FAIL: " + "; ".join(bad))
        return 1
    say("PASS: the extract would give the pinned bytes of each output file")
    return 0


def cmd_extract(a) -> int:
    lay = load_layout(Path(a.layout))
    source, target = Path(a.source), Path(a.target)
    src = Source(source)
    bad = check_copied(source, lay)
    if bad:
        say("FAIL: " + "; ".join(bad))
        return 1
    need = sum(int(s["bytes"]) for s in lay["shards"]) + (64 << 20)
    target.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(target).free
    if free < need:
        say(f"FAIL: {free / 1e9:.1f} GB free at the target folder; the text branch needs {need / 1e9:.1f} GB")
        return 1
    for sh in lay["shards"]:
        t0 = time.time()
        part = target / (sh["name"] + ".part")       # not *.safetensors: the fingerprint does not see it
        got = stream_shard(sh, src, part)
        if got != sh["sha256"]:
            part.unlink()
            say(f"FAIL: {sh['name']}: SHA-256 {got[:16]}..., not {sh['sha256'][:16]}... (no file written)")
            return 1
        os.replace(part, target / sh["name"])
        say(f"PASS: {sh['name']} ({int(sh['bytes']) / 1e9:.2f} GB, {time.time() - t0:.0f} s)")
    for name in WRITTEN:
        (target / name).write_bytes(lay["files"][name]["text"].encode("utf-8"))
        if sha256_file(target / name) != lay["files"][name]["sha256"]:
            say(f"FAIL: {name}: other bytes than the layout")
            return 1
    for name in COPIED:
        shutil.copyfile(source / name, target / name)
    for name, want in lay.get("optional", {}).items():
        p = source / name
        if p.is_file() and sha256_file(p) == want:
            shutil.copyfile(p, target / name)
        else:
            say(f"NOTE: {name} is not in the download (not in the fingerprint). Read it on "
                f"https://huggingface.co/{lay.get('model_repo', 'swiss-ai/Apertus-v1.5-8B')}")
    for p in sorted(target.glob("*.safetensors")):
        if p.name not in {s["name"] for s in lay["shards"]}:
            say(f"FAIL: the target folder holds another safetensors file {p.name}: remove it, then run again")
            return 1
    fp = fingerprint(target)
    if fp != lay["fingerprint"]:
        say(f"FAIL: fingerprint {fp}, not {lay['fingerprint']}")
        return 1
    say(f"PASS: text branch in {target}; fingerprint {fp}")
    return 0


def cmd_check_dir(a) -> int:
    """A present text branch folder (for example of an earlier setup or of the MLX tool): the SHA-256 of each shard,
    of the 2 written files and of each copied file must be the pinned value of the layout (fix step of 16.10.2026:
    the fingerprint alone does not see a damaged shard of the right size)."""
    lay = load_layout(Path(a.layout))
    d = Path(a.model_dir)
    bad = []
    for sh in lay["shards"]:
        p = d / sh["name"]
        if not p.is_file():
            bad.append(f"{sh['name']} absent")
            continue
        t0 = time.time()
        got = sha256_file(p)
        ok = got == sh["sha256"]
        say(f"{'PASS' if ok else 'FAIL'}: {sh['name']} {got[:16]}... ({time.time() - t0:.0f} s)")
        if not ok:
            bad.append(f"{sh['name']} has another SHA-256")
    for name in WRITTEN:
        p = d / name
        if not p.is_file() or sha256_file(p) != lay["files"][name]["sha256"]:
            bad.append(f"{name} absent or other bytes")
    for name in COPIED:
        p = d / name
        if not p.is_file() or sha256_file(p) != lay["copied"][name]:
            bad.append(f"{name} absent or other bytes")
    others = sorted(p.name for p in d.glob("*.safetensors") if p.name not in {s["name"] for s in lay["shards"]})
    if others:
        bad.append(f"other safetensors files: {', '.join(others)}")
    if bad:
        say("FAIL: " + "; ".join(bad))
        return 1
    say("PASS: each file of the text branch has the pinned SHA-256")
    return 0


def cmd_fingerprint(a) -> int:
    d = Path(a.model_dir)
    if not (d / "config.json").is_file():
        say("absent")
        return 2
    say(fingerprint(d))
    return 0


def cmd_layout(a) -> int:
    """Once, on the computer that holds a text branch of the MLX tool: pin its metadata (no weight)."""
    model, source = Path(a.model_dir), Path(a.source)
    fp = fingerprint(model)
    if fp != WANT_FP:
        raise SystemExit(f"FAIL: {model} has the fingerprint {fp}")
    shas = {}
    for line in Path(a.sha_list).read_text(encoding="utf-8").splitlines():
        if line.strip():
            s, name = line.split(None, 1)
            shas[name.strip()] = s
    shards = []
    for p in sorted(model.glob("*.safetensors")):
        _n, raw, _h = read_header(p)
        shards.append({"name": p.name, "bytes": p.stat().st_size, "sha256": shas[p.name], "header": raw.decode("utf-8")})
    src = Source(source)
    for sh in shards:
        plan_shard(sh, src)                         # each tensor has its source; offsets cover the data region
    files = {}
    for name in WRITTEN:
        raw = (model / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != shas[name]:
            raise SystemExit(f"FAIL: {name} differs from the SHA-256 list")
        files[name] = {"sha256": shas[name], "text": raw.decode("utf-8")}
    lay = {"schema": LAYOUT_SCHEMA, "status": "EXCEPTION, NOT RELEASED",
           "what": "metadata of the text branch of swiss-ai/Apertus-v1.5-8B as src/m04_text_branch_extrahieren.py "
                   "(MLX) wrote it on 04.10.2026: the 4 shard headers (tensor names, dtypes, shapes, offsets), "
                   "config.json, model.safetensors.index.json and the SHA-256 of each file. No weight.",
           "model_repo": a.repo, "model_revision": a.revision, "text_rows": TEXT_ROWS,
           "rename": {"from": SOURCE_PREFIX, "to": "model.", "kept": ["lm_head.weight"]},
           "fingerprint": fp, "shards": shards, "files": files,
           "copied": {n: shas[n] for n in COPIED}, "optional": {n: shas[n] for n in OPTIONAL if n in shas},
           "source_shards": {s: {"bytes": (source / s).stat().st_size,
                                 "lfs_sha256": os.path.basename(os.path.realpath(source / s))}
                             for s in sorted({src.weight_map[source_name(k)] for sh in shards
                                              for k in json.loads(sh["header"]) if k != "__metadata__"})}}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(lay, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"PASS: layout written ({Path(a.out).stat().st_size} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="text branch of Apertus-v1.5-8B without MLX")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--source", required=True)
    e.add_argument("--target", required=True)
    e.add_argument("--layout", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--source", required=True)
    v.add_argument("--layout", required=True)
    f = sub.add_parser("fingerprint")
    f.add_argument("--model-dir", required=True)
    c = sub.add_parser("check-dir")
    c.add_argument("--model-dir", required=True)
    c.add_argument("--layout", required=True)
    lo = sub.add_parser("layout")
    lo.add_argument("--model-dir", required=True)
    lo.add_argument("--source", required=True)
    lo.add_argument("--sha-list", required=True)
    lo.add_argument("--out", required=True)
    lo.add_argument("--repo", default="swiss-ai/Apertus-v1.5-8B")
    lo.add_argument("--revision", default="ef4bbc54d6fe658bc782280ff9f3b53a10a9758f")
    a = ap.parse_args()
    return {"extract": cmd_extract, "verify": cmd_verify, "fingerprint": cmd_fingerprint, "check-dir": cmd_check_dir,
            "layout": cmd_layout}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
