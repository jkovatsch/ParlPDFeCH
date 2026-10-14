"""Isolation stage of the converter for new documents: isolation level L9 with the method nos4 (gate 3a version 4).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), step
Runner. Status: NOT RELEASED. This file gives no gate result.

Context: decision E34 of Jonathan (08.10.2026) sets gate 3a version 4 at the isolation level L9 with the method
`nos4` (`crisp-dm/03-data-preparation/isolation-complexity-ladder.md`, chapter 7). Condition 7.1.4 of that
report needs a runner that applies the frozen converter to new documents. The isolation is a rule stage
(D5, option a). Apertus gives only the S1 role of a document with the S1 rule id R1, as in the stored method.

1 Input and output
  Input: a document id, its Docling atoms (`m03_iso_paths.iso_path`) and its export record. The export record
  is the row of `daten/analyse/pdf/docs_pdf_index.csv.gz` with the same id. The S1 rule reads only the fields
  `category_de`, `category_harmonized` and `name_klasse` (as `m03_sub_s1_role.export_meta`).
  Output for each document:
  - `nos4`: one E20 answer for each atom (answer set of E20 version 4.2), before the collapse map.
  - `l9`: the `nos4` answers after the collapse map `SLOT_NOTITLE` and the block form.
  - The claim flag of L9 (scope rule `role_agreement`) and of L8 (scope rule `written_affair`).
  - The S1 rule role with its rule id, and the S1 combined role with its source (rule or Apertus).
  The runner writes no text of a document. A record holds atom ids, answers, roles, rule ids and SHA-256 values.

2 Chain (each step calls the stored function; this file changes no function and no file of another step)
  1. Atoms: `m03_iso_v4.atoms_of`. Fixed answers of E20 chapter 3: `m03_iso_v4.fixed_answers`, which applies
     the rules R1 to R5 of `m03_iso_hilfe.fixed_roles`.
  2. S1 rule: `m03_sub_s1_role.rule` on the atoms and the export record.
  3. S1 combined: the rule role if the rule id is in `SURE_IDS` (all rule ids except R1). Else the role of
     Apertus-v1.5-8B on CSCS: `m03_sub_s1_role.apertus` with the prompt `src/prompts/s1_role.txt`. That
     function calls `m03_sub_common.ask` with its cache, its log and its guards (triage PASS only).
  4. S2 rule: `m03_sub_s2_switch.rule_predict`.
  5. S3 and S4: the method `nos4` gives `text` to each atom (S3) and uses no S4 (`err_recompose3.py` of the
     ladder step). Thus the S3 rule is not an input of `nos4`. The fixed answers still give furniture and none.
  6. S5 rule and composition: `m03_sub_assemble.assemble` with the assembly option `CHOSEN_OPTION`
     (`s4_over_s3` and `s1_start`). It calls `m03_sub_s5_type.predict_rule` and `m03_sub_common.compose`.
  7. Collapse map, block form and scope rules: `m03_ladder.converter_view` with the definitions of L8 and L9
     from `daten/iso/ladder/ladder.json`. The scope rules read the S1 roles of this run, never a stored output.

3 Guards
  1. A group 7 document is always refused.
  2. A development document of `m03_sub_common.load` passes the guards of `m03_sub_common`.
  3. A test document is refused unless its id is in the sealed selection file (`--selection`). The SHA-256 of
     that file must be equal to the value in the SHA-256 file (`--selection-sha256`). If the SHA-256 file also
     lists the atoms file or the prompt text file of a document, these values must be equal too.
  4. Each other document is refused.
  5. For a document of the selection, the runner widens three guards of `m03_sub_common` only for its id and
     only during its run: `_check_allowed_doc`, `triage` (the verdict comes from the selection or `--triage`)
     and the folder of the prompt text (`document_text` reads `daten/gold/test/atome_prompt`). Group 7 stays
     refused, and the triage rule of CSCS stays: no request without triage PASS.
  6. During the run of a document, the loaded record of the document has no reference answers. A read of a
     reference stops the run.
  7. Mode `cache-only` (default): a CSCS request that is not in `daten/iso/sub/cscs_cache` stops the run before
     the key is read. Mode `live` sends the request.

4 Identity check (command `identity`)
  The runner runs on all 205 `dev` and `eval` documents in the mode `cache-only`. It compares the `nos4`
  answers with `daten/iso/ladder/scratch/err_recompose_nos4_<split>.json`. It compares the claim flags with the
  claimed documents of `nos4` at L8 and L9 in `daten/iso/ladder/results.json`. It also compares the S1, S2 and
  export values with the stored sub-task outputs, and it probes the guards (`guard_selftest`). Output:
  `daten/gold/final_v4/runner_identity.json` with the counts, the differences and the SHA-256 of each source file
  that the runner imports.

5 Run on new documents (command `run`)
  The runner keeps all records in memory. It writes the files only if all documents are done:
  `<out>/nos4/<doc>.json` (format of `m03_iso_v4.write`), `<out>/records/<doc>.json` and `<out>/run.json`
  (claim flags and the SHA-256 of each file). A folder with a `run.json` is not written again.
  The output of test documents must be in `daten/gold/final_v4`. The console shows only counts and claim flags.

Usage (from the project folder; one command on one line; the package versions are those of `uv.lock`):
  `uv run --no-project --python 3.12 --with pyyaml==6.0.3 --with mlx-lm==0.32.0 --with mlx==0.32.3`
  `  --with transformers==5.18.0 --with tokenizers==0.23.2 --with jinja2==3.1.6`
  `  python src/m05_iso_runner.py identity`
  `(same uv options) python src/m05_iso_runner.py run --out daten/gold/final_v4/<folder>`
  `  --selection daten/gold/final_v4/selection.csv --selection-sha256 daten/gold/final_v4/selection.sha256`
  `  [--triage <csv with doc_id and final>] [--doc <id> ...] [--cscs cache-only|live]`
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter
from functools import lru_cache
from importlib import metadata
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # the tokenizer is a local folder
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
import m03_ladder as lad  # noqa: E402  (imports m03_iso_v4 and m03_sub_common; loads the ladder definitions)
import m03_iso_v4 as v4  # noqa: E402
import m03_sub_common as sc  # noqa: E402
import m03_sub_s1_role as s1m  # noqa: E402
import m03_sub_s2_switch as s2m  # noqa: E402
import m03_sub_assemble as asm  # noqa: E402
from m03_iso_paths import iso_path  # noqa: E402

RUNNER_VERSION = "iso-runner-1"
RUNNER_PATH = Path(__file__).resolve()
FINAL_V4 = ROOT_DIR / "daten/gold/final_v4"
IDENTITY_OUT = FINAL_V4 / "runner_identity.json"
LADDER_SCRATCH = ROOT_DIR / "daten/iso/ladder/scratch"
RESULTS_JSON = ROOT_DIR / "daten/iso/ladder/results.json"
S1_DIR = ROOT_DIR / "daten/iso/sub/s1_role"
S2_DIR = ROOT_DIR / "daten/iso/sub/s2_switch"
TEST_LISTS = (ROOT_DIR / "daten/gold/test.csv", ROOT_DIR / "daten/gold/bulk_test.csv")
TOKENIZER_DIR = ROOT_DIR / "daten/modelle/apertus-v1.5-8b-text-bf16"

# frozen parameters of the stored method (checked against the stored selection files at the start)
SURE_IDS = ("A1", "A2", "C1", "D0", "E1", "M1", "O1", "O2", "P1", "P2")   # S1 combined: rule role for these ids
S1_PROMPT_SHA = "a458b4258d86"                                         # src/prompts/s1_role.txt (first 12 hex)
NOS4_OPTION = dict(getattr(asm, "OPTIONS")[asm.CHOSEN_OPTION])   # s4_over_s3 and s1_start
AUTHOR_ROLES = ("proposal", "response", "combined")
LEVEL_DEFS = {lv["id"]: lv for lv in getattr(lad, "LEVELS") if lv["id"] in ("L8", "L9")}
EXPORT_FIELDS = ("category_de", "category_harmonized", "name_klasse")
GROUP7 = frozenset(v4.final_docs())


class Refused(ValueError):
    """The runner refuses the document (guard of chapter 3)."""


class CacheMiss(RuntimeError):
    """A CSCS request would leave the cache in the mode cache-only."""


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT_DIR).as_posix() if p.is_relative_to(ROOT_DIR) else str(p)


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def canonical_sha(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ------------------------------------------------------------------ frozen method: checks at the start
def check_frozen_method() -> dict:
    """The stored S1 combined selection, the S1 prompt and the ladder definitions must be the frozen ones."""
    sel = json.loads((S1_DIR / "combined_dev.json").read_text(encoding="utf-8"))
    prompt = s1m.load_prompt()
    out = {"s1_selection_kind": sel["chosen"]["kind"], "s1_sure_ids": sel["sure_ids"],
           "s1_prompt_sha": prompt["sha256"], "s1_selection_prompt_sha": sel["apertus_prompt_sha256"],
           "assembly_option": asm.CHOSEN_OPTION, "option": NOS4_OPTION,
           "L8": {k: LEVEL_DEFS["L8"][k] for k in ("map", "scope", "zones", "unit")},
           "L9": {k: LEVEL_DEFS["L9"][k] for k in ("map", "scope", "zones", "unit")}}
    bad = []
    if sel["chosen"]["kind"] != "sure_ids" or tuple(sel["sure_ids"]) != SURE_IDS:
        bad.append("S1 combined selection is not sure_ids with the frozen rule ids")
    if prompt["sha256"] != S1_PROMPT_SHA or sel["apertus_prompt_sha256"] != S1_PROMPT_SHA:
        bad.append("S1 prompt differs from the frozen prompt")
    if NOS4_OPTION != {"s4_over_s3": True, "s1_start": True}:
        bad.append("assembly option differs")
    want = {"L8": ("SLOT_NOTITLE", "written_affair", [], "block"), "L9": ("SLOT_NOTITLE", "role_agreement", [], "block")}
    for k, (m, s, z, u) in want.items():
        lv = LEVEL_DEFS[k]
        if (lv["map"], lv["scope"], lv["zones"], lv["unit"]) != (m, s, z, u):
            bad.append(f"definition of {k} differs")
    if bad:
        raise SystemExit("frozen method check failed: " + "; ".join(bad))
    return out


# ------------------------------------------------------------------ export records
def export_records(ids: list[str]) -> dict[str, dict]:
    """The export record of each document (one pass over the PDF index). Missing: empty fields, found=False."""
    want = set(ids)
    got: dict[str, dict] = {}
    with gzip.open(s1m.PDF_INDEX, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["id"] in want:
                got[r["id"]] = r
    out = {}
    for d in ids:
        r = got.get(d, {})
        out[d] = {"found": d in got, "body_key": r.get("body_key", ""), "affair_id": r.get("affair_id", ""),
                  **{k: r.get(k, "") for k in EXPORT_FIELDS}}
    return out


# ------------------------------------------------------------------ sealed selection and guards
def read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sealed_selection(csv_path: Path, sha_path: Path, triage_path: Path | None) -> dict:
    """Read the selection only if its SHA-256 is equal to the sealed value. Returns ids, triage verdicts and the
    other sealed files ({path: SHA-256})."""
    csv_path, sha_path = csv_path.resolve(), sha_path.resolve()
    listed: dict[Path, str] = {}
    single = []
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts:
            continue
        if len(parts) == 1:
            single.append(parts[0].lower())
            continue
        p = Path(parts[-1].lstrip("*"))
        listed[(p if p.is_absolute() else ROOT_DIR / p).resolve()] = parts[0].lower()
    want = listed.get(csv_path) or (single[0] if len(single) == 1 and not listed else None)
    if want is None:
        raise SystemExit(f"sealed selection: {rel(sha_path)} gives no SHA-256 for {rel(csv_path)}")
    got = sha256(csv_path)
    if got != want:
        raise SystemExit(f"sealed selection: SHA-256 of {rel(csv_path)} is {got}, sealed value {want}: refused")
    rows = read_csv(csv_path)
    if not rows or "doc_id" not in rows[0]:
        raise SystemExit("sealed selection: no column doc_id")
    ids = [r["doc_id"].strip() for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("sealed selection: a document id occurs more than once")
    verdict = {}
    col = next((c for c in ("triage", "final", "triage_final", "verdict") if c in rows[0]), None)
    if col:
        verdict = {r["doc_id"].strip(): r[col].strip() for r in rows}
    if triage_path is not None:
        t = read_csv(triage_path)
        tcol = next((c for c in ("final", "triage", "triage_final", "verdict") if t and c in t[0]), None)
        if tcol is None:
            raise SystemExit("triage file: no column final, triage, triage_final or verdict")
        for r in t:
            d = r["doc_id"].strip()
            if d in verdict and verdict[d] != r[tcol].strip():
                raise SystemExit(f"triage of {d}: the selection and the triage file differ")
            verdict.setdefault(d, r[tcol].strip())
    return {"path": rel(csv_path), "sha256": got, "sha256_file": rel(sha_path), "ids": ids,
            "triage": {d: verdict.get(d, "") for d in ids}, "triage_column": col,
            "triage_file": rel(triage_path) if triage_path else None,
            "listed": {p: h for p, h in listed.items() if p != csv_path}}


@lru_cache(maxsize=1)
def test_ids() -> frozenset:
    return frozenset(r["doc_id"].strip() for p in TEST_LISTS if p.exists() for r in read_csv(p))


def is_test(d: str, body_key: str) -> bool:
    _, _, test_parl = sc._protected()
    return sc.is_test_document(d) or d in test_ids() or (bool(body_key) and body_key in test_parl)


def admit(d: str, body_key: str, selection: dict | None) -> str:
    """Kind of admission: "known" (development document) or "selected" (sealed selection). Else Refused."""
    d = str(d)
    if d in GROUP7:
        raise Refused(f"{d}: group 7 document: refused")
    if d in sc.load():
        sc._check_allowed_doc(d)
        return "known"
    if selection is not None and d in selection["ids"]:
        return "selected"
    if is_test(d, body_key):
        raise Refused(f"{d}: test document outside the sealed selection: refused")
    raise Refused(f"{d}: not a development document and not in the sealed selection: refused")


def input_files(d: str) -> dict:
    out = {}
    for kind, ext in (("atome", "json"), ("docling", "json"), ("atome_prompt", "txt")):
        p = iso_path(kind, d, ext)
        out[kind] = {"path": rel(p), "sha256": sha256(p) if p.exists() else None}
    return out


def check_sealed_inputs(d: str, files: dict, selection: dict | None) -> None:
    if selection is None:
        return
    for kind, x in files.items():
        want = selection["listed"].get((ROOT_DIR / x["path"]).resolve())
        if want is not None and want != x["sha256"]:
            raise Refused(f"{d}: {kind} file differs from the sealed SHA-256: refused")


# ------------------------------------------------------------------ admission of one document
def runner_doc(d: str, triage_verdict: str, body_key: str) -> sc.Doc:
    """The record of the document for the sub-task code: atom ids and fixed answers, no reference answers."""
    ids = [a["id"] for a in v4.atoms_of(d)]
    return sc.Doc(doc_id=d, kind="runner", group="runner", home="runner", body_key=body_key, language="",
                  meta_role="", triage=triage_verdict, ids=ids, ref=None, fixed=v4.fixed_answers(d))


@contextlib.contextmanager
def admitted(d: str, doc: sc.Doc, selected: bool):
    """Put the runner record of the document into m03_sub_common.load() for the time of its run. For a document
    of the selection, also widen the three guards of chapter 3, item 5 for this id only."""
    docs = sc.load()
    had, saved_doc = d in docs, docs.get(d)
    orig = {n: getattr(sc, n) for n in ("_check_allowed_doc", "triage", "document_text")}

    def check(x: str) -> None:
        x = str(x)
        if x == d:
            if x in GROUP7:
                raise ValueError(f"{x}: group 7 document (final group): refused")
            return
        orig["_check_allowed_doc"](x)

    def triage() -> dict:
        return {**orig["triage"](), d: doc.triage}

    def document_text(x: str) -> str:
        x = str(x)
        if x != d:
            return orig["document_text"](x)
        folder = iso_path("atome_prompt", x, "txt").parent
        old = getattr(sc, "PROMPTS")
        setattr(sc, "PROMPTS", folder)
        try:
            return orig["document_text"](x)
        finally:
            setattr(sc, "PROMPTS", old)

    docs[d] = doc
    if selected:
        sc._check_allowed_doc, sc.triage = check, triage
    sc.document_text = document_text
    try:
        yield
    finally:
        for n, f in orig.items():
            setattr(sc, n, f)
        if had:
            docs[d] = saved_doc
        else:
            docs.pop(d, None)


@contextlib.contextmanager
def runner_signals(d: str, rule_role: str, combined_role: str):
    """The scope rules of m03_ladder read the S1 roles from lad.SIG. Put the roles of this run there."""
    had, saved = d in lad.SIG, lad.SIG.get(d)
    lad.SIG[d] = {"s1_rule": rule_role, "s1_combined": combined_role}
    try:
        yield
    finally:
        if had:
            lad.SIG[d] = saved
        else:
            lad.SIG.pop(d, None)


@contextlib.contextmanager
def cscs_mode(mode: str):
    """cache-only: m03_sub_common._env (called only after a cache miss, before the key is read) stops the run."""
    if mode not in ("cache-only", "live"):
        raise SystemExit(f"unknown CSCS mode {mode}")
    orig = sc._env

    def no_new_request():
        raise CacheMiss("a CSCS request would leave the cache (mode cache-only)")

    if mode == "cache-only":
        sc._env = no_new_request
    try:
        yield
    finally:
        sc._env = orig


# ------------------------------------------------------------------ one document
def abstain_reason(conv_role: str, rule_role: str, combined_role: str, scope: str) -> str | None:
    if conv_role not in AUTHOR_ROLES:
        return "the role of the converter answers is not an author role"
    if combined_role not in AUTHOR_ROLES:
        return "the S1 combined role is not an author role"
    if scope == "role_agreement" and conv_role != rule_role:
        return "role disagreement: the role of the converter answers is not the S1 rule role"
    return None


def run_document(d: str, export: dict, kind: str, triage_verdict: str, prompt: dict, usage: Counter) -> dict:
    """The chain of chapter 2 for one admitted document."""
    files = input_files(d)
    doc = runner_doc(d, triage_verdict, export["body_key"])
    known = sc.load().get(d) if kind == "known" else None
    if known is not None and (known.ids != doc.ids or known.fixed != doc.fixed):
        raise SystemExit(f"{d}: atom ids or fixed answers differ from m03_sub_common.load")
    with admitted(d, doc, kind == "selected"):
        r1 = s1m.rule(d, {d: {k: export[k] for k in EXPORT_FIELDS}})
        rule_role, rule_id = r1["role"], r1["reason"]
        apertus = None
        if rule_id in SURE_IDS:
            combined_role, source = rule_role, "rule"
        else:
            a = s1m.apertus(d, prompt)
            usage.update({k: a["usage"].get(k, 0) for k in ("requests", "cache_hits", "prompt_tokens",
                                                             "completion_tokens")})
            usage["questions"] += 1
            combined_role, source = a["role"], "apertus"
            apertus = {"role": a["role"], "p": a["p"], "probs": a["probs"], "requests": a["usage"]["requests"],
                       "cache_hits": a["usage"]["cache_hits"], "model": getattr(sc, "MODEL"),
                       "prompt_sha": prompt["sha256"]}
        r2 = s2m.rule_predict(d)
        s2_runs = [tuple(e) for e in r2["s2"]]
        weak = r2["start_reason"].startswith("no strong cue")
        lab = {"s1": combined_role, "s2": s2_runs, "s3": {a: "text" for a in doc.ids}, "s4": [], "s2_start_weak": weak}
        nos4 = asm.assemble(d, lab, "rule", dict(NOS4_OPTION))
        with runner_signals(d, rule_role, combined_role):
            c8, h8, z8 = lad.converter_view(LEVEL_DEFS["L8"], d, nos4)
            c9, h9, z9 = lad.converter_view(LEVEL_DEFS["L9"], d, nos4)
            conv_role = lad.role(nos4)
    if z8 or z9 or h8 != h9:
        raise SystemExit(f"{d}: L8 and L9 must have no zone and the same answers")
    claims = {}
    for lid, flag in (("L8", c8), ("L9", c9)):
        scope = LEVEL_DEFS[lid]["scope"]
        why = abstain_reason(conv_role, rule_role, combined_role, scope)
        if (why is None) != bool(flag):
            raise SystemExit(f"{d}: abstention reason and claim flag of {lid} do not agree")
        claims[lid] = {"claimed": bool(flag), "scope": scope, "abstention_reason": why}
    s1_start = combined_role in asm.ROLE_FAMILY and len(s2_runs) == 1 and weak
    return {"doc_id": d, "runner_version": RUNNER_VERSION, "admission": kind, "inputs": files,
            "export_record": {"source": rel(s1m.PDF_INDEX), "found": export["found"],
                              "fields_sha256": canonical_sha({k: export[k] for k in EXPORT_FIELDS})},
            "atoms": len(doc.ids), "fixed_answers": dict(Counter(doc.fixed.values())),
            "s1": {"rule_role": rule_role, "rule_id": rule_id, "combined_role": combined_role, "source": source,
                   "apertus": apertus},
            "s2": {"runs": [list(e) for e in s2_runs], "start_weak": weak, "s1_start_applied": bool(s1_start)},
            "s3": "text for each atom (nos4)", "s4": "not used (nos4)",
            "converter_role": conv_role, "claims": claims,
            "ids": doc.ids, "nos4": nos4, "l9": {"map": LEVEL_DEFS["L9"]["map"], "unit": "block", "answers": h9}}


def core(rec: dict) -> dict:
    """The values that the identity check compares (also for a later run of the same runner)."""
    return {"nos4": rec["nos4"], "l9": rec["l9"]["answers"], "claims": {k: v["claimed"] for k, v in rec["claims"].items()},
            "s1": [rec["s1"]["rule_role"], rec["s1"]["rule_id"], rec["s1"]["combined_role"]]}


# ------------------------------------------------------------------ source and data files
def source_files() -> dict:
    src = (ROOT_DIR / "src").resolve()
    mods = sorted({Path(m.__file__).resolve() for m in list(sys.modules.values())
                   if getattr(m, "__file__", None) and Path(m.__file__).resolve().is_relative_to(src)})
    imported = [{"path": rel(p), "sha256": sha256(p)} for p in mods]
    lazy = []
    p = src / "m04_iso_cscs.py"
    if p not in mods:
        lazy.append({"path": rel(p), "sha256": sha256(p),
                     "note": "m03_sub_common._env imports it only for a new CSCS request (key and address)"})
    return {"imported": imported, "lazy": lazy}


def data_files() -> list[dict]:
    files = [(s1m.PROMPT_FILE, "S1 prompt (Apertus question for the rule id R1)"),
             (S1_DIR / "combined_dev.json", "S1 combined selection on dev (rule ids that keep the rule role)"),
             (ROOT_DIR / "daten/iso/ladder/ladder.json", "collapse maps, scope rules and unit of L8 and L9"),
             (s1m.PDF_INDEX, "export records"),
             (sc.GROUPS_CSV, "guard: group 7 ids"), (sc.POOL_CSV, "guard: pool documents"),
             (sc.TRIAGE_CSV, "guard: triage of development documents"), (sc.SPLIT_CSV, "guard: test parliaments")]
    files += [(p, "guard: test document ids") for p in TEST_LISTS]
    files += [(TOKENIZER_DIR / n, "tokenizer of the CSCS prompt") for n in
              ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja")]
    return [{"path": rel(p), "sha256": sha256(p), "use": u} for p, u in files if Path(p).exists()]


def packages() -> dict:
    out = {"python": platform.python_version()}
    for n in ("mlx-lm", "mlx", "transformers", "tokenizers", "jinja2", "pyyaml"):
        try:
            out[n] = metadata.version(n)
        except metadata.PackageNotFoundError:
            out[n] = None
    return out


# ------------------------------------------------------------------ identity check
def guard_selftest() -> dict:
    """Probes of the guards of chapter 3. No probe opens a file of a document. The result holds no document id."""
    out = {}

    def probe(name: str, fn, refused: bool) -> None:
        try:
            fn()
            got = False
        except (Refused, CacheMiss, ValueError):
            got = True
        out[name] = "refused" if got else "admitted"
        out[name] += "" if got == refused else " (NOT AS EXPECTED)"

    first_test = next(iter(sorted(test_ids())))
    probe("group 7 document", lambda: admit(sorted(GROUP7)[0], "", None), True)
    probe("group 7 document in a selection", lambda: admit(sorted(GROUP7)[0], "", {"ids": sorted(GROUP7)}), True)
    probe("test document without a selection", lambda: admit(first_test, "", None), True)
    probe("test document outside the selection", lambda: admit(first_test, "", {"ids": ["0"]}), True)
    probe("unknown document", lambda: admit("0", "", None), True)
    probe("dev document", lambda: admit(sc.splits()["dev"][0], "", None), False)
    with cscs_mode("cache-only"):
        probe("new CSCS request in the mode cache-only", lambda: sc._env(), True)
    out["all_as_expected"] = not any("NOT AS EXPECTED" in v for v in out.values())
    return out


def stored_documents(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["documents"]


def identity() -> int:
    started = clock()
    frozen = check_frozen_method()
    selftest = guard_selftest()
    sp = sc.splits()
    order = [(s, d) for s in ("dev", "eval") for d in sp[s]]
    ids = [d for _, d in order]
    exports = export_records(ids)
    prompt = s1m.load_prompt()
    usage: Counter = Counter()
    recs: dict[str, dict] = {}
    stop = None
    with cscs_mode("cache-only"):
        for s, d in order:
            try:
                kind = admit(d, exports[d]["body_key"], None)
                if kind != "known" or is_test(d, exports[d]["body_key"]):
                    raise SystemExit(f"{d}: a dev or eval document must be a known development document")
                recs[d] = run_document(d, exports[d], kind, sc.triage().get(d, ""), prompt, usage)
            except CacheMiss as ex:
                stop = {"doc_id": d, "split": s, "reason": str(ex)}
                break
    # stored values (the values that m03_ladder.py uses, and the stored sub-task outputs)
    nos4 = {s: json.loads((LADDER_SCRATCH / f"err_recompose_nos4_{s}.json").read_text(encoding="utf-8"))
            for s in ("dev", "eval")}
    results = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    claimed = {(lid, s): set(results["levels"][lid]["methods"]["nos4"][s]["claimed_documents"])
               for lid in ("L8", "L9") for s in ("dev", "eval")}
    st = {name: {s: stored_documents(base / f"{name}_{s}.json") for s in ("dev", "eval")}
          for base, name in ((S1_DIR, "rule"), (S1_DIR, "combined"), (S1_DIR, "apertus"))}
    s2_rule = {s: stored_documents(S2_DIR / f"rule_{s}.json") for s in ("dev", "eval")}
    meta = json.loads((S1_DIR / "export_meta.json").read_text(encoding="utf-8"))

    cmp = {k: {"documents": 0, "documents_different": 0, "differences": []} for k in
           ("nos4_answers", "l9_answers", "claim_L8", "claim_L9", "claim_recomputed_from_stored", "s1_rule",
            "s1_combined", "s1_apertus", "s2_rule", "export_fields", "export_record_found")}
    atoms = Counter()

    def diff(key: str, d: str, same: bool, what: str = "") -> None:
        cmp[key]["documents"] += 1
        if not same:
            cmp[key]["documents_different"] += 1
            cmp[key]["differences"].append(f"{d}{': ' + what if what else ''}")

    for s, d in order:
        if d not in recs:
            continue
        r = recs[d]
        a_st = nos4[s][d]
        n_diff = sum(1 for x, y in zip(r["nos4"], a_st) if x != y) + abs(len(r["nos4"]) - len(a_st))
        atoms["nos4_atoms"] += len(a_st)
        atoms["nos4_atoms_different"] += n_diff
        diff("nos4_answers", d, n_diff == 0, f"{n_diff} atoms")
        c8, h8, _ = lad.converter_view(LEVEL_DEFS["L8"], d, a_st)     # stored answers, stored S1 signals
        c9, h9, _ = lad.converter_view(LEVEL_DEFS["L9"], d, a_st)
        l9_diff = sum(1 for x, y in zip(r["l9"]["answers"], h9) if x != y)
        atoms["l9_atoms"] += len(h9)
        atoms["l9_atoms_different"] += l9_diff
        diff("l9_answers", d, l9_diff == 0, f"{l9_diff} atoms")
        for lid in ("L8", "L9"):
            diff(f"claim_{lid}", d, r["claims"][lid]["claimed"] == (d in claimed[(lid, s)]),
                 f"runner {r['claims'][lid]['claimed']}, stored {d in claimed[(lid, s)]}")
        diff("claim_recomputed_from_stored", d,
             (bool(c8), bool(c9)) == (d in claimed[("L8", s)], d in claimed[("L9", s)]))
        sr, sco = st["rule"][s][d], st["combined"][s][d]
        diff("s1_rule", d, (r["s1"]["rule_role"], r["s1"]["rule_id"]) == (sr["role"], sr["reason"]))
        diff("s1_combined", d, (r["s1"]["combined_role"], r["s1"]["source"]) == (sco["role"], sco["source"]))
        if r["s1"]["apertus"] is not None:
            sa = st["apertus"][s][d]
            diff("s1_apertus", d, (r["s1"]["apertus"]["role"], r["s1"]["apertus"]["probs"]) == (sa["role"], sa["probs"]))
        s2s = s2_rule[s][d]
        diff("s2_rule", d, (r["s2"]["runs"], r["s2"]["start_weak"]) ==
             (s2s["s2"], s2s["start_reason"].startswith("no strong cue")))
        ex = exports[d]
        diff("export_fields", d, all(ex[k] == meta[d][k] for k in EXPORT_FIELDS))
        diff("export_record_found", d, ex["found"])
    claims_count = {f"{lid}_{s}": {"runner": sum(1 for x, d in order if x == s and d in recs and recs[d]["claims"][lid]["claimed"]),
                                   "stored": len(claimed[(lid, s)])}
                    for lid in ("L8", "L9") for s in ("dev", "eval")}
    inputs_now = {k: sha256(LADDER_SCRATCH / k) if k.startswith("err_") else
                  sha256(ROOT_DIR / "daten/iso/sub" / k) for k in results["inputs"]
                  if k.startswith(("err_recompose", "s1_role/"))}
    inputs_check = {k: {"sha256_now": v, "sha256_in_results_json": results["inputs"][k],
                        "equal": v == results["inputs"][k]} for k, v in inputs_now.items()}
    n_diff = sum(v["documents_different"] for v in cmp.values())
    complete = stop is None and len(recs) == len(order)
    ok = complete and n_diff == 0 and usage["requests"] == usage["cache_hits"] and all(
        v["equal"] for v in inputs_check.values()) and selftest["all_as_expected"]
    out = {
        "schema": "parlpdfech-runner-identity/1", "status": "MET" if ok else "NOT MET",
        "run_date": started, "finished": clock(),
        "actor": "workflow sub-agent (Claude Opus 5.5), step Runner of gate 3a version 4 (decision E34)",
        "runner": {"path": rel(RUNNER_PATH), "sha256": sha256(RUNNER_PATH), "version": RUNNER_VERSION},
        "mode": "identity: all dev and eval documents; CSCS cache only (no new request)",
        "stopped": stop,
        "documents": {"dev": len(sp["dev"]), "eval": len(sp["eval"]), "total": len(order), "done": len(recs)},
        "frozen_method": frozen,
        "guard_selftest": selftest,
        "cscs": {"questions": usage["questions"], "requests": usage["requests"], "cache_hits": usage["cache_hits"],
                 "new_requests": usage["requests"] - usage["cache_hits"],
                 "documents": sorted((d for d, r in recs.items() if r["s1"]["apertus"] is not None), key=int),
                 "note": "Apertus question only for the S1 rule id R1; each call wrote one line to "
                         "daten/iso/sub/cscs_log.jsonl (cache hit)"},
        "differences_total": n_diff,
        "atoms": dict(atoms),
        "claimed_documents": claims_count,
        "comparisons": cmp,
        "comparison_sources": {
            "nos4_answers": "daten/iso/ladder/scratch/err_recompose_nos4_<split>.json (input of m03_ladder.py)",
            "l9_answers": "m03_ladder.converter_view on the stored nos4 answers (collapse map and block form)",
            "claim_L8": "daten/iso/ladder/results.json: levels.L8.methods.nos4.<split>.claimed_documents",
            "claim_L9": "daten/iso/ladder/results.json: levels.L9.methods.nos4.<split>.claimed_documents",
            "claim_recomputed_from_stored": "m03_ladder.converter_view on the stored answers and the stored S1 "
                                            "signals, against results.json",
            "s1_rule": "daten/iso/sub/s1_role/rule_<split>.json (role, reason)",
            "s1_combined": "daten/iso/sub/s1_role/combined_<split>.json (role, source)",
            "s1_apertus": "daten/iso/sub/s1_role/apertus_<split>.json (role, probs), rule id R1 only",
            "s2_rule": "daten/iso/sub/s2_switch/rule_<split>.json (s2, start_reason)",
            "export_fields": "daten/iso/sub/s1_role/export_meta.json (category_de, category_harmonized, name_klasse)",
            "export_record_found": "the PDF index has a row for the document"},
        "stored_inputs_unchanged": inputs_check,
        "runner_outputs_sha256": canonical_sha({d: core(r) for d, r in recs.items()}),
        "source_files": source_files(),
        "data_files": data_files(),
        "packages": packages(),
        "limits": ["The runner reproduces the stored method on the documents that the method was written on "
                   "(dev in-sample, eval validation). Identity is not accuracy.",
                   "No reference answers were read during the run of a document (runner record without ref).",
                   "No group 7 document, no file of daten/iso/v4/final_* and no test document was opened."],
    }
    FINAL_V4.mkdir(parents=True, exist_ok=True)
    IDENTITY_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": out["status"], "documents": out["documents"], "differences_total": n_diff,
                      "atoms": out["atoms"], "claimed_documents": claims_count, "cscs": {
                          k: out["cscs"][k] for k in ("questions", "requests", "cache_hits", "new_requests")},
                      "guard_selftest": selftest["all_as_expected"],
                      "stopped": stop, "file": rel(IDENTITY_OUT), "sha256": sha256(IDENTITY_OUT)}, indent=1))
    return 0 if ok else 2


# ------------------------------------------------------------------ run on new documents
def run(args) -> int:
    started = clock()
    frozen = check_frozen_method()
    selection = None
    if args.selection or args.selection_sha256:
        if not (args.selection and args.selection_sha256):
            raise SystemExit("give --selection and --selection-sha256 together")
        selection = sealed_selection(Path(args.selection), Path(args.selection_sha256),
                                     Path(args.triage) if args.triage else None)
    ids = [str(d) for d in (args.doc or (selection["ids"] if selection else []))]
    if not ids:
        raise SystemExit("no document: give --doc or a sealed selection")
    if len(set(ids)) != len(ids):
        raise SystemExit("a document id occurs more than once")
    out_dir = Path(args.out).resolve()
    if (out_dir / "run.json").exists():
        raise SystemExit(f"{rel(out_dir)} has a run.json: one run only for each output folder")
    exports = export_records(ids)
    kinds = {}
    for d in ids:
        kinds[d] = admit(d, exports[d]["body_key"], selection)
    if any(k == "selected" and is_test(d, exports[d]["body_key"]) for d, k in kinds.items()) \
            and not out_dir.is_relative_to(FINAL_V4.resolve()):
        raise SystemExit("output of test documents only in daten/gold/final_v4 (process rule 6)")
    prompt = s1m.load_prompt()
    usage: Counter = Counter()
    recs = {}
    with cscs_mode(args.cscs):
        for n, d in enumerate(ids, 1):
            files = input_files(d)
            if files["atome"]["sha256"] is None:
                raise SystemExit(f"{d}: no atoms file")
            check_sealed_inputs(d, files, selection)
            tv = selection["triage"].get(d, "") if kinds[d] == "selected" else sc.triage().get(d, "")
            recs[d] = run_document(d, exports[d], kinds[d], tv, prompt, usage)
            print(f"{n}/{len(ids)} {d}: claim L8 {recs[d]['claims']['L8']['claimed']}, "
                  f"claim L9 {recs[d]['claims']['L9']['claimed']}", flush=True)
    sealed = {}
    for d, r in recs.items():
        v4.write(out_dir / "nos4", d, r["nos4"], "converter m05_iso_runner (nos4)",
                 f"{RUNNER_VERSION}: isolation stage, E20 version 4.2 answers before the collapse map")
        err = v4.validate4(out_dir / "nos4" / f"{d}.json")
        if err:
            raise SystemExit(f"{d}: validate4 gives {len(err)} errors")
        (out_dir / "records").mkdir(parents=True, exist_ok=True)
        (out_dir / "records" / f"{d}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        sealed[d] = {"admission": r["admission"],
                     "claim_L8": r["claims"]["L8"]["claimed"], "claim_L9": r["claims"]["L9"]["claimed"],
                     "nos4_sha256": sha256(out_dir / "nos4" / f"{d}.json"),
                     "record_sha256": sha256(out_dir / "records" / f"{d}.json")}
    summary = {"schema": "parlpdfech-runner-run/1", "status": "NOT RELEASED", "run_date": started, "finished": clock(),
               "runner": {"path": rel(RUNNER_PATH), "sha256": sha256(RUNNER_PATH), "version": RUNNER_VERSION},
               "frozen_method": frozen, "cscs_mode": args.cscs,
               "cscs": {k: usage[k] for k in ("questions", "requests", "cache_hits", "prompt_tokens", "completion_tokens")},
               "selection": None if selection is None else {k: selection[k] for k in
                                                            ("path", "sha256", "sha256_file", "triage_column", "triage_file")},
               "documents": len(recs), "validate4_errors": 0,
               "claimed": {lid: sum(1 for x in sealed.values() if x[f"claim_{lid}"]) for lid in ("L8", "L9")},
               "per_document": sealed, "source_files": source_files(), "data_files": data_files(),
               "packages": packages()}
    (out_dir / "run.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"documents": len(recs), "claimed": summary["claimed"], "cscs": summary["cscs"],
                      "run_json": rel(out_dir / "run.json"), "sha256": sha256(out_dir / "run.json")}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="isolation stage of the converter (L9, nos4)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("identity")
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--doc", nargs="*")
    r.add_argument("--selection")
    r.add_argument("--selection-sha256")
    r.add_argument("--triage")
    r.add_argument("--cscs", default="cache-only", choices=["cache-only", "live"])
    a = ap.parse_args()
    try:
        code = identity() if a.cmd == "identity" else run(a)
    except (Refused, CacheMiss, ValueError) as ex:      # ValueError: a guard of m03_sub_common refused
        print(f"stopped ({type(ex).__name__}): {ex}", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()
