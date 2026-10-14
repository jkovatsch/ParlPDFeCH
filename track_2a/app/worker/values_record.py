#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the record whose head values are read from the PDF.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

Task
  serve_convert.py (a sample) and fresh.py (a PDF that is not a sample) call this file after the block
  decisions are written. It calls three converter files of the code layout, by import from the scratch root:
    m11_writer        read_values (the cascade reader), write_record (3 YAML files, manifest.json) and
                      rdf_step (4 RDF files)
    m11_validate      validate_record (checks C1 to C22, validation.json)
  and through them:
    m11_values_cascade  the cascade reader (read_document). The kind of the document selects which of the 7
                      values are searched (decision D1). The kind comes from the rule chain (the S1 rule role
                      and the S1 rule id of the rule file) for a sample and for an unknown PDF. If the rule
                      chain made no decision (S1 rule id D0), rule V5 of the reader decides the kind from 2
                      facts of the PDF: a type word of a proposal of a member, and a responding body that
                      a response rule tier finds. Since version 4 of the reader the kind response needs
                      the tier of an explicit response cue (a heading or a phrase of the first lines says
                      that the executive answers). The cascade is src/m11_cascade.yaml with
                      src/m11_cascade.py (labels_for(kind, affair_type)).
    m11_values_base   the interface of the value readers; the 4 rule modules (code rules with
                      tiers) for the affair type, the title, the affair number, the submission date, the
                      response date, the responder and the first author
  The readers get the block file and the rule file only. They read no export record and no model state.
  The export record of a sample goes to the writer as the cross-check only: no value of the eCH-0295 part
  comes from it.
  States of a value in the record:
    read from the PDF          the value is in the eCH-0295 part with a label pdf-<field>
    not found                  the readers searched and found no value: the value is absent, and the manifest
                               gives the slot the state not_found_in_pdf with a reason
    searched, out of the       the cascade searches the value, and the rule of the value does not read this
    scope of the rule          document (for example the head word Petition, which has no value in the list of
                               eCH-0295; a response with no author in its head): state not_found_in_pdf with
                               the reason reader_scope (finding S3-01). It is a result of a search.
    weak candidate             a value of a rule tier whose stored probability is below 0.5: it is not written
                               to the eCH-0295 part; it stays in the label file (label id candidate-<field>),
                               and the slot has the reason weak_candidate_only
    not searched in this kind  the cascade does not search the value for the kind of the document: the slot
    of document                has the state not_in_this_document_type with the kind and the ids of the
                               cascade rules (decision D1)
  A document of the kind response or combined that prints the author and the date of the proposal in its head
  states them: the record then has a submission step with the sponsorship and the date and with no text block
  (decision D2, cascade rule R30, a project choice). A document of the kind proposal or executive_proposal
  gets no response step: the body that the text addresses is a candidate label only (decision D3).
  An absent affair type or affair number is a recorded gap.
  The probability of a value is the stored value of its rule tier over all folds (key p_all_folds of the
  calibration file), for every document, also a development document (decision D4). The floor of 0.5 uses
  the same number.
  The validator runs the cascade reader again on the block file and the rule file and compares each field
  with the record: value, span, tier and slot state (check C22, decision D6). It makes each value again
  from the wording at its span (check C20). The validator opens the calibration file of the product by its
  own path below the scratch root, never the path that the manifest names (finding S3-02). This file gives
  it no other file, and it stops if the result does not say "the product file".
  A text block whose text slot the cascade does not give to the kind of the document is not written to the
  eCH-0295 part. It stays in the provenance file (the writer; manifest key cascade.text_blocks_not_written).
  Signs of a response (finding S3-03): for a document of the kind proposal or executive_proposal the function
  response_signs runs the responder rule one more time and keeps the rule tiers of its candidates that are
  not the tier of an addressed body. The record does not change. The view shows a notice.

The switch
  PARLPDFECH_VALUES=off   the earlier record path runs (m10_writer.write_one for a sample, worker/pdf_only.py
                          for another PDF). The gate of the earlier stages needs it. The head values of a
                          sample then come from the export, and the view has the notice head_from_export.
  worker/values_hold.json a list of samples (document number and SHA-256 of the PDF) that keep the earlier
                          record path while the list names them. THE LIST IS EMPTY. The mechanism stays for
                          a later use.

The calibration file of the values (decision D5)
  daten/gj_values/round4/calibration_dev_all.json of the code layout (round 4: the cascade reader version 4
  with rule V5, on rule files that are made from the PDF alone). For each pair of field and rule tier it
  holds the share of the 1,793 development documents in which the value of that tier was equal to the
  OpenParlData value (Jeffreys mean). Origin: development documents of 44 parliaments that the rule authors
  read; the rule files of the reader are made from the PDF alone. The one fixed run of 13.10.2026 used 872
  documents of 26 other parliaments. There the share correct (correct / documents with an export value) was
  0.2214 for the affair number and 0.2729 for the submission date. Before the run, AI agents had read 116 or
  more of these documents in earlier work. The
  layout holds no stand-in file. If the file is absent, the conversion stops: no record with synthetic
  numbers is made.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

VERSION = "parlpdfech-values/0.4.0"
MEASURED_REL = "daten/gj_values/round4/calibration_dev_all.json"
# decision D5: the text of each place that names the origin of the calibration file
ORIGIN = ("Development documents of 44 parliaments that the rule authors read; the rule files of the reader "
          "are made from the PDF alone. The one fixed run of 13.10.2026 used 872 documents of 26 other "
          "parliaments. There the share correct (correct / documents with an export value) was 0.2214 for "
          "the affair number and 0.2729 for the submission date. Before the run, AI agents had read 116 or "
          "more of these documents in earlier work.")
KIND = "from_rule_chain"        # stage 0 of the cascade: the kind of the document from the rule chain (rule file)
HOLD_FILE = Path(__file__).resolve().parent / "values_hold.json"
RECORD_SCHEMA = "parlpdfech-pdf-values-record/1"
CHECK_IDS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme",
             "C7_C8_labels", "C9_e19", "C11_wording_at_span", "C12_one_label_for_each_pdf_value",
             "C13_no_export_value_in_the_record", "C14_cross_check", "C15_slot_states",
             "C16_probability_and_calibration", "C17_recorded_gaps", "C18_minted_iris", "C19_value_forms",
             "C20_value_follows_from_wording", "C21_floor",
             "C22_values_from_the_readers")
VALID_RULE = "the writer check of src/m11_writer.py and each check of src/m11_validate.py that ran (C1 to C9, C11 to C22) passed"


def hold_list() -> list[dict]:
    if not HOLD_FILE.is_file():
        return []
    return list(json.loads(HOLD_FILE.read_text(encoding="utf-8")).get("hold") or [])


def state(doc_id: str | None, pdf_sha256: str | None) -> str:
    """pdf: the head values are read from the PDF. off: the switch PARLPDFECH_VALUES=off. held: the hold list
    names the document number or the SHA-256 of the PDF. In the states off and held the earlier record path runs,
    and no value reader runs."""
    if (os.environ.get("PARLPDFECH_VALUES") or "").strip().lower() == "off":
        return "off"
    for row in hold_list():
        if (doc_id is not None and str(row.get("doc_id")) == str(doc_id)) or \
                (pdf_sha256 is not None and row.get("pdf_sha256") == pdf_sha256):
            return "held"
    return "pdf"


def calibration_file(root: Path) -> tuple[Path, bool]:
    """(path below the scratch root, True). The calibration file of the product. There is no stand-in: if the
    file is absent, the call stops with an error (the second value is always True; the callers keep it as the
    key measured of convert.json)."""
    measured = Path(root) / MEASURED_REL
    if not measured.is_file():
        raise RuntimeError("the code layout holds no value calibration file (" + MEASURED_REL + "): run "
                           "worker/layout_add.py --values and worker/layout.py")
    return measured, True


def write(root: Path, folder: Path, block_file: Path, rule_file: Path, decisions: Path, export: dict | None,
          base: str | None, block_calibrations: Path, calibration_base: str | None = None) -> tuple[dict, dict]:
    """The cascade reader (the kind of the document from the rule chain), write_record and rdf_step. Returns
    (manifest, key rdf of the manifest). An error of one reader does not stop the conversion: the field gets the
    reason reader_error."""
    import m11_writer as w11  # noqa: PLC0415  (from the scratch root)
    if Path(w11.ROOT).resolve() != Path(root).resolve():
        raise RuntimeError("m11_writer is not the file of the scratch root")
    if w11.CALIBRATION_REL != MEASURED_REL or w11.CALIBRATION_ORIGIN != ORIGIN:
        raise RuntimeError("the calibration file or its origin text of m11_writer is not that of the package (decision D5)")
    calibration, _ = calibration_file(root)
    values = w11.read_values(block_file, rule_file, strict=False, kind=KIND)
    folder.mkdir(parents=True, exist_ok=True)
    w11.write_record(block_file, rule_file, decisions, values, calibration, export, folder, base,
                     block_calibrations=block_calibrations, root=root, calibration_base=calibration_base,
                     kind=KIND)
    rdf_result = w11.rdf_step(folder, root=root)
    man = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    return man, rdf_result


def validate(root: Path, folder: Path, export: dict | None) -> dict:
    """validate_record of m11_validate. The export record (a sample) lets check C14 make the cross-check again.
    Check C22 runs the cascade reader again (the kind from the rule chain, never from the manifest)."""
    import m11_validate as v11  # noqa: PLC0415  (from the scratch root)
    calibration_file(root)                    # stops if the layout holds no calibration file
    if v11.CALIBRATION_REL != MEASURED_REL:
        raise RuntimeError("the calibration file of m11_validate is not that of the package (decision D5)")
    # no calibration argument: the validator opens the product file by its own path below the root (finding S3-02)
    res = v11.validate_record(folder, root=root, export_record=export, kind=KIND)
    used = res.get("calibration_file") or {}
    if used.get("is_product_file") is not True or used.get("source") != "the product file":
        raise RuntimeError("the validator did not use the calibration file of the product")
    return res


PROPOSAL_KINDS = ("proposal", "executive_proposal")


def response_signs(block_file: Path, rule_file: Path, man: dict) -> dict | None:
    """Finding S3-03. For a record of the kind proposal or executive_proposal: the rule tiers of the candidates of
    the responder rule that are not the tier of an addressed body ({"responder_tiers": [...]}). The cascade does
    not search the responder in these kinds, so the record holds no such candidate. This call reads the block file
    and the rule file only. It changes no file. None: another kind. An error of the rule gives an empty list."""
    if ((man.get("cascade") or {}).get("kind")) not in PROPOSAL_KINDS:
        return None
    import m11_values_base as vb  # noqa: PLC0415  (from the scratch root)
    import m11_values_cascade as vcr  # noqa: PLC0415
    try:
        vb.load_rule_modules()
        doc = vb.load_from_block_file(block_file, rule_file)
        res = vb.read_field(doc, "responder", False, None)
        cands = ([res] if getattr(res, "found", False) else []) + list(getattr(res, "others", None) or [])
        tiers = [str(c.tier) for c in cands if getattr(c, "tier", None) and c.tier not in vcr.ADDRESSEE_TIERS]
    except Exception:  # noqa: BLE001  (a hint only: an error of the rule must not stop the conversion)
        tiers = []
    return {"responder_tiers": tiers}


def summary(man: dict, measured: bool, signs: dict | None = None) -> dict:
    """The facts of the values for convert.json (counts and codes; no value of the PDF). signs: the result of
    response_signs."""
    vc = man.get("value_calibration") or {}
    floor = man.get("value_floor") or {}
    stand_in = bool(vc.get("stand_in") or man.get("synthetic_values"))
    if stand_in:
        raise RuntimeError("the record holds stand-in numbers: the package makes no such record")
    casc = man.get("cascade") or {}
    return {"version": VERSION, "state": "pdf", "record_schema": man.get("schema"),
            "cascade": {"version": casc.get("version"), "reader": casc.get("reader"), "kind": casc.get("kind"),
                        "kind_from": (casc.get("kind_source") or {}).get("from"),
                        "kind_rule": (casc.get("kind_source") or {}).get("rule"),
                        "rule_chain_id": (casc.get("kind_source") or {}).get("s1_rule_id"),
                        "v5": (casc.get("kind_source") or {}).get("v5"),
                        "searched_out_of_scope": sorted(x.get("field") for x in man.get("slots") or []
                                                        if x.get("field") and x.get("reason") == "reader_scope"),
                        "text_blocks_not_written": len(casc.get("text_blocks_not_written") or []),
                        "affair_type": casc.get("affair_type_of_the_cascade"),
                        "not_searched": sorted(f for f, v in (casc.get("selection") or {}).items()
                                               if not v.get("searched"))},
            "writer": (man.get("writer") or {}).get("version"),
            "readers": (man.get("value_readers") or {}).get("interface"),
            "cross_check_with_export": bool(man.get("has_export")),
            "calibration": {"path": vc.get("path"), "sha256": vc.get("sha256"), "measured": bool(measured),
                            "stand_in": False, "probability_from": vc.get("probability_from"),
                            "origin": ORIGIN,
                            "note": "Round 4 (cascade reader version 4, rule files from the PDF alone). For each "
                                    "rule tier: the share of the 1,793 development documents in which a value of "
                                    "the tier was equal to the OpenParlData value (all folds)."},
            "floor": {"threshold": floor.get("threshold"),
                      "not_written": [{"field": x.get("field"), "tier": x.get("tier"),
                                       "tier_probability": x.get("tier_probability")}
                                      for x in floor.get("not_written") or []]},
            "addressee_candidates": [x.get("field") for x in man.get("addressee_candidates") or []],
            "response_signs": None if signs is None else {
                "responder_tiers": list(signs.get("responder_tiers") or []),
                "text_blocks": sum(1 for x in casc.get("text_blocks_not_written") or []
                                   if x.get("slot") == "ResponseStep.texts")},
            "author_rule": man.get("author_rule"),
            "counts": (man.get("counts") or {}).get("values"), "slots": (man.get("counts") or {}).get("slots"),
            "conformance": man.get("conformance"), "i95_gaps": [g.get("slot") for g in man.get("i95_gaps") or []],
            "fields_not_read": man.get("fields_not_read") or []}


PAGE_SCALE = 2.0      # pypdfium2: 1.0 = 72 pixels for each inch (the same scale as worker/make_samples.py)


def _sha256(p: Path) -> str:
    import hashlib  # noqa: PLC0415
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def record_extras(folder: Path, out: Path, d: str, *, sample_dir: Path | None = None,
                  pdf: Path | None = None, max_pages: int = 25) -> dict:
    """The files of a record with values from the PDF that are not converter files of the earlier form (14.10.2026):
      <d>.values.ttl  the values with their probabilities (m11_writer.rdf_step); SHA-256 of the manifest
      source.pdf      the PDF: for a sample the copy of the sample folder, else the PDF of the job
      page-<n>.png    one image of each page: for a sample the images of the sample folder (made by
                      worker/make_samples.py), else made now with pypdfium2 (scale 2)
    Returns {"names": [...], "pages": {"state": "images" | "no_renderer" | "renderer_error", "renderer": ...}}.
    A failure of the renderer does not stop the conversion: the record then has no image, and the page of the
    result draws the lines of the text layer."""
    names: list[str] = []
    man = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    vt = (man.get("outputs") or {}).get("values_ttl")
    if vt:
        name = f"{d}.values.ttl"
        (out / name).write_bytes((folder / name).read_bytes())
        if _sha256(out / name) != vt["sha256"]:
            raise RuntimeError("the copy of the file of the values has another SHA-256")
        names.append(name)
    pages = {"state": "no_renderer", "renderer": None}
    if sample_dir is not None:
        sample = json.loads((Path(sample_dir) / "sample.json").read_text(encoding="utf-8"))
        extra = [f for f in sample.get("files") or [] if f.get("role") in ("source_pdf", "page_image")]
        for f in extra:
            (out / f["name"]).write_bytes((Path(sample_dir) / f["name"]).read_bytes())
            if _sha256(out / f["name"]) != f["sha256"]:
                raise RuntimeError("a file of the sample folder has another SHA-256 than its entry of sample.json")
            names.append(f["name"])
        images = [f for f in extra if f["role"] == "page_image"]
        if images:
            pages = {"state": "images", "renderer": images[0].get("renderer"), "made": "stored with the sample"}
    elif pdf is not None:
        (out / "source.pdf").write_bytes(Path(pdf).read_bytes())
        names.append("source.pdf")
        try:
            from importlib.metadata import version  # noqa: PLC0415

            import pypdfium2  # noqa: PLC0415
        except ImportError:
            pypdfium2 = None
        if pypdfium2 is not None:
            try:
                doc = pypdfium2.PdfDocument(str(out / "source.pdf"))
                try:
                    for i in range(min(len(doc), max_pages)):
                        name = f"page-{i + 1}.png"
                        doc[i].render(scale=PAGE_SCALE).to_pil().convert("RGB").save(out / name, format="PNG",
                                                                                     optimize=True)
                        names.append(name)
                finally:
                    doc.close()
                pages = {"state": "images", "renderer": f"pypdfium2 {version('pypdfium2')}, scale {PAGE_SCALE}",
                         "made": "now"}
            except Exception as e:  # noqa: BLE001  (an image is a help for the page; no failure of the record)
                for n in [n for n in names if n.startswith("page-")]:
                    (out / n).unlink(missing_ok=True)
                names = [n for n in names if not n.startswith("page-")]
                pages = {"state": "renderer_error", "renderer": "pypdfium2", "error": type(e).__name__}
    return {"names": names, "pages": pages}


def earlier(state_code: str) -> dict:
    """The key values of convert.json for the earlier record path."""
    return {"version": VERSION, "state": state_code,
            "note": "The earlier record path ran. No value reader ran. "
                    + ("The switch PARLPDFECH_VALUES is off." if state_code == "off" else
                       "worker/values_hold.json names this document.")}
