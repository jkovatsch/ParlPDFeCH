# SPDX-License-Identifier: Apache-2.0
"""Human gold set (E32): bulk lists of 06.10.2026: download, Docling and atoms.

Two lists (in <data>/gold/):
  bulk_test   300 documents of test parliaments (split role "Gold", process rule 6), roles vorstoss,
              antwort, kombiniert. First the downloaded documents of an earlier test list whose
              parliament is a test parliament of the split v2 (source "auswahl_test", PDF files in
              <data>/pdf/test_dokumente). PDFs in <data>/gold/test/pdf, Docling and atoms in
              <data>/gold/test (never in <data>/iso).
  bulk_train  2,500 documents of training and validation parliaments: 85 % roles vorstoss, antwort,
              kombiniert; 15 % other roles. No parliament of the final group 7. PDFs in <data>/pdf/bulk,
              Docling and atoms in <data>/iso.

Selection of the lists (private project, seed 20261007): the candidates come from the code that
also built the pool of the stratified sample (m03_iso_paths.SAMPLE_LIST): PDF documents at affairs,
with document role and scan class. Not used again: a document of any list of the project, an
inspection document or its file, an R8 copy, a file (SHA-256) that is in a list already. Size 2 KB
to 12 MB. Documents without a text layer ("scan_ohne_text") at most 10 %. Documents of each
parliament in a seeded order; round robin over the parliaments, at most 30 (bulk_test) or 40
(bulk_train) documents for each parliament; language minimums for bulk_train (fr 25 %, it 12 %,
all rm), with at most 100 documents for each parliament in the language phase. The code of the
candidate pool is not in this repository. Thus, this version has no command "select"; it starts
from the two lists.

Download: only files.openparldata.ch, at most 2 requests at the same time, 0.5 s pause; valid if
the file starts with %PDF (white space before it is allowed). The column sha_ok of the status
records if the SHA-256 of the file is equal to the hash in the URL; it does not change the status.
Known limit: for files of files.openparldata.ch, the hash in the URL is not the SHA-256 of the file
(0 of 600 files, 06.10.2026). Thus, sha_ok is False and the printed count "sha mismatches" has no
meaning. pdfinfo (Poppler) gives the pages; more than 25 pages: not prepared. Status:
<data>/gold/<list>_download.csv. Then Docling and atoms (`m03_gold_prepare.py <list>`).

The script prints counts only (no text, no titles).

Usage:  uv run python src/m03_gold_bulk.py check       (test-set check of the two lists)
        uv run python src/m03_gold_bulk.py all         (check, download, prepare)
"""

from __future__ import annotations

import collections
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from m03_iso_paths import DATA  # noqa: E402

GOLD = DATA / "gold"
AN = DATA / "analyse"
MAX_BYTES = 12 * 1024 * 1024
MAX_PAGES = 25
USER_AGENT = "ParlPDFeCH-gold/0.1"
ALLOWED = "https://files.openparldata.ch/"
PARALLEL = 2
PAUSE_S = 0.5
LISTS = {
    "bulk_test": {"pdf": GOLD / "test/pdf"},
    "bulk_train": {"pdf": DATA / "pdf/bulk"},
}


def read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdf_head(b: bytes) -> str:
    if not b:
        return "empty"
    if b[:4] == b"%PDF" or b[:64].lstrip(b" \t\r\n").startswith(b"%PDF"):
        return "ok"
    return "not_pdf"


def pages_of(p: Path) -> int:
    try:
        out = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True, timeout=60).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    except Exception:  # noqa: BLE001
        pass
    return -1


def download(name: str) -> None:
    cfg = LISTS[name]
    rows = read(GOLD / f"{name}.csv")
    cfg["pdf"].mkdir(parents=True, exist_ok=True)
    status_p = GOLD / f"{name}_download.csv"
    status = {r["doc_id"]: r for r in read(status_p)}
    lock = threading.Lock()
    done = [0]

    def one(r: dict) -> dict:
        d = r["doc_id"]
        target = cfg["pdf"] / f"{d}.pdf"
        z = {"doc_id": d, "status": "", "bytes": "", "pages": "", "sha_ok": "", "error": ""}
        if not target.exists() and r.get("source") == "auswahl_test":
            src = DATA / "pdf/test_dokumente" / f"{d}.pdf"
            if src.exists():
                shutil.copy2(src, target)
        if not target.exists():
            url = r["url"]
            if not url.startswith(ALLOWED):
                z.update(status="error", error="url not allowed")
                return z
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = resp.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    z.update(status="error", error="too large")
                    return z
                tmp = target.with_suffix(".part")
                tmp.write_bytes(data)
                tmp.rename(target)
            except Exception as e:  # noqa: BLE001
                z.update(status="error", error=f"{type(e).__name__}: {str(e)[:150]}")
                time.sleep(PAUSE_S)
                return z
            time.sleep(PAUSE_S)
        b = target.read_bytes()
        z["bytes"] = len(b)
        head = pdf_head(b)
        sha_ok = hashlib.sha256(b).hexdigest() == r["hash"] if r.get("hash") else ""
        z["sha_ok"] = sha_ok
        if head != "ok":
            target.rename(target.with_suffix(".invalid"))
            z.update(status="invalid", error=head)
            return z
        pg = pages_of(target)
        z["pages"] = pg
        z["status"] = "ok" if 0 < pg <= MAX_PAGES else ("too_long" if pg > MAX_PAGES else "no_pages")
        return z

    todo = [r for r in rows if status.get(r["doc_id"], {}).get("status") not in ("ok", "too_long", "invalid", "no_pages")]
    print(f"{name}: download {len(todo)} of {len(rows)} (at most {PARALLEL} at the same time)", flush=True)

    def task(r: dict) -> None:
        z = one(r)
        with lock:
            status[r["doc_id"]] = z
            done[0] += 1
            if done[0] % 100 == 0:
                write_status(status_p, status)
                c = collections.Counter(x["status"] for x in status.values())
                print(f"  {name}: {done[0]}/{len(todo)} {dict(c)}", flush=True)

    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        list(ex.map(task, todo))
    write_status(status_p, status)
    c = collections.Counter(x["status"] for x in status.values())
    mb = sum(int(x["bytes"] or 0) for x in status.values()) / 1e6
    print(f"{name}: download done {dict(c)}; {mb:.0f} MB; sha mismatches "
          f"{sum(1 for x in status.values() if str(x['sha_ok']) == 'False')}", flush=True)


def write_status(p: Path, status: dict) -> None:
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "status", "bytes", "pages", "sha_ok", "error"])
        w.writeheader()
        w.writerows(status.values())


def check_lists() -> None:
    r = subprocess.run([sys.executable, str(ROOT / "src/m00_pruefe_testset.py"), str(GOLD / "bulk_train.csv")],
                       capture_output=True, text=True)
    print("bulk_train test-set check:", r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:], flush=True)
    if r.returncode != 0:
        raise SystemExit("bulk_train contains test documents: stop (process rule 6)")
    split = {z["body_key"]: z["rolle"] for z in read(AN / "synthese/split.csv")}
    bad = [x["doc_id"] for x in read(GOLD / "bulk_test.csv") if split.get(x["body_key"]) != "Gold"]
    if bad:
        raise SystemExit(f"bulk_test has {len(bad)} documents outside the test parliaments: stop")
    print("bulk_test: all documents of test parliaments", flush=True)


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.time()
    if cmd not in ("check", "download", "prepare", "all"):
        raise SystemExit("usage: m03_gold_bulk.py check|download|prepare|all")
    if cmd in ("check", "all"):
        check_lists()
    if cmd in ("download", "all"):
        for name in LISTS:
            download(name)
    if cmd in ("prepare", "all"):
        for name in LISTS:
            rc = subprocess.call([sys.executable, str(ROOT / "src/m03_gold_prepare.py"), name])
            print(f"prepare {name}: rc {rc}", flush=True)
    summary = {"finished": time.strftime("%Y-%m-%dT%H:%M:%S"), "minutes": round((time.time() - t0) / 60, 1)}
    for name in LISTS:
        st = read(GOLD / f"{name}_download.csv")
        summary[name] = dict(collections.Counter(x["status"] for x in st))
    (GOLD / "bulk_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("summary", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
