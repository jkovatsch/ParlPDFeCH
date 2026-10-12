# SPDX-License-Identifier: Apache-2.0
"""Validator: examine eCH-0295 instances and provenance side files with linkml-validate.

Written in English to the STE rules (ASD-STE100, Issue 9).

- An instance (YAML) is validated against I95 (`ech-0295_affairs/input/schema.yaml` of the working draft
  eCH-0295, commit 3cab44d, pinned SHA-256 in src/fetch_schema.py), class Container.
- A provenance side file (YAML with the key `describes_delivery`) is validated against the ParlPDFeCH profile
  `src/converter/m06_ech_profil.yaml` (version 0.2.0), class ExtractionRecord. The profile imports
  `schema_common.yaml` of eCH-0292 (same commit).
- Tool: linkml-validate of the package linkml==1.11.1, called with `uvx --offline` (make setup downloads it).

The script makes a temporary folder with the layout that the profile import needs. It changes no input file.
Exit code: 0 if each file is valid, 1 if a file is not valid, 2 if a schema file is missing.

Usage (from track_2a/): python src/validate_ech.py FILE [FILE ...]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_schema as fs  # noqa: E402

LINKML = ["uvx", "--offline", "--from", "linkml==1.11.1", "linkml-validate"]
PROFILE = HERE / "converter" / "m06_ech_profil.yaml"


def kind_of(p: Path) -> str:
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return "provenance" if isinstance(data, dict) and "describes_delivery" in data else "instance"


def validate(schema: Path, cls: str, data: Path) -> tuple[bool, list[str]]:
    p = subprocess.run(LINKML + ["-s", str(schema), "-C", cls, str(data)], capture_output=True, text=True, timeout=900)
    errors = [z for z in p.stdout.splitlines() if z.startswith("[ERROR]")]
    ok = p.returncode == 0 and not errors and "No issues found" in p.stdout
    if not ok and not errors:
        errors = p.stderr.strip().splitlines()[-3:]
    return ok, errors


def main(args: list[str]) -> int:
    if not args or {"-h", "--help"} & set(args):
        print(__doc__)
        return 0 if args else 2
    bad = fs.check()
    if bad:
        print("schema files: " + "; ".join(bad) + ". Run `make setup` first.")
        return 2
    with tempfile.TemporaryDirectory(prefix="parlpdfech-validate-") as tmp:
        root = Path(tmp)
        q = root / "quellen" / "political-affairs-ech-group"
        for rel in fs.FILES:
            (q / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fs.CACHE / rel, q / rel)
        (root / "src").mkdir()
        shutil.copyfile(PROFILE, root / "src" / PROFILE.name)
        schemas = {"instance": (q / "ech-0295_affairs/input/schema.yaml", "Container", "I95"),
                   "provenance": (root / "src" / PROFILE.name, "ExtractionRecord", "profile 0.2.0")}
        n_ok = 0
        for f in map(Path, args):
            k = kind_of(f)
            schema, cls, label = schemas[k]
            ok, errors = validate(schema, cls, f)
            n_ok += ok
            print(f"{'VALID  ' if ok else 'INVALID'}  {f}  ({k}; {label}, class {cls})")
            for e in errors[:5]:
                print(f"         {e[:300]}")
        print(f"{n_ok} of {len(args)} files valid (linkml-validate, linkml==1.11.1)")
    return 0 if n_ok == len(args) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
