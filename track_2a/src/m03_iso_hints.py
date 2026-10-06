# SPDX-License-Identifier: Apache-2.0
"""Layout hints for the isolation readout (E20 version 4, bundle v4b): words relative to the document.

Each hint is a fact of the PDF or of the metadata of the own affair, never a decision (E29: the
title anchor from the metadata of the own affair is allowed; hints from other documents of the same
parliament are not used). The hints go into the repeated atom line of `m03_iso_jev4.py` (format v3h).

  Kopfbereich / Fussbereich   the line is in the top 12 % or the bottom 10 % of its page
  eingerückt / zentriert / rechts
                              left edge relative to the most frequent left edge of the document
  gross / klein               line height >= 1.25 or <= 0.8 times the median line height
  Abstand                     vertical gap to the previous atom on the same page > 1.6 times the
                              median gap of the document
  neue Seite                  first atom of a page
  wiederholt                  the same normalized text (at least 4 characters) is in another atom
                              of the document
  Titelanker                  the atom is part of the first contiguous run of atoms whose words are
                              words of the affair title in the metadata (OpenParlData affairs export,
                              title_de/fr/it/rm): >= 75 % of the content words of each atom (not type
                              words, not numbers) are title words, and the run covers >= 50 % of the
                              content words of the title; up to 2 adjacent atoms before and 1 after
                              with only type words or numbers are also marked
Bold text is not a hint of v4b: the Docling files have no font data.

The affair of each document comes from the list of the stratified sample (m03_iso_paths.SAMPLE_LIST).

Usage:  python3 src/m03_iso_hints.py --titles          (cache of the affair titles: <data>/iso/titles.json)
        python3 src/m03_iso_hints.py --check            (title anchor against the references of groups 1 to 6 and the pool)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, SAMPLE_LIST, iso_path  # noqa: E402
import m03_iso_mass as ms  # noqa: E402

ATOMS = DATA / "iso/atome"
DOCLING = DATA / "iso/docling"
TITLES = DATA / "iso/titles.json"
VERSION = "iso-hints-v1"
WORD = re.compile(r"[^\W_]+", re.UNICODE)
NUMBER = re.compile(r"[a-z]{0,3}\d[\w.]*")
TYPE_WORDS = {
    "motion", "postulat", "interpellation", "anfrage", "kleine", "einfache", "dringliche", "dringlich", "frage",
    "fragen", "antwort", "beantwortung", "stellungnahme", "bericht", "antrag", "parlamentarische", "initiative",
    "auftrag", "vorstoss", "geschäft", "geschäftsnummer", "nr", "no", "n", "objet", "question", "questions",
    "réponse", "reponse", "écrite", "ecrite", "orale", "urgente", "mozione", "postulato", "interrogazione",
    "interpellanza", "risposta", "domanda", "resolution", "résolution", "risoluzione", "petition", "pétition",
    "petizione", "vom", "du", "del", "dal", "betreffend", "betr", "concernant", "concernente", "und", "et", "e",
    "der", "des", "la", "le", "il", "von", "de", "di", "sur", "zur", "zum", "rapport", "rapporto", "gr", "kr",
}


def words(text: str) -> list[str]:
    return [w.lower() for w in WORD.findall(text or "")]


def doc_affairs() -> dict[str, str]:
    with open(SAMPLE_LIST, newline="", encoding="utf-8") as f:
        return {r["doc_id"]: r["affair_id"] for r in csv.DictReader(f)}


def build_titles() -> None:
    aff = doc_affairs()
    docs = {p.stem for p in ATOMS.glob("*.json")}
    need = {aff[d] for d in docs if d in aff}
    titles = {}
    with gzip.open(DATA / "roh/exports/affairs.ndjson.gz", "rt", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            if str(x.get("id")) in need:
                titles[str(x["id"])] = {k: x.get(k) for k in ("title_de", "title_fr", "title_it", "title_rm") if x.get(k)}
    out = {d: titles.get(aff.get(d, ""), {}) for d in sorted(docs)}
    TITLES.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"titles for {sum(bool(v) for v in out.values())} of {len(out)} documents -> {TITLES}")


def content(ws: list[str]) -> list[str]:
    return [w for w in ws if len(w) > 1 and w not in TYPE_WORDS and not NUMBER.fullmatch(w)]


def type_line(text: str) -> bool:
    ws = words(text)
    return bool(ws) and all(w in TYPE_WORDS or NUMBER.fullmatch(w) for w in ws)


def title_anchor(atoms: list[dict], title_variants: list[str]) -> set[str]:
    best: set[str] = set()
    for t in title_variants:
        ts = set(words(t))
        tc = set(content(words(t)))
        if not tc:
            continue
        run, covered = [], set()
        for i, a in enumerate(atoms):
            ac = content(words(a["text"]))
            inside = ac and sum(w in ts for w in ac) / len(ac) >= 0.75
            if inside:
                run.append(i)
                covered |= {w for w in ac if w in tc}
                continue
            if run and len(covered) / len(tc) >= 0.5:
                break
            run, covered = [], set()
        if not run or len(covered) / len(tc) < 0.5:
            continue
        marked = set(run)
        j = run[0] - 1
        while j >= 0 and run[0] - j <= 2 and type_line(atoms[j]["text"]):
            marked.add(j)
            j -= 1
        if run[-1] + 1 < len(atoms) and type_line(atoms[run[-1] + 1]["text"]):
            marked.add(run[-1] + 1)
        ids = {atoms[i]["id"] for i in marked}
        if len(ids) > len(best):
            best = ids
    return best


def hints(doc_id: str, titles: dict | None = None) -> dict[str, list[str]]:
    atoms = json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))["atome"]
    pages = {p["seite"]: (p["breite"], p["hoehe"]) for p in json.loads(iso_path("docling", doc_id).read_text())["seiten"]}
    out = {a["id"]: [] for a in atoms}
    boxes = [(a, a.get("zeilenrahmen") or a.get("rahmen")) for a in atoms]
    lefts = Counter(round(b[0] / 4) * 4 for a, b in boxes if b and a["text"].strip())
    margin = lefts.most_common(1)[0][0] if lefts else 0
    heights = [b[3] - b[1] for a, b in boxes if b and a["text"].strip() and b[3] > b[1]]
    mh = statistics.median(heights) if heights else 0
    gaps, prev = [], None
    for a, b in boxes:
        if b and prev and prev[0]["seite"] == a["seite"] and b[1] >= prev[1][3]:
            gaps.append(b[1] - prev[1][3])
        if b:
            prev = (a, b)
    mg = statistics.median(gaps) if gaps else 0
    norm = Counter(" ".join(words(a["text"])) for a in atoms)
    prev, last_page = None, None
    for a, b in boxes:
        h = out[a["id"]]
        if a["seite"] != last_page:
            h.append("neue Seite")
            last_page = a["seite"]
            prev = None
        if b:
            w, ht = pages.get(a["seite"], (595.0, 842.0))
            cy = (b[1] + b[3]) / 2
            if cy < 0.12 * ht:
                h.append("Kopfbereich")
            elif cy > 0.90 * ht:
                h.append("Fussbereich")
            cx = (b[0] + b[2]) / 2
            if abs(cx - w / 2) < 0.03 * w and b[0] > margin + 20 and b[2] - b[0] < 0.7 * w:
                h.append("zentriert")
            elif b[0] > w / 2 and b[0] > margin + 20:
                h.append("rechts")
            elif b[0] > margin + 10:
                h.append("eingerückt")
            if mh and b[3] > b[1]:
                r = (b[3] - b[1]) / mh
                h.append("gross" if r >= 1.25 else "klein" if r <= 0.8 else "")
            if prev and mg and b[1] - prev[3] > 1.6 * mg + 2:
                h.append("Abstand")
            prev = b
        key = " ".join(words(a["text"]))
        if len(key) >= 4 and norm[key] > 1:
            h.append("wiederholt")
    t = (titles if titles is not None else json.loads(TITLES.read_text(encoding="utf-8"))).get(doc_id, {})
    for a in title_anchor(atoms, list(t.values())):
        out[a].append("Titelanker")
    return {k: [x for x in v if x] for k, v in out.items()}


def check() -> None:
    import m03_iso_v4 as v4

    titles = json.loads(TITLES.read_text(encoding="utf-8"))
    final = v4.final_docs()
    rows = []
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        rows += [(r["doc_id"], DATA / "iso/v4/ref") for r in csv.DictReader(f) if r["group"] not in v4.FINAL_GROUPS]
    with open(DATA / "iso/pool.csv", newline="", encoding="utf-8") as f:
        rows += [(r["doc_id"], DATA / "iso/v4/pool_ref") for r in csv.DictReader(f)]
    tp = fp = fn = docs = with_title = 0
    for d, ref in rows:
        if d in final or not (ref / f"{d}.json").exists():
            continue
        x = json.loads((ref / f"{d}.json").read_text())
        h = hints(d, titles)
        anchor = {a for a, v in h.items() if "Titelanker" in v}
        gold = {a for a, y in zip(x["ids"], x["answers"]) if y == "title"}
        tp += len(anchor & gold)
        fp += len(anchor - gold)
        fn += len(gold - anchor)
        docs += 1
        with_title += bool(titles.get(d))
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    print(f"documents {docs} (with a metadata title {with_title}); title atoms of the references {tp + fn}; "
          f"anchor atoms {tp + fp}; precision {p:.3f}; recall {r:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.titles:
        build_titles()
    if args.check:
        check()


if __name__ == "__main__":
    main()
