# SPDX-License-Identifier: Apache-2.0
"""Check the English project files against the writing rules of the project and its glossary.

The writing rules follow ASD-STE100 (Simplified Technical English, Issue 9) with project terms.

What the script examines (it does not replace a dictionary check of ASD-STE100):

1. Sentence length: procedural sentences (start with an imperative verb) max 20 words,
   descriptive sentences max 25 words. Text in code format, links and quotes counts as one word.
2. Status words: words in capitals with 4 or more letters must be a permitted status value
   (the list STATUS below) or a known acronym.
3. Words with more than one meaning in this project:
   - "gold" only in "gold set";
   - "test" only in "test set", "test document(s)", "test parliament(s)";
   - "reviewer" only in "human reviewer";
   - "section" not followed by a number (use "chapter");
   - "pipeline step" (use "pipeline stage");
   - "level" only in "state level", "isolation level", "labeling level", "conformance level";
   - "draft" only in "draft segmentation", "draft labels", "working draft".
4. German words outside code format, links and quotes.
5. Words that end in "-ing" and are not in the list of technical names (for a manual check).

Usage:  python3 src/m00_pruefe_dokumente.py [files ...]
        Without arguments: README.md of the repository, track_2a/README.md,
        track_2a/technical_report.md, track_2a/docs/*.md.
Exit code: 0 if no rule 1 to 4 finding, else 1. Rule 5 only gives notes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # repository root (this file: track_2a/src/)

STATUS = {"OPEN", "IN WORK", "DONE", "OUT OF ORDER", "MET", "NOT MET", "ACCEPTED", "RELEASED",
          "NOT RELEASED", "EXCEPTION", "SUPERSEDED", "HISTORICAL", "DECIDED", "DECIDED BY DELEGATION",
          "PROPOSED", "UNDECIDED", "PASS", "FAIL", "UNSURE"}
STATUS_WORDS = {w for s in STATUS for w in s.split()}
ACRONYMS = {"JSON", "YAML", "HTML", "SPARQL", "SSSOM", "FRBR", "SKOS", "PROV", "CSCS", "PEFT", "CUDA",
            "JOLUX", "README", "LINKML", "CRISP", "SHACL", "UTF", "NFKC", "BASE", "TODO", "MLX", "OCR",
            "CEST", "AKN", "IRIS", "URLS", "PDFS", "JATS", "RELAX", "EPFL", "CLARIN", "ICML",
            "HTTP", "LOCAL"}
IMPERATIVES = {"use", "write", "do", "start", "stop", "run", "make", "keep", "put", "give", "find",
               "measure", "examine", "send", "record", "select", "add", "remove", "compare", "report",
               "set", "train", "read", "take", "move", "change", "show", "fix", "define", "convert",
               "publish", "submit", "divide", "decide", "deliver", "prepare", "calculate", "describe",
               "download", "verify", "include", "get", "ask", "list", "name", "map", "relate"}
TECH_ING = {"training", "labeling", "modeling", "understanding", "string", "thing", "during",
            "nothing", "something", "anything", "everything", "evening", "morning", "ring",
            "king", "spring", "bring", "sing", "rating", "according", "following", "missing",
            "scaling", "checkpointing", "streaming", "meeting", "building", "setting", "heading",
            "docling", "hugging", "mining", "learning", "wording", "meaning", "mapping", "working",
            "getting"}
GERMAN = {"und", "nicht", "mit", "für", "ist", "sind", "der", "die", "das", "dem", "den", "des",
          "ein", "eine", "einer", "auf", "von", "zu", "bei", "aus", "oder", "wird", "werden",
          "auch", "noch", "nur", "wie", "über", "Geschäft", "Geschäfte", "Antwort", "Frage",
          "Vorstoss", "Entscheid", "Abschnitt", "Einheit"}
LEVEL_OK = ("state level", "isolation level", "labeling level", "conformance level", "conformance levels",
            "state levels")
TEST_OK = ("test set", "test sets", "test document", "test documents", "test parliament",
           "test parliaments")
DRAFT_OK = ("draft segmentation", "draft segmentations", "draft labels", "working draft")


def default_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "track_2a/README.md", ROOT / "track_2a/technical_report.md"]
    files += sorted((ROOT / "track_2a/docs").glob("*.md"))
    return files


def plain(line: str) -> str:
    """Line without code spans, links, URLs and quotes (each becomes the word X)."""
    s = re.sub(r"`[^`]*`", "X", line)
    s = re.sub(r"\[([^\]]*\.md|[^\]]*/[^\]]*)\]\([^)]*\)", "X", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"https?://\S+", "X", s)
    s = re.sub(r"\"[^\"]*\"", "X", s)
    s = re.sub(r"«[^»]*»", "X", s)
    return s


def sentences(text: str) -> list[str]:
    parts = text.split("|") if text.strip().startswith("|") else [text]
    out = []
    for part in parts:
        part = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", part.strip())
        part = re.sub(r"<br>", " ", part)
        out += [x for x in re.split(r"(?<=[.!?:;])\s+", part) if x.strip()]
    return out


def words(sentence: str) -> list[str]:
    return [w for w in re.split(r"\s+", sentence) if re.search(r"[A-Za-z0-9]", w)]


def check(path: Path) -> tuple[list[str], list[str]]:
    findings, notes = [], []
    in_code = False
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.strip().startswith(">") or re.match(r"^\|[-| ]+\|$", line.strip()):
            continue
        p = plain(line)
        where = f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}:{no}"
        for s in sentences(p):
            w = words(s)
            first = re.sub(r"[^A-Za-z]", "", w[0]).lower() if w else ""
            limit = 20 if first in IMPERATIVES else 25
            if len(w) > limit:
                findings.append(f"{where}: rule 1, {len(w)} words (max {limit}): {s[:90]}")
        for m in re.finditer(r"\b[A-Z][A-Z]{3,}\b", p):
            if m.group(0) not in STATUS_WORDS and m.group(0) not in ACRONYMS:
                findings.append(f"{where}: rule 2, status or capital word not permitted: {m.group(0)}")
        low = p.lower()
        for m in re.finditer(r"\bgold\b", low):
            if not low[m.start():].startswith("gold set"):
                findings.append(f"{where}: rule 3, 'gold' without 'set'")
        for m in re.finditer(r"\btest\b", low):
            if not any(low[m.start():].startswith(x) for x in TEST_OK):
                findings.append(f"{where}: rule 3, 'test' outside test set/document/parliament")
        for m in re.finditer(r"\breviewers?\b", low):
            if not low[max(0, m.start() - 6):m.start()].endswith("human "):
                findings.append(f"{where}: rule 3, 'reviewer' without 'human'")
        for m in re.finditer(r"\bsections? \d", low):
            findings.append(f"{where}: rule 3, 'section' with a number (use 'chapter')")
        if "pipeline step" in low:
            findings.append(f"{where}: rule 3, 'pipeline step' (use 'pipeline stage')")
        for m in re.finditer(r"\blevels?\b", low):
            ctx = low[max(0, m.start() - 12):m.end() + 1]
            if not any(x in ctx for x in LEVEL_OK):
                findings.append(f"{where}: rule 3, 'level' without a defined qualifier")
        for m in re.finditer(r"\bdrafts?\b", low):
            ctx = low[max(0, m.start() - 8):m.start() + 20]
            if not any(x in ctx for x in DRAFT_OK):
                findings.append(f"{where}: rule 3, 'draft' without a defined qualifier")
        for wd in re.findall(r"\b[\wäöüÄÖÜ]+\b", p):
            if wd in GERMAN:
                findings.append(f"{where}: rule 4, German word: {wd}")
            if wd.lower().endswith("ing") and wd.lower() not in TECH_ING and len(wd) > 4:
                notes.append(f"{where}: rule 5, -ing word: {wd}")
    return findings, notes


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return 0
    files = [Path(a).resolve() for a in sys.argv[1:]] or default_files()
    all_f, all_n = [], []
    for f in files:
        fi, no = check(f)
        all_f += fi
        all_n += no
    for x in all_f:
        print(x)
    print(f"findings (rules 1 to 4): {len(all_f)}")
    for x in sorted(set(all_n)):
        print(x)
    print(f"notes (rule 5): {len(set(all_n))}")
    return 1 if all_f else 0


if __name__ == "__main__":
    sys.exit(main())
