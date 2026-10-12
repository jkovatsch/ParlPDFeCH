# SPDX-License-Identifier: Apache-2.0
"""Download the two eCH-0295 schema files that the converter and the validator use (make setup).

Written in English to the STE rules (ASD-STE100, Issue 9).

The files come from the working repository of the eCH expert group "Politische Geschäfte"
(https://github.com/swiss/political-affairs-ech-group) at the pinned commit below. This repository holds
no copy of them. The script writes them to track_2a/.cache/ech-0295/ and examines the SHA-256 of each file.
A file with another SHA-256 is not kept.

Usage (from track_2a/): python src/fetch_schema.py          download the missing files
                        python src/fetch_schema.py --check  examine the files only (no network)
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

COMMIT = "3cab44d6a07f60bd8211cccdcf948717ef8fba5c"
BASE = f"https://raw.githubusercontent.com/swiss/political-affairs-ech-group/{COMMIT}/"
# path below the repository root: SHA-256
FILES = {
    "ech-0295_affairs/input/schema.yaml": "7af4c7a712f16270b653a773179d08cbd1859de053b20fe0beac6b2c2ef30d20",
    "ech-0292_meta/input/schema_common.yaml": "ab6c097c41cd57c40ad175e9bb130d70f4d4d8eb85281d329bee8c53c8f08b11",
}
CACHE = Path(__file__).resolve().parents[1] / ".cache" / "ech-0295"
I95 = CACHE / "ech-0295_affairs/input/schema.yaml"


def check() -> list[str]:
    """Problems of the downloaded files (empty list: all files are there with the pinned SHA-256)."""
    bad = []
    for rel, want in FILES.items():
        p = CACHE / rel
        if not p.exists():
            bad.append(f"{rel} is missing")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != want:
            bad.append(f"{rel} has another SHA-256")
    return bad


def fetch() -> int:
    for rel, want in FILES.items():
        p = CACHE / rel
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == want:
            print(f"present  {rel}  {want}")
            continue
        with urllib.request.urlopen(BASE + rel, timeout=60) as r:
            data = r.read()
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            print(f"refused  {rel}: SHA-256 {got}, pinned value {want}")
            return 1
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        print(f"written  {rel}  {got}")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        problems = check()
        print("\n".join(problems) or "all schema files present with the pinned SHA-256")
        sys.exit(1 if problems else 0)
    sys.exit(fetch())
