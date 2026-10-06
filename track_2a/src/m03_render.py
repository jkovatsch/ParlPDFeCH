# SPDX-License-Identifier: Apache-2.0
"""Blockform eines Docling-Dokuments: Blöcke vorbereiten und als Text darstellen.

Reines Hilfsmodul ohne Netz- und Datenzugriff. m03_atome.py nutzt FORM und ELTERN (deutsche
Bezeichnungen der Docling-Formen in den Hinweisen der Atome) und bloecke_vorbereiten() mit
dokument_rendern() für die Schätzung der Tokens der Blockform (Spalte blockformat_tokens_schaetzung).

- bloecke_vorbereiten(): Blöcke aus <data>/docling/<id>.json (m03_docling_zerlegen.py), lange
  Antwortblöcke an Antwortmarkern geteilt (Unter-IDs B25.1, B25.2 …, die übrigen IDs bleiben)
- dokument_rendern(): Blockliste als Text, je Block «[ID] (Form, Merkmale) Text»

Herkunft: der Teil «Blöcke vorbereiten» und «Eingabe rendern» eines Moduls des privaten Projekts,
das nicht in diesem Repository ist. Der Code ist unverändert; nur die Kommentare sind angepasst.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------- Blöcke vorbereiten

# Antwortmarker am Zeilenanfang (de, fr, it, rm). Gedruckte Nummern sind kein verlässlicher
# Schlüssel; geteilt wird nur, damit die Blockform einzelne Antworten zeigen kann. Die Teilung
# ordnet nichts zu.
ANTWORTMARKER = re.compile(
    r"^\s*(zu (den )?(frage|fragen|ziffer|ziffern|punkt|punkten)\s+\d|"
    r"ad (frage |ziffer |punkt |domanda )?\d+\s*[:.)]|antwort (auf|zu) (frage )?\d|"
    r"frage \d+\s*[:.)]|r[ée]ponse (à |a )?(la )?(question )?\d|"
    r"(à |a )?(la )?question \d+\s*[:.)]|risposta (alla )?(domanda )?\d|domanda \d+\s*[:.)]|"
    r"tar la dumonda \d|dumonda \d+\s*[:.)])",
    re.I)
TEILEN_AB_ZEICHEN = 800      # nur längere Blöcke werden geteilt
TEILEN_LABELS = {"text", "list_item"}


def _teile_an_markern(text: str) -> list[tuple[int, int]]:
    """Zeichenbereiche der Teile, wenn der Text mindestens zwei Antwortmarker an
    Zeilenanfängen hat; sonst leere Liste."""
    starts = []
    pos = 0
    for zeile in text.split("\n"):
        if ANTWORTMARKER.match(zeile):
            starts.append(pos)
        pos += len(zeile) + 1
    if len(starts) < 2:
        return []
    if text[:starts[0]].strip():
        starts = [0] + starts
    grenzen = starts + [len(text)]
    return [(grenzen[i], grenzen[i + 1]) for i in range(len(starts))]


def bloecke_vorbereiten(dok: dict, teilen: bool = True) -> list[dict]:
    """Blöcke eines Docling-JSON (m03_docling_zerlegen.py) für die Blockform.

    Je Block: id, label, seite, kopf_fuss, eltern (Label der Gruppe), liste (nummeriert),
    ocr (Anteil ≥ 0,5), text (Wortlaut aus den Textzellen), zeichen, teil_von.
    Lange Text- oder Listenblöcke mit mindestens zwei Antwortmarkern werden geteilt; die
    Teile heissen <ID>.1, <ID>.2 …, ihr Zeichenbereich bezieht sich auf text_gesamt.
    """
    if dok.get("status") != "success":
        raise ValueError(f"Docling-Status {dok.get('status')!r}, Dokument {dok.get('doc_id')}")
    aus = []
    for b in dok["bloecke"]:
        text = b.get("text") or ""
        basis = {
            "id": b["id"], "label": b.get("label") or "", "seite": b.get("seite"),
            "kopf_fuss": b.get("kopf_fuss"),
            "eltern": (b.get("eltern") or {}).get("label"),
            "liste_nummeriert": bool((b.get("liste") or {}).get("nummeriert")),
            "ocr": (b.get("ocr_anteil") or 0) >= 0.5,
            "teil_von": None,
        }
        z0 = (b.get("zeichen") or [0, 0])[0]
        teile = (_teile_an_markern(text) if teilen and basis["label"] in TEILEN_LABELS
                 and len(text) >= TEILEN_AB_ZEICHEN else [])
        if not teile:
            aus.append(basis | {"text": text, "zeichen": b.get("zeichen")})
            continue
        for k, (a, e) in enumerate(teile, 1):
            stueck = text[a:e]
            rechts = len(stueck.rstrip())
            aus.append(basis | {"id": f"{b['id']}.{k}", "teil_von": b["id"],
                                "text": stueck[:rechts], "zeichen": [z0 + a, z0 + a + rechts]})
    return aus


# ---------------------------------------------------------------- Eingabe rendern

FORM = {
    "section_header": "Überschrift", "title": "Überschrift", "text": "Text",
    "list_item": "Listenpunkt", "page_header": "Kopfzeile", "page_footer": "Fusszeile",
    "picture": "Bild", "footnote": "Fussnote", "table": "Tabelle", "caption": "Bildlegende",
    "document_index": "Verzeichnis", "checkbox_selected": "Kästchen angekreuzt",
    "checkbox_unselected": "Kästchen leer", "formula": "Formel", "code": "Code",
}
ELTERN = {"key_value_area": "Feld", "form_area": "Formular", "picture": "im Bild"}
MAX_ZEICHEN_BLOCK = 2000
KOPF_ZEICHEN, FUSS_ZEICHEN = 1500, 400


def _anzeigetext(b: dict, max_zeichen: int) -> str:
    t = b["text"] or ""
    if b["label"] == "table":
        zeilen = [" | ".join(c.strip() for c in z.split("\t")) for z in t.split("\n") if z.strip()]
        t = " / ".join(zeilen)
    else:
        t = re.sub(r"(\w)-\n(?=[a-zäöüàéèç])", r"\1", t)   # nur Anzeige; Wortlaut bleibt im Block
        t = re.sub(r"\s*\n\s*", " ", t)
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    if not t:
        return "(ohne Text)"
    if len(t) > max_zeichen:
        t = (t[:KOPF_ZEICHEN].rstrip() + f" […{len(t) - KOPF_ZEICHEN - FUSS_ZEICHEN} Zeichen "
             "ausgelassen…] " + t[-FUSS_ZEICHEN:].lstrip())
    return t


def dokument_rendern(bloecke: list[dict], max_zeichen_block: int = MAX_ZEICHEN_BLOCK) -> str:
    """Blockliste als Text: Seitenmarken, je Block «[ID] (Form, Merkmale) Text»."""
    zeilen = []
    seite = None
    for b in bloecke:
        if b["seite"] != seite:
            seite = b["seite"]
            zeilen.append(f"=== Seite {seite} ===")
        merkmale = [FORM.get(b["label"], b["label"] or "Block")]
        if b["eltern"] in ELTERN:
            merkmale.append(ELTERN[b["eltern"]])
        if b["label"] == "list_item" and b["liste_nummeriert"]:
            merkmale.append("nummeriert")
        if b["ocr"]:
            merkmale.append("OCR")
        zeilen.append(f"[{b['id']}] ({', '.join(merkmale)}) {_anzeigetext(b, max_zeichen_block)}")
    return "\n".join(zeilen)
