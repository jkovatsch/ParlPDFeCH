#!/usr/bin/env python3
"""Tool of the browser app: the numbers of the one fixed run of 13.10.2026 for the start page and the result view.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file or a number.

Task
  Read the display values of public/track_2a/numbers.json of the project (ids values.last_run.*) and write
  ui/run_numbers.json. The page reads that file: it shows the share correct of the 7 fields on the start page and
  on the page "About", and the precision with its counts (correct of given) next to the probability of a value.
  The page loads no file from another place.

Rules
  - Each number is the display value of numbers.json, not changed. The file names the id of each number.
  - The reader is the reader with rules only (ids values.last_run.rules_only.all.<field>.*). The reference is the
    OpenParlData export. No human checked a value.
  - share correct = correct / documents with a reference value. precision = correct / (correct + wrong).
    given = correct + wrong (the documents with a reference value where the reader gave a value).

Usage (from the folder package/; standard library only)
  python3 ui/tools/make_run_numbers.py            write ui/run_numbers.json
  python3 ui/tools/make_run_numbers.py --check    compare ui/run_numbers.json with numbers.json (exit code 1 if
                                                  a value differs or the source file is absent)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

UI = Path(__file__).resolve().parents[1]
SOURCE = UI.parents[1] / "public" / "track_2a" / "numbers.json"
OUT = UI / "run_numbers.json"
# field of the view (values[].field) -> field of numbers.json
FIELDS = {"affair_type": "affair_type", "title": "title", "affair_number": "affair_number",
          "submission_date": "submission_date", "sponsor": "first_author", "response_date": "response_date",
          "responder": "responder_name"}
STEM = "values.last_run.rules_only.all."


def build() -> dict:
    data = SOURCE.read_bytes()
    entries = {e["id"]: e for e in json.loads(data)["entries"]}

    def value(i: str) -> str:
        if i not in entries:
            raise SystemExit(f"numbers.json has no entry {i}")
        return str(entries[i]["display"])

    fields = {}
    for view_field, f in FIELDS.items():
        ids = {k: f"{STEM}{f}.{k}" for k in ("share_correct", "correct", "with_reference", "precision", "given")}
        fields[view_field] = {k: value(i) for k, i in ids.items()} | {"ids": ids}
    run = {"date": "13.10.2026", "documents": value(f"{STEM}documents"),
           "parliaments": value("values.last_run.parliaments.all"),
           "ids": {"documents": f"{STEM}documents", "parliaments": "values.last_run.parliaments.all"}}
    made = json.loads(data).get("made")
    return {"schema": "parlpdfech-run-numbers/1", "status": "EXCEPTION, NOT RELEASED",
            "note": "Display values of numbers.json of the project. Reader with rules only; reference: the "
                    "OpenParlData export. No human checked a value.",
            "source": {"file": "public/track_2a/numbers.json", "made": made,
                       "sha256": hashlib.sha256(data).hexdigest()},
            "run": run, "fields": fields}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not SOURCE.is_file():
        print(json.dumps({"run_numbers": "the source file is absent", "source": "public/track_2a/numbers.json"}))
        return 1 if a.check else 2
    new = build()
    if a.check:
        old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
        same = {k: v for k, v in old.items() if k != "source"} == {k: v for k, v in new.items() if k != "source"}
        print(json.dumps({"run_numbers": "equal" if same else "DIFFERENT", "source_made": new["source"]["made"]}))
        return 0 if same else 1
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"run_numbers": "written", "fields": len(new["fields"]), "source_made": new["source"]["made"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
