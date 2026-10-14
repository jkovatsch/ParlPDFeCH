# SPDX-License-Identifier: Apache-2.0
"""Rule files from the PDF alone: the chain of `src/m10_rules.py` with the empty export fields of the package.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5) for the AI
agent. No human checked this file. Status: PROPOSED, NOT RELEASED. Each value of this tool has the mark "after the
opening" of addendum G (chapter 6.5), as the values of round 3.

1 Why
  The stored rule files `daten/gj/rules/<doc>.json` were made with 3 export fields of the document
  (`m05_iso_runner.EXPORT_FIELDS`). The S1 rule ids O1, O2, P2 and R1 have a condition on these fields
  (`src/m03_sub_s1_role.py`). The package gives the S1 rule empty fields (`package/worker/fresh.py`, stage 3).
  This tool makes the rule file as the package does. Thus the measured reader and the delivered reader agree.

2 Command `build`
  For each id it calls `m10_rules.run_document(d, EMPTY, admission, split)` and writes
  `daten/gj/rules_pdf/<doc>.json`. The form and the JSON options are those of `m10_rules.run`.
  EMPTY is `{"found": False, "body_key": "", "affair_id": "", "category_de": "", "category_harmonized": "",
  "name_klasse": ""}`: the value of the package. The keys `body_key` and `export_record` of the file show it.
  No export record is read for the rule. The code makes this sure in 3 ways:
  a. The tool does not call `m10_rules.admit_all` (the one function of the run that reads the PDF index).
  b. `block_export` replaces `m05_iso_runner.export_records`, `m03_sub_s1_role.export_meta` and
     `m10_rules.admit_all` by a function that raises `ExportRead`.
  c. `block_export` puts a check before `m03_sub_s1_role.rule`: it raises if one field of the rule is not "".
  The parliament is used in 3 places, and only for a guard. The source is the guard table of `src/m10_guard.py`
  (`daten/analyse/dokumente/dokumente_merkmale.csv.gz`, columns id and parliament):
  1. `m10_guard.check`: the split of the id (dev, validation, group7) and the refusal of a test document.
  2. `m10_score.split_of(d, parliament, allow_group7=True)`: the guard of `m10_rules.admit_all`. Its result
     must be equal to the split of the guard. The value goes to the key `split` of the file.
  3. `m05_iso_runner.is_test(d, parliament)`: the second guard of `m10_rules.admit_all`.
  The rule chain does not get the parliament: `run_document` gives `body_key` "" to the record of the document.
  No step of the chain reads this key. The key `admission` is `known` for a document of `m03_sub_common.load()`
  and `loader` for each other document (`m10_rules.admission_of`). The context `m10_rules.admitted` stops if
  this value is wrong. The package always gives `loader`: its document is never in that list.
  The triage verdict of a `known` document is not read by a step of the chain.
  Default ids: each file name of `daten/gj/rules` that the guard gives the split dev.
  A build that is not a sealed build refuses each id that is not a development document.

3 Sealed build (the documents of the one last run)
  `build --sealed-build --ids-from-guard validation,group7` builds the files of the validation documents and
  of the group 7 documents. The tool takes the ids from the file names of `daten/gj/rules` and from the guard.
  It prints one line: the count of files written and the count of failures. It prints no id, no message of a
  document and no rule output. The output of each called function is discarded for the time of the build.
  Before the first document, it adds one entry (time, tool, command) to
  `daten/gj_values/heads2/last_run_access.json`. The form is that of `m11_value_heads2_data.refuse_sealed`.
  A test document of the guard stops the build before a file is opened. A refusal of the 2 guards of
  `m10_rules.admit_all` is counted as a failure of that document. No file of that document is opened.
  The record of this build has counts only. A sealed build takes no `--access-record`, no `--record` and no
  `--out`: its entry goes to the one access record, and its files go to `daten/gj/rules_pdf`.
  If a document fails, the build removes an older file of that id. Each file is written to a temporary
  name and then renamed. The record holds the count of the files of these ids in the output folder.
  An error of another type outside the document loop prints its type only (exit code 3).

4 Command `compare` (development documents only)
  Counts of the differences between the stored file and the new file. Output:
  `daten/gj_values/round4/rules_compare.json` and `rules_compare.md`.
  The kind of this comparison is the result of `m11_cascade.kind_of_role`. It does not apply rule V5 of
  `src/m11_values_cascade.py`.

5 Command `check` (development documents only)
  a. With the true export fields (read as `m10_rules.admit_all` reads them) the call gives the stored file. This
     proves the call form. 40 development documents at fixed positions of the sorted id list. No key is left out.
  b. The S1 rule with empty fields cannot give the rule ids P2 and R1. It can give O1 and O2 from a heading of
     the PDF. The check runs the decision list on each combination of the feature values.
  c. The 3 public sample documents against the records that the package made for the same PDF with no export
     record (`package/work`, `package/build`; read only). The package is not started.
  Output: `daten/gj_values/round4/rules_pdf_check.json`.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_rules_pdf.py build
  uv run --offline --frozen --no-sync python src/m11_rules_pdf.py compare
  uv run --offline --frozen --no-sync python src/m11_rules_pdf.py check
  uv run --offline --frozen --no-sync python src/m11_rules_pdf.py build --sealed-build --ids-from-guard validation,group7
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import itertools
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import m10_guard as guard  # noqa: E402
import m10_rules as mr  # noqa: E402  (not changed; imports the frozen runner and the sub-tasks)

runner, sc, s1m, ms = mr.runner, mr.sc, mr.s1m, mr.ms

VERSION = "m11-rules-pdf-1"
SCRIPT = Path(__file__).resolve()
ACTOR = "AI agent (Claude Opus 5.5); no human checked this file"
STATUS = "PROPOSED, NOT RELEASED"
MARK = "after the opening (addendum G, chapter 6.5)"
STORED_DIR = mr.OUT_DIR                                   # daten/gj/rules (made with export fields)
OUT_DIR = ROOT / "daten/gj/rules_pdf"
ROUND4 = ROOT / "daten/gj_values/round4"
BUILD_RECORD = ROUND4 / "rules_pdf_build.json"
BUILD_RECORD_LAST = ROUND4 / "rules_pdf_build_last_run.json"
COMPARE_JSON = ROUND4 / "rules_compare.json"
COMPARE_MD = ROUND4 / "rules_compare.md"
CHECK_JSON = ROUND4 / "rules_pdf_check.json"
ACCESS_RECORD = ROOT / "daten/gj_values/heads2/last_run_access.json"
FIX_RECORD = ROOT / "daten/gj_values/heads2/last_run_fix.json"
EMPTY_EXPORT = {"found": False, "body_key": "", "affair_id": "", **{k: "" for k in runner.EXPORT_FIELDS}}
EXPORT_IDS = ("O1", "O2", "P2", "R1")                     # S1 rule ids with a condition on export fields
SEALED_SPLITS = ("validation", "group7")
TEST_REASONS = ("G5", "G6", "G7")
SAMPLES = ("26171", "879163", "714840")
CHECK_DOCUMENTS = 40
PACKAGE_FOLDERS = ("package/work", "package/build")
_TRUE_EXPORT_RECORDS = runner.export_records              # used only by the command `check`, part a


class ExportRead(RuntimeError):
    """A step tried to read an export record, or the S1 rule got a field that is not empty."""


class Stop(SystemExit):
    """The tool refuses the call."""


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path | str) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def write_json(p: Path, obj, indent: int | None = 1) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    tmp.replace(p)


def header(command: str) -> dict:
    return {"actor": ACTOR, "status": STATUS, "mark": MARK, "made": now(), "command": command,
            "tool": {"path": rel(SCRIPT), "sha256": sha256_file(SCRIPT), "version": VERSION},
            "rules": {"path": rel(mr.RULES_PATH), "sha256": sha256_file(mr.RULES_PATH), "version": mr.RULES_VERSION}}


# ------------------------------------------------------------------ no export record for the rule (chapter 2)
def _no_export(*_a, **_k):
    raise ExportRead("m11_rules_pdf: no export record is read for the rule")


_BLOCKED = False


def block_export() -> None:
    """Replace each function that reads an export record, and put a check before the S1 rule."""
    global _BLOCKED
    if _BLOCKED:
        return
    runner.export_records = _no_export
    s1m.export_meta = _no_export
    mr.admit_all = _no_export
    rule = s1m.rule

    def rule_with_empty_fields(doc_id: str, meta: dict) -> dict:
        row = meta.get(doc_id)
        if not isinstance(row, dict) or set(row) != set(runner.EXPORT_FIELDS) or any(v != "" for v in row.values()):
            raise ExportRead("m11_rules_pdf: the S1 rule got an export field that is not empty")
        return rule(doc_id, meta)

    rule_with_empty_fields.unchecked = rule
    s1m.rule = rule_with_empty_fields
    _BLOCKED = True


@contextlib.contextmanager
def true_export_rule():
    """Only for the command `check`, part a: the S1 rule without the check of the empty fields."""
    checked = s1m.rule
    s1m.rule = getattr(checked, "unchecked", checked)
    try:
        yield
    finally:
        s1m.rule = checked


@contextlib.contextmanager
def no_output(active: bool):
    """Discard the output of the called functions (sealed build)."""
    if not active:
        yield
        return
    with open(os.devnull, "w", encoding="utf-8") as null, contextlib.redirect_stdout(null), \
            contextlib.redirect_stderr(null):
        yield


# ------------------------------------------------------------------ ids and guards
def stored_names() -> list[str]:
    """The ids of the file names of daten/gj/rules. No file is opened."""
    return sorted((p.stem for p in STORED_DIR.glob("*.json") if p.stem.isdigit()), key=int)


def ids_of_splits(splits: tuple[str, ...]) -> tuple[list[str], dict, dict]:
    """(ids, {id: split}, {id: parliament}) of the stored names that the guard gives one of the splits.
    A test document or a refusal of another kind stops the tool. The message has counts only."""
    names = stored_names()
    ver = guard.check(names, splits)
    test = [v for v in ver if v["split"] == "test" or any(r.split(" ", 1)[0] in TEST_REASONS for r in v["refused"])]
    if test:
        raise Stop(f"guard: {len(test)} test documents in the id list: refused (process rule 6)")
    other = [v for v in ver if v["refused"] and not all(r.startswith("G9") for r in v["refused"])]
    if other:
        raise Stop(f"guard: {len(other)} ids with a refusal that is not the split: refused")
    take = [v for v in ver if not v["refused"]]
    return ([v["doc_id"] for v in take], {v["doc_id"]: v["split"] for v in take},
            {v["doc_id"]: v["parliament"] for v in take})


def dev_ids() -> tuple[list[str], dict, dict]:
    return ids_of_splits(("dev",))


def given_dev_ids(ids: list[str]) -> tuple[list[str], dict, dict]:
    """Ids of the command line: each one must be a development document (guard, split dev)."""
    if len(set(ids)) != len(ids):
        raise Stop("a document id occurs more than once")
    try:
        g = guard.assert_allowed(ids, ("dev",))
    except guard.GuardRefusal:
        raise Stop("guard: one or more ids are not development documents: refused") from None
    return ids, g["split_of"], g["parliament_of"]


def guards_of_m10(d: str, parliament: str, split: str, allow_final: bool) -> str:
    """The guards of m10_rules.admit_all with the parliament of the guard table. Returns the admission."""
    if ms.split_of(d, parliament, allow_group7=True) != split:
        raise ms.Refused("the split of m10_score and the split of the guard are not equal")
    if runner.is_test(d, parliament):
        raise ms.Refused("test document (process rule 6): refused")
    return mr.admission_of(d, allow_final)


def dump(rec: dict) -> str:
    """The JSON options of m10_rules.run."""
    return json.dumps(rec, ensure_ascii=False, separators=(",", ":"))


# ------------------------------------------------------------------ build
def build_documents(ids: list[str], split: dict, parliament: dict, out: Path, sealed: bool) -> dict:
    """Write one rule file for each id. Sealed: no output of a document, failures are counted by type only."""
    block_export()
    out.mkdir(parents=True, exist_ok=True)
    files, failures, counts, rule_ids = {}, Counter(), Counter(), Counter()
    t0 = time.perf_counter()
    for d in ids:
        p = out / f"{d}.json"
        try:
            with no_output(sealed):
                kind = guards_of_m10(d, parliament[d], split[d], allow_final=sealed)
                rec = mr.run_document(d, dict(EMPTY_EXPORT), kind, split[d])
                if rec["export_record"]["found"] or rec["body_key"] != "":
                    raise ExportRead("the record does not have the empty export fields")
                tmp = p.with_suffix(".json.tmp")
                tmp.write_text(dump(rec), encoding="utf-8")
                tmp.replace(p)
        except KeyboardInterrupt:
            raise
        except BaseException as ex:  # noqa: BLE001  (SystemExit of the chain is a failure of one document)
            if not sealed:
                raise
            failures[type(ex).__name__] += 1
            with contextlib.suppress(OSError):           # an older file of this id must not stay after a failure
                p.unlink(missing_ok=True)
                p.with_suffix(".json.tmp").unlink(missing_ok=True)
            with contextlib.suppress(Exception):
                mr.free_caches()
            continue
        files[rel(p) if p.is_relative_to(ROOT) else str(p)] = sha256_file(p)
        counts[f"split {split[d]}"] += 1
        counts[f"admission {kind}"] += 1
        if not sealed:
            rule_ids[rec["document"]["s1"]["rule_id"]] += 1
            counts["needs_apertus"] += rec["document"]["d1"]["needs_apertus"]
            counts["blocks"] += len(rec["blocks"])
    return {"documents": len(ids), "files_written": len(files), "failures": sum(failures.values()),
            "files_in_output_folder_of_these_ids": sum(1 for d in ids if (out / f"{d}.json").is_file()),
            "failure_types": dict(failures), "counts": dict(counts),
            "s1_rule_ids": dict(sorted(rule_ids.items())) if not sealed else "not counted in a sealed build",
            "seconds": round(time.perf_counter() - t0, 1), "outputs_sha256_canonical": runner.canonical_sha(files),
            "outputs": files if not sealed else "not listed in a sealed build"}


def add_access_entry(access: Path, note: str) -> dict:
    """One entry in the form of m11_value_heads2_data.refuse_sealed (object with the key `entries`)."""
    entry = {"time": now(), "tool": rel(SCRIPT), "command": list(sys.argv), "sealed_paths_named": [],
             "fix_record_sha256": sha256_file(FIX_RECORD) if FIX_RECORD.is_file() else None, "note": note}
    log = json.loads(access.read_text(encoding="utf-8")) if access.is_file() else {
        "schema": "parlpdfech-heads2-last-run-access/1", "rule": "addendum I, chapter 10.2, item 6", "entries": []}
    if not isinstance(log, dict) or not isinstance(log.get("entries"), list):
        raise Stop("the access record does not have the object form with the key entries")
    log["entries"].append(entry)
    write_json(access, log)
    return entry


def cmd_build(a) -> int:
    out = Path(a.out).resolve() if a.out else OUT_DIR
    if out == STORED_DIR.resolve():
        raise Stop("the output folder must not be daten/gj/rules")
    ident = mr.check_identity_record()
    with no_output(a.sealed_build):
        frozen = runner.check_frozen_method()
    if a.sealed_build:
        splits = tuple(s for s in (a.ids_from_guard or "").split(",") if s)
        if not splits or set(splits) - set(SEALED_SPLITS) or a.ids or a.limit:
            raise Stop("a sealed build needs --ids-from-guard with validation, group7 or both, and no --ids, no --limit")
        if a.access_record or a.record or a.out:
            raise Stop("a sealed build takes no --access-record, no --record and no --out")
        ids, split, parliament = ids_of_splits(splits)
        entry = add_access_entry(ACCESS_RECORD,
                                 "rule files from the PDF alone for the documents of the one last run; "
                                 "the tool prints counts only and reads no export record and no reference")
        res = build_documents(ids, split, parliament, out, sealed=True)
        record = BUILD_RECORD_LAST
        write_json(record, {"schema": "parlpdfech-rules-pdf-build/1", **header("build --sealed-build"),
                            "sealed_build": True, "splits": list(splits), "export_fields_given": EMPTY_EXPORT,
                            "identity_record": ident, "frozen_method": frozen, "access_entry": entry,
                            "output_folder": rel(out), **res,
                            "limits": ["Counts only: no id, no rule output and no message of a document."]})
        print(json.dumps({"files_written": res["files_written"], "failures": res["failures"],
                          "files_in_output_folder_of_these_ids": res["files_in_output_folder_of_these_ids"]}))
        return 0 if res["failures"] == 0 and res["files_in_output_folder_of_these_ids"] == res["files_written"] else 2
    if a.ids_from_guard:
        raise Stop("--ids-from-guard is only for a sealed build")
    if a.ids:
        ids, split, parliament = given_dev_ids([x for x in a.ids.split(",") if x])
    else:
        ids, split, parliament = dev_ids()
    if a.limit:
        ids = ids[:a.limit]
    res = build_documents(ids, split, parliament, out, sealed=False)
    complete = not a.ids and not a.limit
    record = Path(a.record) if a.record else (BUILD_RECORD if complete and out == OUT_DIR else out.parent / "rules_pdf_build_part.json")
    write_json(record, {"schema": "parlpdfech-rules-pdf-build/1", **header("build"), "sealed_build": False,
                        "splits": ["dev"], "complete": complete, "export_fields_given": EMPTY_EXPORT,
                        "identity_record": ident, "frozen_method": frozen, "output_folder": rel(out), **res,
                        "limits": ["Counts of rule outputs only: no reference was read, no quality value."]})
    print(json.dumps({k: res[k] for k in ("documents", "files_written", "failures", "counts", "s1_rule_ids", "seconds")}
                     | {"record": rel(record)}, indent=1))
    return 0


# ------------------------------------------------------------------ compare (development documents only)
def kind_of(role: str, rule_id: str) -> str:
    """The kind of the rule chain: `m11_cascade.kind_of_role(rule role, rule id)`. The function `kind_of` of
    `src/m11_values_cascade.py` uses the same call. For a document with the rule id D0 it then applies rule V5.
    This comparison does not apply rule V5."""
    import m11_cascade as casc  # noqa: PLC0415
    return casc.kind_of_role(role, rule_id)


def table(c: Counter) -> dict:
    return {f"{a} -> {b}": n for (a, b), n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))}


def cmd_compare(a) -> int:
    new_dir = Path(a.new).resolve() if a.new else OUT_DIR
    ids, _, _ = dev_ids()
    n = Counter()
    by_id, by_role, by_kind, by_d1, by_option = Counter(), Counter(), Counter(), Counter(), Counter()
    changed_docs, other_keys = [], Counter()
    for d in ids:
        q = new_dir / f"{d}.json"
        if not q.is_file():
            n["new_file_missing"] += 1
            continue
        old = json.loads((STORED_DIR / f"{d}.json").read_text(encoding="utf-8"))
        new = json.loads(q.read_text(encoding="utf-8"))
        n["documents"] += 1
        so, sn = old["document"]["s1"], new["document"]["s1"]
        ko, kn = kind_of(so["rule_role"], so["rule_id"]), kind_of(sn["rule_role"], sn["rule_id"])
        by_id[(so["rule_id"], sn["rule_id"])] += 1
        by_role[(so["rule_role"], sn["rule_role"])] += 1
        by_kind[(ko, kn)] += 1
        by_d1[(old["document"]["d1"]["option"], new["document"]["d1"]["option"])] += 1
        n["stored_rule_id_with_export_condition"] += so["rule_id"] in EXPORT_IDS
        n["new_rule_id_with_export_condition"] += sn["rule_id"] in EXPORT_IDS
        n["s1_rule_id_differs"] += so["rule_id"] != sn["rule_id"]
        n["s1_rule_role_differs"] += so["rule_role"] != sn["rule_role"]
        n["combined_role_differs"] += so["combined_role"] != sn["combined_role"]
        n["d1_option_differs"] += old["document"]["d1"]["option"] != new["document"]["d1"]["option"]
        n["kind_differs"] += ko != kn
        n["needs_apertus_stored"] += old["document"]["d1"]["needs_apertus"]
        n["needs_apertus_new"] += new["document"]["d1"]["needs_apertus"]
        n["claim_L9_differs"] += old["document"]["claims"]["L9"]["claimed"] != new["document"]["claims"]["L9"]["claimed"]
        bo, bn = old["blocks"], new["blocks"]
        if [b["block"] for b in bo] != [b["block"] for b in bn] or old["atoms"]["ids"] != new["atoms"]["ids"]:
            raise Stop(f"{d}: the blocks or the atoms of the two files are not the same")
        diff = [(x["option"], y["option"]) for x, y in zip(bo, bn) if x["option"] != y["option"]]
        by_option.update(diff)
        n["blocks"] += len(bo)
        n["blocks_option_differs"] += len(diff)
        n["documents_with_a_block_option_that_differs"] += bool(diff)
        n["blocks_tier_differs"] += sum(x["tier"] != y["tier"] for x, y in zip(bo, bn))
        n["atoms"] += len(old["atoms"]["nos4"])
        n["atoms_nos4_differs"] += sum(x != y for x, y in zip(old["atoms"]["nos4"], new["atoms"]["nos4"]))
        keys = sorted(k for k in old if old[k] != new.get(k))
        other_keys.update(keys)
        n["files_equal_but_body_key_and_export_record"] += set(keys) <= {"body_key", "export_record"}
        if so["rule_id"] != sn["rule_id"]:
            changed_docs.append({"doc_id": d, "stored": [so["rule_id"], so["rule_role"], ko],
                                 "new": [sn["rule_id"], sn["rule_role"], kn], "blocks": len(bo),
                                 "blocks_option_differs": len(diff)})
    out = {"schema": "parlpdfech-rules-compare/1", **header("compare"),
           "stored_files": rel(STORED_DIR) + " (S1 rule with 3 export fields)",
           "new_files": rel(new_dir) + " (S1 rule with empty fields, as the package)",
           "development_documents": len(ids), "counts": dict(n),
           "s1_rule_id_stored_to_new": table(by_id),
           "s1_rule_id_stored_to_new_only_changes": table(Counter({k: v for k, v in by_id.items() if k[0] != k[1]})),
           "s1_rule_role_stored_to_new_only_changes": table(Counter({k: v for k, v in by_role.items() if k[0] != k[1]})),
           "d1_option_stored_to_new_only_changes": table(Counter({k: v for k, v in by_d1.items() if k[0] != k[1]})),
           "kind_stored_to_new": table(by_kind),
           "kind_stored_to_new_only_changes": table(Counter({k: v for k, v in by_kind.items() if k[0] != k[1]})),
           "block_option_stored_to_new_only_changes": table(by_option),
           "top_keys_that_differ": dict(other_keys),
           "documents_with_another_s1_rule_id": changed_docs,
           "kind_definition": "m11_cascade.kind_of_role(document.s1.rule_role, document.s1.rule_id). The function "
                              "kind_of of src/m11_values_cascade.py uses the same call. For a document with the "
                              "rule id D0 it then applies rule V5. This comparison does not apply rule V5.",
           "limits": ["Counts of rule outputs only: no reference was read, no quality value."]}
    out_json = Path(a.out_json) if a.out_json else COMPARE_JSON
    out_md = Path(a.out_md) if a.out_md else COMPARE_MD
    write_json(out_json, out)
    out_md.write_text(compare_md(out), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("development_documents", "counts", "s1_rule_id_stored_to_new_only_changes",
                                          "kind_stored_to_new_only_changes",
                                          "block_option_stored_to_new_only_changes")} |
                     {"files": [rel(out_json), rel(out_md)]}, indent=1))
    return 0


def md_table(head: tuple[str, str, str], rows: dict) -> list[str]:
    lines = [f"| {head[0]} | {head[1]} | {head[2]} |", "|---|---|---:|"]
    for k, v in rows.items():
        x, y = k.split(" -> ")
        lines.append(f"| `{x}` | `{y}` | {v} |")
    if not rows:
        lines.append("| (no row) | (no row) | 0 |")
    return lines


def compare_md(o: dict) -> str:
    c = o["counts"]
    g = lambda k: c.get(k, 0)  # noqa: E731
    lines = [
        "# Rule files with export fields and rule files from the PDF alone",
        "",
        f"Actor: AI agent (Claude Opus 5.5). No human checked this file. Status: PROPOSED. Made: {o['made']}.",
        "Each value has the mark \"after the opening\" of addendum G (chapter 6.5).",
        "",
        "## 1 Subject",
        "",
        "The stored rule files are in `daten/gj/rules`. The S1 rule of these files got 3 export fields.",
        "The new rule files are in `daten/gj/rules_pdf`. The S1 rule of these files got empty fields, as in the package.",
        "The tool is `src/m11_rules_pdf.py`. The data file is `daten/gj_values/round4/rules_compare.json`.",
        "This file has counts of rule outputs only. No reference was read. It gives no quality value.",
        "",
        "## 2 Counts of documents",
        "",
        "| Count | Documents |",
        "|---|---:|",
        f"| development documents with the two files | {g('documents')} |",
        f"| new file is missing | {g('new_file_missing')} |",
        f"| stored S1 rule id is `O1`, `O2`, `P2` or `R1` | {g('stored_rule_id_with_export_condition')} |",
        f"| new S1 rule id is `O1`, `O2`, `P2` or `R1` | {g('new_rule_id_with_export_condition')} |",
        f"| S1 rule id differs | {g('s1_rule_id_differs')} |",
        f"| S1 rule role differs | {g('s1_rule_role_differs')} |",
        f"| combined role differs | {g('combined_role_differs')} |",
        f"| D1 option differs | {g('d1_option_differs')} |",
        f"| kind of the document differs | {g('kind_differs')} |",
        f"| claim flag of `L9` differs | {g('claim_L9_differs')} |",
        f"| `needs_apertus` in the stored file | {g('needs_apertus_stored')} |",
        f"| `needs_apertus` in the new file | {g('needs_apertus_new')} |",
        f"| one or more block options differ | {g('documents_with_a_block_option_that_differs')} |",
        f"| the file is equal but for `body_key` and `export_record` | {g('files_equal_but_body_key_and_export_record')} |",
        "",
        "## 3 Counts of blocks and atoms",
        "",
        "| Count | Value |",
        "|---|---:|",
        f"| blocks | {g('blocks')} |",
        f"| blocks whose option differs | {g('blocks_option_differs')} |",
        f"| blocks whose tier differs | {g('blocks_tier_differs')} |",
        f"| atoms | {g('atoms')} |",
        f"| atoms whose `nos4` answer differs | {g('atoms_nos4_differs')} |",
        "",
        "## 4 S1 rule id: stored to new (only changes)",
        "",
        *md_table(("Stored rule id", "New rule id", "Documents"), o["s1_rule_id_stored_to_new_only_changes"]),
        "",
        "## 5 Kind of the document: stored to new (only changes)",
        "",
        "The kind is the result of `m11_cascade.kind_of_role` for the S1 rule role and the S1 rule id.",
        "The function `kind_of` of `src/m11_values_cascade.py` uses the same call.",
        "For a document with the rule id D0 it then applies rule V5. This comparison does not apply rule V5.",
        "",
        *md_table(("Stored kind", "New kind", "Documents"), o["kind_stored_to_new_only_changes"]),
        "",
        "## 6 D1 option: stored to new (only changes)",
        "",
        *md_table(("Stored option", "New option", "Documents"), o["d1_option_stored_to_new_only_changes"]),
        "",
        "## 7 Block option: stored to new (only changes)",
        "",
        *md_table(("Stored option", "New option", "Blocks"), o["block_option_stored_to_new_only_changes"]),
        "",
        "## 8 Limits",
        "",
        "The counts are for the development documents only. The documents of the last run were not opened.",
        "A rule id `O1` or `O2` in a new file comes from a heading of the PDF, not from an export field.",
        "The rule ids `P2` and `R1` cannot occur in a new file.",
        "",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ check (development documents only)
def check_a(ids: list[str], split: dict, parliament: dict) -> dict:
    """True export fields give the stored file (the call form)."""
    step = [(i * len(ids)) // CHECK_DOCUMENTS for i in range(CHECK_DOCUMENTS)]
    chosen = [ids[i] for i in step]
    guard.assert_allowed(chosen, ("dev",))
    exports = _TRUE_EXPORT_RECORDS(chosen)               # as m10_rules.admit_all; rows of these 40 ids only
    rows, equal, with_export_id = [], 0, 0
    for d in chosen:
        ex = exports[d]
        if not ex["found"] or ex["body_key"] != parliament[d]:
            raise Stop(f"{d}: the PDF index row and the guard table do not give the same parliament")
        kind = guards_of_m10(d, ex["body_key"], split[d], allow_final=False)
        with true_export_rule():
            rec = json.loads(dump(mr.run_document(d, ex, kind, split[d])))
        stored = json.loads((STORED_DIR / f"{d}.json").read_text(encoding="utf-8"))
        diff = sorted(k for k in set(stored) | set(rec) if stored.get(k) != rec.get(k))
        equal += not diff
        with_export_id += stored["document"]["s1"]["rule_id"] in EXPORT_IDS
        rows.append({"doc_id": d, "equal": not diff, "keys_that_differ": diff,
                     "stored_s1_rule_id": stored["document"]["s1"]["rule_id"]})
    return {"documents": len(chosen), "positions": step, "equal_to_the_stored_file": equal,
            "keys_left_out": [], "documents_with_a_stored_rule_id_O1_O2_P2_R1": with_export_id,
            "note": "The file has no time and no absolute path. Thus the comparison leaves out no key.",
            "passed": equal == len(chosen), "rows": rows}


def check_b(new_dir: Path, ids: list[str]) -> dict:
    """The decision list with empty fields on each combination of the feature values."""
    rule = getattr(s1m.rule, "unchecked", s1m.rule)
    saved = s1m.features
    grid = {"gov_resolution_head": (False, True), "other_kind_head": (False, True),
            "protocol_of_parliament": (False, True), "decision_text_head": (False, True),
            "committee_head_index": (None, 0), "answer": ((None, None), (5, 0.1), (5, 0.9)),
            "n_block_marks": (0, 1), "sponsor_marks_before_answer": (0, 1), "affair_type_line": (False, True),
            "exec_proposal": (False, True)}
    seen, o1_without, o2_without = Counter(), 0, 0
    try:
        for combo in itertools.product(*grid.values()):
            f = dict(zip(grid, combo))
            f["first_answer_index"], f["first_answer_pos"] = f.pop("answer")
            f.update(n_body=10, heads=[], n_answer_marks=0)
            s1m.features = lambda _d, f=f: f
            r = rule("0", {"0": {k: "" for k in runner.EXPORT_FIELDS}})
            seen[r["reason"]] += 1
            o1_without += r["reason"] == "O1" and not f["gov_resolution_head"]
            o2_without += r["reason"] == "O2" and not f["other_kind_head"]
    finally:
        s1m.features = saved
    built = Counter()
    for d in ids:
        q = new_dir / f"{d}.json"
        if q.is_file():
            built[json.loads(q.read_text(encoding="utf-8"))["document"]["s1"]["rule_id"]] += 1
    ok = (seen["P2"] == 0 and seen["R1"] == 0 and o1_without == 0 and o2_without == 0
          and s1m.RX_ANSWER.search("") is None and built["P2"] == 0 and built["R1"] == 0)
    return {"combinations": sum(seen.values()), "rule_ids_of_the_combinations": dict(sorted(seen.items())),
            "P2_possible": seen["P2"] > 0, "R1_possible": seen["R1"] > 0,
            "O1_without_the_PDF_feature_gov_resolution_head": o1_without,
            "O2_without_the_PDF_feature_other_kind_head": o2_without,
            "RX_ANSWER_matches_the_empty_text": s1m.RX_ANSWER.search("") is not None,
            "rule_ids_of_the_new_development_files": dict(sorted(built.items())),
            "new_development_files": sum(built.values()),
            "explanation": ["P2 has only export conditions (category_harmonized, name_klasse): not possible.",
                            "R1 has only export conditions (category_harmonized, category_de, name_klasse): not possible.",
                            "O1 is possible: the PDF feature gov_resolution_head (a heading of the PDF) gives it.",
                            "O2 is possible: the PDF feature other_kind_head (the first heading of the PDF) gives it.",
                            "With no R1, no document needs Apertus for D1: needs_apertus is false and by_d1 is null."],
            "passed": ok}


def package_records(pdf_sha: str) -> list[dict]:
    """Records of the package for this PDF with no export record (convert.json and view.json; read only)."""
    out = []
    for folder in PACKAGE_FOLDERS:
        for p in sorted((ROOT / folder).rglob("convert.json")):
            try:
                text = p.read_text(encoding="utf-8")
                if pdf_sha not in text:
                    continue
                c = json.loads(text)
                fr = (c.get("fresh") or {}).get("rules") or {}
                if c.get("pdf_sha256") != pdf_sha or not str(fr.get("export_fields", "")).startswith("empty"):
                    continue
                view = json.loads((p.parent / "view.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            labels = view.get("labels") or []
            d1 = next((x for x in labels if x.get("id") == "d1"), {})
            blocks = [x for x in labels if x.get("kind") == "block_slot"]
            rule_blocks = all((x.get("source") or {}).get("kind") == "rule" for x in blocks)
            out.append({"path": rel(p), "mode": c.get("mode"), "s1_rule_id": fr.get("s1_rule_id"),
                        "needs_apertus": fr.get("needs_apertus"), "admission": fr.get("admission"),
                        "d1_option": d1.get("value"), "d1_rule_id": (d1.get("source") or {}).get("rule_id"),
                        "block_sources_all_rule": rule_blocks,
                        "block_options": [x.get("value") for x in blocks],
                        "block_tiers": [(x.get("source") or {}).get("tier") for x in blocks],
                        "view_blocks": len(view.get("blocks") or [])})
    return out


def check_c(new_dir: Path) -> dict:
    guard.assert_allowed(list(SAMPLES), ("dev",))
    res, ok = {}, True
    for d in SAMPLES:
        q = new_dir / f"{d}.json"
        if not q.is_file():
            res[d], ok = {"new_file": "missing"}, False
            continue
        new = json.loads(q.read_text(encoding="utf-8"))
        stored = json.loads((STORED_DIR / f"{d}.json").read_text(encoding="utf-8"))
        pdf_sha = json.loads(guard.iso_file("docling", d).read_text(encoding="utf-8")).get("sha256")
        recs = package_records(pdf_sha) if pdf_sha else []
        mine = {"s1_rule_id": new["document"]["s1"]["rule_id"], "s1_rule_role": new["document"]["s1"]["rule_role"],
                "d1_option": new["document"]["d1"]["option"], "blocks": len(new["blocks"]),
                "block_options": [b["option"] for b in new["blocks"]]}
        rows = Counter()
        for r in recs:
            rows["records"] += 1
            rows["s1_rule_id_equal"] += r["s1_rule_id"] == mine["s1_rule_id"]
            rows["d1_option_equal"] += r["d1_option"] == mine["d1_option"]
            if r["block_sources_all_rule"] and len(r["block_options"]) == mine["blocks"]:
                rows["records_with_rule_blocks_of_the_same_count"] += 1
                rows["block_options_equal"] += r["block_options"] == mine["block_options"]
        good = bool(recs) and rows["s1_rule_id_equal"] == rows["records"] and rows["d1_option_equal"] == rows["records"] \
            and rows["block_options_equal"] == rows["records_with_rule_blocks_of_the_same_count"]
        ok = ok and good
        res[d] = {"new_file": {k: mine[k] for k in ("s1_rule_id", "s1_rule_role", "d1_option", "blocks")},
                  "stored_file": {"s1_rule_id": stored["document"]["s1"]["rule_id"],
                                  "s1_rule_role": stored["document"]["s1"]["rule_role"],
                                  "d1_option": stored["document"]["d1"]["option"],
                                  "block_options_equal_to_the_new_file":
                                      [b["option"] for b in stored["blocks"]] == mine["block_options"]},
                  "package_records": dict(rows),
                  "package_values": dict(Counter(f"{r['mode']}: rule id {r['s1_rule_id']}, D1 {r['d1_option']}, "
                                                 f"{len(r['block_options'])} block labels" for r in recs)),
                  "package_paths": [r["path"] for r in recs][:12], "agrees": good}
    return {"documents": res, "passed": ok,
            "notes": ["The package record gives the S1 rule id and the D1 option. It does not give the rule role.",
                      "The D1 option of the rule file is a function of the rule role (m10_rules.D1_OF_ROLE).",
                      "The package made its own Docling file of the PDF. The block options are compared only if the "
                      "count of block labels is equal and each block label has the source rule.",
                      "The package was not started. Only records on the disk were read."]}


def cmd_check(a) -> int:
    new_dir = Path(a.new).resolve() if a.new else OUT_DIR
    mr.check_identity_record()
    runner.check_frozen_method()
    block_export()
    ids, split, parliament = dev_ids()
    out = {"schema": "parlpdfech-rules-pdf-check/1", **header("check"), "development_documents": len(ids),
           "new_files": rel(new_dir),
           "a_true_export_fields_give_the_stored_file": check_a(ids, split, parliament),
           "b_rule_ids_with_empty_fields": check_b(new_dir, ids),
           "c_public_sample_documents": check_c(new_dir)}
    out["passed"] = all(out[k]["passed"] for k in out if k[:2] in ("a_", "b_", "c_"))
    out_json = Path(a.out_json) if a.out_json else CHECK_JSON
    write_json(out_json, out)
    ca, cb, cc = (out[k] for k in ("a_true_export_fields_give_the_stored_file", "b_rule_ids_with_empty_fields",
                                   "c_public_sample_documents"))
    print(json.dumps({"passed": out["passed"],
                      "a": {k: ca[k] for k in ("documents", "equal_to_the_stored_file", "keys_left_out",
                                               "documents_with_a_stored_rule_id_O1_O2_P2_R1", "passed")},
                      "b": {k: cb[k] for k in ("combinations", "rule_ids_of_the_combinations", "P2_possible",
                                               "R1_possible", "rule_ids_of_the_new_development_files", "passed")},
                      "c": {d: {k: v[k] for k in v if k != "package_paths"} for d, v in cc["documents"].items()},
                      "file": rel(out_json)}, indent=1))
    return 0 if out["passed"] else 2


def main() -> None:
    ap = argparse.ArgumentParser(description="rule files from the PDF alone (empty export fields, as the package)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--ids", help="development ids, separated by commas (default: each development document)")
    b.add_argument("--limit", type=int, help="only the first N development ids (trial)")
    b.add_argument("--out", help="output folder (default daten/gj/rules_pdf)")
    b.add_argument("--record", help="file of the build record")
    b.add_argument("--sealed-build", action="store_true", help="the documents of the one last run; counts only")
    b.add_argument("--ids-from-guard", help="with --sealed-build: validation,group7")
    b.add_argument("--access-record", help="file of the access record (default daten/gj_values/heads2/last_run_access.json)")
    for name in ("compare", "check"):
        c = sub.add_parser(name)
        c.add_argument("--new", help="folder of the new rule files (default daten/gj/rules_pdf)")
        c.add_argument("--out-json")
        if name == "compare":
            c.add_argument("--out-md")
    a = ap.parse_args()
    sealed = a.cmd == "build" and a.sealed_build
    try:
        code = {"build": cmd_build, "compare": cmd_compare, "check": cmd_check}[a.cmd](a)
    except (ms.Refused, runner.Refused, mr.NoCSCS, ExportRead, guard.GuardRefusal, ValueError) as ex:
        print(f"stopped ({type(ex).__name__})" + ("" if sealed else f": {ex}"), file=sys.stderr)
        code = 3
    except Exception as ex:  # noqa: BLE001  (sealed build: the message of an error can hold an id)
        if not sealed:
            raise
        print(f"stopped ({type(ex).__name__})", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()
