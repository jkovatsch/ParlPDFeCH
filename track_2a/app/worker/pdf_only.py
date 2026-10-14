#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package (stage P0b): the record of a PDF that has no export record.

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

Why this file exists
  The writer of the converter (m10_writer.write_one) makes the source IRI and the record IRI from an
  OpenParlData document number, and it puts the path of an export record into the output files. A PDF
  that is not in the package has no document number and no export record. With an invented number the
  output files hold an IRI of a document that does not exist. Thus this file is new code. It is not a
  converter file and it changes none. It imports the converter functions that apply without a change:
    m10_writer    check_doc_file, check_decisions, author_runs, path_switches, clip, the constants
    m06_converter block_text, profile_changes, e19_problems, atom_ev, from_ocr (wording and check E19)
    m06_ech_ausgabe schreibe_yaml and the version texts
    m03_iso_v4    fixed_answers
    m10_rdf       layout_record, to_graph, trig_text, bind, slot_iris, linkml_versions
    m10_validate  linkml_check, same_graph, leaf_coverage, leaves, label_checks, shacl_checks
  The contract of the record is CONTRACT.md chapter 10.

The record
  Document IRI   urn:parlpdfech:local:sha256:<64 hex of the PDF bytes>   (no document number)
  Record IRI     <document IRI>/record ; each other IRI of the record is below the record IRI
  Named graphs   <record>/ech-0295, <record>/provenance, <record>/atoms, <record>/labels
  eCH-0295 part  one Container with its IRI and no affair. eCH-0295 has a text block only below a step
                 of an affair, and the PDF gives no affair. Thus each text block is a TextBlockRecord of
                 the provenance graph with the mapping status profile_only and its text.
  Labels         D1 (document), one label for each Docling block, the switch labels, one copy label for
                 each text block, one constant label for the Container IRI. Each label of a rule has its
                 probability, all option probabilities, the value status, the page, the character span
                 and the calibration IRI. No label has the slot in_sample: the package cannot tell if the
                 PDF is one of the documents that the probabilities were fitted on (the slot is optional
                 in the label schema).
  Calibrations   the records of the calibration file, with two changes. (1) The slot reference_source holds
                 the text REFERENCE_TEXT of this file. The text of the calibration file names document numbers
                 and folders of the project, which a record of another PDF must not hold. (2) The slot
                 in_sample is left out (it is optional in the label schema). In the calibration file the slot
                 is a constant of the calibration: it says if the measures of the calibration were taken on
                 its own fit set. It says nothing about the PDF of this record. A reader of the record of an
                 unknown PDF could read it as a statement about that PDF.
  manifest.json  conformance "pdf_only_with_recorded_gaps" and the key recorded_gaps (each absent slot).
  validation.json the checks that can run; each other check has the state skipped with a reason.

File names: the prefix of the 7 converter-form files is the word local (contract chapter 3).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

WRITER = "worker/pdf_only.py"
VERSION = "pdf-only-writer-1"
RECORD_SCHEMA = "parlpdfech-pdf-only-record/1"
CONFORMANCE = "pdf_only_with_recorded_gaps"
IRI_PREFIX = "urn:parlpdfech:local:sha256:"
DOC = "local"                                   # file prefix and the id of the document inside one run
GRAPHS = ("ech-0295", "provenance", "atoms", "labels")
NO_EXPORT = "no OpenParlData export record: the PDF gives no value for this slot"
TEXT_BLOCK_GAP = ("eCH-0295 has a text block only below a step of an affair. The record has no affair. Each text "
                  "block is a TextBlockRecord of the provenance graph with the mapping status profile_only.")
SKIPPED = (("metadata_values", "no_export_record",
            "the check of the metadata values against the export record (m06_converter.check_values)"),
           ("i95_gap_rule", "no_affair", "rule A2 for the required slots of an affair (m10_gaps.gap_rule)"),
           ("independent_wording_comparison", "no_text_block_in_ech_instance",
            "the information item of check C9 (m06_ech_ausgabe.wortlaut_abgleich) for a TextBlock of the instance"))
# The reference that the probabilities are about, in words that hold no document number and no folder name.
REFERENCE_TEXT = ("reference labels of the development documents, made by a language model and not checked by a human")
NOT_KNOWN = ("The package holds the SHA-256 of its samples only. It cannot tell if this PDF is one of the "
             "development documents that the probabilities were fitted on.")
NOT_CHECKED = "The probabilities of this record were not checked on other documents. No value of a report applies."
CHECK_IDS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme",
             "C7_C8_labels", "C9_e19")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iris(pdf_sha256: str) -> dict:
    """Each IRI of the record. The document IRI holds the SHA-256 of the PDF bytes and no number."""
    if not re.fullmatch(r"[0-9a-f]{64}", pdf_sha256 or ""):
        raise ValueError("pdf_sha256 is not a SHA-256")
    doc = IRI_PREFIX + pdf_sha256
    rec = f"{doc}/record"
    return {"document": doc, "record": rec, "container": f"{rec}/i95", "extraction": f"{rec}/extraction",
            "run": f"{rec}/run", "label_record": f"{rec}/label-record",
            "named_graphs": {g: f"{rec}/{g}" for g in GRAPHS}}


def file_info(root: Path, p: Path) -> dict:
    p = Path(p).resolve()
    return {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "abs": p}


def affair_slots(rdf) -> list[dict]:
    """The slots of the class Affair of the I95 schema with their required flag (read from the schema)."""
    sv, _, _ = rdf.bundle(rdf.WRAPPER)
    with rdf.in_src():
        return [{"slot": f"Affair.{s.name}", "required_in_i95": bool(s.required)}
                for s in sv.class_induced_slots("Affair")]


# ---------------------------------------------------------------------------------------------- writer
def build(m, root: Path, doc: dict, dec: dict, cals: dict, calibration_base: str, files: dict, pdf_sha256: str) -> dict:
    """The eCH-0295 part, the provenance file and the label file of one PDF with no export record.
    m: the converter modules (writer, mc, ea, gr, v4, rdf). No value of this function is invented: each value
    comes from the PDF (atoms, blocks), from the decisions file, from a calibration record or from a schema."""
    writer, mc, ea, gr, v4, rdf = m.writer, m.mc, m.ea, m.gr, m.v4, m.rdf
    d = DOC
    iri = iris(pdf_sha256)
    record, doc_iri, container_iri, run_iri = iri["record"], iri["document"], iri["container"], iri["run"]
    atoms_file = read_json(files["atoms"]["abs"])
    atoms_list = atoms_file["atome"]
    by_id = {a["id"]: a for a in atoms_list}
    fixed = v4.fixed_answers(d)
    blocks, decided = doc["blocks"], dec["blocks"]
    options = [b["option"] for b in decided]
    problems: list[str] = []
    not_mapped: list[dict] = []

    def status(p: float, cid: str) -> str:
        t = cals[cid].get("certain_threshold")
        return "certain" if t is not None and p >= float(t) else "unsure"

    block_status = {i: status(writer.clip(b["probs"][b["option"]]), b["calibration"]) for i, b in enumerate(decided)}

    # author blocks: maximal runs of blocks with one text option (the rule of the converter)
    runs = writer.author_runs(options)
    e19 = {"text_blocks": 0, "characters": 0, "hyphens": 0, "markers": 0, "problems": []}
    tb = []
    for k, (opt, idx) in enumerate(runs, 1):
        ids = [a for i in idx for a in blocks[i]["atoms"] if a not in fixed]
        r = {"k": k, "option": opt, "idx": idx, "ids": ids, "global_uri": f"{record}/textblock/{k}"}
        if not any((by_id[a].get("text") or "").strip() for a in ids):
            r["reason"] = "The blocks of the author block have no text atom (all atoms are fixed or empty). " + TEXT_BLOCK_GAP
            r["text"], r["tc"] = "", {"hyphens_removed": [], "list_markers_removed": [], "empty_atoms": list(ids),
                                      "nfc_changed": False}
        else:
            text, ch = mc.block_text(d, ids)
            tc = mc.profile_changes(ch)
            bad = mc.e19_problems(d, by_id, ids, text, tc)
            e19["text_blocks"] += 1
            e19["characters"] += len(gr.signature_text(text))
            e19["hyphens"] += len(tc["hyphens_removed"])
            e19["markers"] += len(tc["list_markers_removed"])
            e19["problems"] += [f"author block {k}: {b}" for b in bad]
            r |= {"text": text, "tc": tc, "reason": TEXT_BLOCK_GAP}
        tb.append(r)

    # eCH-0295 part: one Container with its IRI
    instance = {"global_uri": container_iri}
    not_mapped.append({"not_mapped_item": "Affair", "not_mapped_reason":
                       "The record has no OpenParlData export record. The PDF gives no affair, no affair number, no "
                       "affair type, no title and no date.", "candidate_source": "no export record"})
    for b in decided:
        if b["option"] == "title":
            not_mapped.append({"not_mapped_item": f"Title block {b['block']}", "not_mapped_reason":
                               "A title block from the PDF goes to the label graph only. The record has no affair "
                               "that can hold a title.", "candidate_value": f"{record}/block/{b['block']}",
                               "candidate_source": f"label {record}/label/{b['block']}-slot"})
    for r in tb:
        not_mapped.append({"not_mapped_item": f"TextBlock of author block {r['k']} ({r['option']})",
                           "not_mapped_reason": r["reason"], "candidate_value": r["global_uri"],
                           "candidate_source": "TextBlockRecord"})

    # provenance file (profile 0.2.0, class ExtractionRecord)
    fp = hashlib.sha256(json.dumps([[a["id"], a["zeichen"]] for a in atoms_list], separators=(",", ":"))
                        .encode("utf-8")).hexdigest()
    lang = doc.get("language") if doc.get("language") in ea.SPRACHEN else None
    pipeline_run = {
        "script_name": WRITER,
        "decomposition_source": f"block options of the decisions file {files['decisions']['path']} (SHA-256 "
                                f"{files['decisions']['sha256']}, mode {dec['mode']}); blocks {files['docs']['path']} "
                                f"(SHA-256 {files['docs']['sha256']}); no export record",
        "decomposition_accepted": False,
        "taxonomy_version": "author blocks from the options of the Docling blocks (the rule of m10_writer.author_runs); "
                            "PDF-only record of the package, CONTRACT.md chapter 10",
        "atom_version": f"{atoms_file.get('version', '')} {atoms_file.get('erzeugt_utc', '')}".strip(),
        "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": utc_now()}
    src = {"global_uri": doc_iri, "file_sha256": pdf_sha256,
           "docling_json_sha256": atoms_file.get("quelle_sha256") or "", "atom_fingerprint": fp,
           "page_count": len(read_json(files["docling"]["abs"])["seiten"])}
    if lang:
        src["document_language"] = lang
        src["document_language_source"] = ("language of the block file (stop-word rule of the converter, "
                                           "m05_cls_data.language); no export record")
    else:
        src["document_language_source"] = "no language: the stop-word rule gives no language, and no export record exists"
    src["document_kind"] = (f"PDF with no export record, mode {dec['mode']}, D1 option {dec['document']['d1']['option']} "
                            f"({writer.D1_OPTIONS[dec['document']['d1']['option']]})")
    tbr = []
    for r in tb:
        x = {"global_uri": r["global_uri"], "about_entity": container_iri, "section_key": r["option"],
             "mapping_status": "profile_only", "not_mapped_reason": r["reason"],
             "extent_value_status": "certain" if all(block_status[i] == "certain" for i in r["idx"]) else "unsure",
             "text_form": "richtext", "text_content": r["text"], "char_count": len(r["text"]),
             "source_document": doc_iri,
             "units": [{"unit_id": blocks[i]["block"], "unit_type": r["option"],
                        "atom_evidence": [mc.atom_ev(by_id[a]) for a in blocks[i]["atoms"] if a not in fixed]}
                       for i in r["idx"]],
             "text_changes": r["tc"]}
        x["units"] = [u for u in x["units"] if u["atom_evidence"]] or x["units"][:1]
        tbr.append(x)
    value_records = [{"about_entity": container_iri, "instance_path": "global_uri", "ech_slot": "Container.global_uri",
                      "recorded_value": container_iri, "derivation": "identifier_minted",
                      "rule_applied": f"{IRI_PREFIX}{{SHA-256 of the PDF bytes}}/record/i95 (deterministic; {WRITER})",
                      "mapping_match": "not_applicable", "pdf_consistency": "not_checked"}]
    check_passed = not e19["problems"]
    prov = {"global_uri": iri["extraction"], "describes_delivery": container_iri,
            "ech_schema_version": ea.FASSUNG_TEXT["i95"], "pipeline_run": pipeline_run, "source_documents": [src],
            "text_block_records": tbr, "value_records": value_records, "not_mapped_records": not_mapped,
            "verbatim_check": {
                "check_method": "Each leaf value needs a ValueRecord. Each author block: its letters (no markup, no white "
                                "space) are the letters of the Docling wording of its atoms (without fixed atoms) after "
                                "the recorded changes only (line-end hyphens, list markers at the atom start, empty "
                                "atoms, NFC). No metadata value is checked: the record has no export record.",
                "text_blocks_checked": e19["text_blocks"], "characters_checked": e19["characters"],
                "hyphens_removed_count": e19["hyphens"], "list_markers_removed_count": e19["markers"],
                "metadata_values_checked": 0, "leaves_without_provenance": 0, "check_passed": check_passed}}

    # label file (label schema 0.1.0, class LabelRecord)
    iri_of = rdf.slot_iris(rdf.WRAPPER)
    pages = [b["page"] for b in blocks]
    whole = {"page": min(pages), "last_page": max(pages), "span_start": min(b["char_start"] for b in blocks),
             "span_end": max(b["char_end"] for b in blocks)}

    def prob_label(gid, subject, predicate, obj, kind, x, probs, extra) -> dict:
        p = writer.clip(probs[obj])
        cid = str(x["calibration"])
        la = {"global_uri": gid, "label_subject": subject, "label_predicate": predicate, "label_object": obj,
              "label_kind": kind, "label_source": writer.SOURCE[x["source"]], "label_probability": p,
              "option_probabilities": [{"option_value": k, "label_probability": writer.clip(v)} for k, v in probs.items()],
              "value_status": status(p, cid), "calibration": f"{calibration_base}calibration/{cid}", "model_run": run_iri}
        return la | extra

    labels = []
    d1 = dec["document"]["d1"]
    d1_label = prob_label(f"{record}/label/d1", doc_iri, f"{writer.PLB}documentTextParts", d1["option"],
                          "document_text_parts", d1, d1["probs"], {})
    if d1.get("rule_id"):
        d1_label["rule_id"] = str(d1["rule_id"])
    d1_label |= whole              # no slot in_sample: see the head of this file
    labels.append(d1_label)
    for b, x in zip(blocks, decided, strict=True):
        extra = {"page": b["page"], "span_start": b["char_start"], "span_end": b["char_end"]}
        if x.get("tier"):
            extra["tier"] = str(x["tier"])
        labels.append(prob_label(f"{record}/label/{b['block']}-slot", f"{record}/block/{b['block']}",
                                 f"{writer.AFF}textType", x["option"], "block_slot", x, x["probs"], extra))
    pos = {b["block"]: i for i, b in enumerate(blocks)}
    for x in dec.get("boundaries") or []:
        i = pos[x["after_block"]]
        a, n = blocks[i], blocks[i + 1]
        labels.append(prob_label(f"{record}/label/switch-after-{a['block']}", f"{record}/boundary/after-{a['block']}",
                                 f"{writer.PLB}authorSwitch", "switch", "author_switch",
                                 x | {"source": x.get("source", "rule")}, {"switch": x["p"], "no_switch": 1 - x["p"]},
                                 {"page": n["page"], "last_page": max(a["page"], n["page"]),
                                  "span_start": min(a["char_end"], n["char_start"]),
                                  "span_end": max(a["char_end"], n["char_start"]),
                                  "label_note": f"switch between block {a['block']} and block {n['block']}"}))
    labels.append({"global_uri": f"{record}/label/value-global_uri", "label_subject": container_iri,
                   "label_predicate": iri_of["global_uri"], "label_object": container_iri,
                   "label_kind": "constant_value", "label_source": "constant", "model_run": run_iri,
                   "about_entity": container_iri, "instance_path": "global_uri",
                   "label_note": "derivation identifier_minted (ValueRecord of the provenance file)"})
    for r in tb:
        bl = [blocks[i] for i in r["idx"]]
        labels.append({"global_uri": f"{record}/label/textblock-{r['k']}-text", "label_subject": r["global_uri"],
                       "label_predicate": iri_of["text"], "label_object": f"sha256:{sha256_text(r['text'])}",
                       "label_kind": "text_wording", "label_source": "copy", "model_run": run_iri,
                       "page": min(b["page"] for b in bl), "last_page": max(b["page"] for b in bl),
                       "span_start": min(b["char_start"] for b in bl), "span_end": max(b["char_end"] for b in bl),
                       "label_note": "verbatim copy of the atoms of the author block (check E19); the text and the text "
                                     "changes are in the TextBlockRecord of the provenance graph"})
    used = sorted({la["calibration"].rsplit("/", 1)[1] for la in labels if "calibration" in la})
    label_run = {"global_uri": run_iri, "script_name": WRITER, "run_mode": dec["mode"],
                 "process_status": writer.PROCESS_STATUS,
                 "input_files": [{"file_role": k, "file_path": f["path"], "file_digest": f["sha256"]}
                                 for k, f in files.items()],
                 "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": utc_now()}
    label_rec = {"global_uri": iri["label_record"], "describes_record": record, "ech_delivery": container_iri,
                 "source_document": doc_iri, "label_run": label_run, "label_assertions": labels,
                 "calibrations": [{"global_uri": f"{calibration_base}calibration/{c}"}
                                  | {k: v for k, v in cals[c].items() if k != "in_sample"}
                                  | ({"reference_source": REFERENCE_TEXT} if "reference_source" in cals[c] else {})
                                  for c in used]}
    switches = writer.path_switches(options)
    covered = {pos[x["after_block"]] for x in dec.get("boundaries") or []}
    counts = {"blocks": len(blocks), "block_options": {o: options.count(o) for o in writer.OPTIONS if o in options},
              "author_blocks": len(runs), "textblocks_by_slot": {"submission": 0, "response": 0},
              "textblock_records_profile_only": len(tb), "path_switch_points": len(switches),
              "path_switch_points_without_boundary_label": sum(1 for a, b in switches
                                                               if not any(a <= c < b for c in covered)),
              "boundary_labels": len(dec.get("boundaries") or []), "label_assertions": len(labels),
              "label_assertions_by_source": {s: sum(1 for la in labels if la["label_source"] == s)
                                             for s in sorted({la["label_source"] for la in labels})},
              "certain_labels": sum(1 for la in labels if la.get("value_status") == "certain"),
              "unsure_labels": sum(1 for la in labels if la.get("value_status") == "unsure"),
              "r2_agrees_with_block_path": None, "d1_option": d1["option"], "leaf_values": 1,
              "value_records": len(value_records),
              "e19": {"text_blocks": e19["text_blocks"], "characters": e19["characters"],
                      "hyphens_removed": e19["hyphens"], "list_markers_removed": e19["markers"],
                      "problems": len(e19["problems"])},
              "metadata_check": {"values_checked": 0, "problems": 0, "leaves_without_provenance": 0,
                                 "state": "skipped", "reason": "no_export_record"}}
    return {"instance": instance, "provenance": prov, "labels": label_rec, "iri": iri, "calibrations": used,
            "check_passed": check_passed and not problems, "problems": problems + e19["problems"], "counts": counts}


def write_record(m, root: Path, folder: Path, doc_p: Path, dec_p: Path, cal_p: Path, atoms_p: Path, docling_p: Path,
                 pdf_p: Path, pdf_sha256: str, calibration_base: str) -> dict:
    """Writes local.ech.yaml, local.provenance.yaml, local.labels.yaml and manifest.json. Returns the manifest."""
    writer, ea, rdf, mc = m.writer, m.ea, m.rdf, m.mc
    t0 = time.perf_counter()
    d = DOC
    doc, dec = read_json(doc_p), read_json(dec_p)
    cals, cal_file = writer.load_calibrations(Path(cal_p).resolve())
    atoms = read_json(atoms_p)["atome"]
    # the input checks of the converter; its split rule does not apply: an own PDF has no split
    bad = [x for x in writer.check_doc_file(d, doc, atoms) if not x.startswith("split ")]
    bad += writer.check_decisions(d, doc, dec, cals)
    if doc.get("pdf_sha256") != pdf_sha256:
        bad.append("the block file names another PDF")
    if dec.get("mode") != "floor" or dec.get("r2") is not None:
        bad.append("the PDF-only writer accepts the floor mode with no R2 value only")
    if bad:
        raise SystemExit(f"input check failed: {bad[:8]}")
    files = {"pdf": file_info(root, pdf_p), "docs": file_info(root, doc_p), "decisions": file_info(root, dec_p),
             "atoms": file_info(root, atoms_p), "docling": file_info(root, docling_p)}
    files["calibrations"] = {"path": cal_file["path"], "sha256": cal_file["sha256"], "abs": Path(cal_p).resolve()}
    b = build(m, root, doc, dec, cals, calibration_base, files, pdf_sha256)
    outs = {"ech_yaml": folder / f"{d}.ech.yaml", "provenance_yaml": folder / f"{d}.provenance.yaml",
            "labels_yaml": folder / f"{d}.labels.yaml"}
    ea.schreibe_yaml(outs["ech_yaml"], b["instance"],
                     f"# eCH-0295 part of a PDF with no export record (root class Container, no affair), {WRITER} "
                     f"({VERSION})\n# Status EXCEPTION, NOT RELEASED. This is not a full eCH-0295 record. Side files: "
                     f"{d}.provenance.yaml, {d}.labels.yaml\n")
    ea.schreibe_yaml(outs["provenance_yaml"], b["provenance"],
                     f"# Provenance file (profile 0.2.0, class ExtractionRecord) of {d}.ech.yaml; it holds the text blocks\n")
    ea.schreibe_yaml(outs["labels_yaml"], b["labels"],
                     f"# Label file (label schema 0.1.0, class LabelRecord) of {d}.ech.yaml\n")
    src = Path(writer.__file__).resolve().parent
    reused = ("m10_writer.py", "m06_converter.py", "m06_ech_ausgabe.py", "m03_gold_record.py", "m03_iso_v4.py",
              "m10_rdf.py", "m10_validate.py")
    iri = b["iri"]
    man = {"schema": RECORD_SCHEMA, "doc_id": d, "status": writer.PROCESS_STATUS, "synthetic_values": False,
           "mode": dec["mode"], "split": None, "source_iri": iri["document"], "pdf_sha256": pdf_sha256,
           "calibration_base_iri": calibration_base, "record_iri": iri["record"], "container_iri": iri["container"],
           "named_graphs": iri["named_graphs"],
           "writer": {"path": WRITER, "version": VERSION, "sha256": sha256_file(Path(__file__)),
                      "run_date": time.strftime("%d.%m.%Y, %H:%M:%S %Z")},
           "reused_files": {f"src/{n}": sha256_file(src / n) for n in reused},
           "schemas": {"i95": {"path": rdf.rel(mc.I95), "sha256": sha256_file(mc.I95)},
                       "wrapper": {"path": rdf.rel(rdf.WRAPPER), "sha256": sha256_file(rdf.WRAPPER)},
                       "profile": {"path": rdf.rel(rdf.PROFILE), "sha256": sha256_file(rdf.PROFILE), "version": "0.2.0"},
                       "labels": {"path": rdf.rel(rdf.LABEL_SCHEMA), "sha256": sha256_file(rdf.LABEL_SCHEMA),
                                  "version": "0.1.0"}},
           "inputs": {k: {"path": f["path"], "sha256": f["sha256"]} for k, f in files.items()},
           "model": {k: dec[k] for k in ("model", "template", "template_sha256", "heads", "calibration") if k in dec}
                    or "the decisions file names no model, template or head",
           "calibration_ids": b["calibrations"], "conformance": CONFORMANCE,
           "apertus": "none",
           "apertus_note": "No Apertus state was read and no model ran. No label of this record is from Apertus.",
           "sample_of_the_package": False, "development_document": None, "development_document_note": NOT_KNOWN,
           "probabilities_checked_on_other_documents": False, "probabilities_note": NOT_CHECKED,
           "calibration_reference_source": {"replaced": True, "text": REFERENCE_TEXT,
                                            "why": "the text of the calibration file names document numbers and "
                                                   "folders of the project"},
           "calibration_in_sample": {"left_out": True,
                                     "why": "the slot is a constant of the calibration file (measures taken on the fit "
                                            "set of the calibration); it says nothing about this PDF"},
           "recorded_gaps": {"cause": NO_EXPORT, "export_record": None,
                             "absent_slots": [{"slot": "Container.affairs", "required_in_i95": False}] + affair_slots(rdf),
                             "text_blocks": TEXT_BLOCK_GAP,
                             "not_a_full_ech_0295_record": True},
           "check_passed": b["check_passed"], "problems": b["problems"], "notes": [], "counts": b["counts"],
           "outputs": {k: {"path": p.name, "sha256": sha256_file(p), "bytes": p.stat().st_size} for k, p in outs.items()},
           "seconds": {"write": round(time.perf_counter() - t0, 3)}}
    write_json(folder / "manifest.json", man)
    return man


# ---------------------------------------------------------------------------------------------- RDF step
def accept_urn(rdf) -> None:
    """The LinkML dumper reads an IRI with no "//" as a CURIE and stops for the unknown prefix urn. This function
    adds the prefix urn (= "urn:") to the prefix map of the three schema views in memory. Then the dumper gives the
    IRI urn:... as it is written. No schema file changes, and no class or slot of a schema view changes."""
    for schema in (rdf.WRAPPER, rdf.PROFILE, rdf.LABEL_SCHEMA):
        sv, _, _ = rdf.bundle(schema)
        with rdf.in_src():
            ns = sv.namespaces()
            if "urn" not in ns:
                ns["urn"] = "urn:"
            if sv.namespaces().get("urn") is None or str(sv.namespaces()["urn"]) != "urn:":
                raise SystemExit("the prefix map of a schema view does not keep the prefix urn")


def record_paths(folder: Path) -> dict[str, Path]:
    d = DOC
    return {"ech_yaml": folder / f"{d}.ech.yaml", "provenance_yaml": folder / f"{d}.provenance.yaml",
            "labels_yaml": folder / f"{d}.labels.yaml", "gesamt_trig": folder / f"{d}.gesamt.trig",
            "gesamt_rdfxml": folder / f"{d}.gesamt.rdf.xml", "ech_ttl": folder / f"{d}.ech.ttl",
            "ech_rdfxml": folder / f"{d}.ech.rdf.xml", "manifest": folder / "manifest.json"}


def part_graphs(m, root: Path, folder: Path) -> tuple[dict, dict]:
    """The 4 graphs of the record from its YAML files, the block file and the atom file (the route of
    m10_rdf.part_graphs: the same schemas, classes and functions; no gap slot)."""
    rdf = m.rdf
    accept_urn(rdf)
    paths = record_paths(folder)
    man = read_json(paths["manifest"])
    labels = rdf.load_yaml(paths["labels_yaml"])
    record_iri = man["record_iri"]
    if labels["describes_record"] != record_iri:
        raise SystemExit("the label file and the manifest name different records")
    doc_p, atoms_p = root / man["inputs"]["docs"]["path"], root / man["inputs"]["atoms"]["path"]
    if sha256_file(doc_p) != man["inputs"]["docs"]["sha256"] or sha256_file(atoms_p) != man["inputs"]["atoms"]["sha256"]:
        raise SystemExit("the block file or the atom file differs from the file that the writer read")
    doc = read_json(doc_p)
    layout = rdf.layout_record(doc, read_json(atoms_p), record_iri, labels["source_document"])
    graphs = {"ech-0295": rdf.to_graph(rdf.WRAPPER, "Container", rdf.load_yaml(paths["ech_yaml"])),
              "provenance": rdf.to_graph(rdf.PROFILE, "ExtractionRecord", rdf.load_yaml(paths["provenance_yaml"])),
              "atoms": rdf.to_graph(rdf.LABEL_SCHEMA, "PdfLayout", layout),
              "labels": rdf.to_graph(rdf.LABEL_SCHEMA, "LabelRecord", labels)}
    return graphs, {"manifest": man, "layout": layout, "record_iri": record_iri, "doc": doc}


def rdf_step(m, root: Path, folder: Path) -> dict:
    """Writes the 4 RDF files and adds them to the manifest (the route of m10_rdf.convert_record)."""
    import rdflib  # noqa: PLC0415
    rdf = m.rdf
    t0 = time.perf_counter()
    paths = record_paths(folder)
    graphs, info = part_graphs(m, root, folder)
    man, record_iri = info["manifest"], info["record_iri"]
    union = rdflib.Graph()
    rdf.bind(union)
    for name in GRAPHS:
        for t in graphs[name]:
            union.add(t)
    text = rdf.trig_text(graphs, record_iri)
    if text is None:
        raise SystemExit("two graphs bind one prefix to two IRIs")
    paths["gesamt_trig"].write_text(text, encoding="utf-8")
    union.serialize(paths["gesamt_rdfxml"], format="pretty-xml")
    graphs["ech-0295"].serialize(paths["ech_ttl"], format="turtle")
    graphs["ech-0295"].serialize(paths["ech_rdfxml"], format="pretty-xml")
    out = {k: {"path": paths[k].name, "sha256": sha256_file(paths[k]), "bytes": paths[k].stat().st_size}
           for k in ("gesamt_trig", "gesamt_rdfxml", "ech_ttl", "ech_rdfxml")}
    result = {"script": {"path": WRITER, "sha256": sha256_file(Path(__file__)),
                         "functions_of": {"path": rdf.SCRIPT, "sha256": sha256_file(Path(rdf.__file__))}},
              "tools": rdf.linkml_versions(),
              "schemas": {rdf.rel(s): sha256_file(s) for s in (rdf.WRAPPER, rdf.PROFILE, rdf.LABEL_SCHEMA)},
              "named_graphs": {name: f"{record_iri}/{name}" for name in GRAPHS},
              "triples": {name: len(graphs[name]) for name in GRAPHS} | {"union": len(union)},
              "files": out, "seconds": round(time.perf_counter() - t0, 3)}
    man["rdf"] = result
    man["outputs"] |= out
    man.pop("validation", None)
    write_json(paths["manifest"], man)
    return result


# ---------------------------------------------------------------------------------------------- checks
def e19_check(m, root: Path, prov: dict, labels: dict, doc: dict, man: dict) -> dict:
    """Check E19 for each text block of the record: m06_converter.e19_problems with the text, the atoms and the
    text changes of its TextBlockRecord. The atoms of the TextBlockRecord must be the atoms of its blocks without
    the fixed atoms, and the copy label of the text block must hold the SHA-256 of the text."""
    mc, gr, v4 = m.mc, m.gr, m.v4
    atoms = read_json(root / man["inputs"]["atoms"]["path"])["atome"]
    by_id = {a["id"]: a for a in atoms}
    fixed = v4.fixed_answers(DOC)
    block_atoms = {b["block"]: b["atoms"] for b in doc["blocks"]}
    copy = {la["label_subject"]: la["label_object"] for la in labels["label_assertions"]
            if la["label_kind"] == "text_wording"}
    bad, n, chars = [], 0, 0
    for r in prov.get("text_block_records") or []:
        name = r["global_uri"].rsplit("/", 1)[-1]
        text = r.get("text_content") or ""
        ids = [e["atom_id"] for u in r["units"] for e in u.get("atom_evidence") or []]
        want = [a for u in r["units"] for a in block_atoms[u["unit_id"]] if a not in fixed]
        if ids != want:
            bad.append(f"text block {name}: the atoms of the TextBlockRecord are not the atoms of its blocks")
        if copy.get(r["global_uri"]) != f"sha256:{sha256_text(text)}":
            bad.append(f"text block {name}: the copy label does not hold the SHA-256 of the text")
        if r.get("char_count") != len(text):
            bad.append(f"text block {name}: char_count differs from the text")
        if not text:
            continue
        n += 1
        bad += [f"text block {name}: {x}" for x in mc.e19_problems(DOC, by_id, ids, text, r["text_changes"])]
        chars += len(gr.signature_text(text))
    return {"passed": not bad, "text_blocks": n, "characters": chars, "problems": bad[:50],
            "form": "PDF-only record: the text is the key text_content of each TextBlockRecord of the provenance file"}


def validate(m, root: Path, folder: Path) -> dict:
    """The checks of the converter that can run for a PDF-only record, through the functions of m10_validate.
    Writes validation.json and the key validation of the manifest. The key passed uses C1 to C9."""
    import rdflib  # noqa: PLC0415
    rdf, val = m.rdf, m.val
    t0 = time.perf_counter()
    paths = record_paths(folder)
    man = read_json(paths["manifest"])
    ech, prov, labels = (rdf.load_yaml(paths[k]) for k in ("ech_yaml", "provenance_yaml", "labels_yaml"))
    parts, info = part_graphs(m, root, folder)
    doc, record = info["doc"], info["record_iri"]
    res: dict = {"doc_id": DOC, "script": {"path": WRITER, "sha256": sha256_file(Path(__file__)),
                                           "functions_of": {"path": val.SCRIPT, "sha256": sha256_file(Path(val.__file__))}},
                 "tools": rdf.linkml_versions(), "conformance": CONFORMANCE,
                 "conformance_note": "not a full eCH-0295 record: the eCH-0295 part is a Container with no affair",
                 "recorded_gaps": man["recorded_gaps"]}
    c1 = [val.linkml_check(val.I95, "Container", ech, paths["ech_yaml"].name),
          val.linkml_check(rdf.PROFILE, "ExtractionRecord", prov, paths["provenance_yaml"].name),
          val.linkml_check(rdf.LABEL_SCHEMA, "LabelRecord", labels, paths["labels_yaml"].name),
          val.linkml_check(rdf.LABEL_SCHEMA, "PdfLayout", info["layout"], "atom layout (in memory)")]
    res["C1_linkml"] = {"passed": all(x["valid"] for x in c1), "results": c1,
                        "note": "The eCH-0295 file is a Container with no affair. I95 permits a Container with no "
                                "affair. This check does not show a full eCH-0295 record."}
    parsed, c2 = {}, []
    for key, fmt in (("gesamt_trig", "trig"), ("gesamt_rdfxml", "xml"), ("ech_ttl", "turtle"), ("ech_rdfxml", "xml")):
        try:
            parsed[key] = (rdflib.Dataset() if fmt == "trig" else rdflib.Graph()).parse(paths[key], format=fmt)
            c2.append({"file": paths[key].name, "parsed": True, "triples": len(parsed[key])})
        except Exception as e:  # noqa: BLE001  (each parse error is a finding)
            c2.append({"file": paths[key].name, "parsed": False, "error": str(e)[:300]})
    res["C2_parse"] = {"passed": all(x["parsed"] for x in c2), "results": c2}
    if res["C2_parse"]["passed"]:
        named = {str(g.identifier): g for g in parsed["gesamt_trig"].graphs() if len(g)}
        trig = {name: named.get(f"{record}/{name}") for name in GRAPHS}
        union = rdflib.Graph()
        for g in named.values():
            for t in g:
                union.add(t)
        iso = val.same_graph
        c3 = {"union_equals_gesamt_rdfxml": iso(union, parsed["gesamt_rdfxml"]),
              "ech_ttl_equals_ech_rdfxml": iso(parsed["ech_ttl"], parsed["ech_rdfxml"]),
              "ech_ttl_equals_trig_graph": trig["ech-0295"] is not None and iso(parsed["ech_ttl"], trig["ech-0295"])}
        res["C3_isomorphism"] = {"passed": all(c3.values()), **c3, "method": "m10_validate.same_graph"}
        c4 = {name: trig[name] is not None and iso(trig[name], parts[name]) for name in GRAPHS}
        extra = sorted(set(named) - {f"{record}/{n}" for n in GRAPHS})
        res["C4_parts"] = {"passed": all(c4.values()) and not extra, "graphs": c4, "other_graphs": extra,
                           "triples": {n: len(parts[n]) for n in GRAPHS}}
        c5 = {"ech_yaml": val.leaf_coverage(ech, parts["ech-0295"], rdf.WRAPPER),
              "provenance_yaml": val.leaf_coverage(prov, parts["provenance"], rdf.PROFILE),
              "labels_yaml": val.leaf_coverage(labels, parts["labels"], rdf.LABEL_SCHEMA),
              "atom_layout": val.leaf_coverage(info["layout"], parts["atoms"], rdf.LABEL_SCHEMA)}
        res["C5_leaf_values"] = {"passed": not any(c5.values()),
                                 "leaves": {"ech_yaml": sum(1 for _ in val.leaves(ech)),
                                            "provenance_yaml": sum(1 for _ in val.leaves(prov)),
                                            "labels_yaml": sum(1 for _ in val.leaves(labels)),
                                            "atom_layout": sum(1 for _ in val.leaves(info["layout"]))},
                                 "missing": {k: v[:20] for k, v in c5.items()}}
        no_scheme = sorted({str(x) for g in parts.values() for t in g for x in t
                            if isinstance(x, rdflib.URIRef) and not val.RX_SCHEME.match(str(x))})
        res["C6_iri_scheme"] = {"passed": not no_scheme, "iris_without_scheme": no_scheme[:20]}
        res["C7_C8_labels"] = val.label_checks(parts, doc)
        res["C9_e19"] = e19_check(m, root, prov, labels, doc, man)
        try:
            c10 = val.shacl_checks(parts)
        except Exception as e:  # noqa: BLE001  (C10 is information only, as in the converter)
            c10 = {"status": "error", "error_type": type(e).__name__, "reason": f"{type(e).__name__}: {str(e)[:200]}"}
        res["C10_shacl"] = c10 | {"information_only": True}
    keys = [k for k in CHECK_IDS if k in res]
    res["passed"] = len(keys) == len(CHECK_IDS) and all(res[k]["passed"] for k in keys)
    res["skipped_checks"] = [{"id": i, "state": "skipped", "reason": why, "check": what} for i, why, what in SKIPPED]
    res["shacl_information_only"] = True
    res["seconds"] = round(time.perf_counter() - t0, 3)
    p = folder / "validation.json"
    write_json(p, res)
    shacl = res.get("C10_shacl") or {}
    man["validation"] = {"passed": res["passed"], "conformance": CONFORMANCE,
                         "checks": {k: res[k]["passed"] for k in keys},
                         "skipped": {x["id"]: x["reason"] for x in res["skipped_checks"]},
                         "shacl": shacl.get("status"), "shacl_passed": shacl.get("passed"),
                         "shacl_information_only": True, "file": p.name, "sha256": sha256_file(p)}
    man["seconds"]["validate"] = res["seconds"]
    if "rdf" in man:
        man["seconds"]["rdf"] = man["rdf"]["seconds"]
    write_json(folder / "manifest.json", man)
    return res
