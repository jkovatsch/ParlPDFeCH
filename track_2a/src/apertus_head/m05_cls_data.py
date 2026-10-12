# SPDX-License-Identifier: Apache-2.0
"""Path 2 (E34), step Data: datasets for the classifications R1 and R2 of a whole document.

R1  The formal recommendation of the executive on a motion or a postulate. I95 output:
    ProcedureState.decision = recommended_for or recommended_against at the stage executive_response
    (I95 ProcedureDecisionEnum; finer value ResponseStep.recommendation from RecommendationEnum).
    Label: one recommendation event of the source system (OpenParlData events.title_harmonized_id):
    29 = recommended_against; 30, 31, 32 = recommended_for; 33 (transfer as postulate) has no I95
    decision value and is left out. An affair with more than one distinct event id is left out
    (same filter as daten/opd_research/report/scripts/fixes.py, part C: 878 affairs in S).
    One response document for each affair (rule RESPONSE_DOC_RULE below).
R2  The document holds an executive response (yes or no). Silver label from the local category
    (rule rolle() of src/m02_dokumente_profil.py, called as in fixes.py part D):
    antwort_exekutive = yes, vorstoss_eingereicht = no. Other roles are not in R2.

Population of both tasks: PDF documents with affair_id and at least 200 characters that are not
spaces in docs.text of the export (the term "PDF text" of the connection-point report).

Splits by parliament (daten/analyse/synthese/split.csv): dev = Training, validation = Validierung,
final = Gold (test parliaments). The 8 parliaments of group 7 (m03_iso_v4.final_parliaments()) are
left out completely. Documents of daten/gold/test.csv, bulk_test.csv, daten/gold/final_v4 and
daten/gold/test/ never go into dev or validation. For final, the script keeps COUNTS ONLY: no text,
no title, no label for each document is written or printed (process rule 6).

Text of a document: the Docling atom text (daten/iso/atome/<doc_id>.json, status success) if it
exists, else docs.text of the export. The text cache daten/cls/text/<doc_id>.txt holds exactly the
model input text of the document (only dev and validation). No export field (category, name, URL,
date) goes into the text.

Outputs (daten/cls/): r1_dataset.csv, r2_dataset.csv, splits.json, data_stats.json, text/.
No network request, no model run. The tokenizer (tokenizer.json of the local bf16 model) counts
the tokens.

Usage:  uv run python src/m05_cls_data.py build
        uv run python src/m05_cls_data.py check        (assertions on the written files)
        uv run python src/m05_cls_data.py audit        (dev checks: daten/cls/audit_dev.json)

Reusable functions for later steps: rows(task), text(doc_id), model_lock(purpose), assert_allowed().
"""

from __future__ import annotations

import collections
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import re
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

EXPORTS = ROOT / "daten/roh/exports"
SPLIT_CSV = ROOT / "daten/analyse/synthese/split.csv"
ATOMS = ROOT / "daten/iso/atome"
OUT = ROOT / "daten/cls"
TEXT_DIR = OUT / "text"
LOCK = OUT / "model.lock"
MODEL_DIR = ROOT / "daten/modelle/apertus-v1.5-8b-text-bf16"
VERSION = "cls-data-3"
SEED = "cls-data-1"
DESIGN_N = 150                       # target size of the dev design sample for each task
MIN_NONSPACE = 200                   # "PDF text": at least 200 characters that are not spaces
RESP_CATEGORY_MIN = 10               # response category for motions and postulates from this number of documents
LONG_TOKENS = (8192, 32768)          # length classes (E18: 8,192 = training limit on the Mac)

R1_TYPES = {2: "motion", 3: "postulate"}
REC_EVENTS = (29, 30, 31, 32, 33)
I95_DECISION = {29: "recommended_against", 30: "recommended_for", 31: "recommended_for", 32: "recommended_for"}
# finer I95 RecommendationEnum value of the admin event table (match: 29, 30 exact; 32 near; 31 further)
I95_RECOMMENDATION = {29: "reject", 30: "accept", 31: "already_done", 32: "accept"}
R2_LABEL = {"antwort_exekutive": "yes", "vorstoss_eingereicht": "no"}

RESPONSE_DOC_RULE = """\
Candidates: PDF documents of the affair with PDF text. Role of each candidate from rolle().
Tier 1: role antwort_exekutive. Tier 2: role exekutivbeschluss. Tier 3: no category (ohne_kategorie).
Tier 4: another category (role andere), only in a parliament without a response category for
motions and postulates (fewer than RESP_CATEGORY_MIN PDF documents with PDF text and the role
antwort_exekutive on affairs of type 2 or 3). A document with the role
vorstoss_eingereicht is never the response document. Take the first tier that has a candidate.
In the tier, take the document nearest to a recommendation event by docs.date (rule G11: the date
only links a document to an event): first the documents with a date at most 7 days after the event
(or before it), then the other dated documents, then documents without a date; in each class the
smallest absolute difference in days, then the smallest doc_id. An affair without a candidate is
left out (reason no_response_document)."""

NOWS = re.compile(r"\s")
WORD = re.compile(r"[a-zàâäéèêëïîôöùûüçœ]+")
STOP = {
    "de": set("der die das und ist nicht zu den mit von für auf des dem im eine ein sich wird werden auch als "
              "bei oder nach über wie durch sind wurde kann".split()),
    "fr": set("le la les et des du est une un pour dans que qui au aux pas par sur ne ce il sont avec plus "
              "cette être été".split()),
    "it": set("il lo che di per del della delle una non sono con gli nel alla dei al anche come questo "
              "essere stato".split()),
    "rm": set("ils las dals betg ina cun quai vegn vegnan nus vus sias ses dentant tenor".split()),
    "en": set("the and of to is that for with on are this be by as from".split()),
}


# ---------------------------------------------------------------- protected sets and splits

def _read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group7_parliaments() -> set[str]:
    import m03_iso_v4 as v4
    return set(v4.final_parliaments())


def protected_doc_ids() -> set[str]:
    """Doc ids of the test lists and of the final_v4 lists, and the atom files of test documents."""
    ids: set[str] = set()
    files = [ROOT / "daten/gold/test.csv", ROOT / "daten/gold/bulk_test.csv"]
    files += sorted((ROOT / "daten/gold/final_v4").rglob("*.csv"))
    for p in files:
        for r in _read_csv(p):
            if r.get("doc_id"):
                ids.add(str(r["doc_id"]).strip())
    ids |= {p.stem for p in (ROOT / "daten/gold/test/atome").glob("*.json")}
    return ids


def body_splits() -> dict[str, str]:
    """body_key -> dev, validation, final or excluded_group7."""
    g7 = group7_parliaments()
    m = {"Training": "dev", "Validierung": "validation", "Gold": "final"}
    out = {}
    for r in _read_csv(SPLIT_CSV):
        out[r["body_key"]] = "excluded_group7" if r["body_key"] in g7 else m[r["rolle"]]
    assert sum(v == "dev" for v in out.values()) == 48 and sum(v == "validation" for v in out.values()) == 18
    assert sum(v == "final" for v in out.values()) == 15 and not (g7 & {b for b, v in out.items() if v == "final"})
    return out


def assert_allowed(doc_ids, splits_allowed=("dev",)) -> None:
    """Raise if a document is not in the allowed splits of the written datasets (use before a model run)."""
    allowed = {}
    for task in ("r1", "r2"):
        for r in rows(task):
            allowed[r["doc_id"]] = r["split"]
    prot = protected_doc_ids()
    for d in doc_ids:
        d = str(d)
        if d in prot:
            raise ValueError(f"{d}: document of a test list: refused")
        if allowed.get(d) not in splits_allowed:
            raise ValueError(f"{d}: split {allowed.get(d)} is not in {splits_allowed}: refused")


# ---------------------------------------------------------------- helpers

def nonspace(t: str) -> int:
    return len(NOWS.sub("", t or ""))


def dparse(s) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def language(text: str) -> str:
    """de, fr, it, rm, en or unk: the most frequent stop-word set in the first 20,000 characters
    (at least 3 hits and more than 1.5 times the hits of the second set, else unk)."""
    words = WORD.findall((text or "")[:20000].lower())
    n = {k: sum(1 for w in words if w in s) for k, s in STOP.items()}
    first, second = sorted(n.values(), reverse=True)[:2]
    best = max(n, key=n.get)
    return best if first >= 3 and first > 1.5 * second else "unk"


def doc_role(d: dict) -> tuple[str, str]:
    """Role of a document from its local category: rolle() of m02_dokumente_profil, as in fixes.py part D."""
    from m02_dokumente_extrakt import kategorie
    from m02_dokumente_profil import rolle
    cats = [kategorie(d.get(k))[0] for k in ("category_de", "category_fr", "category_it")]
    return rolle(d.get("category_harmonized") or "", *cats, [], [])


def is_pdf(d: dict) -> bool:
    from m02_dokumente_profil import ist_pdf
    return ist_pdf(d.get("format") or "", (d.get("url") or "").rsplit(".", 1)[-1].lower())


def atom_text(doc_id: str) -> str | None:
    """Plain text of the Docling atoms: atoms in reading order; a new line in a block = newline,
    a new block = empty line, parts of one line = space. None if no atoms or not status success."""
    p = ATOMS / f"{doc_id}.json"
    if not p.exists():
        return None
    x = json.loads(p.read_text(encoding="utf-8"))
    if x.get("status") != "success":
        return None
    out, prev = [], None
    for a in x["atome"]:
        t = (a.get("text") or "").strip()
        if not t:
            continue
        if prev is not None:
            out.append(" " if (a["block"], a["zeile"]) == prev else "\n" if a["block"] == prev[0] else "\n\n")
        out.append(t)
        prev = (a["block"], a["zeile"])
    return "".join(out)


def rank_key(task: str, doc_id: str) -> str:
    return hashlib.sha256(f"{SEED}|{task}|{doc_id}".encode()).hexdigest()


def md5(t: str) -> str:
    return hashlib.md5(re.sub(r"\s+", " ", t).strip().encode()).hexdigest()


def length_class(n: int) -> str:
    if n <= LONG_TOKENS[0]:
        return f"le{LONG_TOKENS[0]}"
    if n <= LONG_TOKENS[1]:
        return f"le{LONG_TOKENS[1]}"
    return f"gt{LONG_TOKENS[1]}"


def tokenizer():
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))


# ---------------------------------------------------------------- R1 response document

def select_response_doc(cands: list[dict], event_dates: list[dt.date], resp_category: bool):
    """(document, tier, signed day difference to the nearest event or None) or (None, None, None)."""
    tiers = (
        (1, lambda c: c["role"] == "antwort_exekutive"),
        (2, lambda c: c["role"] == "exekutivbeschluss"),
        (3, lambda c: c["role"] == "ohne_kategorie"),
        (4, lambda c: c["role"] == "andere" and not resp_category),
    )

    def diff(c):
        if c["date"] is None or not event_dates:
            return None
        return min(((c["date"] - e).days for e in event_dates), key=abs)

    def key(c):
        x = diff(c)
        cls = 2 if x is None else (0 if x <= 7 else 1)
        return (cls, abs(x) if x is not None else 0, int(c["doc_id"]) if c["doc_id"].isdigit() else 0, c["doc_id"])

    for tier, ok in tiers:
        pool = [c for c in cands if ok(c)]
        if pool:
            best = min(pool, key=key)
            return best, tier, diff(best)
    return None, None, None


# ---------------------------------------------------------------- design sample

def allocate(sizes: dict, total: int, cap_frac: float = 0.5) -> dict:
    """Design sample size for each stratum: proportional to sqrt(size), at least 1, at most
    ceil(cap_frac * size) (so that the check set keeps about half of each small stratum)."""
    cap = {s: (math.ceil(cap_frac * n) if n > 1 else 0) for s, n in sizes.items()}
    total = min(total, sum(cap.values()))
    fixed: dict = {}
    open_ = {s for s in sizes if cap[s] > 0}
    q: dict = {}
    while open_:
        rem = total - sum(fixed.values())
        z = sum(math.sqrt(sizes[s]) for s in open_)
        q = {s: rem * math.sqrt(sizes[s]) / z for s in open_}
        over = {s for s in open_ if q[s] >= cap[s]}
        if not over:
            break
        for s in over:
            fixed[s] = cap[s]
        open_ -= over
    alloc = {s: 0 for s in sizes}
    alloc.update(fixed)
    base = {s: max(1, math.floor(q[s])) for s in open_}
    diff = total - sum(fixed.values()) - sum(base.values())
    if diff < 0:       # more strata than places: the strata with the smallest quota give a place back
        for s in sorted(open_, key=lambda s: (q[s], str(s))):
            if diff == 0:
                break
            if base[s] > 0:
                base[s] -= 1
                diff += 1
    else:              # largest remainder
        for s in sorted(open_, key=lambda s: (-(q[s] - math.floor(q[s])), str(s))):
            if diff == 0:
                break
            if base[s] < cap[s]:
                base[s] += 1
                diff -= 1
    alloc.update(base)
    return alloc


def design_split(rows_: list[dict], task: str) -> None:
    """Set subset = design or check for dev rows (stratum = parliament, label, language).
    Rows with a text duplicate of an earlier row get subset duplicate."""
    dev = [r for r in rows_ if r["split"] == "dev" and r["subset"] != "duplicate"]
    strata = collections.defaultdict(list)
    for r in dev:
        strata[(r["body_key"], r["label"], r["language"])].append(r)
    alloc = allocate({s: len(v) for s, v in strata.items()}, DESIGN_N)
    for s, v in strata.items():
        v.sort(key=lambda r: r["rank"])
        for i, r in enumerate(v):
            r["subset"] = "design" if i < alloc[s] else "check"


# ---------------------------------------------------------------- build

FIELDS_R1 = ["doc_id", "affair_id", "body_key", "split", "subset", "language", "label", "label_source",
             "label_evidence", "recommendation_fine", "affair_type", "selection_tier", "date_diff_days",
             "n_candidates", "doc_role", "text_source", "text_path", "export_ref", "n_chars", "n_tokens",
             "length_class", "text_md5", "rank"]
FIELDS_R2 = ["doc_id", "affair_id", "body_key", "split", "subset", "language", "label", "label_source",
             "label_evidence", "doc_role", "affair_type", "in_r1", "text_source", "text_path", "export_ref",
             "n_chars", "n_tokens", "length_class", "text_md5", "rank"]


def build() -> None:
    t_all = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    split = body_splits()
    prot = protected_doc_ids()
    keep_bodies = {b for b, s in split.items() if s in ("dev", "validation", "final")}
    stats: dict = {"version": VERSION, "run_start": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                   "export": (EXPORTS / "abgerufen_utc.txt").read_text().strip(),
                   "protected_doc_ids": len(prot)}

    # affairs and recommendation events
    aff = {}
    for line in gzip.open(EXPORTS / "affairs.ndjson.gz", "rt", encoding="utf-8"):
        d = json.loads(line)
        if d["body_key"] in keep_bodies:
            aff[d["id"]] = (d["body_key"], d.get("type_harmonized_id"))
    rec = collections.defaultdict(list)
    for line in gzip.open(EXPORTS / "events.ndjson.gz", "rt", encoding="utf-8"):
        d = json.loads(line)
        a = d.get("affair_id")
        if a in aff and aff[a][1] in R1_TYPES and d.get("title_harmonized_id") in REC_EVENTS:
            rec[a].append((d["title_harmonized_id"], dparse(d.get("date"))))
    r1_aff, r1_filter = {}, collections.defaultdict(collections.Counter)
    for a, ev in rec.items():
        b = aff[a][0]
        ids = {e[0] for e in ev}
        if len(ids) > 1:
            r1_filter[b]["more_than_one_event_id"] += 1
        elif 33 in ids:
            r1_filter[b]["event_33_only"] += 1
        else:
            r1_aff[a] = ev

    # documents, body by body: dev and validation first (R8 needs their text hashes before final)
    order = sorted(keep_bodies, key=lambda b: ({"dev": 0, "validation": 1, "final": 2}[split[b]], b))
    r1_rows, r2_rows = [], []
    final_counts = {"r1": collections.Counter(), "r2": collections.Counter(),
                    "r1_no_doc": collections.Counter(), "r1_in_test_lists": 0, "r2_in_test_lists": 0,
                    "r1_text_copy_of_dev_val": 0, "r2_text_copy_of_dev_val": 0}
    body_info = {}
    r2_protected = collections.Counter()   # dev and validation documents of a protected list (left out)
    seen_md5 = {}                      # text md5 of dev and validation rows -> split
    texts: dict[str, str] = {}         # doc_id -> model input text (dev and validation only)
    src_of: dict[str, tuple] = {}
    for b in order:
        t0 = time.time()
        sp = split[b]
        docs_by_aff = collections.defaultdict(list)
        n = collections.Counter()
        seen_ids = set()
        for line in gzip.open(EXPORTS / f"docs/docs_{b}.ndjson.gz", "rt", encoding="utf-8"):
            d = json.loads(line)
            assert d["body_key"] == b
            a = d.get("affair_id")
            if a not in aff or not is_pdf(d):
                continue
            did = str(d["id"])
            if did in seen_ids:
                n["repeated_doc_id_rows"] += 1
                continue
            seen_ids.add(did)
            t = d.get("text") or ""
            if nonspace(t) < MIN_NONSPACE:
                n["pdf_without_text"] += 1
                continue
            role, rsrc = doc_role(d)
            n[f"role|{role}"] += 1
            if role == "antwort_exekutive" and aff[a][1] in R1_TYPES:
                n["response_role_on_motion_postulate"] += 1
            need = a in r1_aff or role in R2_LABEL
            if not need:
                continue
            c = {"doc_id": did, "affair_id": a, "role": role, "role_source": rsrc, "date": dparse(d.get("date")),
                 "category": " | ".join(str(d.get(k)) for k in ("category_harmonized", "category_de",
                                                                     "category_fr", "category_it") if d.get(k)),
                 "export_text": t, "in_test_list": did in prot}
            docs_by_aff[a].append(c)
        resp_cat = n["response_role_on_motion_postulate"] >= RESP_CATEGORY_MIN
        body_info[b] = {"split": sp, "response_category": resp_cat,
                        "antwort_exekutive_docs": n["role|antwort_exekutive"],
                        "antwort_exekutive_docs_on_motion_postulate": n["response_role_on_motion_postulate"],
                        "repeated_doc_id_rows": n["repeated_doc_id_rows"]}

        def model_text(c) -> tuple[str, str, str]:
            """(text, text_source, text_path of the source)"""
            at = atom_text(c["doc_id"])
            if at is not None and nonspace(at) >= MIN_NONSPACE:
                return at, "docling_atoms", f"daten/iso/atome/{c['doc_id']}.json"
            return c["export_text"], "export_text", f"daten/roh/exports/docs/docs_{b}.ndjson.gz#id={c['doc_id']}"

        # ---- R1
        r1_docs_here = set()
        for a, ev in r1_aff.items():
            if aff[a][0] != b:
                continue
            cands = docs_by_aff.get(a, [])
            best, tier, diff = select_response_doc(cands, [e[1] for e in ev if e[1]], resp_cat)
            eid = ev[0][0]
            if best is None:
                if sp == "final":
                    final_counts["r1_no_doc"][b] += 1
                else:
                    r1_filter[b]["no_response_document"] += 1
                continue
            if best["doc_id"] in r1_docs_here:
                r1_filter[b]["document_already_used_for_another_affair"] += 1
                continue
            r1_docs_here.add(best["doc_id"])
            if sp == "final":
                tx, _, _ = model_text_final(best)
                final_counts["r1"][(b, language(tx))] += 1
                final_counts["r1_in_test_lists"] += best["in_test_list"]
                final_counts["r1_text_copy_of_dev_val"] += md5(tx) in seen_md5
                continue
            if best["in_test_list"]:         # a protected document is never dev or validation material
                r1_filter[b]["response_document_in_protected_list"] += 1
                continue
            tx, tsrc, tpath = model_text(best)
            texts[best["doc_id"]] = tx
            src_of[best["doc_id"]] = (tsrc, tpath)
            r1_rows.append({
                "doc_id": best["doc_id"], "affair_id": a, "body_key": b, "split": sp, "subset": "",
                "language": language(tx), "label": I95_DECISION[eid],
                "label_source": f"events.title_harmonized_id={eid}",
                "label_evidence": ";".join(sorted({f"{e[0]}@{e[1]}" for e in ev})),
                "recommendation_fine": I95_RECOMMENDATION[eid], "affair_type": R1_TYPES[aff[a][1]],
                "selection_tier": tier, "date_diff_days": "" if diff is None else diff,
                "n_candidates": len([c for c in cands if c["role"] != "vorstoss_eingereicht"]),
                "doc_role": best["role"], "text_source": tsrc, "text_path": f"daten/cls/text/{best['doc_id']}.txt",
                "export_ref": f"daten/roh/exports/docs/docs_{b}.ndjson.gz#id={best['doc_id']}",
                "n_chars": len(tx), "n_tokens": 0, "length_class": "", "text_md5": md5(tx),
                "rank": rank_key("r1", best["doc_id"])})

        # ---- R2
        r1_ids = {r["doc_id"] for r in r1_rows if r["body_key"] == b}
        for a, cands in docs_by_aff.items():
            for c in cands:
                if c["role"] not in R2_LABEL:
                    continue
                if sp == "final":
                    tx, _, _ = model_text_final(c)
                    final_counts["r2"][(b, language(tx))] += 1
                    final_counts["r2_in_test_lists"] += c["in_test_list"]
                    final_counts["r2_text_copy_of_dev_val"] += md5(tx) in seen_md5
                    continue
                if c["in_test_list"]:
                    r2_protected[b] += 1
                    continue
                if c["doc_id"] in texts:
                    tx = texts[c["doc_id"]]
                    tsrc, tpath = src_of[c["doc_id"]]
                else:
                    tx, tsrc, tpath = model_text(c)
                    texts[c["doc_id"]] = tx
                    src_of[c["doc_id"]] = (tsrc, tpath)
                r2_rows.append({
                    "doc_id": c["doc_id"], "affair_id": a, "body_key": b, "split": sp, "subset": "",
                    "language": language(tx), "label": R2_LABEL[c["role"]],
                    "label_source": f"rolle()/{c['role_source']}", "label_evidence": c["category"][:120],
                    "doc_role": c["role"], "affair_type": aff[a][1] if aff[a][1] is not None else "",
                    "in_r1": c["doc_id"] in r1_ids, "text_source": tsrc,
                    "text_path": f"daten/cls/text/{c['doc_id']}.txt",
                    "export_ref": f"daten/roh/exports/docs/docs_{b}.ndjson.gz#id={c['doc_id']}",
                    "n_chars": len(tx), "n_tokens": 0, "length_class": "", "text_md5": md5(tx),
                    "rank": rank_key("r2", c["doc_id"])})
        if sp in ("dev", "validation"):
            for r in r1_rows + r2_rows:
                if r["body_key"] == b:
                    seen_md5.setdefault(r["text_md5"], sp)
        print(f"{b} {sp}: {round(time.time() - t0, 1)} s", flush=True)

    # ---- duplicates (same normalized text): R8 and within a split
    for rows_ in (r1_rows, r2_rows):
        first = {}
        for r in sorted(rows_, key=lambda r: ({"dev": 0, "validation": 1}[r["split"]], r["rank"])):
            f = first.get(r["text_md5"])
            if f is None:
                first[r["text_md5"]] = r
            elif f["split"] != r["split"]:
                r["subset"] = "duplicate"          # R8: copy of a dev text in validation
                r["dup_reason"] = "copy_of_dev_text"
            else:
                r["subset"] = "duplicate"
                r["dup_reason"] = f"copy_of_{f['doc_id']}"

    # ---- tokens
    tok = tokenizer()
    ids = sorted(texts)
    ntok = {}
    for i in range(0, len(ids), 256):
        chunk = ids[i:i + 256]
        enc = tok.encode_batch([texts[x] for x in chunk], add_special_tokens=False)
        for x, e in zip(chunk, enc):
            ntok[x] = len(e.ids)
    for r in r1_rows + r2_rows:
        r["n_tokens"] = ntok[r["doc_id"]]
        r["length_class"] = length_class(r["n_tokens"])
        if r["split"] == "validation" and r["subset"] != "duplicate":
            r["subset"] = "validation"

    # ---- text cache
    for x in ids:
        p = TEXT_DIR / f"{x}.txt"
        if not p.exists() or p.read_text(encoding="utf-8") != texts[x]:
            p.write_text(texts[x], encoding="utf-8")

    # ---- design sample
    design_split(r1_rows, "r1")
    design_split(r2_rows, "r2")

    # ---- write
    for name, rows_, fields in (("r1_dataset.csv", r1_rows, FIELDS_R1), ("r2_dataset.csv", r2_rows, FIELDS_R2)):
        rows_.sort(key=lambda r: ({"dev": 0, "validation": 1}[r["split"]], r["body_key"], r["rank"]))
        with open(OUT / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields + ["dup_reason"], extrasaction="ignore")
            w.writeheader()
            for r in rows_:
                w.writerow({**r, "dup_reason": r.get("dup_reason", "")})

    # ---- statistics (counts only for final)
    def counts(rows_, keys):
        c = collections.Counter()
        for r in rows_:
            c["|".join(str(r[k]) for k in keys)] += 1
        return dict(sorted(c.items()))

    stats["r1"] = {
        "filter_by_body": {b: dict(v) for b, v in sorted(r1_filter.items()) if split.get(b) != "final"},
        "labelled_affairs_by_split": dict(collections.Counter(split[aff[a][0]] for a in r1_aff)),
        "by_split_subset": counts(r1_rows, ["split", "subset"]),
        "by_split_label": counts(r1_rows, ["split", "label"]),
        "by_split_language": counts(r1_rows, ["split", "language"]),
        "by_body_label": counts(r1_rows, ["split", "body_key", "label"]),
        "by_split_subset_body_label_language": counts(r1_rows, ["split", "subset", "body_key", "label", "language"]),
        "by_split_text_source": counts(r1_rows, ["split", "text_source"]),
        "by_split_tier": counts(r1_rows, ["split", "body_key", "selection_tier"]),
        "by_split_length": counts(r1_rows, ["split", "length_class"]),
        "fine_by_split": counts(r1_rows, ["split", "recommendation_fine"]),
    }
    stats["r2"] = {
        "by_split_subset": counts(r2_rows, ["split", "subset"]),
        "by_split_label": counts(r2_rows, ["split", "label"]),
        "by_split_language": counts(r2_rows, ["split", "language"]),
        "by_body_label": counts(r2_rows, ["split", "body_key", "label"]),
        "by_split_subset_label": counts(r2_rows, ["split", "subset", "label"]),
        "design_by_body_label_language": counts([r for r in r2_rows if r["subset"] == "design"],
                                                ["body_key", "label", "language"]),
        "by_split_text_source": counts(r2_rows, ["split", "text_source"]),
        "by_split_length": counts(r2_rows, ["split", "length_class"]),
        "by_split_label_source": counts(r2_rows, ["split", "label_source"]),
        "in_r1": counts(r2_rows, ["split", "in_r1"]),
    }
    for task, rows_ in (("r1", r1_rows), ("r2", r2_rows)):
        tk = collections.defaultdict(list)
        for r in rows_:
            if r["subset"] != "duplicate":
                tk[f"{r['split']}|{r['subset']}"].append(r["n_tokens"])
        stats[task]["tokens"] = {k: tok_summary(v) for k, v in sorted(tk.items())}
    stats["final_counts_only"] = {
        "r1_by_body_language": {f"{k[0]}|{k[1]}": v for k, v in sorted(final_counts["r1"].items())},
        "r2_by_body_language": {f"{k[0]}|{k[1]}": v for k, v in sorted(final_counts["r2"].items())},
        "r1_total": sum(final_counts["r1"].values()), "r2_total": sum(final_counts["r2"].values()),
        "r1_labelled_affairs_without_response_document": sum(final_counts["r1_no_doc"].values()),
        "r1_in_test_lists": final_counts["r1_in_test_lists"], "r2_in_test_lists": final_counts["r2_in_test_lists"],
        "r1_text_copy_of_dev_or_validation": final_counts["r1_text_copy_of_dev_val"],
        "r2_text_copy_of_dev_or_validation": final_counts["r2_text_copy_of_dev_val"],
    }
    stats["bodies"] = body_info
    stats["r2"]["left_out_protected_by_body"] = dict(r2_protected)
    stats["text_cache_files"] = len(ids)
    stats["seconds"] = round(time.time() - t_all)
    (OUT / "data_stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")

    sj = {
        "version": VERSION, "made": stats["run_start"], "seed": SEED, "design_n": DESIGN_N,
        "source": "daten/analyse/synthese/split.csv (rolle Training -> dev, Validierung -> validation, Gold -> final)",
        "parliaments": {s: sorted(b for b, v in split.items() if v == s)
                        for s in ("dev", "validation", "final", "excluded_group7")},
        "protected_documents": {"sources": ["daten/gold/test.csv", "daten/gold/bulk_test.csv",
                                            "daten/gold/final_v4/**/*.csv", "daten/gold/test/atome/*.json"],
                                "count": len(prot), "in_dev_or_validation": 0},
        "rules": {"response_document": RESPONSE_DOC_RULE, "response_category_min_docs": RESP_CATEGORY_MIN,
                  "min_nonspace_chars": MIN_NONSPACE,
                  "design_sample": "dev rows without text duplicates; stratum = parliament, label, language; "
                                   "size of a stratum proportional to sqrt(stratum size), at least 1, at most "
                                   "ceil(size / 2); inside a stratum the smallest rank (sha256 of seed, task, doc_id)",
                  "duplicates": "same normalized text (md5): the copy in validation of a dev text (R8) and later "
                                "copies in the same split get subset duplicate"},
        "r1": {"subsets": stats["r1"]["by_split_subset"]},
        "r2": {"subsets": stats["r2"]["by_split_subset"]},
        "final_counts_only": {"r1_total": stats["final_counts_only"]["r1_total"],
                              "r2_total": stats["final_counts_only"]["r2_total"]},
        "files": {},
    }
    for name in ("r1_dataset.csv", "r2_dataset.csv", "data_stats.json"):
        sj["files"][f"daten/cls/{name}"] = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
    sj["files"]["src/m05_cls_data.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT / "splits.json").write_text(json.dumps(sj, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"r1": stats["r1"]["by_split_subset"], "r2": stats["r2"]["by_split_subset"],
                      "final": {"r1": sj["final_counts_only"]["r1_total"], "r2": sj["final_counts_only"]["r2_total"]},
                      "seconds": stats["seconds"]}, indent=1))


def model_text_final(c: dict) -> tuple[str, str, str]:
    """Text of a document of a test parliament: export text only (the atoms of test documents are
    not read). Used only in memory for counts (language, R8 copy); never written."""
    return c["export_text"], "export_text", ""


def tok_summary(v: list[int]) -> dict:
    if not v:
        return {}
    v = sorted(v)
    q = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]  # noqa: E731
    return {"n": len(v), "sum": sum(v), "mean": round(sum(v) / len(v)), "p25": q(0.25), "p50": q(0.5),
            "p75": q(0.75), "p90": q(0.9), "p99": q(0.99), "max": v[-1],
            "gt8192": sum(x > 8192 for x in v), "gt32768": sum(x > 32768 for x in v)}


# ---------------------------------------------------------------- reading for later steps

def rows(task: str) -> list[dict]:
    """Rows of r1_dataset.csv or r2_dataset.csv (task r1 or r2)."""
    with open(OUT / f"{task}_dataset.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def text(doc_id: str) -> str:
    """Model input text of a dev or validation document (never a final document)."""
    p = TEXT_DIR / f"{doc_id}.txt"
    if not p.exists():
        raise ValueError(f"{doc_id}: no text in the cache (not a dev or validation document of R1 or R2)")
    return p.read_text(encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextlib.contextmanager
def model_lock(purpose: str, wait_s: float = 0.0):
    """Exclusive lock for loading the local model (one model process at a time, 32 GB RAM).
    The lock file daten/cls/model.lock exists while a process holds it (atomic create). A lock of a
    dead process on this host is moved to model.lock.stale-<time> and the call tries again."""
    OUT.mkdir(parents=True, exist_ok=True)
    info = {"pid": os.getpid(), "host": socket.gethostname(), "purpose": purpose,
            "start": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "argv": sys.argv}
    end = time.time() + wait_s
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            break
        except FileExistsError:
            try:
                holder = json.loads(LOCK.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                holder = {}
            if holder.get("host") == socket.gethostname() and holder.get("pid") and not _pid_alive(int(holder["pid"])):
                with contextlib.suppress(FileNotFoundError):
                    LOCK.rename(LOCK.with_name(f"model.lock.stale-{int(time.time())}"))
                print(f"stale model lock of dead pid {holder.get('pid')} moved", flush=True)
                continue
            if time.time() >= end:
                raise SystemExit(f"model lock held: {holder or 'unreadable lock file'}")
            time.sleep(10)
    with os.fdopen(fd, "w") as f:
        json.dump(info, f)
    try:
        yield info
    finally:
        with contextlib.suppress(FileNotFoundError):
            cur = json.loads(LOCK.read_text(encoding="utf-8"))
            if cur.get("pid") == os.getpid():
                LOCK.unlink()


def check() -> None:
    """Assertions on the written files: splits, protected documents, text cache, design sample."""
    split = body_splits()
    prot = protected_doc_ids()
    for task in ("r1", "r2"):
        rs = rows(task)
        assert rs, task
        ids = [r["doc_id"] for r in rs]
        assert len(ids) == len(set(ids)), f"{task}: repeated doc_id"
        for r in rs:
            assert split[r["body_key"]] == r["split"] and r["split"] in ("dev", "validation"), r["doc_id"]
            assert r["doc_id"] not in prot, r["doc_id"]
            assert (TEXT_DIR / f"{r['doc_id']}.txt").exists(), r["doc_id"]
            assert r["subset"] in (("design", "check", "duplicate") if r["split"] == "dev"
                                   else ("validation", "duplicate")), r
        n_design = sum(r["subset"] == "design" for r in rs)
        print(f"{task}: {len(rs)} rows, design {n_design}, OK")
    print("final split: no row in the CSV files (counts only in data_stats.json)")


# keyword rule of daten/opd_research/verify_critic/scripts/checks.py (same pattern as fixes.py part C)
RX_REC = re.compile(
    r"(?P<against>nicht\s*erheblich|nichterheblich|abzulehnen|ablehnung|nicht\s+zu\s+überweisen|"
    r"nicht\s+entgegenzunehmen|rejeter|rejet\b|ne\s+pas\s+(?:prendre\s+en\s+considération|accepter|transmettre)|"
    r"respinger|non\s+(?:accogliere|accettare))"
    r"|(?P<for>erheblich\s*zu\s*erklären|erheblicherklärung|anzunehmen|annahme|zu\s+überweisen|entgegenzunehmen|"
    r"abzuschreiben|accepter|prendre\s+en\s+considération|transmettre|classer|accoglier|accettar|evader)",
    re.I)
# heading or formula of an executive response (indicator only, for the R2 label noise on dev)
RX_EXEC_RESPONSE = re.compile(
    r"antwort\s+des\s+(regierungsrat|gemeinderat|stadtrat|kleinen\s+rat|bundesrat|landrat)|"
    r"stellungnahme\s+des\s+(regierungsrat|gemeinderat|stadtrat|bundesrat)|"
    r"(der|das)\s+(regierungsrat|gemeinderat|stadtrat|bundesrat)\s+(beantwortet|antwortet|nimmt\s+wie\s+folgt)|"
    r"r[ée]ponse\s+du\s+(conseil|municipal|gouvernement)|le\s+conseil\s+d.[ée]tat\s+r[ée]pond|"
    r"risposta\s+del\s+(consiglio|municipio|governo)|il\s+consiglio\s+di\s+stato\s+risponde", re.I)


def audit() -> None:
    """Checks on dev only (content) and on validation (metadata only). Output daten/cls/audit_dev.json.
    1. R1: local category of the chosen response document, by parliament, tier and label (dev and
       validation; metadata). On dev only: the keyword rule on the whole chosen text.
    2. Leak check (dev): the text holds the document name or the URL of the export record.
    3. R2 label noise indicator (dev): proposal-role documents with an executive response heading in
       the first 3,000 characters, and response-role documents without one."""
    split = body_splits()
    r1 = rows("r1")
    r2 = rows("r2")
    need = collections.defaultdict(set)
    for r in r1 + r2:
        need[r["body_key"]].add(r["doc_id"])
    meta = {}
    for b, ids in need.items():
        for line in gzip.open(EXPORTS / f"docs/docs_{b}.ndjson.gz", "rt", encoding="utf-8"):
            d = json.loads(line)
            did = str(d["id"])
            if did in ids and did not in meta:
                meta[did] = {"category": (d.get("category_de") or d.get("category_fr") or d.get("category_it")
                                          or d.get("category_harmonized") or "")[:40],
                             "name": d.get("name") or "", "url": d.get("url") or ""}
    out: dict = {"made": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "version": VERSION}
    c = collections.Counter()
    kw = collections.Counter()
    for r in r1:
        c[f"{r['split']}|{r['body_key']}|tier{r['selection_tier']}|{r['label']}|{meta[r['doc_id']]['category']}"] += 1
        if r["split"] == "dev":
            ms = list(RX_REC.finditer(text(r["doc_id"])))
            p = None if not ms else ("recommended_against" if ms[-1].group("against") else "recommended_for")
            kw[f"{r['body_key']}|{'no_answer' if p is None else 'correct' if p == r['label'] else 'wrong'}"] += 1
    out["r1_chosen_category"] = dict(sorted(c.items()))
    out["r1_dev_keyword_rule_whole_text"] = dict(sorted(kw.items()))
    leak = collections.Counter()
    for task, rs in (("r1", r1), ("r2", r2)):
        for r in rs:
            if r["split"] != "dev":
                continue
            t = text(r["doc_id"]).lower()
            m = meta[r["doc_id"]]
            stem = re.sub(r"\.[a-z0-9]{2,4}$", "", m["name"].lower()).strip()
            leak[f"{task}|documents"] += 1
            hit = len(stem) >= 8 and stem in t
            leak[f"{task}|name_in_text"] += hit
            if hit:
                leak[f"{task}|name_in_text|{r['body_key']}"] += 1
            leak[f"{task}|url_in_text"] += bool(m["url"]) and m["url"].lower() in t
    out["dev_leak_check"] = dict(leak)
    noise = collections.Counter()
    for r in r2:
        if r["split"] != "dev" or r["subset"] == "duplicate":
            continue
        hit = bool(RX_EXEC_RESPONSE.search(text(r["doc_id"])[:3000]))
        noise[f"{r['body_key']}|{r['label']}|{'heading' if hit else 'no_heading'}"] += 1
    out["r2_dev_response_heading_first_3000_chars"] = dict(sorted(noise.items()))
    out["splits_seen"] = sorted({split[r["body_key"]] for r in r1 + r2})
    (OUT / "audit_dev.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("written", OUT / "audit_dev.json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build()
    elif cmd == "check":
        check()
    elif cmd == "audit":
        audit()
    else:
        raise SystemExit(__doc__)
