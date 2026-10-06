# SPDX-License-Identifier: Apache-2.0
"""Isolation readout at the level of E20 version 4 (answers only from eCH-0295 I95; `m03_iso_v4.py`).

Same readout design as `m03_iso_jev.py` format v3: the instruction, the whole document (E18), then
each atom line again in full, followed by " ->" as the readout position; no answers in the sequence
(no decision depends on an earlier decision). The 13 answers of `m03_iso_v4.ANSWERS` are the letters
A to M (one token each, with a leading space). The model writes no text (E19).

Version 2 (bundle v4b): 12 answers A to L without furniture; the repeated atom line has the layout
hints of `m03_iso_hints.py` in square brackets ("Seitenrand" for a fixed furniture atom).

Fixed answers (E20 v4, chapter 3; procedure of `m03_iso_hilfe.py`): R1, R4, R5 -> furniture; a picture
atom (R3, Docling form Bild) -> none. Footnotes and captions are not fixed: they take the answer of
the text that contains them.

Usage:  uv run python src/m03_iso_jev4.py --show DOC_ID   (sequence of one document; terminal only)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, MODEL, PROMPTS, ROOT, iso_path  # noqa: E402,F401
import m03_iso_hilfe as hf  # noqa: E402
import m03_iso_jev as jev  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

VERSION = "iso-jev4-v2"
LETTERS = "ABCDEFGHIJKLM"
MEANING = {
    "title": "Titel des Geschäfts (eCH-0295 Affair.title, title): die gedruckte Überschrift mit dem Betreff",
    "short_title": "Kurztitel (Affair.title, short_title), nur wenn das Dokument ihn eigens angibt",
    "submitted": "eingereichter Text der Urheberschaft (Submission.texts, submitted): Vorstosstext, Forderung, Fragen",
    "reasoning": "Begründung der Urheberschaft (Submission.texts, reasoning), nur mit Überschrift Begründung",
    "response": "Antwort der Exekutive (ResponseStep.texts, response), auch wiederholte Einzelfragen",
    "recommendation": "formeller Antrag der Exekutive (ResponseStep.texts, recommendation), eigener Absatz",
    "summary": "Zusammenfassung (summary), nur mit Überschrift Zusammenfassung",
    "committee_recommendation": "Text eines Kommissionsentscheids (CommitteeDecision.text)",
    "speech": "mündliches Votum in einem Protokoll (Speech.text), nicht die Antwort der Exekutive",
    "proposition": "Wortlaut eines Antrags in der Debatte (Proposition.text)",
    "vote": "Wortlaut, über den abgestimmt wird (Vote.text)",
    "none": "kein Textfeld: Briefkopf, Formularfelder, Anrede, Meldung der Einreichung, Beschlussformel, "
            "Gruss, Dank, Unterschriften, Ort und Datum, Verteiler, Beilagen, Bilder",
    "furniture": "Seitenrand: Seitenzahl, wiederkehrende Kopf- oder Fusszeile, Dateiname",
}
OPTIONS = tuple((LETTERS[i], a, MEANING[a]) for i, a in enumerate(v4.ANSWERS))
ANSWERS = v4.ANSWERS
# Version 2 (bundle v4b): 12 answers; furniture only by the fixed rules (decision of 05.10.2026, 22:39)
ANSWERS12 = tuple(a for a in v4.ANSWERS if a != "furniture")
OPTIONS12 = tuple((LETTERS[i], a, MEANING[a]) for i, a in enumerate(ANSWERS12))
SYSTEM = "Du ordnest die Zeilen von Dokumenten aus Schweizer Parlamenten den Textfeldern des Standards eCH-0295 zu."
INSTRUCTION = """\
Ordne jede Zeile (Atom) des Dokuments einem Textfeld von eCH-0295 zu, oder «kein Textfeld». Überschriften \
gehören zum Text, den sie einleiten; Fussnoten und Bildlegenden zum Text, in dem sie stehen. Wiederholt die \
Exekutive den ganzen Vorstoss, behält er seine Felder; einzelne wiederholte Fragen gehören zur Antwort. Antworten:
""" + "\n".join(f"{l} = {d}" for l, _, d in OPTIONS) + """

Nach dem Dokument folgt jede Zeile noch einmal, mit «->» am Ende."""


INSTRUCTION12 = """\
Ordne jede Zeile (Atom) des Dokuments einem Textfeld von eCH-0295 zu, oder «kein Textfeld». Überschriften \
gehören zum Text, den sie einleiten; Fussnoten und Bildlegenden zum Text, in dem sie stehen. Wiederholt die \
Exekutive den ganzen Vorstoss, behält er seine Felder; einzelne wiederholte Fragen gehören zur Antwort. Antworten:
""" + "\n".join(f"{l} = {d}" for l, _, d in OPTIONS12) + """

Nach dem Dokument folgt jede Zeile noch einmal, mit Lagehinweisen in eckigen Klammern und «->» am Ende. \
Lagehinweise: Kopfbereich, Fussbereich, eingerückt, zentriert, rechts, gross, klein (Zeilenhöhe), Abstand \
(grosser Abstand zur vorigen Zeile), neue Seite, wiederholt (gleicher Text noch einmal im Dokument), Titelanker \
(Wörter des Geschäftstitels aus den Metadaten), Seitenrand (fest; Seitenzahl, Kopf- oder Fusszeile, Dateiangabe)."""


def messages(doc_id: str, v2: bool = False) -> list[dict]:
    text = iso_path("atome_prompt", doc_id, "txt").read_text(encoding="utf-8")
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": (INSTRUCTION12 if v2 else INSTRUCTION) + "\n\nDokument:\n" + text}]


def fixed_answers(doc_id: str) -> dict[str, str]:
    """R1, R4, R5 -> furniture; R3 (picture atom or logo fragment) -> none."""
    out = {}
    for a, (role, rule) in hf.fixed_roles(doc_id)[0].items():
        if rule.startswith(("R1", "R4", "R5")):
            out[a] = "furniture"
        elif rule.startswith("R3"):
            out[a] = "none"
    return out


class Tokens:
    def __init__(self, tok, v2: bool = False):
        self.tok = tok
        self.v2 = v2
        self.answer_ids = []
        for letter, _, _ in (OPTIONS12 if v2 else OPTIONS):
            x = tok.encode(" " + letter, add_special_tokens=False)
            assert len(x) == 1, (letter, x)
            self.answer_ids.append(x[0])
        assert len(set(self.answer_ids)) == len(OPTIONS12 if v2 else OPTIONS)
        self.nl = tok.encode("\n", add_special_tokens=False)
        assert len(self.nl) == 1
        self.head = tok.encode("Zuordnung:\n", add_special_tokens=False)

    def prefix(self, doc_id: str) -> list[int]:
        p = list(self.tok.apply_chat_template(messages(doc_id, self.v2), add_generation_prompt=True,
                                              enable_thinking=False, return_dict=False))
        return p + self.head

    def repeat_sequence(self, doc_id: str, ids: list[str],
                        hints: dict[str, list[str]] | None = None) -> tuple[list[int], list[int]]:
        lines = {}
        for raw in iso_path("atome_prompt", doc_id, "txt").read_text(encoding="utf-8").splitlines():
            head = raw.split(" | ", 1)[0]
            if head in ids:
                lines[head] = raw
        seq = self.prefix(doc_id)
        pos = []
        for a in ids:
            h = (hints or {}).get(a) or []
            seq += self.tok.encode(lines.get(a, a) + (f" [{', '.join(h)}]" if h else "") + " ->",
                                   add_special_tokens=False)
            pos.append(len(seq) - 1)
            seq += self.nl
        return seq, pos


def hints_v2(doc_id: str, titles: dict) -> dict[str, list[str]]:
    """Layout hints of `m03_iso_hints.py` and "Seitenrand" for the fixed furniture atoms."""
    import m03_iso_hints as mh

    h = mh.hints(doc_id, titles)
    for a, x in fixed_answers(doc_id).items():
        if x == "furniture":
            h[a] = h.get(a, []) + ["Seitenrand"]
    return h


def reference(ref_dir: Path, doc_id: str) -> tuple[list[str], list[str]]:
    x = json.loads((ref_dir / f"{doc_id}.json").read_text(encoding="utf-8"))
    ids = [a["id"] for a in v4.atoms_of(doc_id)]
    assert x["ids"] == ids, doc_id
    assert all(a in ANSWERS for a in x["answers"]), doc_id
    return ids, x["answers"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", required=True)
    ap.add_argument("--ref", default="iso/v4/ref", help="reference folder, relative to the data root")
    args = ap.parse_args()
    from mlx_lm.utils import load_tokenizer

    tk = Tokens(load_tokenizer(MODEL))
    ids, answers = reference(DATA / args.ref, args.show)
    seq, pos = tk.repeat_sequence(args.show, ids)
    print(tk.tok.decode(seq[:400]))
    print(len(seq), len(pos), list(zip(ids, answers))[:12])


if __name__ == "__main__":
    main()
