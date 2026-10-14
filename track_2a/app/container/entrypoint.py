#!/usr/bin/env python3
"""Start command of the image.

The work folder of a container is a temporary file system; it is empty at each start.
This script copies the records of the samples, which the image build made, to
<work folder>/records/. Then it replaces itself with the server process.

Environment: PARLPDFECH_SEED_DIR (default /app/seed/records), PARLPDFECH_WORK_DIR (default /work),
PARLPDFECH_SERVER (default /app/parlpdfech-server). Standard library only.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def copy_seed(seed: Path, records: Path) -> int:
    if not seed.is_dir():
        return 0
    records.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(p for p in seed.iterdir() if p.is_dir() and not p.name.startswith(".")):
        dst = records / src.name
        if dst.exists():
            continue
        tmp = records / f".seed-{src.name}"
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(src, tmp)
        os.replace(tmp, dst)
        n += 1
    return n


def main() -> None:
    seed = Path(os.environ.get("PARLPDFECH_SEED_DIR", "/app/seed/records"))
    work = Path(os.environ.get("PARLPDFECH_WORK_DIR", "/work"))
    server = os.environ.get("PARLPDFECH_SERVER", "/app/parlpdfech-server")
    try:
        n = copy_seed(seed, work / "records")
        print(f"entrypoint: {n} sample records copied to the work folder", file=sys.stderr, flush=True)
    except OSError as exc:
        # The server works with no stored record: the page then starts a conversion for a sample.
        print(f"entrypoint: sample records not copied ({type(exc).__name__})", file=sys.stderr, flush=True)
    os.execv(server, [server] + sys.argv[1:])


if __name__ == "__main__":
    main()
