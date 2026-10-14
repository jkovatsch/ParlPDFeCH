#!/usr/bin/env python3
"""Make the record of each sample with the worker command.

The script reads the sample index of the data folder. For each sample and each of its modes it
starts the worker (CONTRACT.md chapter 4.1) and moves the output to <out>/<record id>/.
It stops with exit code 1 if a worker run does not end with a valid record.

Uses:
  - image build: the records and views of the samples (Dockerfile, last step of each target);
  - offline check: one sample in a container with no network (Makefile, target check-offline).

Environment (CONTRACT.md chapter 2.1): PARLPDFECH_DATA_DIR, PARLPDFECH_WORKER_CMD (JSON array),
PARLPDFECH_WORKER_CWD. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def worker_command() -> list[str]:
    raw = os.environ.get("PARLPDFECH_WORKER_CMD")
    if not raw:
        return [sys.executable, str(PACKAGE / "worker" / "serve_convert.py")]
    cmd = json.loads(raw)
    if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) for x in cmd):
        raise SystemExit("PARLPDFECH_WORKER_CMD is not a JSON array of strings")
    return cmd


def last_json_line(text: str) -> dict:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line:
            try:
                obj = json.loads(line)
            except ValueError:
                return {}
            return obj if isinstance(obj, dict) else {}
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path, help="folder that gets one folder for each record")
    ap.add_argument("--limit", type=int, default=0, help="number of samples to convert; 0 = all")
    ap.add_argument("--modes", default="", help="comma list of modes; default = the modes of each sample")
    args = ap.parse_args()

    data_dir = Path(os.environ.get("PARLPDFECH_DATA_DIR") or PACKAGE / "data").resolve()
    index_path = data_dir / "samples" / "index.json"
    try:
        samples = json.loads(index_path.read_text(encoding="utf-8"))["samples"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: cannot read the sample index samples/index.json ({type(exc).__name__})", file=sys.stderr)
        return 1
    if args.limit > 0:
        samples = samples[: args.limit]
    only = [m for m in args.modes.split(",") if m]

    cmd = worker_command()
    cwd = os.environ.get("PARLPDFECH_WORKER_CWD") or None
    env = dict(os.environ, PARLPDFECH_DATA_DIR=str(data_dir))
    out_root = args.out.resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    made = 0
    for sample in samples:
        doc_id = str(sample["doc_id"])
        for mode in only or sample.get("modes", ["auto"]):
            record_id = sample["record_id"] + ("" if mode == "auto" else f"-{mode}")
            tmp = out_root / f".tmp-{record_id}"
            if tmp.exists():
                shutil.rmtree(tmp)
            t0 = time.monotonic()
            proc = subprocess.run(
                cmd + ["--sample", doc_id, "--mode", mode, "--out", str(tmp), "--data-dir", str(data_dir)],
                cwd=cwd, env=env, capture_output=True, text=True, check=False,
            )
            seconds = time.monotonic() - t0
            last = last_json_line(proc.stdout)
            ok = (
                proc.returncode == 0
                and last.get("event") == "done"
                and last.get("valid") is True
                and last.get("record_id") == record_id
                and (tmp / "view.json").is_file()
            )
            if not ok:
                print(f"FAIL: sample {doc_id}, mode {mode}: exit code {proc.returncode}, "
                      f"last line {json.dumps(last, ensure_ascii=False)[:400]}", file=sys.stderr)
                print("\n".join(proc.stderr.splitlines()[-25:]), file=sys.stderr)
                shutil.rmtree(tmp, ignore_errors=True)
                return 1
            target = out_root / record_id
            if target.exists():
                shutil.rmtree(target)
            os.replace(tmp, target)
            made += 1
            print(f"record {record_id}: valid, apertus {last.get('apertus')}, "
                  f"{len(list(target.iterdir()))} files, {seconds:.1f} s", flush=True)
    if made == 0:
        print("FAIL: the sample index has no sample", file=sys.stderr)
        return 1
    print(f"PASS: {made} records made", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
