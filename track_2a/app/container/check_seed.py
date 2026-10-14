#!/usr/bin/env python3
"""Compare the sample records of container/seed_records.py with the reference values of the samples.

For each sample of the index and each of its modes the script reads <records>/<record id>/convert.json
and view.json. Checks: the record exists; convert.json has the profile of the run; in the mode auto the
SHA-256 of the decisions file is the value of the reference run (data/samples/<document>/reference.json).
The mode rules has no reference value in the sample data: the script prints its SHA-256 only.

Use, from the root of the package or of the source tree:
  python container/check_seed.py --records DIR [--data-dir DIR]
Prints one JSON line for each record and one summary line. Exit code 0: all checks passed; 1: a difference.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True, type=Path)
    ap.add_argument("--data-dir", type=Path, default=Path(os.environ.get("PARLPDFECH_DATA_DIR") or PACKAGE / "data"))
    a = ap.parse_args()
    samples = json.loads((a.data_dir / "samples" / "index.json").read_text(encoding="utf-8"))["samples"]
    bad = 0
    rows = 0
    for s in samples:
        doc = str(s["doc_id"])
        ref = json.loads((a.data_dir / "samples" / doc / "reference.json").read_text(encoding="utf-8"))
        for mode in s.get("modes", ["auto"]):
            rid = s["record_id"] + ("" if mode == "auto" else f"-{mode}")
            row = {"record": rid, "mode": mode}
            try:
                conv = json.loads((a.records / rid / "convert.json").read_text(encoding="utf-8"))
                view_ok = (a.records / rid / "view.json").is_file()
            except (OSError, ValueError) as exc:
                row.update(result="NOT PASSED", note=f"record not readable ({type(exc).__name__})")
                bad += 1
                print(json.dumps(row))
                continue
            row["decisions_sha256"] = conv.get("decisions_sha256")
            row["view"] = view_ok
            ok = view_ok and isinstance(conv.get("decisions_sha256"), str)
            if mode == "auto":
                row["equal_to_the_reference_run"] = conv.get("decisions_sha256") == ref.get("decisions_sha256")
                ok = ok and row["equal_to_the_reference_run"]
            row["result"] = "passed" if ok else "NOT PASSED"
            bad += 0 if ok else 1
            rows += 1
            print(json.dumps(row))
    print(json.dumps({"check_seed": "passed" if not bad and rows else "NOT PASSED", "records": rows, "not_passed": bad}))
    return 0 if not bad and rows else 1


if __name__ == "__main__":
    sys.exit(main())
