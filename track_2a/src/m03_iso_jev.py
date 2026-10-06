# SPDX-License-Identifier: Apache-2.0
"""Isolation readout at the level of E20 (step 3.9): one readout for each atom over the whole document.

SUPERSEDED: this file is the readout format of E20 version 3.1 (13 answers, letters A to M). The
current format is E20 version 4.1 in m03_iso_jev4.py; the measurement for gate 3a is in m03_iso_v4.py.
This file stays, because m03_iso_v4.py (conversion of the version 3.1 references) and m04_iso_bundle.py
(schema v31: its Tokens class, answers and references) use it.

Apertus reads the whole document (E18). Then, for each atom, it gives one of 13 answers: the role
page furniture, the role insert, or the segment class of a main atom (E20, chapters 3 and 4). Each
answer is one token. The code reads only the logits of the 13 answer tokens; the model writes no
text (E19).

Sequence (same assembly for training and readout):
  system:     short role
  user:       instruction, then the whole document (<data>/iso/atome_prompt/<doc_id>.txt:
              one line for each atom, ID | page | hints | text, with the legend)
  assistant:  "Zuordnung:" and one line for each atom: "<atom id>:" + answer token + newline
The atom id and the colon are given. The readout position is the colon; the logits at that position
predict the answer token. In training, the line of each earlier atom contains its reference answer;
in the readout, it contains the answer that the model chose (greedy, KV cache line by line).

The prompt text is German, because most documents are German. The answer tokens are the letters
A to M with a leading space; the instruction gives their meaning.

Usage:  uv run python src/m03_iso_jev.py --lengths     (token lengths of all documents with atoms; no model)
        uv run python src/m03_iso_jev.py --show DOC_ID (sequence of one document with its reference;
                                                       terminal only, contains document text)
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, MODEL, PROMPTS, ROOT, iso_path  # noqa: E402,F401
import m03_iso_mass as ms  # noqa: E402

VERSION = "iso-jev-v1"

# letter, answer, meaning (German, for the model)
OPTIONS = (
    ("A", "furniture", "Seitenrand: Seitenzahl, Kopf- oder Fusszeile, die auf 2 oder mehr Seiten steht (alle Kopien), "
                       "Dateiname, Pfad, Dokumenteigenschaft, Strichlinie über Fussnoten, Druckvorlage einer Beilage"),
    ("B", "insert", "Einschub: Fussnotentext; Bild und jeder Text im Rahmen eines Bildes (Logo, Siegel, Unterschrift, "
                    "einzelne Zeichen) und die Bildlegende; Kopfangaben, die die Lesereihenfolge mitten in einen "
                    "anderen Teil stellt (z.B. Adressblock oder Aktenzeichen oben rechts)"),
    ("C", "head", "Kopf: Briefkopf, Adresse, Ort und Datum, Nummern, Anrede, Urheberzeilen, Formularfelder, "
                  "ein Satz, der nur die Einreichung meldet (Datum, Urheber, Nummer, Titel)"),
    ("D", "title", "Titel: die Betreffzeilen des Geschäfts, mit einer Zeile nur mit Dokumenttyp, Geschäftstyp "
                   "oder Nummer direkt darüber oder darunter"),
    ("E", "short_title", "Kurztitel, den das Dokument getrennt angibt"),
    ("F", "submitted", "Text der Einreichenden (Vorstosstext, Fragen, Forderungen), ohne die Teile mit "
                       "Begründungs-Überschrift"),
    ("G", "reasoning", "Begründung: Teil des Textes der Einreichenden mit Überschrift Begründung, Développement, "
                       "Motivazione"),
    ("H", "response", "Antwort der Exekutive, auch wiederholte Einzelfragen zwischen den Antworten"),
    ("I", "recommendation", "Antrag: eigener Schlussabsatz oder Abschnitt nur mit dem formellen Antrag der Exekutive "
                            "an das Parlament (beantragt, propose, invita)"),
    ("J", "summary", "Zusammenfassung mit Überschrift Zusammenfassung, Résumé, Riassunto"),
    ("K", "closing", "Schluss: Gruss, Dank, Unterschriftszeilen, Ort und Datum am Ende eines Textes"),
    ("L", "distribution", "Verteiler: Mitteilung an, Zustellung, Copie à"),
    ("M", "other_text", "anderer Inhalt: Beschlussformel (beschliesst, arrête) bis zum Antworttext, Bericht, "
                        "Protokoll, Kostenhinweis, Hinweis zur Übermittlung, Beilage als Ganzes"),
)
ANSWERS = tuple(o[1] for o in OPTIONS)
SYSTEM = "Du ordnest die Zeilen von Dokumenten aus Schweizer Parlamenten den Teilen eines Geschäfts zu."
INSTRUCTION = """\
Ordne jede Zeile (Atom) des Dokuments einem Teil zu. Seitenrand und Einschub unterbrechen einen Teil \
nicht. Eine Überschrift gehört zum Teil, den sie einleitet. Wiederholt die Exekutive den Text der \
Einreichenden, ordne ihn wie den Originaltext zu (Text der Einreichenden, Begründung). Teile:
""" + "\n".join(f"{l} = {d}" for l, _, d in OPTIONS) + """

Nach dem Dokument folgt für jede Zeile ihre ID und der Buchstabe ihres Teils."""


def messages(doc_id: str) -> list[dict]:
    text = iso_path("atome_prompt", doc_id, "txt").read_text(encoding="utf-8")
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": INSTRUCTION + "\n\nDokument:\n" + text}]


def answers_from_segmentation(seg: dict, ids: list[str]) -> list[str]:
    """One answer for each atom: furniture, insert or the class of the segment of the main atom."""
    furn, ins = set(seg.get("furniture", [])), set(seg.get("insert", []))
    cls = ms.labels(seg, ids)
    return ["furniture" if a in furn else "insert" if a in ins else cls[a][0] for a in ids]


def segmentation_from_answers(doc_id: str, ids: list[str], answers: list[str], coder: str) -> dict:
    """Segmentation file (format of m03_iso_mass.py): a segment is a run of main atoms with one class."""
    segs = []
    for a, x in zip(ids, answers):
        if x in ("furniture", "insert"):
            continue
        if segs and segs[-1]["class"] == x:
            segs[-1]["last"] = a
        else:
            segs.append({"class": x, "first": a, "last": a})
    return {"doc_id": doc_id, "coder": coder,
            "furniture": [a for a, x in zip(ids, answers) if x == "furniture"],
            "insert": [a for a, x in zip(ids, answers) if x == "insert"],
            "segments": segs, "notes": ""}


class Tokens:
    """Assembly of the sequence in pieces (same for training and readout)."""

    def __init__(self, tok):
        self.tok = tok
        self.answer_ids = []
        for letter, _, _ in OPTIONS:
            x = tok.encode(" " + letter, add_special_tokens=False)
            assert len(x) == 1, (letter, x)
            self.answer_ids.append(x[0])
        assert len(set(self.answer_ids)) == len(OPTIONS)
        self.nl = tok.encode("\n", add_special_tokens=False)
        assert len(self.nl) == 1, self.nl
        self.head = tok.encode("Zuordnung:\n", add_special_tokens=False)

    def prefix(self, doc_id: str) -> list[int]:
        p = list(self.tok.apply_chat_template(messages(doc_id), add_generation_prompt=True,
                                              enable_thinking=False, return_dict=False))
        return p + self.head

    def line(self, atom_id: str) -> list[int]:
        return self.tok.encode(f"{atom_id}:", add_special_tokens=False)

    def pointer_sequence(self, doc_id: str, ids: list[str]) -> tuple[list[int], list[int]]:
        """Version 2 (iso-jev-v2): the lines contain no answers ("<atom id>:" and a newline).
        Each readout position sees the whole document but no earlier decision, so the model
        cannot copy its own earlier answer. One forward pass gives all atoms."""
        seq = self.prefix(doc_id)
        pos = []
        for a in ids:
            seq += self.line(a)
            pos.append(len(seq) - 1)
            seq += self.nl
        return seq, pos

    def repeat_sequence(self, doc_id: str, ids: list[str]) -> tuple[list[int], list[int]]:
        """Version 3 (iso-jev-v3): after the whole document, each atom line comes again in full
        ("ID | page | hints | text"), followed by " ->" as the readout position. The readout
        position sees the whole document and the line itself; there are no answers in the
        sequence, so no decision depends on an earlier decision."""
        lines = {}
        for raw in iso_path("atome_prompt", doc_id, "txt").read_text(encoding="utf-8").splitlines():
            head = raw.split(" | ", 1)[0]
            if head in ids:
                lines[head] = raw
        seq = self.prefix(doc_id)
        pos = []
        for a in ids:
            seq += self.tok.encode(lines.get(a, a) + " ->", add_special_tokens=False)
            pos.append(len(seq) - 1)
            seq += self.nl
        return seq, pos

    def sequence(self, doc_id: str, ids: list[str], answers: list[str]) -> tuple[list[int], list[int]]:
        """(tokens, readout positions). The logits at position s predict the answer token at s + 1."""
        seq = self.prefix(doc_id)
        pos = []
        for a, x in zip(ids, answers):
            seq += self.line(a)
            pos.append(len(seq) - 1)
            seq += [self.answer_ids[ANSWERS.index(x)]] + self.nl
        for s, x in zip(pos, answers):
            assert seq[s + 1] == self.answer_ids[ANSWERS.index(x)]
        return seq, pos


def reference(ref_dir: Path, doc_id: str) -> tuple[list[str], list[str]]:
    """(atom ids, answers) from a valid segmentation file."""
    seg = json.loads((ref_dir / f"{doc_id}.json").read_text(encoding="utf-8"))
    ids = ms.atom_ids(doc_id)
    err = ms.validate(seg, ids)
    if err:
        raise SystemExit(f"{ref_dir.name}/{doc_id} not valid: {err[:3]}")
    return ids, answers_from_segmentation(seg, ids)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lengths", action="store_true")
    ap.add_argument("--show", default=None)
    ap.add_argument("--ref", default="iso/ref", help="reference folder, relative to the data root")
    args = ap.parse_args()
    from mlx_lm.utils import load_tokenizer

    tk = Tokens(load_tokenizer(MODEL))
    if args.show:
        ids, answers = reference(DATA / args.ref, args.show)
        seq, _ = tk.sequence(args.show, ids, answers)
        print(tk.tok.decode(seq))
        return
    rows = []
    for p in sorted(PROMPTS.glob("*.txt")):
        doc_id = p.stem
        ids = ms.atom_ids(doc_id)
        n_prefix = len(tk.prefix(doc_id))
        n_lines = sum(len(tk.line(a)) + 2 for a in ids)
        rows.append({"doc_id": doc_id, "atoms": len(ids), "tokens_document": n_prefix,
                     "tokens_total": n_prefix + n_lines})
    out = DATA / "analyse/iso/jev_lengths.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    t = [r["tokens_total"] for r in rows]
    print(f"{len(rows)} documents; tokens total: median {statistics.median(t):.0f}, max {max(t)}; "
          + ", ".join(f"<= {k}: {sum(x <= k for x in t)}" for k in (8192, 12288, 16384, 24576)))


if __name__ == "__main__":
    main()
