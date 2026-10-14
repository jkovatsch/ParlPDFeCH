#!/usr/bin/env python3
"""Compare each file of a self-contained source tree with DIST-MANIFEST.json.

Use, from the root of the tree:  python container/check_dist.py
Prints one JSON line. Exit code 0: each file of the manifest is present with its SHA-256 and the tree
holds no other file. The files of site/ (an optional static site) are rows of the manifest like each
other file. Not counted: a top-level folder with one of the exact names work, .git, target, target-server
and target-wasm (the build outputs of this tree), the folder ui/pkg, and a compiled Python file (*.pyc)
in a folder __pycache__ at each level. Counted: each other file in a folder __pycache__, and a folder
with another name that starts with target.
Exit code 1: a difference.
Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The first path part only, exact names: the work folder, the git folder, and the build output folders
# (Makefile and rdfcheck/build.sh: target-server, target-wasm; cargo with no setting: target).
NOT_COUNTED_ROOT = ("work", ".git", "target", "target-server", "target-wasm")


def not_counted(parts: tuple[str, ...]) -> bool:
    if len(parts) < 2:
        return False  # a file at the root of the tree is always counted
    first = parts[0]
    if first in NOT_COUNTED_ROOT or parts[:2] == ("ui", "pkg"):
        return True
    # The interpreter writes compiled files there. Each other file in such a folder is counted.
    return parts[-2] == "__pycache__" and parts[-1].endswith(".pyc")


def main() -> int:
    man_p = ROOT / "DIST-MANIFEST.json"
    if not man_p.is_file():
        print(json.dumps({"dist": "refused", "note": "DIST-MANIFEST.json is absent: this folder is not a made source tree"}))
        return 1
    man = json.loads(man_p.read_text(encoding="utf-8"))
    want = {f["path"]: f for f in man["files"]}
    absent, different = [], []
    for path, f in want.items():
        p = ROOT / path
        if not p.is_file():
            absent.append(path)
        elif hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            different.append(path)
    extra = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if not p.is_file() or rel.as_posix() in want or rel.as_posix() == "DIST-MANIFEST.json":
            continue
        if not_counted(rel.parts):
            continue
        extra.append(rel.as_posix())
    print(json.dumps({"dist": "checked", "files": len(want), "absent": absent, "different": different,
                      "not_in_manifest": extra[:20], "not_in_manifest_count": len(extra)}))
    return 1 if absent or different or extra else 0


if __name__ == "__main__":
    sys.exit(main())
