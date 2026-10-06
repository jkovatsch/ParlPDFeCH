# SPDX-License-Identifier: Apache-2.0
"""Human gold set (E32): freeze E20 before the author checks test documents (process rule 6, G3a.1).

Run this script only after the author accepts E20 (the definition of the isolation task). The file
records the version line and the SHA-256 of the E20 file, the person who accepts, the words of the
acceptance and the date. After the freeze, a change of E20 needs a new freeze, and the test
documents that were checked before it are checked again. The output (<data>/gold/e20_freeze.json)
contains the words of the acceptance; it stays out of the public data. It records the path of the
E20 file relative to the folder that contains the data root (m03_iso_paths.rel), so that
m03_gold_review.py finds the file from each working folder.

Usage:  python3 src/m03_gold_freeze.py --e20 FILE --accepted-by NAME --quote "<words of the acceptance>" \\
            --date "DD.MM.YYYY, HH:MM"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402

OUT = DATA / "gold/e20_freeze.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e20", required=True, help="file of the E20 definition (Markdown)")
    ap.add_argument("--accepted-by", required=True, help="name of the person who accepts E20")
    ap.add_argument("--quote", required=True)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    if not args.quote.strip():
        raise SystemExit("no acceptance text")
    e20 = Path(args.e20)
    text = e20.read_text(encoding="utf-8")
    version = next((line for line in text.splitlines() if line.startswith("Version ")), "")
    rec = {"file": rel(e20.resolve()), "sha256": hashlib.sha256(e20.read_bytes()).hexdigest(),
           "version_line": version, "accepted_by": args.accepted_by, "quote": args.quote, "date": args.date}
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        rec["previous"] = old
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"E20 frozen: {rec['sha256'][:16]} ({version[:60]})")


if __name__ == "__main__":
    main()
