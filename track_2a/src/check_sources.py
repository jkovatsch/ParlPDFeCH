# SPDX-License-Identifier: Apache-2.0
"""make test, part 1: examine the copied files against SOURCES.json.

Written in English to the STE rules (ASD-STE100, Issue 9).

For each file of SOURCES.json:
  1. The file in this repository has the recorded SHA-256 (copy_sha256).
  2. Code and prompt files without edits: remove the added license line (line 1). The result must have the
     SHA-256 of the source file in the private project (source_sha256).
  3. Code files with edits: remove line 1; the recorded new text must be on the recorded lines. Then make
     the recorded lines empty. The result must have the SHA-256 that SOURCES.json gives for the source file
     with the same lines empty (masked_source_sha256). The edits keep the number of lines.
  Thus anyone can examine that the published code is the code of the private project, with only the
  recorded edits. SOURCES.json does not repeat the old text of an edit (it held paths of the private
  computer or quotations of internal notes).
  4. The R2 template: the SHA-256 of its canonical JSON must be the template SHA-256 of the frozen head.
Exit code 0 only if all checks pass.

Usage (from track_2a/): python src/check_sources.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

TRACK = Path(__file__).resolve().parents[1]
R2_TEMPLATE_SHA256 = "2a48e04bb8996dd331df38c79fa3121db63420b9c2e3eb5c8afaf053b8e5872e"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    src = json.loads((TRACK / "SOURCES.json").read_text(encoding="utf-8"))
    line1 = src["spdx_line"] + "\n"
    n_ok = n = 0
    for f in src["files"]:
        n += 1
        p = TRACK / f["copy"]
        raw = p.read_bytes() if p.exists() else b""
        problems = []
        if sha(raw) != f["copy_sha256"]:
            problems.append("SHA-256 of the copy differs from SOURCES.json")
        if f["kind"] in ("code", "prompt"):
            text = raw.decode("utf-8")
            if not text.startswith(line1):
                problems.append("line 1 is not the license line")
            text = text[len(line1):]
            if not f["edits"]:
                if sha(text.encode("utf-8")) != f["source_sha256"]:
                    problems.append("without line 1, the SHA-256 differs from the source")
            else:
                lines = text.split("\n")
                for e in f["edits"]:
                    a, b = e["lines"]
                    if e["new"] not in "\n".join(lines[a - 1:b]):
                        problems.append(f"the recorded edit is not on the lines {a} to {b}")
                for e in f["edits"]:
                    a, b = e["lines"]
                    for i in range(a - 1, b):
                        lines[i] = ""
                if sha("\n".join(lines).encode("utf-8")) != f.get("masked_source_sha256"):
                    problems.append("outside the recorded lines, the copy differs from the source")
        if f["kind"] == "prompt template":
            tmpl = json.loads(raw.decode("utf-8"))
            canon = json.dumps(tmpl, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if sha(canon) != R2_TEMPLATE_SHA256:
                problems.append("template SHA-256 differs from the frozen head")
        n_ok += not problems
        if problems:
            print(f"FAIL  {f['copy']}: {'; '.join(problems)}")
    print(f"{n_ok} of {n} files of SOURCES.json pass (copy SHA-256; code and prompts: equal to the source, "
          f"except the license line and the recorded lines)")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
