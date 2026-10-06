# SPDX-License-Identifier: Apache-2.0
"""Human gold set (E32): Docling and atoms for the documents of a list (test or extension).

Same procedure as for the groups (Docling run `m03_docling_zerlegen.py`, atome-v3 of `m03_atome.py`,
prompt form with legend). Docling runs in chunks of CHUNK documents. The time limit of a chunk is
TIMEOUT seconds times the number of its documents; a document without a result file after this is
tried again alone (time limit TIMEOUT) and then listed in <data>/gold/<list>_docling_skipped.txt.
Known limits: one document that hangs can stop a chunk for up to CHUNK x TIMEOUT seconds; a result
file counts when it exists (the script does not examine its content or its status).

Test documents go to <data>/gold/test/ (process rule 6); extension documents go to <data>/iso/. The
script prints counts only (no text), so that the developer of a method does not see the content of
test documents.

The atoms of a document that has atoms already are kept (--force makes them again, but never for a
document with a human decision: new atoms could change the atom ids).

PDF folders: the stratified sample (m03_iso_paths.SAMPLE_PDF) for the lists test and extension;
<data>/gold/test/pdf and <data>/pdf/bulk for the bulk lists of `m03_gold_bulk.py`.

For a list with a download status (<data>/gold/<list>_download.csv) only the documents with the
status "ok" (valid PDF, at most 25 pages) are prepared.

Usage:  uv run python src/m03_gold_prepare.py test|extension|bulk_test|bulk_train
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from m03_iso_paths import DATA, SAMPLE_PDF  # noqa: E402
CHUNK = 25          # documents for each Docling process
TIMEOUT = 420       # seconds for each document of a chunk (limit of a chunk: TIMEOUT x its documents)
LISTS = {   # list: (base of Docling and atoms, PDF folder); test documents never in <data>/iso (process rule 6)
    "test": (DATA / "gold/test", SAMPLE_PDF),
    "extension": (DATA / "iso", SAMPLE_PDF),
    "bulk_test": (DATA / "gold/test", DATA / "gold/test/pdf"),
    "bulk_train": (DATA / "iso", DATA / "pdf/bulk"),
}


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    which = sys.argv[1]
    if which not in LISTS:
        raise SystemExit(f"usage: m03_gold_prepare.py {'|'.join(LISTS)}")
    base, pdf_dir = LISTS[which]
    with open(DATA / "gold" / f"{which}.csv", newline="", encoding="utf-8") as f:
        docs = [r["doc_id"] for r in csv.DictReader(f)]
    st = DATA / "gold" / f"{which}_download.csv"
    if st.exists():
        with open(st, newline="", encoding="utf-8") as f:
            ok = {r["doc_id"] for r in csv.DictReader(f) if r["status"] == "ok"}
        docs = [d for d in docs if d in ok]
    (base / "docling").mkdir(parents=True, exist_ok=True)
    todo = [d for d in docs if not (base / "docling" / f"{d}.json").exists()]
    skipped_file = DATA / "gold" / f"{which}_docling_skipped.txt"
    skipped = set(skipped_file.read_text().split()) if skipped_file.exists() else set()
    todo = [d for d in todo if d not in skipped]
    if todo:
        log = DATA / "laeufe/docling" / f"gold_{which}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(todo), CHUNK):
            chunk = todo[i: i + CHUNK]
            with open(log, "a") as lf:
                try:
                    rc = subprocess.call([sys.executable, str(ROOT / "src/m03_docling_zerlegen.py"),
                                          *[str(pdf_dir / f"{d}.pdf") for d in chunk],
                                          "--name", f"gold_{which}", "--ausgabe", str(base / "docling")],
                                         stdout=lf, stderr=lf, timeout=TIMEOUT * len(chunk))
                except subprocess.TimeoutExpired:
                    rc = "timeout"
            missing = [d for d in chunk if not (base / "docling" / f"{d}.json").exists()]
            if missing and len(chunk) == 1:
                skipped |= set(missing)
                skipped_file.write_text("\n".join(sorted(skipped)) + "\n")
            elif missing:
                for d in missing:
                    with open(log, "a") as lf:
                        try:
                            subprocess.call([sys.executable, str(ROOT / "src/m03_docling_zerlegen.py"),
                                             str(pdf_dir / f"{d}.pdf"),
                                             "--name", f"gold_{which}", "--ausgabe", str(base / "docling")],
                                            stdout=lf, stderr=lf, timeout=TIMEOUT)
                        except subprocess.TimeoutExpired:
                            pass
                    if not (base / "docling" / f"{d}.json").exists():
                        skipped.add(d)
                        skipped_file.write_text("\n".join(sorted(skipped)) + "\n")
            print(f"docling chunk {i // CHUNK + 1}: rc {rc}, {len(chunk)} documents, skipped so far {len(skipped)}", flush=True)
    import m03_atome as at

    at.PDF = pdf_dir.resolve()
    at.DOCLING = (base / "docling").resolve()
    (base / "atome").mkdir(parents=True, exist_ok=True)
    (base / "atome_prompt").mkdir(parents=True, exist_ok=True)
    stats = {"documents": 0, "success": 0, "complete": 0, "atoms": 0, "missing_docling": 0}
    force = "--force" in sys.argv
    for d in docs:
        p = at.DOCLING / f"{d}.json"
        if not p.exists():
            stats["missing_docling"] += 1
            continue
        if (base / "atome" / f"{d}.json").exists() and not force:
            stats["kept"] = stats.get("kept", 0) + 1
            continue
        if any((DATA / "gold").glob(f"*/decisions/{d}.json")):
            raise SystemExit(f"{d}: a human decision exists; new atoms would change the atom ids (not allowed)")
        aus, zeile = at.dokument(p, None, at.VERSION_V3)
        (base / "atome" / f"{d}.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1), encoding="utf-8")
        (base / "atome_prompt" / f"{d}.txt").write_text(
            at.prompt_text(aus["atome"], mit_legende=True, fassung=at.VERSION_V3), encoding="utf-8")
        stats["documents"] += 1
        stats["success"] += zeile.get("status") == "success"
        stats["complete"] += zeile.get("vollstaendig") == "ja"
        stats["atoms"] += int(zeile.get("atome") or 0)
    print(which, json.dumps(stats))


if __name__ == "__main__":
    main()
