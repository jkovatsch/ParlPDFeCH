#!/usr/bin/env python3
"""Build tool of the ParlPDFeCH package: the code layout.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

Task
  Copy each file of worker/layout_files.json from the project folder into <package>/build/layout/
  under its project path (src/..., daten/..., quellen/..., crisp-dm/...). Each copy is byte-equal to
  its source. The tool compares the SHA-256 of each copy with the value of the list. The converter
  has SHA-256 self-checks, so no copy is changed.
  The tool writes build/layout/layout_manifest.json (the list of the copies). The worker reads it.
  The tool compiles the Python files (src/__pycache__), so a run of the worker does not compile them.
  The manifest records the SHA-256 of each compiled file. The worker uses a compiled file only if it
  has this SHA-256: a compiled file that was changed after the build is not run.

  build/ is not tracked by git. Read: 4 converter files hold a name or a home path, and the criteria
  files are internal texts. Their publication is a decision of the owner.

  --update keeps an existing layout in use: it copies only a file that is absent or different, it
  removes no file of the list, and it puts the new manifest in place with one rename. A worker that
  runs at the same time finds each file of the old manifest and of the new manifest.

  Compiled files that the manifest does not record (for example the files of another Python version,
  made by an import from the layout folder) are removed by a build and by --update, and --check
  reports them (key not_recorded_compiled, exit code 1). The worker never uses such a file, but a
  copy of the layout folder (the image build) would hold it. Do not import from build/layout/src.

Usage (from the project folder)
  python package/worker/layout.py [--project DIR] [--out DIR] [--list FILE] [--no-compile] [--update]
  python package/worker/layout.py --check [--out DIR]     compare an existing layout with its manifest
Exit code: 0 all copies equal; 1 one or more differences; 2 a source file is absent.
"""

from __future__ import annotations

import argparse
import compileall
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
MANIFEST = "layout_manifest.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compiled_files(out: Path, files: list[dict]) -> list[dict]:
    """The compiled file of each Python file of the list (this Python version), with its SHA-256."""
    cache = out / "src" / "__pycache__"
    rows = []
    for f in files:
        if f["path"].startswith("src/") and f["path"].endswith(".py"):
            pyc = cache / f"{Path(f['path']).stem}.{sys.implementation.cache_tag}.pyc"
            if pyc.is_file():
                rows.append({"name": pyc.name, "sha256": sha256(pyc)})
    return rows


def not_recorded(out: Path, recorded: list[dict]) -> list[Path]:
    """Each compiled file below the layout that the manifest does not record."""
    names = {c["name"] for c in recorded}
    return sorted(p for p in out.rglob("*.py[co]")
                  if not (p.parent == out / "src" / "__pycache__" and p.name in names))


def check(out: Path) -> int:
    man = json.loads((out / MANIFEST).read_text(encoding="utf-8"))
    bad = [f["path"] for f in man["files"] if not (out / f["path"]).is_file() or sha256(out / f["path"]) != f["sha256"]]
    cache = out / "src" / "__pycache__"
    bad_compiled = [c["name"] for c in man.get("compiled") or []
                    if (cache / c["name"]).is_file() and sha256(cache / c["name"]) != c["sha256"]]
    extra = [p.relative_to(out).as_posix() for p in not_recorded(out, man.get("compiled") or [])]
    print(json.dumps({"layout": "checked", "files": len(man["files"]), "different": bad,
                      "compiled": len(man.get("compiled") or []), "different_compiled": bad_compiled,
                      "not_recorded_compiled": len(extra), "not_recorded_compiled_names": extra[:10]}))
    return 1 if bad or bad_compiled or extra else 0


def build(project: Path, out: Path, list_file: Path, compile_py: bool, update: bool = False) -> int:
    spec = json.loads(list_file.read_text(encoding="utf-8"))
    missing = [f["path"] for f in spec["files"] if not (project / f["path"]).is_file()]
    if missing:
        print(json.dumps({"layout": "refused", "absent_sources": missing}))
        return 2
    if out.exists() and not update:
        shutil.rmtree(out)
    different, copied = [], 0
    for f in spec["files"]:
        dst = out / f["path"]
        if update and dst.is_file() and dst.stat().st_size == f["bytes"] and sha256(dst) == f["sha256"]:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / f["path"], dst)          # copy2 keeps the modification time (valid compiled files)
        copied += 1
        if sha256(dst) != f["sha256"] or dst.stat().st_size != f["bytes"]:
            different.append(f["path"])
    compiled = None
    if compile_py and not different:
        compiled = bool(compileall.compile_dir(str(out / "src"), quiet=1, legacy=False))
    man = {"schema": "parlpdfech-layout-manifest/1", "status": "EXCEPTION, NOT RELEASED",
           "list": {"file": "worker/layout_files.json", "sha256": sha256(list_file)},
           "python_compiled": compiled, "compiled": compiled_files(out, spec["files"]) if compiled else [],
           "files": [{k: f[k] for k in ("path", "bytes", "sha256", "kind", "modes")}
                                                  for f in spec["files"]]}
    tmp = out / (MANIFEST + ".new")
    tmp.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, out / MANIFEST)                     # one rename: no half manifest is visible
    removed = 0
    for p in not_recorded(out, man["compiled"]):        # compiled files that the manifest does not record
        p.unlink(missing_ok=True)
        removed += 1
    print(json.dumps({"layout": "updated" if update else "built", "files": len(spec["files"]), "copied": copied,
                      "bytes": sum(f["bytes"] for f in spec["files"]), "different": different,
                      "python_compiled": compiled, "compiled_recorded": len(man["compiled"]),
                      "compiled_not_recorded_removed": removed}))
    return 1 if different else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="byte-equal copies of the converter files for the worker")
    ap.add_argument("--project", default=str(PACKAGE.parent), help="the project folder that holds src/ and daten/")
    ap.add_argument("--out", default=str(PACKAGE / "build" / "layout"))
    ap.add_argument("--list", default=str(PACKAGE / "worker" / "layout_files.json"))
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true", help="keep the existing files; copy only absent or different files")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if a.check:
        return check(out)
    return build(Path(a.project).resolve(), out, Path(a.list).resolve(), not a.no_compile, a.update)


if __name__ == "__main__":
    sys.exit(main())
