# SPDX-License-Identifier: Apache-2.0
"""Paths of the isolation inputs for one document (process rule 6: test documents stay separate).

Development documents: daten/iso/<kind>/. Test documents (split role "Gold", human gold set):
daten/gold/test/<kind>/. A glob over daten/iso/<kind>/ never finds a test document; a script that
reads a test document must name it by its id.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "daten/iso"
TEST = ROOT / "daten/gold/test"


def iso_path(kind: str, doc_id: str, ext: str = "json") -> Path:
    """kind: atome, docling or atome_prompt."""
    p = DEV / kind / f"{doc_id}.{ext}"
    if p.exists():
        return p
    q = TEST / kind / f"{doc_id}.{ext}"
    return q if q.exists() else p


PDF_DIRS = [ROOT / "daten/pdf/lehrer_stichprobe", ROOT / "daten/pdf/bulk", TEST / "pdf"]


def pdf_path(doc_id: str) -> Path:
    """The PDF of a document: teacher sample, bulk download, or test PDFs (daten/gold/test/pdf)."""
    for d in PDF_DIRS:
        p = d / f"{doc_id}.pdf"
        if p.exists():
            return p
    return PDF_DIRS[0] / f"{doc_id}.pdf"
