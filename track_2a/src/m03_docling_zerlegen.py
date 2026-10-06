# SPDX-License-Identifier: Apache-2.0
"""3.3 Zerlegen mit Docling: PDF -> Blockliste mit Provenienz (Iteration 3).

Für jedes PDF:
  - Docling-Konvertierung (Layout-Modell, Tabellenstruktur, wahlweise OCR) mit Zeitmessung
  - Blockliste in Lesereihenfolge: Block-ID B1..Bn, Docling-Label, Inhaltsschicht (body /
    furniture), Seite, Rahmen (bbox), Text, Zeichenbereich im Gesamttext, Eltern-Gruppe
    (Liste, Schlüssel-Wert-Bereich, Bild), Anteil OCR-Zellen und OCR-Konfidenz
  - Kopf- und Fusszeilen werden markiert (`kopf_fuss`), nicht gelöscht (Grundsatz der konservativen
    Extraktion: nichts löschen, nur markieren)
  - Text eines Blocks (`text_quelle` = "zeilen"): die Textzellen des zugehörigen Layout-Clusters
    (Textschicht oder OCR) im Wortlaut, Zellen derselben Zeile durch Leerzeichen, Zeilen durch
    Zeilenumbruch getrennt, Trennstriche erhalten.
    Docling fügt Zeilen zusammen und entfernt Trennstriche am Zeilenende, auch echte Bindestriche
    (Doppelnamen, «Arbeits- und»); sein Text steht deshalb nur zusätzlich in `text_docling`.
    Stimmen Zeilen und Docling-Text ohne Leerraum und Trennstriche nicht überein oder fehlt der
    Cluster, gilt Doclings `orig` (`text_quelle` = "docling"). Listen behalten ihr Aufzählungszeichen.
  - Tabellen: Zellen mit Zeile, Spalte, Spannweite, Kopf-Merkmal, Text und Rahmen; der Blocktext
    ist die Zellfolge zeilenweise (Zellen durch Tabulator, Zeilen durch Zeilenumbruch getrennt)
  - Gesamttext = Blocktexte in Lesereihenfolge, getrennt durch eine Leerzeile; leere Blöcke
    (Bilder) erhalten einen leeren Bereich. Geprüft wird text_gesamt[a:b] == Blocktext.
  - Vollständigkeitsprüfung gegen `pdftotext -layout` (Poppler): Anteil der pdftotext-Wörter
    (Multimenge, klein geschrieben, NFKC, ohne weiche Trennstriche), der in den Blöcken
    wiedergefunden wird; dazu die Gegenrichtung und die Wortfolge-Ähnlichkeit (difflib auf den
    ersten 3000 Wörtern)

Ersatz-Backend: Rendert Doclings Standard-Backend (docling-parse) eine Seite einfarbig, wird das
Dokument mit dem pypdfium2-Backend wiederholt (Feld `backend`, Anlass G06 = 882087).

Koordinaten: PDF-Punkte, Ursprung oben links, bbox = [links, oben, rechts, unten].

Ausgabe:
  - <ausgabe>/<doc_id>.json je Dokument (Standard <data>/docling/)
  - <data>/analyse/docling/lauf_<name>.csv (eine Zeile je Dokument: Laufzeit, Seiten, Status,
    Speicher, Blöcke je Label, Prüfwerte, Docling-Zeiten je Stufe)
  - <data>/analyse/docling/lauf_<name>.json (Konfiguration, Versionen, Initialisierung, Summen)

OCR-Engine (--ocr-engine): standard = ocrmac (Apple Vision, nur macOS, geschlossene Gewichte), wenn
installiert, sonst die automatische Wahl von Docling; ocrmac oder auto erzwingen eine Engine. Die
Ausgabe hält die Engine fest (konfiguration.ocr_engine). Atome von Scans können sich mit einer
anderen Engine ändern. Alle Scans der Entwicklungsgruppen liefen mit ocrmac.

pdftotext: die Umgebungsvariable PDFTOTEXT, sonst pdftotext im PATH (Poppler).

Aufruf (Hauptlauf, OCR automatisch, Gerät automatisch; im Ordner track_2a):
  uv run python src/m03_docling_zerlegen.py
Varianten:
  --ocr aus|auto|voll   (voll = OCR der ganzen Seite, Textschicht wird ignoriert)
  --ocr-engine standard|ocrmac|auto
  --geraet auto|cpu|mps
  --tabellen genau|schnell|aus   --zellabgleich an|aus
  --name <laufname> --ausgabe <ordner>   (ein relativer <ordner> liegt unter dem Datenordner <data>)
  PDFs oder doc_ids als Argumente, sonst alle unter <data>/pdf/augenschein/

Das Apertus-Modell wird nicht geladen.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import importlib.metadata as md
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
PDFDIR = DATA / "pdf/augenschein"
AUSGABE = DATA / "docling"
ANALYSE = DATA / "analyse/docling"
PDFTOTEXT = os.environ.get("PDFTOTEXT") or shutil.which("pdftotext") or "pdftotext"
OCR_ENGINE = "standard"   # standard | ocrmac | auto (Argument --ocr-engine)

TRENNER = "\n\n"
OCR_SPRACHEN = ["de-DE", "fr-FR", "it-IT", "en-US"]
KOPF_FUSS = {"page_header": "kopf", "page_footer": "fuss"}
LABELS_CSV = [
    "text", "section_header", "title", "list_item", "table", "picture", "caption", "footnote",
    "page_header", "page_footer", "key_value_region", "form", "code", "formula", "document_index",
    "checkbox_selected", "checkbox_unselected", "handwritten_text", "andere",
]
STUFEN = ["pipeline_total", "doc_build", "doc_assemble", "page_init", "page_parse", "layout",
          "table_structure", "ocr", "page_assemble", "reading_order"]


# ---------------------------------------------------------------- Hilfen


def versionen() -> dict:
    out = {}
    for p in ["docling", "docling-core", "docling-parse", "docling-ibm-models", "torch", "ocrmac"]:
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = None
    try:
        out["pdftotext"] = subprocess.run([PDFTOTEXT, "-v"], capture_output=True, text=True).stderr.split("\n")[0]
    except OSError:
        out["pdftotext"] = None
    return out


def sha256(pfad: Path) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for teil in iter(lambda: f.read(1 << 20), b""):
            h.update(teil)
    return h.hexdigest()


def normtext(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("­", "")
    return s.lower()


def woerter(s: str) -> list[str]:
    """Wörter inkl. Zahlen (Daten, Geschäftsnummern zählen für die Vollständigkeit)."""
    return re.findall(r"\w+", normtext(s))


def pdftotext_layout(pfad: Path) -> str:
    r = subprocess.run([PDFTOTEXT, "-layout", "-enc", "UTF-8", str(pfad), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def vollstaendigkeit(bloecke_text: str, pt: str) -> dict:
    pw, bw = woerter(pt), woerter(bloecke_text)
    cp, cb = Counter(pw), Counter(bw)
    gemeinsam = sum((cp & cb).values())
    fehlend = cp - cb
    # Silbentrennung: Docling kann "Wort-\nteil" zu "Wortteil" zusammenziehen; solche Paare
    # zählen als gefunden, wenn die zusammengesetzte Form in den Blöcken steht.
    getrennt_gefunden = 0
    for a, b in re.findall(r"(\w+)-\s*\n\s*(\w+)", normtext(pt)):
        if fehlend[a] > 0 and fehlend[b] > 0 and cb[a + b] > 0:
            fehlend[a] -= 1
            fehlend[b] -= 1
            getrennt_gefunden += 2
    fehlend = +fehlend
    gefunden = sum(cp.values()) - sum(fehlend.values())
    sm = difflib.SequenceMatcher(None, bw[:3000], pw[:3000], autojunk=False) if (pw and bw) else None
    # Gegenprobe unabhängig von Wortgrenzen (Sperrschrift, verlorene Leerzeichen): 5-Gramme der
    # Zeichen ohne Leerraum und ohne Trennstriche
    def gramme(t: str) -> Counter:
        k = re.sub(r"[\s\-]", "", normtext(t))
        return Counter(k[i:i + 5] for i in range(max(0, len(k) - 4)))
    gp, gb = gramme(pt), gramme(bloecke_text)
    return {
        "pdftotext_woerter": len(pw),
        "bloecke_woerter": len(bw),
        "wiedergefunden": gefunden,
        "anteil_pdftotext_in_bloecken": round(gefunden / len(pw), 4) if pw else None,
        "davon_ueber_silbentrennung": getrennt_gefunden,
        "anteil_bloecke_in_pdftotext": round(gemeinsam / len(bw), 4) if (bw and pw) else None,
        "wortfolge_aehnlichkeit": round(sm.ratio(), 4) if sm else None,
        "anteil_5gramme_pdftotext_in_bloecken": round(sum((gp & gb).values()) / sum(gp.values()), 4) if gp else None,
        "fehlend_haeufigste": [[w, n] for w, n in fehlend.most_common(25)],
    }


def bbox_oben_links(bbox, seitenhoehe: float) -> list[float]:
    b = bbox.to_top_left_origin(page_height=seitenhoehe)
    return [round(b.l, 2), round(b.t, 2), round(b.r, 2), round(b.b, 2)]


# ---------------------------------------------------------------- Docling


def baue_konverter(ocr: str, geraet: str, threads: int, tabellen: str, sprachen: list[str],
                   backend: str = "parse", zellabgleich: bool = True):
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        OcrAutoOptions,
        OcrMacOptions,
        OcrMode,
        PdfPipelineOptions,
        TableFormerMode,
    )
    from docling.datamodel.settings import settings
    from docling.document_converter import DocumentConverter, PdfFormatOption

    settings.debug.profile_pipeline_timings = True
    opts = PdfPipelineOptions()
    opts.accelerator_options = AcceleratorOptions(num_threads=threads, device=AcceleratorDevice(geraet))
    opts.document_timeout = 900
    opts.do_table_structure = tabellen != "aus"
    if tabellen != "aus":
        opts.table_structure_options.mode = TableFormerMode.FAST if tabellen == "schnell" else TableFormerMode.ACCURATE
        opts.table_structure_options.do_cell_matching = zellabgleich
    engine = "keine"
    if ocr == "aus":
        opts.do_ocr = False
    else:
        opts.do_ocr = True
        modus = OcrMode.FULL_PAGE if ocr == "voll" else OcrMode.DEFAULT
        try:
            if OCR_ENGINE == "auto":
                raise ImportError("auto")
            import ocrmac  # noqa: F401

            opts.ocr_options = OcrMacOptions(mode=modus, lang=sprachen, recognition="accurate", framework="vision")
            engine = "ocrmac (Apple Vision, accurate)"
        except ImportError:
            if OCR_ENGINE == "ocrmac":
                raise SystemExit("--ocr-engine ocrmac: ocrmac is not installed (macOS only)")
            opts.ocr_options = OcrAutoOptions(mode=modus, lang=sprachen)
            engine = "auto"
    # Seitenbilder behalten (Massstab 1), um einfarbig gerenderte Seiten zu erkennen (siehe main)
    opts.generate_page_images = True
    opts.images_scale = 1.0
    fo = {"pipeline_options": opts}
    if backend == "pdfium":
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        fo["backend"] = PyPdfiumDocumentBackend
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(**fo)})
    konfig = {
        "ocr": ocr, "ocr_engine": engine, "ocr_sprachen": sprachen if ocr != "aus" else [],
        "geraet": geraet, "threads": threads, "tabellen": tabellen, "zellabgleich": zellabgleich,
        "backend": "pypdfium2" if backend == "pdfium" else "docling-parse",
        "layout_modell": opts.layout_options.model_spec.name,
        "document_timeout_s": opts.document_timeout,
    }
    return conv, konfig


def cluster_info(res) -> dict[int, list[dict]]:
    """Je Seite die Layout-Cluster mit Rahmen (oben links) und Textzeilen-Zellen.

    Zellen sind die Textzeilen der PDF-Textschicht bzw. der OCR, im Wortlaut vor Doclings
    Zusammenfügen (Zeilenumbrüche und Trennstriche erhalten). Kind-Cluster (z.B. Text in Bildern)
    werden für die Zuordnung zu Blöcken mitgeführt, für die Seitensummen aber nur die oberste
    Ebene gezählt, damit keine Zelle doppelt zählt.
    """
    out: dict[int, list[dict]] = {}
    for page in res.pages:
        if not (page.predictions and page.predictions.layout):
            continue
        liste = []
        stapel = [(c, True) for c in page.predictions.layout.clusters]
        while stapel:
            c, oben = stapel.pop()
            stapel.extend((k, False) for k in (c.children or []))
            zellen = sorted(c.cells, key=lambda z: z.index)
            liste.append({"bbox": c.bbox, "oben": oben, "zellen": zellen})
        out[page.page_no] = liste  # Page.page_no ist in Docling 2.133 bereits 1-basiert
    return out


def cluster_fuer_prov(clusters: list[dict], bbox_tl) -> dict | None:
    """Cluster mit der grössten Überdeckung (IoU >= 0.5) zum Rahmen eines Blocks."""
    bester, iou_max = None, 0.0
    for c in clusters:
        iou = c["bbox"].intersection_over_union(bbox_tl)
        if iou > iou_max:
            bester, iou_max = c, iou
    return bester if iou_max >= 0.5 else None


def zeilen_aus_zellen(zellen: list) -> list[str]:
    """Textzellen (Reihenfolge nach Index) zu Zeilen: Zellen auf derselben Grundlinie (vertikale
    Überdeckung mindestens die halbe Zellhöhe) werden mit Leerzeichen verbunden, sonst beginnt
    eine neue Zeile. docling-parse teilt eine Zeile teils in mehrere Zellen (Aufzählungszeichen,
    Spalten eines Formulars)."""
    zeilen: list[str] = []
    vorher = None
    for z in zellen:
        t = z.orig.strip()
        if not t:
            continue
        bb = z.rect.to_bounding_box().to_top_left_origin(page_height=1e6) if z.rect else None
        gleiche_zeile = False
        if vorher is not None and bb is not None:
            ueberdeckung = min(bb.b, vorher.b) - max(bb.t, vorher.t)
            hoehe = min(bb.b - bb.t, vorher.b - vorher.t)
            gleiche_zeile = hoehe > 0 and ueberdeckung >= 0.5 * hoehe and bb.l >= vorher.l
        if gleiche_zeile and zeilen:
            zeilen[-1] = zeilen[-1] + " " + t
        else:
            zeilen.append(t)
        vorher = bb
    return zeilen


def kern(s: str) -> str:
    """Vergleichsform: ohne Leerraum und Trennstriche (Docling fügt Zeilen und Silben zusammen)."""
    return re.sub(r"[\s\-\u00ad\u2010\u2011]", "", unicodedata.normalize("NFKC", s))


def tabelle(item, doc, seitenhoehe: dict[int, float]) -> tuple[dict, str]:
    data = item.data
    zellen = sorted(data.table_cells, key=lambda z: (z.start_row_offset_idx, z.start_col_offset_idx))
    seite = item.prov[0].page_no if item.prov else None
    zl = []
    for z in zellen:
        bb = None
        if z.bbox is not None and seite is not None:
            bb = bbox_oben_links(z.bbox, seitenhoehe[seite])
        zl.append({
            "zeile": z.start_row_offset_idx, "spalte": z.start_col_offset_idx,
            "zeilen_spann": z.row_span, "spalten_spann": z.col_span,
            "spaltenkopf": z.column_header, "zeilenkopf": z.row_header,
            "text": z.text, "bbox": bb,
        })
    zeilen = []
    for r in range(data.num_rows):
        teile = [z["text"] for z in zl if z["zeile"] == r and z["text"]]
        if teile:
            zeilen.append("\t".join(teile))
    return {"zeilen": data.num_rows, "spalten": data.num_cols, "zellen": zl}, "\n".join(zeilen)


def einfarbige_seiten(res) -> list[int]:
    """Seiten, deren Seitenbild einfarbig ist (Spannweite je Farbkanal <= 2).

    Beobachtet bei G06 (882087): Das Standard-Backend (docling-parse) rendert den Scan als gelbe
    Fläche, das Layout-Modell sieht dann nichts. pypdfium2 und Poppler rendern die Seite richtig.
    """
    out = []
    for nr, pg in sorted(res.document.pages.items()):
        if pg.image is None or pg.image.pil_image is None:
            continue
        ext = pg.image.pil_image.getextrema()
        if not isinstance(ext[0], tuple):
            ext = (ext,)
        if all(hi - lo <= 2 for lo, hi in ext):
            out.append(nr)
    return out


def bloecke_aus(res) -> tuple[list[dict], list[dict], str]:
    from docling_core.types.doc import BoundingBox, ContentLayer, CoordOrigin
    from docling_core.types.doc.document import GroupItem, ListItem, TableItem

    doc = res.document
    seiten = {}
    for nr, p in sorted(doc.pages.items()):
        seiten[nr] = {"seite": nr, "breite": round(p.size.width, 2), "hoehe": round(p.size.height, 2)}
    seitenhoehe = {nr: s["hoehe"] for nr, s in seiten.items()}
    clinfo = cluster_info(res)

    bloecke = []
    for item, _lvl in doc.iterate_items(included_content_layers=set(ContentLayer), traverse_pictures=True,
                                        with_groups=False):
        label = item.label.value
        b = {
            "id": None,
            "docling_ref": item.self_ref,
            "label": label,
            "schicht": item.content_layer.value,
            "kopf_fuss": KOPF_FUSS.get(label),
        }
        eltern = item.parent.resolve(doc) if item.parent else None
        if eltern is not None and eltern.self_ref != "#/body":
            b["eltern"] = {"ref": eltern.self_ref, "label": eltern.label.value if hasattr(eltern, "label") else None,
                           "gruppe": isinstance(eltern, GroupItem)}
        else:
            b["eltern"] = None
        # Rahmen und Zellen je Provenienz-Eintrag (ein Block kann über Seiten laufen)
        prov, zeilen_je_prov = [], []
        n_zellen = n_ocr = 0
        konf = []
        for p in item.prov:
            bb = bbox_oben_links(p.bbox, seitenhoehe[p.page_no])
            prov.append({"seite": p.page_no, "bbox": bb, "zeichen_docling": list(p.charspan)})
            bb_tl = BoundingBox(l=bb[0], t=bb[1], r=bb[2], b=bb[3], coord_origin=CoordOrigin.TOPLEFT)
            c = cluster_fuer_prov(clinfo.get(p.page_no, []), bb_tl)
            zellen = c["zellen"] if c else []
            zeilen_je_prov.append(zeilen_aus_zellen(zellen))
            n_zellen += len(zellen)
            for z in zellen:
                if z.from_ocr:
                    n_ocr += 1
                    konf.append(z.confidence)
        if isinstance(item, TableItem):
            b["tabelle"], text = tabelle(item, doc, seitenhoehe)
            b["text_quelle"] = "tabellenzellen"
        else:
            orig = getattr(item, "orig", None) or getattr(item, "text", "") or ""
            zeilen_text = "\n".join(z for zl in zeilen_je_prov for z in zl)
            kz = kern(zeilen_text)
            # Listen: Docling ersetzt teils das Aufzählungszeichen (z.B. "o" -> "·"); der Zeilentext
            # gilt, wenn er bis auf ein kurzes Präfix mit Doclings Text ohne Marker übereinstimmt.
            listen_ok = (isinstance(item, ListItem) and kz and kz.endswith(kern(item.text))
                         and len(kz) - len(kern(item.text)) <= 4)
            if zeilen_text and (kz == kern(orig) or listen_ok):
                text = zeilen_text
                b["text_quelle"] = "zeilen"
            else:
                text = orig
                b["text_quelle"] = "docling"
            if orig != text:
                b["text_docling"] = orig
            td = getattr(item, "text", None)
            if td is not None and td != orig and td != text:
                b["text_docling_normalisiert"] = td
        b["text"] = text
        if isinstance(item, ListItem):
            b["liste"] = {"marker": item.marker, "nummeriert": item.enumerated}
        b["seite"] = prov[0]["seite"] if prov else None
        b["bbox"] = prov[0]["bbox"] if prov else None
        if len(prov) > 1:
            b["prov"] = prov
            b["_zeilen_je_prov"] = zeilen_je_prov
        b["ocr_anteil"] = round(n_ocr / n_zellen, 3) if n_zellen else None
        b["ocr_konfidenz"] = round(sum(konf) / len(konf), 3) if konf else None
        bloecke.append(b)

    # IDs und Zeichenbereiche
    teile, pos = [], 0
    for i, b in enumerate(bloecke, 1):
        b["id"] = f"B{i}"
        t = b["text"]
        if t:
            if teile:
                teile.append(TRENNER)
                pos += len(TRENNER)
            b["zeichen"] = [pos, pos + len(t)]
            teile.append(t)
            pos += len(t)
        else:
            b["zeichen"] = [pos, pos]
        if "prov" in b:
            # Zeichenbereich je Seite: bei Zeilentext aus den Zeilen je Provenienz-Eintrag,
            # sonst aus Doclings charspan (bezieht sich auf Doclings Text)
            start = b["zeichen"][0]
            if b["text_quelle"] == "zeilen":
                for p, zl in zip(b["prov"], b.pop("_zeilen_je_prov")):
                    lang = len("\n".join(zl))
                    p["zeichen"] = [start, start + lang]
                    start += lang + (1 if zl else 0)
            else:
                b.pop("_zeilen_je_prov", None)
                for p in b["prov"]:
                    a, e = p["zeichen_docling"]
                    if 0 <= a <= e <= len(t):
                        p["zeichen"] = [start + a, start + e]
        b.pop("_zeilen_je_prov", None)
    gesamt = "".join(teile)
    for b in bloecke:
        a, e = b["zeichen"]
        assert gesamt[a:e] == b["text"], b["id"]
    # Seiten: Textquelle aus den OCR-Anteilen der Cluster
    for nr, s in seiten.items():
        cl = [c for c in clinfo.get(nr, []) if c["oben"]]
        nz = sum(len(c["zellen"]) for c in cl)
        no = sum(sum(1 for z in c["zellen"] if z.from_ocr) for c in cl)
        s["zellen"] = nz
        s["ocr_zellen"] = no
        s["textquelle"] = "leer" if nz == 0 else ("ocr" if no == nz else ("pdf" if no == 0 else "gemischt"))
    return bloecke, list(seiten.values()), gesamt


# ---------------------------------------------------------------- Lauf


def mps_speicher() -> int | None:
    try:
        import torch

        if torch.backends.mps.is_available():
            return int(torch.mps.driver_allocated_memory())
    except Exception:
        return None
    return None


def max_rss() -> int:
    # ru_maxrss: macOS in Bytes, Linux in Kilobytes
    wert = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return wert if sys.platform == "darwin" else wert * 1024


def finde_pdfs(argumente: list[str]) -> list[Path]:
    if not argumente:
        return sorted(PDFDIR.glob("*.pdf"), key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)
    out = []
    for a in argumente:
        p = Path(a)
        if p.suffix.lower() == ".pdf" and p.exists():
            out.append(p.resolve())
        else:
            out.append(PDFDIR / f"{a}.pdf")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="*")
    ap.add_argument("--ocr", choices=["aus", "auto", "voll"], default="auto")
    ap.add_argument("--ocr-engine", choices=["standard", "ocrmac", "auto"], default="standard")
    ap.add_argument("--geraet", choices=["auto", "cpu", "mps"], default="auto")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--tabellen", choices=["genau", "schnell", "aus"], default="genau")
    ap.add_argument("--zellabgleich", choices=["an", "aus"], default="an",
                    help="TableFormer: Tabellenzellen mit den Textzellen der PDF-Schicht abgleichen (Docling-Standard)")
    ap.add_argument("--sprachen", default=",".join(OCR_SPRACHEN),
                    help="OCR-Sprachen in Vorzugsreihenfolge (BCP 47), leer = Standard der Engine")
    ap.add_argument("--name", default=None, help="Laufname für die Messdateien")
    ap.add_argument("--ausgabe", default=str(AUSGABE))
    ap.add_argument("--ohne-aufwaermen", action="store_true")
    ap.add_argument("--ohne-ersatz", action="store_true",
                    help="kein Ersatz-Backend bei einfarbig gerenderten Seiten (nur zum Vergleich)")
    args = ap.parse_args()
    global OCR_ENGINE
    OCR_ENGINE = args.ocr_engine

    name = args.name or f"ocr-{args.ocr}_geraet-{args.geraet}"
    ausgabe = Path(args.ausgabe).expanduser()
    if not ausgabe.is_absolute():
        ausgabe = DATA / ausgabe
    ausgabe.mkdir(parents=True, exist_ok=True)
    ANALYSE.mkdir(parents=True, exist_ok=True)
    pdfs = finde_pdfs(args.pdfs)
    sprachen = [s for s in args.sprachen.split(",") if s]

    t0 = time.perf_counter()
    from docling.datamodel.base_models import InputFormat

    zellabgleich = args.zellabgleich == "an"
    conv, konfig = baue_konverter(args.ocr, args.geraet, args.threads, args.tabellen, sprachen,
                                  zellabgleich=zellabgleich)
    conv_ersatz = None  # pypdfium2-Backend, erst bei Bedarf
    conv.initialize_pipeline(InputFormat.PDF)
    t_init = time.perf_counter() - t0
    rss_init = max_rss()

    t_auf = None
    if not args.ohne_aufwaermen and pdfs:
        kleinste = min(pdfs, key=lambda p: p.stat().st_size)
        t1 = time.perf_counter()
        conv.convert(kleinste, raises_on_error=False)
        t_auf = time.perf_counter() - t1

    vers = versionen()
    zeilen = []
    mps_max = mps_speicher() or 0
    for pfad in pdfs:
        doc_id = pfad.stem
        t1 = time.perf_counter()
        fehler = []
        try:
            res = conv.convert(pfad, raises_on_error=False)
        except Exception as e:  # noqa: BLE001
            res = None
            fehler.append(f"{type(e).__name__}: {e}")
        dauer = time.perf_counter() - t1
        rss = max_rss()
        mps = mps_speicher()
        if mps:
            mps_max = max(mps_max, mps)
        zeile = {"doc_id": doc_id, "sekunden": round(dauer, 3), "max_rss_mb": round(rss / 2**20, 1),
                 "mps_mb": round(mps / 2**20, 1) if mps else ""}
        if res is None:
            zeile.update({"status": "abbruch", "fehler": " | ".join(fehler)})
            zeilen.append(zeile)
            print(doc_id, "ABBRUCH", fehler, flush=True)
            continue
        # Ersatz-Backend, wenn eine Seite einfarbig gerendert wurde, obwohl die Datei Text oder
        # Bilder hat (Seite ist dann für Layout und OCR leer)
        einfarbig = einfarbige_seiten(res) if res.status.value in ("success", "partial_success") else []
        backend = konfig["backend"]
        if einfarbig and not args.ohne_ersatz:
            if conv_ersatz is None:
                conv_ersatz, _ = baue_konverter(args.ocr, args.geraet, args.threads, args.tabellen, sprachen,
                                                backend="pdfium", zellabgleich=zellabgleich)
            t2 = time.perf_counter()
            res2 = conv_ersatz.convert(pfad, raises_on_error=False)
            if res2.status.value in ("success", "partial_success") and len(einfarbige_seiten(res2)) < len(einfarbig):
                res = res2
                backend = "pypdfium2 (Ersatz)"
            dauer += time.perf_counter() - t2
            zeile["sekunden"] = round(dauer, 3)
        status = res.status.value
        fehler += [f"{e.component_type.value}: {e.error_message}" for e in res.errors]
        bloecke, seiten, gesamt = bloecke_aus(res)
        pt = pdftotext_layout(pfad)
        pruef = vollstaendigkeit(gesamt, pt)
        n_seiten = len(res.pages) or len(seiten)
        zeiten = {}
        for k, v in (res.timings or {}).items():
            try:
                zeiten[k] = round(sum(v.times), 3)
            except AttributeError:
                pass
        aus = {
            "doc_id": doc_id,
            "quelle": rel(pfad),
            "sha256": sha256(pfad),
            "erzeugt_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "skript": "src/m03_docling_zerlegen.py",
            "lauf": name,
            "werkzeug": vers,
            "konfiguration": konfig,
            "koordinaten": "PDF-Punkte, Ursprung oben links, bbox = [links, oben, rechts, unten]",
            "gesamttext_trenner": TRENNER,
            "status": status,
            "backend": backend,
            "einfarbige_seiten_standard_backend": einfarbig,
            "fehler": fehler,
            "laufzeit_s": round(dauer, 3),
            "seiten": seiten,
            "bloecke": bloecke,
            "text_gesamt": gesamt,
            "pruefung": pruef,
        }
        with open(ausgabe / f"{doc_id}.json", "w", encoding="utf-8") as f:
            json.dump(aus, f, ensure_ascii=False, indent=1)
        labels = Counter(b["label"] for b in bloecke)
        zeile.update({
            "status": status,
            "backend": backend,
            "einfarbige_seiten": len(einfarbig),
            "fehler": " | ".join(fehler),
            "seiten": n_seiten,
            "s_pro_seite": round(dauer / n_seiten, 3) if n_seiten else "",
            "seiten_ocr": sum(1 for s in seiten if s["textquelle"] == "ocr"),
            "seiten_gemischt": sum(1 for s in seiten if s["textquelle"] == "gemischt"),
            "bloecke": len(bloecke),
            "bloecke_mehrseitig": sum(1 for b in bloecke if "prov" in b),
            "bloecke_ohne_prov": sum(1 for b in bloecke if b["seite"] is None),
            "bloecke_mit_ocr": sum(1 for b in bloecke if (b["ocr_anteil"] or 0) > 0),
            "kopf": sum(1 for b in bloecke if b["kopf_fuss"] == "kopf"),
            "fuss": sum(1 for b in bloecke if b["kopf_fuss"] == "fuss"),
            "tabellen_zellen": sum(len(b["tabelle"]["zellen"]) for b in bloecke if "tabelle" in b),
            "text_zeichen": len(gesamt),
        })
        for lab in LABELS_CSV:
            zeile[f"n_{lab}"] = labels.get(lab, 0) if lab != "andere" else sum(
                n for k, n in labels.items() if k not in LABELS_CSV)
        for k in ["pdftotext_woerter", "bloecke_woerter", "anteil_pdftotext_in_bloecken",
                  "anteil_5gramme_pdftotext_in_bloecken",
                  "anteil_bloecke_in_pdftotext", "wortfolge_aehnlichkeit", "davon_ueber_silbentrennung"]:
            zeile[k] = pruef[k] if pruef[k] is not None else ""
        for k in STUFEN:
            zeile[f"t_{k}"] = zeiten.get(k, "")
        zeilen.append(zeile)
        print(f"{doc_id:>7} {status:8} {n_seiten:3d} S. {dauer:7.2f} s {dauer / max(1, n_seiten):5.2f} s/S. "
              f"{len(bloecke):4d} Bl. voll={pruef['anteil_pdftotext_in_bloecken']} "
              f"rss={rss / 2**30:.2f} GB", flush=True)

    t_gesamt = time.perf_counter() - t0
    felder = []
    for z in zeilen:
        for k in z:
            if k not in felder:
                felder.append(k)
    with open(ANALYSE / f"lauf_{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder)
        w.writeheader()
        w.writerows(zeilen)
    ok = [z for z in zeilen if z.get("status") == "success"]
    zusammenfassung = {
        "lauf": name,
        "erzeugt_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "konfiguration": konfig,
        "werkzeug": vers,
        "plattform": {"python": sys.version.split()[0], "system": sys.platform},
        "ausgabe": rel(ausgabe),
        "dokumente": len(zeilen),
        "erfolgreich": len(ok),
        "seiten": sum(z.get("seiten", 0) or 0 for z in zeilen),
        "init_s": round(t_init, 2),
        "aufwaermen_s": round(t_auf, 2) if t_auf is not None else None,
        "summe_konvertierung_s": round(sum(z["sekunden"] for z in zeilen), 2),
        "gesamt_s": round(t_gesamt, 2),
        "max_rss_init_mb": round(rss_init / 2**20, 1),
        "max_rss_mb": round(max_rss() / 2**20, 1),
        "mps_max_mb": round(mps_max / 2**20, 1) if mps_max else None,
    }
    with open(ANALYSE / f"lauf_{name}.json", "w", encoding="utf-8") as f:
        json.dump(zusammenfassung, f, ensure_ascii=False, indent=1)
    print(json.dumps(zusammenfassung, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
