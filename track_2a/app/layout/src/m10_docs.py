"""Gate GJ (status EXCEPTION), plan chapters 3.1 and 5.2: the document files daten/gj/docs/<doc_id>.json.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream B,
for the main agent. This file does not change an existing file. It writes only under daten/gj/.

1 Input (explicit paths, no fallback of src/m03_iso_paths.py)
  daten/iso/docling/<doc_id>.json   the stored Docling output (Docling 2.133.0, src/m03_docling_zerlegen.py)
  daten/iso/atome/<doc_id>.json     the stored atoms (atome-v3, src/m03_atome.py)
  the PDF of the key "quelle" of the Docling output (daten/pdf/bulk or daten/pdf/lehrer_stichprobe); the
  guard allows the doc id first (src/m10_guard.py), then the script reads the PDF bytes for the SHA-256 only.
  The documents: all files of daten/iso/docling (2,665 documents, no test document). The guard must refuse 0.

2 Document text and character spans (interface 2; all m10 code imports these functions)
  SEP = "\\n\\n" (the key gesamttext_trenner of the Docling output).
  doc_text(blocks) = SEP.join(text of each block with a text), in Docling order. A block without text adds
  nothing and no separator. This text is equal to the key text_gesamt of the Docling output.
  block_spans(blocks): for each block (char_start, char_end) in doc_text, so that
  doc_text[char_start:char_end] == block text. A block without text has char_start == char_end (the position
  where the next text starts after the separator is not added). The spans are equal to the Docling key
  zeichen. The atoms keep their own key zeichen in the same text.
  The build stops for a document if one of these equalities is false.

3 Output daten/gj/docs/<doc_id>.json (interface 2)
  {"doc_id", "parliament", "split": dev | validation | group7, "pdf_sha256", "language", "blocks": [{"block",
  "page", "docling_label", "text", "atoms", "char_start", "char_end"}], "source_files": {path: sha256}}
  block = the Docling block id "B<n>" (n = 1, 2, ... in reading order); page = the Docling page; docling_label =
  the Docling label (text, section_header, page_header, picture, ...); text = the Docling block text, unchanged;
  atoms = the atom ids of the block in atom order. language = m05_cls_data.language(doc_text) (de, fr, it, rm,
  en), null for unk. The split value dev_sample of interface 2 is not used here.
  Run record: daten/gj/docs_build.json (inputs, guard summary, counts, SHA-256 of each output file).

Usage:
  uv run --offline --frozen --no-sync python src/m10_docs.py build [--ids ITEM ...]
  uv run --offline --frozen --no-sync python src/m10_docs.py check      (reads the written files again)
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402

VERSION = "m10-docs-1"
ROOT = guard.ROOT
SEP = "\n\n"
GJ = ROOT / "daten/gj"
DOCS_DIR = GJ / "docs"
RECORD = GJ / "docs_build.json"
PDF_DIRS = ("daten/pdf/bulk/", "daten/pdf/lehrer_stichprobe/")
ATOMS_VERSION = "atome-v3"


# ---------------------------------------------------------------- the text of interface 2

def doc_text(blocks: list[dict]) -> str:
    """The concatenated document text: the texts of the blocks with a text, joined by SEP, in block order."""
    return SEP.join(b["text"] for b in blocks if b["text"])


def block_spans(blocks: list[dict]) -> list[tuple[int, int]]:
    """(char_start, char_end) of each block in doc_text(blocks)."""
    out, pos, first = [], 0, True
    for b in blocks:
        t = b["text"]
        if t:
            if not first:
                pos += len(SEP)
            first = False
            out.append((pos, pos + len(t)))
            pos += len(t)
        else:
            out.append((pos, pos))
    return out


def check_doc(doc: dict) -> None:
    """Stop if the spans of a doc file do not give the block texts."""
    t = doc_text(doc["blocks"])
    for b, (s, e) in zip(doc["blocks"], block_spans(doc["blocks"])):
        if (b["char_start"], b["char_end"]) != (s, e) or t[s:e] != b["text"]:
            raise ValueError(f"{doc['doc_id']} {b['block']}: span does not give the block text")


def doc_path(doc_id: str) -> Path:
    return DOCS_DIR / f"{doc_id}.json"


def load(doc_id: str) -> dict:
    """A doc file of daten/gj/docs (the guard allows dev, validation and group 7)."""
    guard.assert_allowed([doc_id])
    return json.loads(doc_path(doc_id).read_text(encoding="utf-8"))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- build

def build_one(doc_id: str, split: str, parliament: str, lists: dict) -> tuple[dict, dict]:
    """(doc file, check values) of one document from the stored Docling and atom outputs."""
    import m05_cls_data as cd

    dp = guard.iso_file("docling", doc_id)
    ap = guard.iso_file("atome", doc_id)
    db, ab = dp.read_bytes(), ap.read_bytes()
    d, a = json.loads(db), json.loads(ab)
    dsha, asha = sha256_bytes(db), sha256_bytes(ab)
    if d.get("doc_id") != doc_id or a.get("doc_id") != doc_id:
        raise ValueError(f"{doc_id}: doc_id in the stored files differs")
    if d.get("status") != "success" or a.get("status") != "success":
        raise ValueError(f"{doc_id}: stored output without status success")
    if d.get("gesamttext_trenner") != SEP:
        raise ValueError(f"{doc_id}: other block separator in the Docling output")
    if a.get("version") != ATOMS_VERSION or a.get("quelle_sha256") != dsha:
        raise ValueError(f"{doc_id}: atoms are not {ATOMS_VERSION} of this Docling output")
    if (a.get("textschicht") or {}).get("pdf_sha256") != d.get("sha256"):
        raise ValueError(f"{doc_id}: the PDF SHA-256 of the atoms and of the Docling output differ")
    blocks = d["bloecke"]
    if [b["id"] for b in blocks] != [f"B{i}" for i in range(1, len(blocks) + 1)]:
        raise ValueError(f"{doc_id}: block ids are not B1..Bn in order")
    atoms_of: dict[str, list[str]] = collections.defaultdict(list)
    for x in a["atome"]:
        atoms_of[x["block"]].append(x["id"])
    if set(atoms_of) != {b["id"] for b in blocks}:
        raise ValueError(f"{doc_id}: atom blocks and Docling blocks differ")
    text = doc_text(blocks)
    if text != d["text_gesamt"]:
        raise ValueError(f"{doc_id}: doc_text differs from text_gesamt")
    spans = block_spans(blocks)
    for b, sp in zip(blocks, spans):
        if list(sp) != list(b["zeichen"]):
            raise ValueError(f"{doc_id} {b['id']}: span differs from the Docling key zeichen")
    q = d["quelle"]
    if not q.startswith(PDF_DIRS):
        raise ValueError(f"{doc_id}: PDF source {q} is not in {PDF_DIRS}")
    pdf = ROOT / q
    pc = guard.check_pdf(doc_id, pdf, lists)
    if not pc["equal"]:
        raise ValueError(f"{doc_id}: PDF SHA-256 differs from the stored value")
    lang = cd.language(text)
    out = {
        "doc_id": doc_id,
        "parliament": parliament,
        "split": split,
        "pdf_sha256": d["sha256"],
        "language": None if lang == "unk" else lang,
        "blocks": [{"block": b["id"], "page": int(b["seite"]), "docling_label": b["label"], "text": b["text"],
                    "atoms": atoms_of[b["id"]], "char_start": s, "char_end": e}
                   for b, (s, e) in zip(blocks, spans)],
        "source_files": {guard.rel(dp): dsha, guard.rel(ap): asha, guard.rel(pdf): pc["sha256"]},
    }
    check_doc(out)
    info = {"pdf_lists": len(pc["list_sha256"]), "pdf_dir": q.rsplit("/", 1)[0], "chars": len(text)}
    return out, info


def all_doc_ids() -> list[str]:
    return sorted((p.stem for p in (guard.ISO / "docling").glob("*.json")), key=int)


def cmd_build(args) -> int:
    ids = [i for a in args.ids for i in guard.read_items(a)] if args.ids else all_doc_ids()
    g = guard.assert_allowed(ids)          # stops on any refusal (0 test documents)
    lists = guard.list_sha256()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    n = collections.Counter()
    blocks = collections.Counter()
    empty = collections.Counter()
    labels = collections.Counter()
    lang = collections.Counter()
    pdf_dirs = collections.Counter()
    pdf_lists = 0
    outputs = {}
    for i, d in enumerate(ids, 1):
        split = g["split_of"][d]
        doc, info = build_one(d, split, g["parliament_of"][d], lists)
        raw = (json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8")
        doc_path(d).write_bytes(raw)
        outputs[guard.rel(doc_path(d))] = sha256_bytes(raw)
        n[split] += 1
        blocks[split] += len(doc["blocks"])
        empty[split] += sum(1 for b in doc["blocks"] if not b["text"])
        labels.update(b["docling_label"] for b in doc["blocks"])
        lang[doc["language"] or "null"] += 1
        pdf_dirs[info["pdf_dir"]] += 1
        pdf_lists += info["pdf_lists"] > 0
        if i % 500 == 0:
            print(f"{i} of {len(ids)}", flush=True)
    rec = {
        "version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "EXCEPTION (process rule 10, gate GJ)",
        "script": {guard.rel(Path(__file__)): guard.sha256_file(Path(__file__)),
                   guard.rel(Path(guard.__file__)): guard.sha256_file(Path(guard.__file__))},
        "guard": {k: v for k, v in g.items() if k not in ("split_of", "parliament_of")},
        "guard_tables": guard.tables().sources,
        "documents": dict(n), "blocks": dict(blocks), "blocks_without_text": dict(empty),
        "docling_labels": dict(labels.most_common()), "language": dict(lang.most_common()),
        "pdf_folders": dict(pdf_dirs),
        "pdf_sha256_checks": {"equal_to_docling_value": sum(n.values()),
                              "also_equal_to_a_list_value": pdf_lists},
        "text_definition": "doc_text = SEP.join(block texts with text); SEP = '\\n\\n'; equal to Docling "
                           "text_gesamt; spans equal to Docling zeichen (all documents)",
        "outputs": outputs,
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("documents", "blocks", "blocks_without_text", "language", "pdf_folders",
                                         "pdf_sha256_checks")}, ensure_ascii=False))
    return 0


def cmd_check(_args) -> int:
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    bad = 0
    for p, h in rec["outputs"].items():
        raw = (ROOT / p).read_bytes()
        if sha256_bytes(raw) != h:
            bad += 1
            continue
        check_doc(json.loads(raw))
    print(json.dumps({"files": len(rec["outputs"]), "sha256_different": bad}))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--ids", nargs="*", default=None)
    sub.add_parser("check")
    args = ap.parse_args()
    return cmd_build(args) if args.cmd == "build" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
