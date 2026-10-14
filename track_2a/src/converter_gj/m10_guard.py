# SPDX-License-Identifier: Apache-2.0
"""Gate GJ (status EXCEPTION), plan chapter 5.2 item 1: the split guard of the m10 converter (process rule 6).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream B,
for the AI agent. This file does not change an existing file. It reads only lists, tables and file names. It
never reads a test document, and it never uses the fallbacks of src/m03_iso_paths.py (iso_path, pdf_path).

1 Rules (a document is allowed only if no rule refuses it)
  G1  The item is not a doc id (digits only).
  G2  The doc id is not in the export table daten/analyse/dokumente/dokumente_merkmale.csv.gz, or the table
      gives it more than one parliament.
  G3  The parliament (body key) is not in daten/analyse/synthese/split.csv, or not in the path-2 split
      daten/cls/splits.json (key parliaments). This refuses unknown body keys and the R9 parliaments.
  G4  split.csv and the path-2 split disagree for the parliament (Training -> dev or excluded_group7,
      Validierung -> validation or excluded_group7, Gold -> final).
  G5  The parliament is a test parliament (split.csv role Gold, path-2 split final).
  G6  The doc id is a protected test id: the doc_id column of daten/gold/test.csv, daten/gold/bulk_test.csv and
      of each CSV file under daten/gold/final_v4, and the file names of daten/gold/test/atome. The guard never
      prints these ids. EXEMPT_LISTS are 2 scratch lists of final_v4 that hold dev, validation and group-7
      documents (a copy of the triage table and the runner smoke selection). A list is exempt only if it holds
      0 ids of a test parliament; else all of its ids are protected. Note: m05_cls_data.protected_doc_ids()
      reads these 2 lists too, so it refuses 328 non-test documents of daten/iso/docling (12.10.2026).
  G7  A file of the document is in a test folder (TEST_PROBES; existence probe only, the file is not read).
  G8  The document is an R8 copy (daten/analyse/synthese/split_ausschluss_duplikate.csv: copies that split v2
      removed from the validation and the test set).
  G9  The split of the document is not in the splits that the caller allows. Default: dev, validation,
      group7. Training lists must use --allowed dev.
  Group 7 (never training data): ZH, AG, GR, LU, VD, JU, 5192, 6621. The guard stops if this constant, the
  group-7 rows of daten/iso/gruppen.csv and the key excluded_group7 of daten/cls/splits.json are not equal.
  Split names of the guard: dev, validation, group7, test, unknown.

2 Paths
  iso_file(kind, doc_id): the explicit path daten/iso/<kind>/<doc_id>.<ext>. No fallback. A missing file stops.
  check_path(path, doc_id): refuses a path in a test folder (REFUSED_PARTS) and a path in
  daten/pdf/lehrer_stichprobe (it holds PDFs of test parliaments) unless the file name is the doc id that
  the guard allowed.
  check_pdf(doc_id, pdf): SHA-256 of the PDF against the stored Docling output and the list values.

3 Command line (exit code 0: no refusal; 1: one or more refusals; 2: usage error)
  uv run --offline --frozen --no-sync python src/m10_guard.py check [--allowed dev,validation,group7]
      [--record FILE] ITEM ...
      ITEM: a doc id; a .csv file (column doc_id or id); a .jsonl file (key doc_id); a .json file (a list, an
      object with doc_id, or an object of id lists such as daten/gj/sets.json); a .txt file (one id per line);
      a folder (items.jsonl of a job folder, else the names of the *.json files).
  uv run --offline --frozen --no-sync python src/m10_guard.py selftest
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "m10-guard-1"
ROOT = Path(__file__).resolve().parents[1]
SPLIT_CSV = ROOT / "daten/analyse/synthese/split.csv"
PATH2_JSON = ROOT / "daten/cls/splits.json"
GROUPS_CSV = ROOT / "daten/iso/gruppen.csv"
R8_CSV = ROOT / "daten/analyse/synthese/split_ausschluss_duplikate.csv"
DOCS_CSV = ROOT / "daten/analyse/dokumente/dokumente_merkmale.csv.gz"
ISO = ROOT / "daten/iso"
ISO_EXT = {"docling": "json", "atome": "json", "atome_prompt": "txt"}
PROTECTED_LISTS = (ROOT / "daten/gold/test.csv", ROOT / "daten/gold/bulk_test.csv")
FINAL_V4 = ROOT / "daten/gold/final_v4"
TEST_ATOMS = ROOT / "daten/gold/test/atome"
EXEMPT_LISTS = ("daten/gold/final_v4/scratch/triage.before_v4.csv", "daten/gold/final_v4/scratch/runner_smoke/")
GROUP7 = frozenset({"ZH", "AG", "GR", "LU", "VD", "JU", "5192", "6621"})
FINAL_GROUP = "7"
SPLIT_NAME = {"dev": "dev", "validation": "validation", "excluded_group7": "group7", "final": "test"}
ROLE_TO_PATH2 = {"Training": {"dev", "excluded_group7"}, "Validierung": {"validation", "excluded_group7"},
                 "Gold": {"final"}}
DEFAULT_ALLOWED = ("dev", "validation", "group7")
SPLITS = ("dev", "validation", "group7", "test", "unknown")
# existence probes of G7 (folder, file extension); the guard never opens these files
TEST_PROBES = (("daten/gold/test/pdf", "pdf"), ("daten/gold/test/docling", "json"), ("daten/gold/test/atome", "json"),
               ("daten/gold/test/atome_prompt", "txt"), ("daten/pdf/test_dokumente", "pdf"),
               ("daten/pdf/blind_final", "pdf"))
# folders and file name parts that a path of the m10 code must not touch
REFUSED_PARTS = ("daten/gold/test/", "daten/pdf/test_dokumente/", "daten/pdf/blind_final", "daten/cls/final_prep/",
                 "daten/cls/final/", "daten/gold/final_v4/", "daten/score26/", "daten/iso/v4/final_",
                 "daten/iso/v4/hyp_g7_final", "daten/iso/v4/report_g7_final")
TEACHER_PDF = "daten/pdf/lehrer_stichprobe/"


class GuardRefusal(Exception):
    """A document or a path was refused."""


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return p.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def _read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- tables

@dataclass
class Tables:
    roles: dict[str, str]                    # body_key -> split.csv role
    path2: dict[str, str]                    # body_key -> dev | validation | final | excluded_group7
    group7: frozenset[str]
    r8: frozenset[str]
    protected: frozenset[str]
    bodies: dict[str, set[str]] = field(default_factory=dict)   # doc_id -> body keys (filled on demand)
    sources: dict[str, str] = field(default_factory=dict)       # input file -> SHA-256
    exempt: dict[str, int] = field(default_factory=dict)        # exempt list -> number of ids
    from_disk: bool = True

    def doc_bodies(self, ids) -> dict[str, set[str]]:
        want = {str(i) for i in ids} - set(self.bodies)
        if want and self.from_disk:
            for d in want:
                self.bodies[d] = set()
            with gzip.open(DOCS_CSV, "rt", newline="", encoding="utf-8") as f:
                for z in csv.DictReader(f):
                    if z["id"] in want:
                        self.bodies[z["id"]].add(z["body_key"])
        return {str(i): self.bodies.get(str(i), set()) for i in ids}


def _protected_ids(roles: dict[str, str]) -> tuple[frozenset[str], dict[str, str], dict[str, int]]:
    """(protected ids, list file -> SHA-256, exempt list -> number of ids). Only doc_id columns and file names."""
    test_parl = {b for b, r in roles.items() if r == "Gold"}
    ids: set[str] = set()
    sources: dict[str, str] = {}
    exempt: dict[str, int] = {}
    lists = list(PROTECTED_LISTS) + sorted(FINAL_V4.rglob("*.csv"))
    exempt_rows: dict[str, set[str]] = {}
    for p in lists:
        r = rel(p)
        got = {str(x["doc_id"]).strip() for x in _read_csv(p) if (x.get("doc_id") or "").strip()}
        sources[r] = sha256_file(p)
        if any(r == e or (e.endswith("/") and r.startswith(e)) for e in EXEMPT_LISTS):
            exempt_rows[r] = got
        else:
            ids |= got
    if exempt_rows:
        # an exempt list keeps its exemption only if it holds no id of a test parliament
        want = set().union(*exempt_rows.values())
        bodies: dict[str, set[str]] = {d: set() for d in want}
        with gzip.open(DOCS_CSV, "rt", newline="", encoding="utf-8") as f:
            for z in csv.DictReader(f):
                if z["id"] in want:
                    bodies[z["id"]].add(z["body_key"])
        for r, got in exempt_rows.items():
            if any(not bodies[d] or bodies[d] & test_parl for d in got):
                ids |= got
            else:
                exempt[r] = len(got)
    ids |= {p.stem for p in TEST_ATOMS.glob("*.json")}
    sources[rel(TEST_ATOMS) + "/*.json (file names)"] = hashlib.sha256(
        "\n".join(sorted(p.name for p in TEST_ATOMS.glob("*.json"))).encode()).hexdigest()
    return frozenset(ids), sources, exempt


def load_tables() -> Tables:
    roles = {r["body_key"]: r["rolle"] for r in _read_csv(SPLIT_CSV)}
    bad_roles = sorted(set(roles.values()) - set(ROLE_TO_PATH2))
    if bad_roles:
        raise GuardRefusal(f"split.csv has unknown roles: {bad_roles}")
    sp = json.loads(PATH2_JSON.read_text(encoding="utf-8"))["parliaments"]
    path2: dict[str, str] = {}
    for s, keys in sp.items():
        if s not in SPLIT_NAME:
            raise GuardRefusal(f"daten/cls/splits.json: unknown split {s}")
        for b in keys:
            if b in path2:
                raise GuardRefusal(f"daten/cls/splits.json: parliament {b} in two splits")
            path2[b] = s
    g7_groups = {r["body_key"] for r in _read_csv(GROUPS_CSV) if r["group"] == FINAL_GROUP}
    g7_path2 = {b for b, s in path2.items() if s == "excluded_group7"}
    if not (GROUP7 == g7_groups == g7_path2):
        raise GuardRefusal("the group-7 parliaments of the guard, of daten/iso/gruppen.csv and of daten/cls/splits.json "
                           "are not equal")
    r8 = frozenset(r["doc_id"] for r in _read_csv(R8_CSV))
    protected, psources, exempt = _protected_ids(roles)
    sources = {rel(p): sha256_file(p) for p in (SPLIT_CSV, PATH2_JSON, GROUPS_CSV, R8_CSV, DOCS_CSV)}
    sources.update(psources)
    return Tables(roles, path2, frozenset(GROUP7), r8, protected, {}, sources, exempt)


_TABLES: Tables | None = None


def tables() -> Tables:
    global _TABLES
    if _TABLES is None:
        _TABLES = load_tables()
    return _TABLES


# ---------------------------------------------------------------- checks

def test_files(doc_id: str) -> list[str]:
    """G7: files of the doc id in a test folder (existence probe only)."""
    return [f"{d}/{doc_id}.{e}" for d, e in TEST_PROBES if (ROOT / d / f"{doc_id}.{e}").exists()]


def check(ids, allowed=DEFAULT_ALLOWED, tab: Tables | None = None, probe_files: bool = True) -> list[dict]:
    """One verdict for each item: {doc_id, parliament, split, refused: [reasons]}. An empty list = allowed."""
    tab = tab or tables()
    bad_allowed = set(allowed) - set(DEFAULT_ALLOWED)
    if bad_allowed:
        raise GuardRefusal(f"allowed splits must be in {DEFAULT_ALLOWED}: {sorted(bad_allowed)}")
    items = [str(i).strip() for i in ids]
    bodies = tab.doc_bodies([i for i in items if i.isdigit()])
    out = []
    for d in items:
        v = {"doc_id": d, "parliament": None, "split": "unknown", "refused": []}
        out.append(v)
        if not d.isdigit():
            v["refused"].append("G1 not a doc id")
            continue
        bs = bodies.get(d) or set()
        if not bs:
            v["refused"].append("G2 doc id not in the export table")
        elif len(bs) > 1:
            v["refused"].append("G2 doc id with more than one parliament")
        else:
            b = next(iter(bs))
            v["parliament"] = b
            role, p2 = tab.roles.get(b), tab.path2.get(b)
            if role is None or p2 is None:
                v["refused"].append("G3 unknown parliament (not in split.csv or not in the path-2 split)")
            elif p2 not in ROLE_TO_PATH2[role] or ((b in tab.group7) != (p2 == "excluded_group7")):
                v["refused"].append("G4 split.csv and the path-2 split disagree")
            else:
                v["split"] = SPLIT_NAME[p2]
            if role == "Gold" or p2 == "final":
                v["split"] = "test"
                v["refused"].append("G5 test parliament")
        if d in tab.protected:
            v["refused"].append("G6 protected test id")
        if probe_files and test_files(d):
            v["refused"].append("G7 file in a test folder")
        if d in tab.r8:
            v["refused"].append("G8 R8 copy")
        if not v["refused"] and v["split"] not in allowed:
            v["refused"].append(f"G9 split {v['split']} not allowed")
    return out


def summary(verdicts: list[dict], allowed) -> dict:
    by_split = {s: 0 for s in SPLITS}
    reasons: dict[str, int] = {}
    for v in verdicts:
        by_split[v["split"]] += 1
        for r in v["refused"]:
            k = r.split(" ", 1)[0]
            reasons[k] = reasons.get(k, 0) + 1
    refused = [v for v in verdicts if v["refused"]]
    return {"items": len(verdicts), "distinct": len({v["doc_id"] for v in verdicts}), "allowed_splits": list(allowed),
            "by_split": by_split, "refused": len(refused), "test_documents": by_split["test"],
            "refusal_rules": dict(sorted(reasons.items()))}


def assert_allowed(ids, allowed=DEFAULT_ALLOWED, tab: Tables | None = None) -> dict:
    """Raise GuardRefusal if one item is refused. Returns the summary and the split of each doc id."""
    ver = check(ids, allowed, tab)
    s = summary(ver, allowed)
    if s["refused"]:
        first = [f"{v['doc_id']}: {'; '.join(v['refused'])}" for v in ver if v["refused"]][:10]
        raise GuardRefusal(f"guard: {s['refused']} of {s['items']} items refused ({s['refusal_rules']}): "
                           + " | ".join(first))
    s["split_of"] = {v["doc_id"]: v["split"] for v in ver}
    s["parliament_of"] = {v["doc_id"]: v["parliament"] for v in ver}
    return s


def check_path(p: Path, doc_id: str | None = None) -> Path:
    """Refuse a path in a test folder. A path in daten/pdf/lehrer_stichprobe passes only with its allowed doc id."""
    r = rel(p)
    if any(x in r + "/" if x.endswith("/") else x in r for x in REFUSED_PARTS) or \
            "h7k" in r and "26" in Path(r).name:
        raise GuardRefusal(f"guard: path {r} refused (test or final material, process rule 6)")
    if r.startswith(TEACHER_PDF):
        if doc_id is None or Path(r).name != f"{doc_id}.pdf":
            raise GuardRefusal(f"guard: path {r} refused (teacher sample folder holds test PDFs; name the allowed doc id)")
        assert_allowed([doc_id])
    return Path(p)


def iso_file(kind: str, doc_id: str) -> Path:
    """Explicit path daten/iso/<kind>/<doc_id>.<ext>; no fallback to a test folder."""
    p = ISO / kind / f"{doc_id}.{ISO_EXT[kind]}"
    if not p.is_file():
        raise GuardRefusal(f"guard: {rel(p)} does not exist (no fallback)")
    return p


def list_sha256() -> dict[str, dict[str, str]]:
    """doc_id -> {list file: sha256} of the non-test lists with a sha256 column (gruppen.csv, pool.csv,
    extension.csv). These are list values, not a read of the PDF."""
    out: dict[str, dict[str, str]] = {}
    for p in (GROUPS_CSV, ISO / "pool.csv", ROOT / "daten/gold/extension.csv"):
        for r in _read_csv(p):
            if r.get("sha256"):
                out.setdefault(r["doc_id"], {})[rel(p)] = r["sha256"]
    return out


def check_pdf(doc_id: str, pdf: Path, lists: dict | None = None) -> dict:
    """G-PDF: the SHA-256 of the PDF must equal the stored Docling value (and the list values, if any)."""
    assert_allowed([doc_id])
    check_path(pdf, doc_id)
    h = sha256_file(pdf)
    stored = None
    dp = ISO / "docling" / f"{doc_id}.json"
    if dp.is_file():
        stored = json.loads(dp.read_text(encoding="utf-8")).get("sha256")
    lv = (lists if lists is not None else list_sha256()).get(doc_id, {})
    ok = (stored is None or stored == h) and all(v == h for v in lv.values())
    return {"doc_id": doc_id, "pdf": rel(pdf), "sha256": h, "docling_sha256": stored, "list_sha256": lv, "equal": ok}


# ---------------------------------------------------------------- items of the command line

def read_items(arg: str) -> list[str]:
    p = Path(arg)
    if p.is_dir():
        if (p / "items.jsonl").is_file():
            with open(p / "items.jsonl", encoding="utf-8") as f:
                return [str(json.loads(x)["doc_id"]) for x in f if x.strip()]
        return sorted(q.stem for q in p.glob("*.json"))
    if p.is_file():
        if p.suffix == ".csv":
            rows = _read_csv(p)
            if rows and "doc_id" not in rows[0] and "id" not in rows[0]:
                raise ValueError(f"{arg}: no column doc_id or id")
            return [str(r.get("doc_id") or r.get("id") or "") for r in rows]
        if p.suffix == ".jsonl":
            with open(p, encoding="utf-8") as f:
                return [str(json.loads(x).get("doc_id", "")) for x in f if x.strip()]
        if p.suffix == ".json":
            x = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(x, list):
                return [str(i) for i in x]
            if isinstance(x, dict) and "doc_id" in x:
                return [str(x["doc_id"])]
            if isinstance(x, dict):
                out = []
                for v in x.values():
                    if isinstance(v, list) and all(isinstance(i, (str, int)) for i in v):
                        out += [str(i) for i in v]
                return out
            raise ValueError(f"{arg}: no doc ids found")
        if p.suffix == ".txt":
            return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        raise ValueError(f"{arg}: unknown file type")
    if "/" in arg or "." in arg:
        raise ValueError(f"{arg}: file or folder does not exist")
    return [arg]


def cmd_check(args) -> int:
    allowed = tuple(x for x in args.allowed.split(",") if x)
    try:
        items = [i for a in args.items for i in read_items(a)]
    except ValueError as e:
        print(f"usage error: {e}", file=sys.stderr)
        return 2
    if not items:
        print("usage error: no items", file=sys.stderr)
        return 2
    try:
        ver = check(items, allowed)
    except GuardRefusal as e:
        print(str(e), file=sys.stderr)
        return 2
    s = summary(ver, allowed)
    for v in ver:
        if v["refused"]:
            print(f"REFUSED {v['doc_id']}: {'; '.join(v['refused'])}")
    print(json.dumps(s, ensure_ascii=False))
    if args.record:
        tab = tables()
        rec = {"version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "script": {"path": rel(Path(__file__)), "sha256": sha256_file(Path(__file__))},
               "inputs": {a: (sha256_file(Path(a)) if Path(a).is_file() else None) for a in args.items
                          if Path(a).exists()},
               "tables": tab.sources, "exempt_lists": tab.exempt, "summary": s,
               "refused": [v for v in ver if v["refused"]]}
        Path(args.record).parent.mkdir(parents=True, exist_ok=True)
        Path(args.record).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 1 if s["refused"] else 0


def selftest() -> dict:
    """Probes on the real tables. No probe opens a test document; the output holds no test doc id."""
    tab = tables()
    out: dict[str, str] = {}

    def probe(name, ids, allowed=DEFAULT_ALLOWED, want_refused=True, rule=None):
        v = check(ids, allowed, tab)[0]
        hit = bool(v["refused"]) and (rule is None or any(r.startswith(rule) for r in v["refused"]))
        ok = hit if want_refused else not v["refused"]
        out[name] = "as expected" if ok else "NOT AS EXPECTED"

    probe("not_a_doc_id", ["abc"], rule="G1")
    probe("unknown_doc_id", ["0"], rule="G2")
    g7 = [r["doc_id"] for r in _read_csv(GROUPS_CSV) if r["group"] == FINAL_GROUP]
    probe("group7_document_training", g7[:1], ("dev",), rule="G9")
    probe("group7_document_report", g7[:1], DEFAULT_ALLOWED, want_refused=False)
    test_parl = {b for b, r in tab.roles.items() if r == "Gold"}
    first_test = None
    with gzip.open(DOCS_CSV, "rt", newline="", encoding="utf-8") as f:
        for z in csv.DictReader(f):
            if z["body_key"] in test_parl:
                first_test = z["id"]
                break
    probe("test_parliament_document", [first_test], rule="G5")
    r8v = [r["doc_id"] for r in _read_csv(R8_CSV) if r["rolle"] == "Validierung"]
    probe("r8_copy", r8v[:1], rule="G8")
    t = [r["doc_id"] for r in _read_csv(PROTECTED_LISTS[0])]
    probe("protected_test_id", t[:1], rule="G6")
    pool_dev = [r["doc_id"] for r in _read_csv(ISO / "pool.csv")
                if tab.path2.get(r["body_key"]) == "dev" and r["doc_id"] not in tab.protected]
    probe("dev_document", pool_dev[:1], ("dev",), want_refused=False)
    for name, p in (("test_folder", ROOT / "daten/gold/test/pdf/probe.pdf"),
                    ("final_reference", ROOT / "daten/iso/v4/final_ref41/probe.json"),
                    ("score26", ROOT / "daten/score26/probe.json"),
                    ("teacher_pdf_without_id", ROOT / "daten/pdf/lehrer_stichprobe/probe.pdf")):
        try:
            check_path(p)
            out[name] = "NOT AS EXPECTED"
        except GuardRefusal:
            out[name] = "as expected"
    try:
        iso_file("atome", "0")
        out["iso_file_no_fallback"] = "NOT AS EXPECTED"
    except GuardRefusal:
        out["iso_file_no_fallback"] = "as expected"
    out["exempt_lists"] = json.dumps(tab.exempt)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--allowed", default=",".join(DEFAULT_ALLOWED))
    c.add_argument("--record", default=None)
    c.add_argument("items", nargs="+")
    sub.add_parser("selftest")
    args = ap.parse_args()
    if args.cmd == "check":
        return cmd_check(args)
    res = selftest()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if all(v != "NOT AS EXPECTED" for v in res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
