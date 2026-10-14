# SPDX-License-Identifier: Apache-2.0
"""Examine the prompt files of the template gj_jev_v1_de (prompts/gj_jev_v1_de/).

Written in English to the STE rules (ASD-STE100, Issue 9).

The definition of the template SHA-256 (the same as in the job builder of the project, m10_prompts.py):
  1. Read template.json as JSON. Remove the key "sha256".
  2. Write the canonical JSON: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).
  3. The template SHA-256 is the SHA-256 of the UTF-8 bytes of this text.
The job records and the state files of the project hold this value. It is not the SHA-256 of the file
template.json (the file has indents and the key "sha256").

Checks:
  1. Each file of PROMPTS.sha256 has the recorded SHA-256.
  2. The file template.json has the SHA-256 that the job records give for it (TEMPLATE_FILE_SHA256).
  3. The template SHA-256 of template.json (definition above) is TEMPLATE_SHA256, and the key "sha256" of the
     file holds the same value.
  4. Line 1 of each text file is the license line. This program removes line 1 before use.
  5. This program builds the template again from the 4 text files only (build_template). The result must be
     equal to template.json: the same JSON value, the same template SHA-256 and the same bytes of the file.
  6. Each option line of a question file ("<letter> = <text>") has a letter of the letter list, in order.
Exit code 0 only if all checks pass.

The format of the text files:
  system.txt, prefix_format.txt   line 1, then one line "<name> = <JSON value>" for each item
  d1_question.txt, b1_question.txt   line 1, then the exact question text, then one line end

Usage (from track_2a/):
  python src/check_prompts.py             the checks
  python src/check_prompts.py --example   also prints the prefix and the suffixes of a small invented document
This program needs only the Python standard library. It loads no model and it uses no network.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

FOLDER = Path(__file__).resolve().parent / "prompts" / "gj_jev_v1_de"
TEMPLATE_ID = "gj_jev_v1_de"
TEMPLATE_SHA256 = "72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c"
TEMPLATE_FILE_SHA256 = "9a6d72a0b9577b13ce3a328e0e83dacdf60fb38796f1f9b964d0e6bfff545100"
LICENSE_LINE = "# SPDX-License-Identifier: Apache-2.0\n"
TEXT_FILES = ("system.txt", "prefix_format.txt", "d1_question.txt", "b1_question.txt")


def sha256_json(x) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def template_sha(t: dict) -> str:
    return sha256_json({k: v for k, v in t.items() if k != "sha256"})


def body(name: str) -> str:
    """The text of a text file without line 1 (the license line)."""
    text = (FOLDER / name).read_bytes().decode("utf-8")
    if not text.startswith(LICENSE_LINE):
        raise ValueError(f"{name}: line 1 is not the license line")
    return text[len(LICENSE_LINE):]


def items(name: str) -> dict:
    """The items of a file with lines "<name> = <JSON value>"."""
    out = {}
    for line in body(name).split("\n"):
        if not line:
            continue
        key, sep, value = line.partition(" = ")
        if not sep or key in out:
            raise ValueError(f"{name}: not an item line, or the name is there two times: {line[:40]!r}")
        out[key] = json.loads(value)
    return out


def question(name: str) -> str:
    """The exact question text: the file without line 1 and without the one line end at the end."""
    text = body(name)
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise ValueError(f"{name}: the file must end with one line end")
    return text[:-1]


def options(name: str, option_of_letter: dict) -> list[dict]:
    """The option lines of a question file: all lines but the first line (the question) and the last line."""
    lines = question(name).split("\n")[1:-1]
    out = []
    for line in lines:
        letter, sep, text = line.partition(" = ")
        if not sep:
            raise ValueError(f"{name}: not an option line: {line!r}")
        out.append({"letter": letter, "option": option_of_letter.get(letter), "text": text})
    if [o["letter"] for o in out] != list(option_of_letter):
        raise ValueError(f"{name}: the letters of the option lines differ from the letter list")
    return out


def build_template() -> dict:
    """The template from the 4 text files only. Key order as in the job builder, so the file bytes are equal too."""
    s, p = items("system.txt"), items("prefix_format.txt")
    t = {
        "template_id": TEMPLATE_ID,
        "system_text_source": {
            "file": s["source_file"], "file_sha256": s["source_file_sha256"], "constants": s["source_constants"],
            "system": s["system"], "doc_head": s["doc_head"], "sep": s["sep"], "answer_prefix": s["answer_prefix"]},
        "prefix_format": {
            "chat_head": p["chat_head"].replace("{system}", s["system"]), "doc_head": s["doc_head"],
            "line": p["line"], "line_join": p["line_join"], "line_rules": p["line_rules"],
            "prefix_end": s["sep"], "suffix": p["suffix"], "suffix_start": p["suffix_start"],
            "chat_tail": p["chat_tail"], "answer_prefix": s["answer_prefix"], "suffix_order": p["suffix_order"],
            "tokenization": p["tokenization"],
            "chat_template": {"file": p["chat_template_file"], "sha256": p["chat_template_sha256"],
                              "call": p["chat_template_call"]}},
        "d1_question": question("d1_question.txt"),
        "b1_question": question("b1_question.txt"),
        "options": {
            "d1": options("d1_question.txt", p["d1_option_of_letter"]),
            "b1": options("b1_question.txt", p["b1_option_of_letter"]),
            "first_words": p["first_words"], "no_text": p["no_text"]},
    }
    t["sha256"] = sha256_json(t)
    return {k: t[k] for k in ("template_id", "sha256", "system_text_source", "prefix_format", "d1_question",
                              "b1_question", "options")}


def example(t: dict) -> str:
    """The prefix and the suffixes of a small invented document (2 blocks), as the job builder makes them."""
    p = t["prefix_format"]
    blocks = [{"block": "B1", "page": 1, "label": "section_header", "text": "Motion 2026/1\nBeispiel"},
              {"block": "B2", "page": 1, "label": "text", "text": ""}]

    def one_line(text: str) -> str:
        return " ".join(x.strip() for x in text.splitlines() if x.strip())

    def line(b: dict) -> str:
        head = f"[{b['block']} | S.{b['page']} | {b['label']}]"
        return head + " " + one_line(b["text"]) if one_line(b["text"]) else head

    def first_words(text: str) -> str:
        w = text.split()
        return " ".join(w[:t["options"]["first_words"]]) if w else t["options"]["no_text"]

    tail = p["chat_tail"] + p["answer_prefix"]
    prefix = p["chat_head"] + p["doc_head"] + p["line_join"].join(line(b) for b in blocks) + p["prefix_end"]
    out = ["--- prefix (one for the document) ---", prefix, "--- suffix D1 ---", t["d1_question"] + tail]
    for b in blocks:
        q = t["b1_question"].format(block=b["block"], page=b["page"], first_words=first_words(b["text"]))
        out += [f"--- suffix {b['block']} ---", q + tail]
    return "\n".join(out)


def main() -> int:
    problems: list[str] = []
    n_listed = 0
    for row in (FOLDER / "PROMPTS.sha256").read_text(encoding="utf-8").splitlines():
        value, name = row.split("  ", 1)
        n_listed += 1
        if hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() != value:
            problems.append(f"{name}: the SHA-256 differs from PROMPTS.sha256")
    raw = (FOLDER / "template.json").read_bytes()
    stored = json.loads(raw.decode("utf-8"))
    if hashlib.sha256(raw).hexdigest() != TEMPLATE_FILE_SHA256:
        problems.append("template.json: the SHA-256 of the file differs from the job records")
    if template_sha(stored) != TEMPLATE_SHA256 or stored.get("sha256") != TEMPLATE_SHA256:
        problems.append("template.json: the template SHA-256 differs")
    if stored.get("template_id") != TEMPLATE_ID:
        problems.append("template.json: the template id differs")
    built = None
    try:
        built = build_template()
    except (ValueError, KeyError, OSError) as e:
        problems.append(f"the text files do not give a template: {e!r}")
    if built is not None:
        if built != stored:
            keys = sorted(k for k in set(built) | set(stored) if built.get(k) != stored.get(k))
            problems.append(f"the template from the text files differs from template.json in: {', '.join(keys)}")
        if built["sha256"] != TEMPLATE_SHA256:
            problems.append("the template SHA-256 of the template from the text files differs")
        if (json.dumps(built, ensure_ascii=False, indent=1) + "\n").encode("utf-8") != raw:
            problems.append("the template from the text files does not give the bytes of template.json")
    for p in problems:
        print(f"FAIL  {p}")
    if not problems:
        print(f"PASS  prompts/{TEMPLATE_ID}: {n_listed} files equal to PROMPTS.sha256; template.json has the file "
              f"SHA-256 {TEMPLATE_FILE_SHA256[:8]}...; the template from the {len(TEXT_FILES)} text files is equal "
              f"to template.json (value and bytes); template SHA-256 {built['sha256']}")
    if "--example" in sys.argv[1:] and built is not None:
        print(example(built))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
