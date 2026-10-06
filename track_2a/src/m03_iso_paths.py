# SPDX-License-Identifier: Apache-2.0
"""Data root of all scripts, and the paths of the isolation inputs for one document.

Data root: the environment variable PARLPDFECH_DATA; without it, the folder data/ of the project
folder (track_2a/data). All scripts take their data paths from DATA. The sub-paths below the data
root are the sub-paths of the private project, except the two paths of the stratified sample
(SAMPLE_LIST, SAMPLE_PDF). When PARLPDFECH_DATA points to the data folder of the private project
and PARLPDFECH_SAMPLE_LIST and PARLPDFECH_SAMPLE_PDF point to the sample of the private project,
the scripts use the private layout unchanged.

Development documents: <data>/iso/<kind>/. Test documents (split role "Gold", human gold set):
<data>/gold/test/<kind>/ (test documents stay separate). A glob over <data>/iso/<kind>/ never
finds a test document; a script that reads a test document must name it by its id. Limit: the PDF
files of the test list of m03_gold_select.py are in SAMPLE_PDF, together with development documents
(pdf_path() also searches there first).
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("PARLPDFECH_DATA") or ROOT / "data").expanduser().resolve()
DEV = DATA / "iso"
TEST = DATA / "gold/test"
# Local text weights of Apertus-v1.5-8B in bf16 (m04_text_branch_extrahieren.py); never in the repository.
MODEL = DATA / "modelle/apertus-v1.5-8b-text-bf16"
PROMPTS = DEV / "atome_prompt"


def _setting(name: str, default: Path) -> Path:
    """A path from the environment variable name, else the default."""
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default


# Stratified sample of PDF documents: the list and the downloaded files. An earlier script selected
# and downloaded this sample; that script is not in this repository. The environment variables
# PARLPDFECH_SAMPLE_LIST and PARLPDFECH_SAMPLE_PDF give other places, for example the folders of the
# private project.
SAMPLE_LIST = _setting("PARLPDFECH_SAMPLE_LIST", DATA / "analyse/stichprobe/auswahl.csv")
SAMPLE_PDF = _setting("PARLPDFECH_SAMPLE_PDF", DATA / "pdf/stichprobe")


def rel(p: Path) -> str:
    """A path for records and messages: relative to the folder that contains the data root
    (private layout: daten/..., public layout: data/...), else the full path."""
    q = Path(p).resolve()
    return str(q.relative_to(DATA.parent)) if q.is_relative_to(DATA.parent) else str(p)


def iso_path(kind: str, doc_id: str, ext: str = "json") -> Path:
    """kind: atome, docling or atome_prompt."""
    p = DEV / kind / f"{doc_id}.{ext}"
    if p.exists():
        return p
    q = TEST / kind / f"{doc_id}.{ext}"
    return q if q.exists() else p


PDF_DIRS = [SAMPLE_PDF, DATA / "pdf/bulk", TEST / "pdf"]


def pdf_path(doc_id: str) -> Path:
    """The PDF of a document: stratified sample, bulk download, or test PDFs (<data>/gold/test/pdf)."""
    for d in PDF_DIRS:
        p = d / f"{doc_id}.pdf"
        if p.exists():
            return p
    return PDF_DIRS[0] / f"{doc_id}.pdf"
