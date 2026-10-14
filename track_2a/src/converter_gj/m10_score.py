# SPDX-License-Identifier: Apache-2.0
"""Scorer of gate GJ: an answer set against the AI references at the isolation level L9 and for the 6 options of
each Docling block.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream F
of the plan `crisp-dm/00-cross-cutting/plan-full-conversion.md` (chapter 3.4 item 9, chapter 6.3 items 3 and 6).
Phase 4 (modeling), gate GJ (OPEN). Status: EXCEPTION (process rule 10). This file gives no gate result.

1 Copies (not imports)
  The plan says that this scorer copies the lower functions and uses its own document table. Thus this file
  imports no function of `m03_ladder.py` and of `m05_gate3a_v4_measure.py`. Copied without a change of the
  formulas:
  - from `m03_iso_v4.py`: `TEXT`, `ANSWERS`, `carried_ids`, `boundaries`, `_betai`, `jeffreys_lower`;
  - from `m03_sub_common.py`: `FAMILY`, `AUTHOR_FAMILIES`, `role_of`, `ROLE_DEFAULT_FAMILY`, `DEFAULT_TYPE`;
  - from `m03_ladder.py`: `cmap`, `block_form`, `mask`, `blocks`, `doc_counts`, `f1`, `lower_f1`, `aggregate`,
    `role`, `trivial_role`, the scope rules `written_affair` and `role_agreement`;
  - from `m05_gate3a_v4_measure.py`: `measure_level`.
  The changes are only in the access to the data: a function reads the atom ids, the fixed answers and the
  carried atoms from the document table of this file (not from `m03_sub_common.load()`), the S1 roles come
  from the answer set (not from `m03_ladder.SIG`), and the claim flags come from the answer set. The check
  script `src/m10_score_test.py` compares each copy with the original function on synthetic data.

2 Document table (`doc_entry`)
  For each document: the atom ids and the Docling block of each atom from `daten/iso/atome/<doc>.json`, the
  fixed answers (rules R1, R3, R4, R5 of `m03_iso_hilfe.fixed_roles`, mapped as `m03_iso_v4.fixed_answers`
  does), and the carried atoms (footnotes and captions outside a picture). The paths are explicit. The
  fallbacks of `m03_iso_paths` (`iso_path`, `pdf_path`) are never reached: the guard first checks that the
  atom file and the Docling file of the document exist in `daten/iso`.

3 References
  Atoms (isolation level L9): the E20 answers of `daten/iso/v4/ref41/<doc>.json` (group documents) or
  `daten/iso/v4/pool_ref41/<doc>.json` (pool documents). With the pilot overrides (default of the command
  `score`, plan chapter 2.1 item 3): for 879163, 375917 and 549658 the answers of the review record of the author
  (`daten/gold/records/review/<doc>/provenance.yaml`, `m03_gold_record.derive`). The command `reproduce` uses
  no override, because the stored values used ref41 and pool_ref41.
  Docling blocks: the 6 options of `daten/gj/labels/<doc>.json` (interface 4, stream B), or with
  `--block-ref derived` the majority option of the atom reference (`block_option`).

4 Options of a Docling block (interface 4; shared with `m10_rules.py`)
  Map of the 13 E20 answers to the 6 options: submitted, reasoning, response, recommendation; title and
  short_title -> title; summary, committee_recommendation, speech, proposition, vote, none and furniture ->
  none. The option of a block is the option with the most atoms of the block. If two options have the same
  count, the option with more characters of atom text wins, then the first option in the order above (the rule
  of `m10_labels.block_option`, stream B). `mixed` is true when the atoms of the block have more than one E20
  answer (as in the label files).

5 Answer sets (`load_answer_set`)
  rules      `daten/gj/rules/<doc>.json` of `m10_rules.py`: the nos4 answers of each atom, the L9 claim flag,
             the rule option of each block, the D1 option and the S1 roles.
  decisions  `daten/gj/decisions/<doc>.json` (interface 7): the option of each block, the D1 option. Each atom
             gets the E20 answer of the option of its block (submitted, reasoning, response, recommendation,
             title, none); an atom with a fixed answer keeps it. The cascade does not abstain: claim = true.
  atoms      a folder of answer files in the format of `m03_iso_v4.write` ({doc_id, ids, answers}); claim =
             true; the block options come from `block_option`.

6 Values (`score_set`)
  L9 (map SLOT_NOTITLE, block form, exact rule exact_block; definitions of `daten/iso/ladder/ladder.json`), two
  times: on the documents that the answer set claims, and on all documents (no abstention). Each time: exact
  documents with the Jeffreys lower bound; switch-document exact in two forms (`switch_l9`: the reference has 2
  or more blocks after the map, the stratum of the stored values; `switch_sr`: the family sequence of the
  `SPONSOR` and `EXECUTIVE` text atoms of the reference changes at least once, the Submission <-> Response switch of
  the plan); labelled boundary F1 with the lower bound; text intrusion, omission and class error; block omission
  and intrusion.
  Docling blocks: 6-option accuracy, L9-family accuracy (submitted and reasoning -> submitted; response and
  recommendation -> response; title and none -> none), recall, precision and F1 of each option, macro F1, the
  confusion table. `--exclude-tiers` removes the blocks whose rule tier (from `daten/gj/rules`) is in the list,
  for each answer set in the same way (paired comparison).
  D1: accuracy and confusion when the answer set and the block reference give a D1 option.
  Each value has the counts. The output also has one line for each document (counts and flags, no text).

7 Reproduction before any other use (command `reproduce`, plan chapter 6.3 item 6)
  The stored nos4 answers (`daten/iso/ladder/scratch/err_recompose_nos4_<split>.json`) with the stored claim
  flags (`daten/iso/ladder/results.json`) and the stored S1 combined roles, scored by this file, must give the
  stored values of `results.json` (`levels.L9.methods.nos4.dev` and `.eval`): dev 99 of 124 exact, labelled
  boundary F1 0.655 (19 correct, 33 reference and 25 method boundaries), switch 19 of 30; eval 15 of 15. The
  command also compares the document table with `m03_sub_common.load()` (atom ids and fixed answers of the 205
  documents) and the stored claim flags with the scope rule role_agreement on the stored S1 roles. It writes
  `daten/gj/runs/m10_score_reproduction.json`. The command `score` refuses to run when that record is missing,
  when its status is not MET, or when the SHA-256 of this file is not the SHA-256 in the record.
  The stored eval set (groups 4 to 6) has 7 documents of group 7 parliaments. Their values are part of the
  stored values, so the command reproduces them; it computes no other value on them.

8 Guards (process rule 6)
  A document must be a Docling document that is not a test document: the atom file and the Docling file exist in `daten/iso`, the
  id is not in `daten/gold/test.csv` or `daten/gold/bulk_test.csv` (ids only), and its parliament
  (`daten/analyse/dokumente/dokumente_merkmale.csv.gz`) has the role Training or Validierung in
  `daten/analyse/synthese/split.csv`. A document of a group 7 parliament or of the final group 7 needs
  `--allow-group7` (plan: one report-only run after the method freeze). No path under `daten/gold/test` is read.
  The scorer never scores the 26 reviewed records of test documents.

Usage (from the project folder):
  `uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python src/m10_score.py reproduce`
  `(same uv options) python src/m10_score.py score --answers rules|decisions|atoms --dir <folder>`
  `  (--set daten/gj/sets.json:<key> | --doc <id> ...) --out daten/gj/scores/<name>.json`
  `  [--block-ref labels|derived] [--labels-dir daten/gj/labels] [--no-pilot-overrides]`
  `  [--exclude-tiers <tier,...>] [--rules-dir daten/gj/rules] [--allow-group7]`
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

SCORER_VERSION = "m10-score-1"
SCORER_PATH = Path(__file__).resolve()
ATOMS_DIR = ROOT_DIR / "daten/iso/atome"
DOCLING_DIR = ROOT_DIR / "daten/iso/docling"
REF41 = ROOT_DIR / "daten/iso/v4/ref41"
POOL41 = ROOT_DIR / "daten/iso/v4/pool_ref41"
GOLD_REVIEW = ROOT_DIR / "daten/gold/records/review"
LADDER_JSON = ROOT_DIR / "daten/iso/ladder/ladder.json"
LADDER_SHA = "1b040f8cde2c5bcbb0b8575ade123bcb81ce73b46a05872c4edf743386da8652"   # FROZEN_FILES value
RESULTS_JSON = ROOT_DIR / "daten/iso/ladder/results.json"
SCRATCH = ROOT_DIR / "daten/iso/ladder/scratch"
S1_DIR = ROOT_DIR / "daten/iso/sub/s1_role"
GROUPS_CSV = ROOT_DIR / "daten/iso/gruppen.csv"
SPLIT_CSV = ROOT_DIR / "daten/analyse/synthese/split.csv"
MERKMALE = ROOT_DIR / "daten/analyse/dokumente/dokumente_merkmale.csv.gz"
TEST_LISTS = (ROOT_DIR / "daten/gold/test.csv", ROOT_DIR / "daten/gold/bulk_test.csv")
TEST_DIR = ROOT_DIR / "daten/gold/test"
GJ = ROOT_DIR / "daten/gj"
RUNS = GJ / "runs"
REPRODUCTION = RUNS / "m10_score_reproduction.json"
PILOTS = ("879163", "375917", "549658")         # plan chapter 2.1 item 3
LEVEL_ID = "L9"

# ------------------------------------------------------------------ copies of m03_iso_v4 (no change)
TEXT = ("title", "short_title", "submitted", "reasoning", "response", "recommendation", "summary",
        "committee_recommendation", "speech", "proposition", "vote")
ANSWERS = TEXT + ("none", "furniture")
TEXT_SET = set(TEXT)

# ------------------------------------------------------------------ copies of m03_sub_common (no change)
FAMILY = {
    "title": "TITLE", "short_title": "TITLE",
    "submitted": "SPONSOR", "reasoning": "SPONSOR",
    "response": "EXECUTIVE", "recommendation": "EXECUTIVE",
    "committee_recommendation": "COMMITTEE",
    "speech": "PLENARY", "proposition": "PLENARY", "vote": "PLENARY",
    "summary": "SUMMARY",
    "none": "FRAME",
    "furniture": "FURNITURE",
}
AUTHOR_FAMILIES = ("SPONSOR", "EXECUTIVE", "COMMITTEE", "PLENARY", "SUMMARY")
DEFAULT_TYPE = {"TITLE": "title", "SPONSOR": "submitted", "EXECUTIVE": "response",
                "COMMITTEE": "committee_recommendation", "PLENARY": "vote", "SUMMARY": "summary"}
ROLE_DEFAULT_FAMILY = {"proposal": "SPONSOR", "response": "EXECUTIVE", "combined": "SPONSOR",
                       "minutes": "PLENARY", "committee": "COMMITTEE", "other": "SPONSOR"}
AUTHOR = ("proposal", "response", "combined")


def role_of(families) -> str:
    """S1: the document role from the families of the text atoms (TITLE is not an author)."""
    a = set(families) & set(AUTHOR_FAMILIES)
    if "PLENARY" in a:
        return "minutes"
    if "COMMITTEE" in a:
        return "committee"
    if {"SPONSOR", "EXECUTIVE"} <= a:
        return "combined"
    if "SPONSOR" in a:
        return "proposal"
    if "EXECUTIVE" in a:
        return "response"
    return "other"


# ------------------------------------------------------------------ the 6 options (interface 4)
OPTIONS = ("submitted", "reasoning", "response", "recommendation", "title", "none")
OPTION_OF_ANSWER = {
    "submitted": "submitted", "reasoning": "reasoning", "response": "response", "recommendation": "recommendation",
    "title": "title", "short_title": "title",
    "summary": "none", "committee_recommendation": "none", "speech": "none", "proposition": "none", "vote": "none",
    "none": "none", "furniture": "none",
}
assert set(OPTION_OF_ANSWER) == set(ANSWERS)
ANSWER_OF_OPTION = {"submitted": "submitted", "reasoning": "reasoning", "response": "response",
                    "recommendation": "recommendation", "title": "title", "none": "none"}
L9_FAMILY_OF_OPTION = {"submitted": "submitted", "reasoning": "submitted", "response": "response",
                       "recommendation": "response", "title": "none", "none": "none"}
D1_OPTIONS = ("A", "B", "C", "D")


def block_option(answers: list[str], chars: list[int]) -> tuple[str, bool]:
    """(option of the block, mixed) from the E20 answers of its atoms and the characters of their texts. The
    most atoms win; for the same count, more characters win, then the order of OPTIONS (as m10_labels). mixed:
    more than one E20 answer. A block without atoms has the option none."""
    if not answers:
        return "none", False
    n, ch = Counter(), Counter()
    for a, c in zip(answers, chars, strict=True):
        n[OPTION_OF_ANSWER[a]] += 1
        ch[OPTION_OF_ANSWER[a]] += c
    top = max(n.values())
    cand = [o for o in OPTIONS if n[o] == top]
    best = max(ch[o] for o in cand)
    return next(o for o in cand if ch[o] == best), len(set(answers)) > 1


def d1_of_answers(answers: list[str]) -> str:
    """D1 option from the author families SPONSOR and EXECUTIVE of the text atoms (plan chapter 3.3 item 2):
    A only SPONSOR, B only EXECUTIVE, C both, D neither. Committee, vote and speech text do not force D."""
    fam = {FAMILY[x] for x in answers if x in TEXT_SET}
    s, e = "SPONSOR" in fam, "EXECUTIVE" in fam
    return "C" if s and e else "A" if s else "B" if e else "D"


# ------------------------------------------------------------------ small helpers
def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT_DIR).as_posix() if p.is_relative_to(ROOT_DIR) else str(p)


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def canonical_sha(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ratio(a, b):
    return a / b if b else None


def read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Refused(ValueError):
    """A guard of chapter 8 refuses a document or a path."""


# ------------------------------------------------------------------ guards (chapter 8)
@lru_cache(maxsize=1)
def protected() -> dict:
    """Ids and parliaments of the final group 7, group 7 parliaments, parliament roles, test ids (ids only)."""
    groups = read_csv(GROUPS_CSV)
    g7 = [r for r in groups if r["group"] == "7"]
    return {"g7_ids": frozenset(r["doc_id"] for r in g7), "g7_parliaments": frozenset(r["body_key"] for r in g7),
            "roles": {r["body_key"]: r["rolle"] for r in read_csv(SPLIT_CSV)},
            "test_ids": frozenset(r["doc_id"].strip() for p in TEST_LISTS if p.exists() for r in read_csv(p))}


def parliaments(ids: list[str]) -> dict[str, str]:
    """Parliament (body_key) of each document from dokumente_merkmale.csv.gz (as m00_pruefe_testset.doc_bodies)."""
    want, out = set(ids), {}
    with gzip.open(MERKMALE, "rt", newline="", encoding="utf-8") as f:
        for z in csv.DictReader(f):
            if z["id"] in want:
                out[z["id"]] = z["body_key"]
    return out


def check_path(p: Path) -> Path:
    """No path inside the folder of the test documents (process rule 6)."""
    if Path(p).resolve().is_relative_to(TEST_DIR.resolve()):
        raise Refused(f"{rel(p)}: path in daten/gold/test (process rule 6): refused")
    return Path(p)


def split_of(d: str, body_key: str | None, allow_group7: bool) -> str:
    """dev | validation | group7 of a non-test Docling document. Else Refused."""
    d = str(d)
    pr = protected()
    if not d.isdigit():
        raise Refused(f"{d}: not a document id")
    if d in pr["test_ids"]:
        raise Refused(f"{d}: test document (process rule 6): refused")
    if not (ATOMS_DIR / f"{d}.json").exists() or not (DOCLING_DIR / f"{d}.json").exists():
        raise Refused(f"{d}: no atom file or no Docling file in daten/iso: refused")
    role = pr["roles"].get(body_key or "")
    if body_key is None or role is None:
        raise Refused(f"{d}: unknown parliament: refused")
    if role == "Gold":
        raise Refused(f"{d}: document of a test parliament (process rule 6): refused")
    if d in pr["g7_ids"] or body_key in pr["g7_parliaments"]:
        if not allow_group7:
            raise Refused(f"{d}: group 7 document: only with --allow-group7 (report-only run after the freeze)")
        return "group7"
    if role == "Training":
        return "dev"
    if role == "Validierung":
        return "validation"
    raise Refused(f"{d}: parliament role {role!r}: refused")


# ------------------------------------------------------------------ document table (chapter 2)
def carried_ids(atoms: list[dict]) -> set[str]:
    """Copy of m03_iso_v4.carried_ids."""
    return {a["id"] for a in atoms if a["label"] == "footnote" or (a["label"] == "caption" and a.get("eltern") != "picture")}


@dataclass(frozen=True)
class DocEntry:
    doc_id: str
    ids: tuple
    block_of: tuple            # Docling block id of each atom
    chars: tuple               # characters of the text of each atom (tie rule of block_option)
    fixed: dict                # {atom id: furniture | none} (rules R1, R3, R4, R5)
    fixed_rule: dict           # {atom id: R1 | R3 | R4 | R5}
    carried: frozenset         # positions of the carried atoms
    block_order: tuple         # Docling block ids in reading order
    atoms_sha256: str

    def block_index(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for i, b in enumerate(self.block_of):
            out.setdefault(b, []).append(i)
        return out


def fixed_of(doc_id: str, atoms: list[dict]) -> tuple[dict, dict]:
    """({atom: answer}, {atom: rule id}) as m03_iso_v4.fixed_answers. The atom file and the Docling file are the
    files of daten/iso (checked by the guard), so m03_iso_hilfe.page_heights reads the Docling file of daten/iso."""
    import m03_iso_hilfe as hf

    if not (DOCLING_DIR / f"{doc_id}.json").exists():
        raise Refused(f"{doc_id}: no Docling file in daten/iso")
    out, rule_of = {}, {}
    for a, (_, rule) in hf.fixed_roles(doc_id, atoms)[0].items():
        if rule.startswith(("R1", "R4", "R5")):
            out[a], rule_of[a] = "furniture", rule.split()[0]
        elif rule.startswith("R3"):
            out[a], rule_of[a] = "none", rule.split()[0]
    return out, rule_of


@lru_cache(maxsize=None)
def doc_entry(doc_id: str) -> DocEntry:
    """The table line of a document. The caller must run the guard (split_of) first."""
    p = ATOMS_DIR / f"{doc_id}.json"
    if not p.exists():
        raise Refused(f"{doc_id}: no atom file in daten/iso/atome")
    raw = p.read_bytes()
    atoms = json.loads(raw.decode("utf-8"))["atome"]
    fixed, rule_of = fixed_of(doc_id, atoms)
    carried = carried_ids(atoms)
    ids = tuple(a["id"] for a in atoms)
    order: list[str] = []
    for a in atoms:
        if not order or order[-1] != a["block"]:
            order.append(a["block"])
    if len(set(order)) != len(order):
        raise SystemExit(f"{doc_id}: the atoms of a Docling block are not consecutive")
    return DocEntry(doc_id, ids, tuple(a["block"] for a in atoms), tuple(len(a.get("text") or "") for a in atoms),
                    fixed, rule_of,
                    frozenset(i for i, a in enumerate(ids) if a in carried), tuple(order),
                    hashlib.sha256(raw).hexdigest())


# ------------------------------------------------------------------ ladder definitions (read only)
@lru_cache(maxsize=1)
def ladder() -> dict:
    got = sha256(LADDER_JSON)
    if got != LADDER_SHA:
        raise SystemExit(f"ladder.json has SHA-256 {got}, frozen value {LADDER_SHA}")
    lj = json.loads(LADDER_JSON.read_text(encoding="utf-8"))
    lv = next(x for x in lj["levels"] if x["id"] == LEVEL_ID)
    level = {"id": lv["id"], "map": lv["collapse_map_id"], "scope": lv["scope_rule"]["id"],
             "zones": [z["id"] for z in lv["abstention_rule"]["zones"]], "unit": lv["unit_rule"]["id"],
             "exact_rule": lv["metrics"]["exact_rule"]}
    want = {"map": "SLOT_NOTITLE", "scope": "role_agreement", "zones": [], "unit": "block", "exact_rule": "exact_block"}
    if any(level[k] != v for k, v in want.items()):
        raise SystemExit(f"definition of {LEVEL_ID} differs from the frozen definition: {level}")
    return {"level": level, "maps": lj["rule_library"]["collapse_maps"]}


# ------------------------------------------------------------------ copies of m03_iso_v4 (pure functions)
def boundaries(ref: list[str], hyp: list[str], skip: set[int]):
    """Copy of m03_iso_v4.boundaries."""
    seq = [i for i, x in enumerate(ref) if x in TEXT and i not in skip]
    br, bh, good, inner = set(), set(), set(), set()
    prev_r = prev_h = None
    for k, i in enumerate(seq):
        r = ref[i]
        h = hyp[i] if hyp[i] in TEXT else prev_h
        if k > 0 and r != prev_r:
            br.add(k)
            if prev_r != "title":
                inner.add(k)
        if k > 0 and prev_h is not None and h != prev_h:
            bh.add(k)
            if h == r and prev_h == prev_r:
                good.add(k)
        prev_r, prev_h = r, h
    return br, bh, good, inner


def _betai(a: float, b: float, x: float) -> float:
    """Copy of m03_iso_v4._betai (regularized incomplete beta function, Numerical Recipes 6.4)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)

    def cf(a, b, x):
        qab, qap, qam = a + b, a + 1, a - 1
        c, d = 1.0, 1 - qab * x / qap
        d = 1 / (d if abs(d) > 1e-30 else 1e-30)
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-30 else 1e-30)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-30 else 1e-30
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-30 else 1e-30)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-30 else 1e-30
            de = d * c
            h *= de
            if abs(de - 1) < 1e-12:
                break
        return h

    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * cf(a, b, x) / a
    return 1 - math.exp(lbt) * cf(b, a, 1 - x) / b


def jeffreys_lower(x: int, n: int, level: float = 0.95) -> float | None:
    """Copy of m03_iso_v4.jeffreys_lower."""
    if n == 0:
        return None
    if x == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _betai(x + 0.5, n - x + 0.5, mid) < 1 - level:
            lo = mid
        else:
            hi = mid
    return round(lo, 4)


# ------------------------------------------------------------------ copies of m03_ladder (table access changed)
def cmap(name: str, a: list[str]) -> list[str]:
    m = ladder()["maps"][name]
    return [m[x] for x in a]


def role(h: list[str]) -> str:
    return role_of(FAMILY[x] for x in h if x in TEXT_SET)


def scope_written_affair(h: list[str], s1_combined: str) -> bool:
    return role(h) in AUTHOR and s1_combined in AUTHOR


def scope_role_agreement(h: list[str], s1_rule: str, s1_combined: str) -> bool:
    return scope_written_affair(h, s1_combined) and role(h) == s1_rule


def block_form(hm: list[str], e: DocEntry) -> list[str]:
    """Block unit: each atom without a fixed answer gets the text answer of the run before it; before the first
    run, the answer of the first run."""
    fx, ids = e.fixed, e.ids
    first = next((i for i, x in enumerate(hm) if x in TEXT_SET), None)
    if first is None:
        return list(hm)
    out, prev = list(hm), hm[first]
    for i, x in enumerate(hm):
        if x in TEXT_SET:
            prev = x
        elif ids[i] not in fx:
            out[i] = prev
    return out


def converter_view(lv: dict, e: DocEntry, h_raw: list[str]) -> tuple[list[str], set]:
    """The answers after the map and the unit form, and the zone (L9 has no zone)."""
    if lv["zones"]:
        raise SystemExit("zones are not copied: the isolation level must have no zone")
    hm = cmap(lv["map"], h_raw)
    if lv["unit"] == "block":
        hm = block_form(hm, e)
    return hm, set()


def mask(a: list[str], zone: set) -> list[str]:
    return ["none" if i in zone and x in TEXT_SET else x for i, x in enumerate(a)]


def blocks(a):
    out, cur, cls = [], [], None
    for i, x in enumerate(a):
        if x in TEXT_SET:
            if cls is not None and x != cls:
                out.append((cls, cur))
                cur = []
            cls = x
            cur.append(i)
    if cur:
        out.append((cls, cur))
    return out


def doc_counts(e: DocEntry, r, h):
    br, bh, good, inner = boundaries(r, h, set(e.carried))
    om = sum(1 for x, y in zip(r, h) if x in TEXT_SET and y not in TEXT_SET)
    it = sum(1 for x, y in zip(r, h) if y in TEXT_SET and x not in TEXT_SET)
    both = sum(1 for x, y in zip(r, h) if x in TEXT_SET and y in TEXT_SET)
    ce = sum(1 for x, y in zip(r, h) if x in TEXT_SET and y in TEXT_SET and x != y)
    rt = {i for i, x in enumerate(r) if x in TEXT_SET}
    ht = {i for i, x in enumerate(h) if x in TEXT_SET}
    bo = sum(1 for _, b in blocks(r) if not (set(b) & ht))
    bi = sum(1 for _, b in blocks(h) if not (set(b) & rt))
    bnd_ok = good == br and bh == br
    return dict(br=len(br), bh=len(bh), good=len(good), inner=len(inner), om=om, it=it, both=both, ce=ce,
                tr=len(rt), th=len(ht), bo=bo, bi=bi,
                exact_atom=bnd_ok and om == 0 and it == 0 and ce == 0,
                exact_block=bnd_ok and om == 0 and ce == 0 and bo == 0 and bi == 0,
                exact_document={x for x in r if x in TEXT_SET} == {x for x in h if x in TEXT_SET})


def f1(tp, nh, nr, nd=4):
    p = tp / nh if nh else 0.0
    q = tp / nr if nr else 0.0
    if not p + q:
        return 0.0
    v = 2 * p * q / (p + q)
    return round(v, nd) if nd is not None else v


def lower_f1(tp, nh, nr):
    lp, lr = jeffreys_lower(tp, nh) or 0.0, jeffreys_lower(tp, nr) or 0.0
    return round(2 * lp * lr / (lp + lr), 4) if lp and lr else 0.0


def aggregate(rows: list[dict], exact_rule: str) -> dict:
    c = Counter()
    for x in rows:
        for k, v in x.items():
            c[k] += int(v)
    n = len(rows)
    ex = c[exact_rule]
    dom = sum(1 for x in rows if x["om"] > 0)
    return {"documents": n, "boundaries_ref": c["br"], "boundaries_hyp": c["bh"], "correct": c["good"],
            "labelled_f1": f1(c["good"], c["bh"], c["br"]), "labelled_f1_lower": lower_f1(c["good"], c["bh"], c["br"]),
            "inner_boundaries_ref": c["inner"],
            "text_omission": round(c["om"] / c["tr"], 4) if c["tr"] else None,
            "documents_with_omission": dom,
            "documents_with_omission_share": round(dom / n, 4) if n else None,
            "text_intrusion": round(c["it"] / c["th"], 4) if c["th"] else None,
            "text_class_error": round(c["ce"] / c["both"], 4) if c["both"] else None,
            "block_omission": c["bo"], "block_intrusion": c["bi"],
            "documents_with_block_intrusion": sum(1 for x in rows if x["bi"] > 0),
            "exact_rule": exact_rule, "exact": ex, "exact_rate": round(ex / n, 4) if n else None,
            "exact_lower": jeffreys_lower(ex, n) if n else None, "exact_atom_rule": c["exact_atom"],
            "text_ref": c["tr"], "text_hyp": c["th"], "omitted": c["om"], "intruded": c["it"],
            "class_err_atoms": c["ce"], "both_text": c["both"],
            "unrounded": {"labelled_f1": f1(c["good"], c["bh"], c["br"], None),
                          "text_omission": c["om"] / c["tr"] if c["tr"] else None,
                          "documents_with_omission_share": dom / n if n else None,
                          "text_intrusion": c["it"] / c["th"] if c["th"] else None,
                          "text_class_error": c["ce"] / c["both"] if c["both"] else None,
                          "exact_rate": ex / n if n else None}}


def trivial_role(e: DocEntry, s1_combined: str) -> list[str]:
    """Trivial converter 'role only': each atom without a fixed answer gets the default answer of the S1
    combined role."""
    fam = ROLE_DEFAULT_FAMILY.get(s1_combined, "SPONSOR")
    fill = DEFAULT_TYPE[fam]
    return [e.fixed.get(a, fill) for a in e.ids]


def switch_sr(ref: list[str]) -> bool:
    """The family sequence of the SPONSOR and EXECUTIVE text atoms of the reference changes at least once."""
    seq = [FAMILY[x] for x in ref if x in TEXT_SET and FAMILY[x] in ("SPONSOR", "EXECUTIVE")]
    return any(a != b for a, b in zip(seq, seq[1:]))


# ------------------------------------------------------------------ copy of m05_gate3a_v4_measure.measure_level
def measure_level(lv: dict, docs: list[str], answers: dict, flags: dict, ref: dict, table: dict,
                  roles: dict | None = None) -> dict:
    """The answers against the reference at one isolation level: the loop of m03_ladder.measure with the claim
    flags of the answer set. Changes against the original: the table of this file; the claim flags are inputs
    (no check against a scope rule here); the trivial converter only when the S1 combined roles are given;
    no strata other than the switch strata, no frame share, no Apertus share."""
    rule = lv["exact_rule"]
    rows, trows, info, claimed, measured, no_record = [], [], [], [], [], []
    bf_changed = 0
    per_doc = {}
    for d in docs:
        e = table[d]
        hm, zone = converter_view(lv, e, answers[d])
        c = bool(flags[d])
        if lv["unit"] == "block":
            bf_changed += sum(1 for x, y in zip(cmap(lv["map"], answers[d]), hm) if x != y)
        rec = dict(doc=d, claimed=c, measured=False, ref_blocks="no record", exact=False, trivial_exact=False,
                   switch_sr=False)
        if c:
            claimed.append(d)
        r0 = ref.get(d)
        if not c or r0 is None:
            if c:
                no_record.append(d)
            info.append(rec)
            continue
        rz, hz = mask(cmap(lv["map"], r0), zone), mask(hm, zone)
        dc = doc_counts(e, rz, hz)
        rows.append(dc)
        measured.append(d)
        rec.update(measured=True, ref_blocks=min(len(blocks(rz)), 2), exact=bool(dc[rule]),
                   frame_atoms_in_text=dc["it"], text_atoms=dc["th"], switch_sr=switch_sr(r0))
        if roles is not None:
            tv = cmap(lv["map"], trivial_role(e, roles[d]))
            if lv["unit"] == "block":
                tv = block_form(tv, e)
            tc = doc_counts(e, rz, mask(tv, zone))
            trows.append(tc)
            rec["trivial_exact"] = bool(tc[rule])
        info.append(rec)
        per_doc[d] = {"claimed": True, "exact": bool(dc[rule]), "reference_blocks": len(blocks(rz)),
                      "method_blocks": len(blocks(hz)), "switch_l9": len(blocks(rz)) >= 2, "switch_sr": switch_sr(r0),
                      "boundaries_ref": dc["br"], "boundaries_hyp": dc["bh"], "boundaries_correct": dc["good"],
                      "text_atoms_method": dc["th"], "intruded_atoms": dc["it"], "omitted_atoms": dc["om"],
                      "class_error_atoms": dc["ce"], "block_omission": dc["bo"], "block_intrusion": dc["bi"]}
    m = aggregate(rows, rule)
    tr = aggregate(trows, rule) if roles is not None else None
    sw = [r for r in info if r["measured"] and r["ref_blocks"] == 2]
    sr = [r for r in info if r["measured"] and r["switch_sr"]]
    return {
        "isolation_level": lv["id"], "map": lv["map"], "unit": lv["unit"], "exact_rule": rule,
        "documents_available": len(docs), "claimed": len(claimed), "claimed_without_record": len(no_record),
        "documents": m["documents"], "exact": m["exact"], "exact_rate": m["unrounded"]["exact_rate"],
        "exact_lower": m["exact_lower"], "coverage_documents": ratio(len(claimed), len(docs)),
        "trivial_role_same_documents": ({"exact": tr["exact"], "documents": tr["documents"]} if tr else None),
        "switch_l9": {"documents": len(sw), "exact": sum(1 for r in sw if r["exact"]),
                      "trivial_exact": (sum(1 for r in sw if r["trivial_exact"]) if roles is not None else None),
                      "definition": "reference with 2 or more blocks after the map (stratum ref_blocks 2)"},
        "switch_sr": {"documents": len(sr), "exact": sum(1 for r in sr if r["exact"]),
                      "definition": "the family sequence of the SPONSOR and EXECUTIVE text atoms of the reference "
                                    "changes at least once"},
        "labelled_f1": m["unrounded"]["labelled_f1"] if m["documents"] else None,
        "labelled_f1_lower": m["labelled_f1_lower"] if m["documents"] else None,
        "boundaries_ref": m["boundaries_ref"], "boundaries_hyp": m["boundaries_hyp"], "correct": m["correct"],
        "text_omission": m["unrounded"]["text_omission"], "omitted_atoms": m["omitted"],
        "text_intrusion": m["unrounded"]["text_intrusion"], "intruded_atoms": m["intruded"],
        "text_class_error": m["unrounded"]["text_class_error"],
        "block_omission": m["block_omission"], "block_intrusion": m["block_intrusion"],
        "documents_with_block_intrusion": m["documents_with_block_intrusion"],
        "block_form_changed_atoms": bf_changed,
        "claimed_documents": claimed, "measured_documents": measured,
        "exact_documents": [r["doc"] for r in info if r["measured"] and r["exact"]],
        "switch_l9_documents": [r["doc"] for r in sw], "switch_sr_documents": [r["doc"] for r in sr],
        "per_document": per_doc,
    }


# ------------------------------------------------------------------ block level and D1
def block_level(docs: list[str], hyp: dict, ref: dict, exclude: dict | None = None) -> dict:
    """6-option accuracy and L9-family accuracy over the Docling blocks. hyp, ref: {doc: {block: option}}.
    exclude: {doc: set of blocks} that are not counted."""
    conf: dict[str, Counter] = {o: Counter() for o in OPTIONS}
    n = ok6 = okf = skipped = 0
    per_doc = {}
    for d in docs:
        r, h = ref.get(d), hyp.get(d)
        if r is None:
            continue
        if set(h) != set(r):
            raise SystemExit(f"{d}: the blocks of the answer set and of the reference differ")
        ex = (exclude or {}).get(d, set())
        dn = d6 = df = 0
        for b, ro in r.items():
            if b in ex:
                skipped += 1
                continue
            ho = h[b]
            conf[ro][ho] += 1
            dn += 1
            d6 += ro == ho
            df += L9_FAMILY_OF_OPTION[ro] == L9_FAMILY_OF_OPTION[ho]
        n, ok6, okf = n + dn, ok6 + d6, okf + df
        per_doc[d] = {"blocks": dn, "correct_6": d6, "correct_l9_family": df, "excluded_blocks": len(ex & set(r))}
    per, f1s = {}, []
    for o in OPTIONS:
        tp = conf[o][o]
        nr = sum(conf[o].values())
        npred = sum(conf[x][o] for x in OPTIONS)
        p, q = ratio(tp, npred), ratio(tp, nr)
        f = 2 * p * q / (p + q) if p and q else 0.0
        if nr:
            f1s.append(f)
        per[o] = {"reference": nr, "predicted": npred, "correct": tp, "precision": p, "recall": q, "f1": f}
    return {"blocks": n, "excluded_blocks": skipped, "documents": len(per_doc),
            "accuracy_6": ratio(ok6, n), "correct_6": ok6, "accuracy_6_lower": jeffreys_lower(ok6, n),
            "accuracy_l9_family": ratio(okf, n), "correct_l9_family": okf,
            "macro_f1_6": (sum(f1s) / len(f1s)) if f1s else None, "per_option": per,
            "confusion_ref_to_hyp": {o: dict(conf[o]) for o in OPTIONS if conf[o]}, "per_document": per_doc}


def d1_level(docs: list[str], hyp: dict, ref: dict) -> dict:
    conf: dict[str, Counter] = {o: Counter() for o in D1_OPTIONS}
    n = ok = 0
    for d in docs:
        r, h = ref.get(d), hyp.get(d)
        if r is None or h is None:
            continue
        conf[r][h] += 1
        n += 1
        ok += r == h
    return {"documents": n, "correct": ok, "accuracy": ratio(ok, n), "accuracy_lower": jeffreys_lower(ok, n),
            "confusion_ref_to_hyp": {o: dict(conf[o]) for o in D1_OPTIONS if conf[o]}}


# ------------------------------------------------------------------ references (chapter 3)
def atom_reference(e: DocEntry, pilots: bool) -> tuple[list[str], str, str]:
    """(answers, source, SHA-256 of the file) of the E20 reference of one document."""
    d = e.doc_id
    if pilots and d in PILOTS:
        import yaml
        import m03_gold_record as gr

        p = check_path(GOLD_REVIEW / d / "provenance.yaml")
        prov = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not ((prov.get("review_run") or {}).get("datetime_finished")):
            raise SystemExit(f"{d}: the review record is not finished")
        ans = gr.derive(d, prov)
        if len(ans) != len(e.ids):
            raise SystemExit(f"{d}: the review record gives {len(ans)} answers for {len(e.ids)} atoms")
        return ans, "pilot", sha256(p)
    paths = [p for p in (REF41 / f"{d}.json", POOL41 / f"{d}.json") if p.exists()]
    if len(paths) != 1:
        raise SystemExit(f"{d}: {len(paths)} reference files in ref41 and pool_ref41 (one expected)")
    x = json.loads(paths[0].read_text(encoding="utf-8"))
    if x.get("ids") != list(e.ids):
        raise SystemExit(f"{rel(paths[0])}: atom ids differ from the atoms of {d}")
    bad = [a for a in x["answers"] if a not in ANSWERS]
    if bad:
        raise SystemExit(f"{rel(paths[0])}: answers outside of E20 v4: {sorted(set(bad))[:5]}")
    return x["answers"], "ref41" if paths[0].parent == REF41 else "pool_ref41", sha256(paths[0])


def options_of_atoms(e: DocEntry, answers: list[str]) -> dict[str, str]:
    """{block: option} by the majority rule of chapter 4."""
    idx = e.block_index()
    return {b: block_option([answers[i] for i in idx[b]], [e.chars[i] for i in idx[b]])[0] for b in e.block_order}


def block_reference(e: DocEntry, mode: str, labels_dir: Path, atom_ref: list[str] | None) -> tuple[dict, str | None, str]:
    """({block: option}, D1 option, source) of one document."""
    if mode == "derived":
        if atom_ref is None:
            raise SystemExit(f"{e.doc_id}: no atom reference for the derived block reference")
        return options_of_atoms(e, atom_ref), d1_of_answers(atom_ref), "derived from the atom reference"
    p = check_path(Path(labels_dir) / f"{e.doc_id}.json")
    if not p.exists():
        raise SystemExit(f"{rel(p)}: no label file (stream B); use --block-ref derived only on purpose")
    x = json.loads(p.read_text(encoding="utf-8"))
    got = {b["block"]: b["option"] for b in x["blocks"]}
    if list(got) != list(e.block_order):
        raise SystemExit(f"{rel(p)}: the blocks differ from the Docling blocks of {e.doc_id}")
    if any(o not in OPTIONS for o in got.values()):
        raise SystemExit(f"{rel(p)}: an option outside of {OPTIONS}")
    return got, x.get("d1"), f"{rel(p)} ({x.get('reference')})"


# ------------------------------------------------------------------ answer sets (chapter 5)
def expand(e: DocEntry, options: dict[str, str]) -> list[str]:
    """Atom answers from block options: the E20 answer of the option; a fixed answer stays."""
    if set(options) != set(e.block_order):
        raise SystemExit(f"{e.doc_id}: the answer set does not give one option for each Docling block")
    return [e.fixed.get(a, ANSWER_OF_OPTION[options[b]]) for a, b in zip(e.ids, e.block_of)]


def load_answer_set(kind: str, folder: Path, docs: list[str], table: dict) -> tuple[dict, dict]:
    """({doc: {atoms, claim, blocks, d1, role, tiers}}, {path: SHA-256})."""
    folder = check_path(Path(folder))
    out, shas = {}, {}
    for d in docs:
        e = table[d]
        p = folder / f"{d}.json"
        if not p.exists():
            raise SystemExit(f"{rel(p)}: missing answer file")
        shas[rel(p)] = sha256(p)
        x = json.loads(p.read_text(encoding="utf-8"))
        if str(x.get("doc_id")) != d:
            raise SystemExit(f"{rel(p)}: doc_id differs")
        if kind == "rules":
            at = x["atoms"]
            if at["ids"] != list(e.ids):
                raise SystemExit(f"{rel(p)}: atom ids differ from the table")
            opts = {b["block"]: b["option"] for b in x["blocks"]}
            out[d] = {"atoms": list(at["nos4"]), "claim": bool(x["document"]["claims"]["L9"]["claimed"]),
                      "blocks": opts, "d1": x["document"]["d1"]["option"],
                      "role": x["document"]["s1"]["combined_role"], "tiers": {b["block"]: b["tier"] for b in x["blocks"]}}
        elif kind == "decisions":
            opts = {b["block"]: b["option"] for b in x["blocks"]}
            if any(o not in OPTIONS for o in opts.values()):
                raise SystemExit(f"{rel(p)}: an option outside of {OPTIONS}")
            d1 = ((x.get("document") or {}).get("d1") or {}).get("option")
            out[d] = {"atoms": expand(e, opts), "claim": True, "blocks": opts, "d1": d1, "role": None, "tiers": None}
        elif kind == "atoms":
            if x.get("ids") != list(e.ids):
                raise SystemExit(f"{rel(p)}: atom ids differ from the table")
            ans = list(x["answers"])
            if any(a not in ANSWERS for a in ans):
                raise SystemExit(f"{rel(p)}: answers outside of E20 v4")
            out[d] = {"atoms": ans, "claim": True, "blocks": options_of_atoms(e, ans), "d1": None, "role": None,
                      "tiers": None}
        else:
            raise SystemExit(f"unknown answer set kind {kind}")
        if len(out[d]["atoms"]) != len(e.ids) or any(a not in ANSWERS for a in out[d]["atoms"]):
            raise SystemExit(f"{d}: bad atom answers")
        bad = [a for a, x in zip(e.ids, out[d]["atoms"]) if a in e.fixed and x != e.fixed[a]]
        if bad:
            raise SystemExit(f"{d}: atoms without their fixed answer (shared by definition): {bad[:5]}")
    return out, shas


def score_set(docs: list[str], aset: dict, table: dict, atom_ref: dict, block_ref: dict, d1_ref: dict,
              exclude: dict | None = None) -> dict:
    lv = ladder()["level"]
    answers = {d: aset[d]["atoms"] for d in docs}
    claimed = measure_level(lv, docs, answers, {d: aset[d]["claim"] for d in docs}, atom_ref, table)
    all_docs = measure_level(lv, docs, answers, {d: True for d in docs}, atom_ref, table)
    bl = block_level(docs, {d: aset[d]["blocks"] for d in docs}, block_ref, exclude)
    d1 = d1_level(docs, {d: aset[d]["d1"] for d in docs if aset[d]["d1"]}, d1_ref)
    return {"l9_claimed": claimed, "l9_all_documents": all_docs, "blocks_6": bl, "d1": d1}


# ------------------------------------------------------------------ reproduction (chapter 7)
STORED_KEYS = ("documents", "exact", "exact_lower", "boundaries_ref", "boundaries_hyp", "correct", "labelled_f1_lower",
               "block_omission", "block_intrusion", "documents_with_block_intrusion", "documents_available")
STORED_UNROUNDED = ("labelled_f1", "text_omission", "text_intrusion", "text_class_error", "exact_rate")


def stored_roles(split: str) -> dict[str, dict]:
    rule = json.loads((S1_DIR / f"rule_{split}.json").read_text(encoding="utf-8"))["documents"]
    comb = json.loads((S1_DIR / f"combined_{split}.json").read_text(encoding="utf-8"))["documents"]
    return {d: {"s1_rule": rule[d]["role"], "s1_combined": comb[d]["role"]} for d in comb}


def compare_stored(mine: dict, st: dict) -> list[str]:
    diff = []
    for k in STORED_KEYS:
        if mine.get(k) != st.get(k):
            diff.append(f"{k}: scorer {mine.get(k)}, stored {st.get(k)}")
    for k in STORED_UNROUNDED:
        a, b = mine.get(k), st["unrounded"].get(k)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
            diff.append(f"{k}: scorer {a}, stored {b}")
    if round(mine["labelled_f1"], 4) != st["labelled_f1"]:
        diff.append(f"labelled_f1 (4 digits): scorer {round(mine['labelled_f1'], 4)}, stored {st['labelled_f1']}")
    for k in ("claimed_documents", "exact_documents"):
        if sorted(mine[k]) != sorted(st[k]):
            diff.append(f"{k}: the lists differ")
    s2 = st["strata"]["ref_blocks"].get("2", {})
    if (mine["switch_l9"]["documents"], mine["switch_l9"]["exact"]) != (s2.get("claimed", 0), s2.get("exact", 0)):
        diff.append(f"switch: scorer {mine['switch_l9']['exact']}/{mine['switch_l9']['documents']}, "
                    f"stored {s2.get('exact')}/{s2.get('claimed')}")
    if (mine["switch_l9"]["trivial_exact"] or 0) != s2.get("trivial_exact", 0):
        diff.append("switch trivial exact differs")
    tr = st["trivial_role_same_scope"]
    if mine["trivial_role_same_documents"] != {"exact": tr["exact"], "documents": tr["documents"]}:
        diff.append(f"trivial role: scorer {mine['trivial_role_same_documents']}, stored {tr}")
    return diff


def reproduce(args) -> int:
    """Chapter 7: the stored nos4 values of dev and eval, then the record for the command score."""
    import m03_sub_common as sc       # only for the table check against the loaded development documents

    started = clock()
    results = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    lv = ladder()["level"]
    out_splits, total_diff = {}, 0
    loaded = sc.load()
    table_check = Counter()
    inputs = {rel(RESULTS_JSON): sha256(RESULTS_JSON), rel(LADDER_JSON): sha256(LADDER_JSON)}
    ref_shas = {}
    stored = {s: json.loads((SCRATCH / f"err_recompose_nos4_{s}.json").read_text(encoding="utf-8"))
              for s in ("dev", "eval")}
    bodies = parliaments([d for s in stored.values() for d in s])
    for split in ("dev", "eval"):
        p = SCRATCH / f"err_recompose_nos4_{split}.json"
        inputs[rel(p)] = sha256(p)
        for f in (S1_DIR / f"rule_{split}.json", S1_DIR / f"combined_{split}.json"):
            inputs[rel(f)] = sha256(f)
            if results["inputs"].get(f"s1_role/{f.name}") != inputs[rel(f)]:
                raise SystemExit(f"{rel(f)}: SHA-256 differs from the value in results.json")
        if results["inputs"].get(p.name) != inputs[rel(p)]:
            raise SystemExit(f"{rel(p)}: SHA-256 differs from the value in results.json")
        nos4 = stored[split]
        docs = list(nos4)
        table, ref = {}, {}
        for d in docs:
            if d in protected()["test_ids"]:
                raise Refused(f"{d}: test document in the stored nos4 answers")
            if (protected()["roles"].get(bodies.get(d, "")) or "Gold") == "Gold":
                raise Refused(f"{d}: unknown parliament or test parliament")
            if not (ATOMS_DIR / f"{d}.json").exists() or not (DOCLING_DIR / f"{d}.json").exists():
                raise Refused(f"{d}: no atom file or Docling file in daten/iso")
            e = doc_entry(d)
            table[d] = e
            x = loaded[d]
            table_check["documents"] += 1
            table_check["ids_equal"] += list(e.ids) == x.ids
            table_check["fixed_equal"] += e.fixed == x.fixed
            ref[d], src, h = atom_reference(e, pilots=False)
            table_check[f"reference_{src}"] += 1
            table_check["reference_equal_loaded"] += ref[d] == x.ref
            ref_shas[d] = h
        st = results["levels"][LEVEL_ID]["methods"]["nos4"][split]
        claims = set(st["claimed_documents"])
        roles = stored_roles(split)
        recomputed = {d: scope_role_agreement(nos4[d], roles[d]["s1_rule"], roles[d]["s1_combined"]) for d in docs}
        claim_diff = sorted(d for d in docs if recomputed[d] != (d in claims))
        mine = measure_level(lv, docs, nos4, {d: d in claims for d in docs}, ref, table,
                             {d: roles[d]["s1_combined"] for d in docs})
        diff = compare_stored(mine, st)
        if claim_diff:
            diff.append(f"claim flags of the scope rule differ from the stored flags: {len(claim_diff)} documents")
        total_diff += len(diff)
        keep = ("documents_available", "claimed", "documents", "exact", "exact_rate", "exact_lower", "labelled_f1",
                "labelled_f1_lower", "boundaries_ref", "boundaries_hyp", "correct", "text_omission", "text_intrusion",
                "text_class_error", "block_omission", "block_intrusion", "switch_l9", "trivial_role_same_documents")
        out_splits[split] = {"reproduced": {k: mine[k] for k in keep},
                             "stored": {"documents": st["documents"], "exact": st["exact"],
                                        "labelled_f1": st["labelled_f1"], "boundaries_ref": st["boundaries_ref"],
                                        "boundaries_hyp": st["boundaries_hyp"], "correct": st["correct"],
                                        "text_intrusion": st["text_intrusion"],
                                        "switch": {k: st["strata"]["ref_blocks"].get("2", {}).get(k)
                                                   for k in ("claimed", "exact", "trivial_exact")},
                                        "trivial_role_same_scope": st["trivial_role_same_scope"]},
                             "claims_recomputed_by_scope_rule_equal": not claim_diff,
                             "differences": diff}
    tc = dict(table_check)
    table_ok = tc["ids_equal"] == tc["documents"] == tc["fixed_equal"] == tc["reference_equal_loaded"]
    ok = total_diff == 0 and table_ok
    inputs["references_sha256_canonical"] = canonical_sha(ref_shas)
    rec = {"schema": "parlpdfech-gj-score-reproduction/1", "status": "MET" if ok else "NOT MET",
           "run_date": started, "finished": clock(),
           "actor": "AI agent (Claude Opus 5.5), stream F of plan gate GJ",
           "gate": "GJ (OPEN); status of the work: EXCEPTION (process rule 10)",
           "scorer": {"path": rel(SCORER_PATH), "sha256": sha256(SCORER_PATH), "version": SCORER_VERSION},
           "what": "stored nos4 answers and stored claim flags, scored at L9 by this file, against the stored values "
                   "of daten/iso/ladder/results.json (levels.L9.methods.nos4); reference ref41 and pool_ref41 without "
                   "pilot overrides",
           "table_check": {**tc, "against": "m03_sub_common.load() (atom ids, fixed answers, reference answers)",
                           "equal": table_ok},
           "splits": out_splits, "differences_total": total_diff, "inputs": inputs,
           "limits": ["The values are the stored values of the frozen rules (dev in-sample, eval measured several "
                      "times before). No value of a new method is computed here.",
                      "No test document, no file of daten/gold/test and no group 7 file of daten/iso/v4/final_* is read."]}
    RUNS.mkdir(parents=True, exist_ok=True)
    REPRODUCTION.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": rec["status"], "differences_total": total_diff, "table_check": rec["table_check"],
                      **{s: {k: v["reproduced"][k] for k in ("claimed", "exact", "labelled_f1", "boundaries_ref",
                                                             "boundaries_hyp", "correct", "switch_l9")}
                         for s, v in out_splits.items()},
                      "file": rel(REPRODUCTION), "sha256": sha256(REPRODUCTION)}, indent=1))
    return 0 if ok else 2


def check_reproduction() -> dict:
    """The command score runs only after a MET reproduction with this version of the file (chapter 7)."""
    if not REPRODUCTION.exists():
        raise SystemExit("no reproduction record: run the command reproduce first (plan chapter 6.3 item 6)")
    rec = json.loads(REPRODUCTION.read_text(encoding="utf-8"))
    if rec.get("status") != "MET":
        raise SystemExit("the reproduction record is not MET: no comparison value (plan chapter 11 item 9)")
    if (rec.get("scorer") or {}).get("sha256") != sha256(SCORER_PATH):
        raise SystemExit("the scorer changed after the reproduction: run the command reproduce again")
    return {"path": rel(REPRODUCTION), "sha256": sha256(REPRODUCTION)}


# ------------------------------------------------------------------ command score
def docs_of(args) -> list[str]:
    if args.doc:
        return [str(d) for d in args.doc]
    if not args.set:
        raise SystemExit("give --set <file>:<key> or --doc")
    path, key = args.set.rsplit(":", 1)
    x = json.loads(check_path(Path(path)).read_text(encoding="utf-8"))
    return [str(d) for d in x[key]]


def tiers_to_exclude(docs: list[str], rules_dir: Path, tiers: list[str], table: dict) -> dict:
    out = {}
    for d in docs:
        p = check_path(Path(rules_dir) / f"{d}.json")
        x = json.loads(p.read_text(encoding="utf-8"))
        if [b["block"] for b in x["blocks"]] != list(table[d].block_order):
            raise SystemExit(f"{rel(p)}: blocks differ from the table")
        out[d] = {b["block"] for b in x["blocks"] if b["tier"] in tiers}
    return out


def score_command(args) -> int:
    started = clock()
    repro = check_reproduction()
    docs = docs_of(args)
    if len(set(docs)) != len(docs):
        raise SystemExit("a document id occurs more than once")
    bodies = parliaments(docs)
    split = {d: split_of(d, bodies.get(d), args.allow_group7) for d in docs}
    table = {d: doc_entry(d) for d in docs}
    aset, ans_shas = load_answer_set(args.answers, Path(args.dir), docs, table)
    atom_ref, block_ref, d1_ref, src = {}, {}, {}, Counter()
    ref_shas = {}
    for d in docs:
        atom_ref[d], s, ref_shas[d] = atom_reference(table[d], pilots=not args.no_pilot_overrides)
        src[s] += 1
        block_ref[d], d1, _ = block_reference(table[d], args.block_ref, Path(args.labels_dir), atom_ref[d])
        if d1:
            d1_ref[d] = d1
    exclude = None
    if args.exclude_tiers:
        exclude = tiers_to_exclude(docs, Path(args.rules_dir), [t.strip() for t in args.exclude_tiers.split(",")], table)
    values = score_set(docs, aset, table, atom_ref, block_ref, d1_ref, exclude)
    out = Path(args.out)
    if not out.resolve().is_relative_to(GJ.resolve()):
        raise SystemExit("the output must be inside daten/gj")
    rec = {"schema": "parlpdfech-gj-score/1", "status": "EXCEPTION (NOT RELEASED)", "run_date": started,
           "finished": clock(), "scorer": {"path": rel(SCORER_PATH), "sha256": sha256(SCORER_PATH),
                                           "version": SCORER_VERSION},
           "reproduction_record": repro, "answer_set": {"kind": args.answers, "folder": rel(Path(args.dir)),
                                                        "files_sha256_canonical": canonical_sha(ans_shas)},
           "documents": len(docs), "splits": dict(Counter(split.values())),
           "reference": {"atoms": dict(src), "pilot_overrides": not args.no_pilot_overrides,
                         "atoms_sha256_canonical": canonical_sha(ref_shas), "blocks": args.block_ref,
                         "labels_dir": rel(Path(args.labels_dir)) if args.block_ref == "labels" else None},
           "excluded_tiers": args.exclude_tiers, "values": values}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    v = values
    print(json.dumps({"documents": len(docs), "l9_claimed": {k: v["l9_claimed"][k] for k in ("claimed", "exact",
                                                                                             "labelled_f1")},
                      "l9_all": {k: v["l9_all_documents"][k] for k in ("documents", "exact", "labelled_f1")},
                      "blocks_6": {k: v["blocks_6"][k] for k in ("blocks", "accuracy_6")},
                      "file": rel(out), "sha256": sha256(out)}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="scorer of gate GJ (L9 and 6-option blocks)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("reproduce")
    s = sub.add_parser("score")
    s.add_argument("--answers", required=True, choices=["rules", "decisions", "atoms"])
    s.add_argument("--dir", required=True)
    s.add_argument("--set")
    s.add_argument("--doc", nargs="*")
    s.add_argument("--out", required=True)
    s.add_argument("--block-ref", default="labels", choices=["labels", "derived"])
    s.add_argument("--labels-dir", default=str(GJ / "labels"))
    s.add_argument("--no-pilot-overrides", action="store_true")
    s.add_argument("--exclude-tiers")
    s.add_argument("--rules-dir", default=str(GJ / "rules"))
    s.add_argument("--allow-group7", action="store_true")
    a = ap.parse_args()
    try:
        code = reproduce(a) if a.cmd == "reproduce" else score_command(a)
    except Refused as ex:
        print(f"stopped (Refused): {ex}", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()
