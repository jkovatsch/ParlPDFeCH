"""Gate GJ (status EXCEPTION), criteria chapters 6, 7, 9 and 10, handoff 2026-10-12 chapter 3.3 item 2: the one
validation run of the candidates of the design freeze, and the entry decisions GJ.15 and GJ.16.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream A of
workflow wf_d5120f1f-fd4, for the main agent. No human checked this file. This file changes no existing file.
Status of each output: EXCEPTION (process rule 10), NOT RELEASED. The main agent runs the real run. The check
script (src/m10_validation_run_test.py) runs the same chain on dev documents only (check run, chapter 7).
Change of 13.10.2026 (stream H of wave 4, Claude Opus 5.5; protocol 13.10.2026, 00:02): decision M7 (baseline of
GJ.16), GJ.12 with the rules A2 and A3 of addendum A, and the refusals of the chapters 0 and 2.
Change of 13.10.2026 (stream X1 of wave 5, Claude Opus 5.5), after the findings of the second AI agents of wave 4.
Chapter 2 has the new checks R2 required and GJ.11 inputs. Chapter 0 has the safe write of run.json and the files
of a killed process. Chapter 4 has the gap count under the key GJ.21.

0 Order of the records (GJ.2) and the one-run rule (criteria 10.3)
  The run record <out>/run.json gets the SHA-256 of this file (and of each imported m10 module) before the first
  value. The event log <out>/run.events.jsonl gives the clock time of each event in their order: script_sha256,
  then checks_passed, then first_value. A second run is refused when <out>/run.json exists.
  State refused: the run stopped before the first value (a refusal or another error). It made no value. Thus a
  new start is possible, and the record of the refused start stays as <out>/run.refused-<time>.json.
  State stopped: the run stopped after the first value. Only --continue-missing continues it, with the same files:
  it makes only the outputs that do not exist with the SHA-256 of the run record. It refuses another script,
  another freeze file, another document list and other R2 inputs. The R2 inputs are the files of --r2,
  --r2-calibrations, --r2-gj14 and --r2-platt: path and SHA-256 must be equal to the first start.
  Decisions checks: a decisions file is an output of the run only after its checks passed (chapter 3). If a check
  fails, the run stops, and the files of the document go to <out>/decisions_failed/ (they are not outputs). A
  continuation makes these files again and does the checks of each kept file again.
  The real run always writes the records (GJ.12): it refuses the option --no-records.
  Killed process: the run writes run.json to a temp file and then renames it (run.json.tmp). Thus run.json is
  always a complete record. Before the run writes the decisions files of a document, the key writing of run.json
  names these files. A killed process leaves the state started. Then --continue-missing continues the run. It
  makes the files of the key writing again, also a floor file that the run record does not name as an output.
  The key orphan_files_made_again lists such a file. No hand edit is necessary.

1 Inputs (explicit paths; never a fallback of src/m03_iso_paths.py)
  documents  the key validation of daten/gj/sets.json (44 documents), in the order of the numeric doc id.
  freeze     daten/gj/design_freeze.json (src/m10_freeze.py): not a dry run, no problems.
  design     daten/gj/design/ (frozen by the freeze file; src/m10_design.py does not change).
  states     daten/gj/states/gpu1_labelled/states/<doc>.npz (GPU-1), each file with the SHA-256 of outputs.json.
  floor      daten/gj/calibration/floor_v1.json (src/m10_calibrate.py floor-fit; named in the freeze file).
  rules      daten/gj/rules/<doc>.json (src/m10_rules.py), labels daten/gj/labels/<doc>.json (src/m10_labels.py),
             both with the SHA-256 of the run records of their streams (m10_calibrate.load_documents).
  S1 cache   the cached CSCS answers of the S1 role (daten/iso/sub/s1_role/combined_dev.json and combined_eval.json,
             key role) for the documents with the S1 rule id R1 (criteria 6.1 item 11). Only the keys of the run
             documents are used.
  R2         --r2 FILE {doc_id: {"p", "calibration"}} (the format of m10_design.cascade_decisions) with
             --r2-calibrations FILE {"calibrations": {id: record}} for src/m10_writer.py. The run clips p to
             [0.005, 0.995] with 4 decimals (criteria 8.5). The real run needs these options and --r2-gj14 when
             the design freeze names the R2 Platt map (chapter 2, check R2 required). A check run can omit them.
  GJ.14      --r2-gj14 FILE {doc_id: p_raw} or {doc_id: {"p_raw": x, "p": y}} (the readout of the head H
             without the Platt map on Docling text) and the Platt map --r2-platt (default daten/gj/r2/step0b_platt.json;
             the keys alpha and beta). The map file must have the SHA-256 of the freeze file. The set: the rows of
             daten/gj/jobs/r2_docling/index.csv with set validation and in_gj14_set 1; the reference: the field label
             of the validation rows (subset validation) of daten/cls/r2_dataset.csv (criteria 2.6 item 2).

2 Checks before the first value (a failed check stops the run; nothing is measured)
  guard      src/m10_guard.py allows each document for the split validation only (check run: dev only) and each
             document is in the key of its split in daten/gj/sets.json; src/m00_pruefe_testset.py finds 0 test
             documents (GJ.3).
  freeze     m10_design.load_frozen (SHA-256 of src/m10_design.py and of each design file); the freeze file names
             this file and each file that the run uses (MODULES, src/m10_label_schema.yaml), and these files are
             unchanged now (GJ.11; another changed file of the key code is listed for the protocol),
             m10_calibrate.freeze_check("validation", floor_v1.json), m10_convert.held_out_check, and
             m10_design.assert_apply_allowed on the 44 documents (real path of the freeze file).
  GJ.11 inputs  each input file that the freeze file names has the SHA-256 of the freeze file now (function
             gj11_inputs_check). The files are daten/gj/sets.json, each label file, daten/gj/labels_build.json and
             daten/gj/docs_build.json. More files are the rule run record, outputs.json of the GPU-1 states,
             addendum A and the 3 files of the R2 step 0b fit. A difference refuses the run. An entry that the
             freeze file does not name is listed (key not_named_in_the_freeze_file).
  frozen     FROZEN_FILES of src/m05_gate3a_v4_measure.py: 0 changes (GJ.4), at the start and at the end.
  template   the items of the job gpu1_labelled again from the frozen template and the stored block files: the
             SHA-256 must be the value of the build record (criteria 4 item 7, GJ.8).
  scorer     the reproduction record of src/m10_score.py is MET for this version of the scorer (GJ.6).
  states     the SHA-256 of each states file is the value of outputs.json (the run reads no value for this check).
  S1 cache   the S1 baseline of GJ.15 can be made from the rule files and the S1 cache files (no value is measured).
  R2 files   each R2 file that the command names exists, and the file of --r2 has a value for 1 or more documents
             of the run. In the real run with --r2-gj14, the Platt map is the file of the design freeze.
  R2 required  real run only (function r2_required_check). Condition: the design freeze names the R2 Platt map
             with a SHA-256 and with 0 fit problems. Then the run is refused unless all these items are true:
             --r2, --r2-calibrations and --r2-gj14 are given; the R2 file has a value for each document of the
             run; the GJ.14 set of the index file has the count of the build record
             daten/gj/jobs/r2_docling.build.json (key counts.gj14_set.documents); each document of the set has a
             label yes or no in daten/cls/r2_dataset.csv; the file of --r2-gj14 has a readout p_raw in [0, 1]
             for each document of the set. Cause: without these files the one run ends with GJ.14 NOT MET, and
             criteria 10.3 permits no second run. The option --accept-gj14-not-met stops this check: the main
             agent then accepts GJ.14 NOT MET and R2 as information (criteria chapter 9, note 2). Use it only
             if the command apply of src/m10_r2_step0b.py cannot make the R2 files. The run record keeps it.
  packages   with the record phase only: each package and module of phase C can be imported (RECORD_PACKAGES and
             RECORD_MODULES: yaml, rdflib, linkml, linkml_runtime, src/m06_converter.py, src/m10_gaps.py,
             src/m10_writer.py, src/m10_rdf.py, src/m10_validate.py), and the linkml validators and the Python
             classes of the 3 schemas can be made, also for a record with the gap slot affair_type (addendum A).
             If not, the run is refused before the first value. Without this check, each record fails, and the
             one run ends without GJ.12.

3 Decisions (phase A; one file for each document and each variant)
  floor      m10_cascade.floor_decisions (floor converter F1, criteria 7.4) -> daten/gj/decisions_floor/<doc>.json.
  cascade    m10_design.cascade_decisions for the 4 variants of the entry decisions: d1y_b12y, d1y_b12n, d1n_b12y,
             d1n_b12n (D1 entered yes/no; B1 and B2 entered yes/no) -> <out>/decisions/<variant>/<doc>.json and
             <out>/decisions/<variant>/calibrations.json (m10_design.calibration_file). A document without a
             states file gets the floor decisions with the value status unsure (criteria 4 item 7): the floor
             calibration records lose the key certain_threshold.
  Each file passes m10_cascade.check_decisions and m10_writer.check_decisions before it is an output of the run.

4 Measures and entry decisions (phase B, criteria 6 and 7; <out>/measures.json)
  bootstrap  the documents in the order of the numeric doc id have the indices 0 to D - 1;
             m10_calibrate.bootstrap_draws(D, 2000, 20261013); a resample takes all units of each drawn document
             (a document drawn two times counts two times); the bounds are the 5 % and 95 % quantiles. Paired: the
             same resamples for method and baseline, value = method minus baseline (criteria 6.3).
  GJ.15 D1   method: the D1 decision of the head (variant d1y_b12y). Baseline: the S1 rule role with the cached
             CSCS answers where they exist (criteria 6.1 item 11, map P3). D1 enters if the 5 % quantile of the
             paired gain in accuracy is more than 0 and the count of correct D1 decisions on the documents with the
             reference D1 C is not lower than the count of the baseline minus 1 (criteria 7.1; function entry_d1).
  GJ.16 B1+B2  criteria 7.2 with 6.1 items 5 to 10, and decision M7 of the protocol (13.10.2026, 00:02).
             Units: the non-certain blocks. A certain block has the key certain_pair in the decisions of the
             cascade. The set is the same in each variant (checked), for the method and for the rules.
             Method: the option of the block in the variant d1y_b12y (Viterbi path of B2).
             Baseline: the rule option of the same block as src/m10_rules.py gives it (criteria 6.1 item 10). It
             is the key option of the block in daten/gj/rules/<doc>.json: the plain rule output of the nos4 chain
             without CSCS. A document with the S1 rule id R1 also has the plain rule output (the chain with the
             rule role, not with a D1 decision).
             Condition 1 (decides): the 5 % quantile of the paired document bootstrap of the gain is more than 0.
             The gain is the 6-option accuracy of the method minus the accuracy of this baseline, on the
             non-certain blocks (key accuracy_gain_non_certain, value low_5).
             Condition 2 (decides): the count of L9 exact documents of the method is not lower than the count of
             the rules minus 1. Condition 3 (decides): the same rule for the count of switch-document exact.
             The counts come from m10_score.score_set on all documents (no abstention). The method is the answer
             set "decisions" of the variant d1y_b12y. The rules are the answer set "rules": the nos4 answers of
             daten/gj/rules, thus the same plain rule output. Switch-document exact is the key switch_sr (the
             Submission and Response families of the atom reference change, criteria 2.5).
             B1 and B2 enter if the 3 conditions are true (function entry_blocks).
             Information only: the same bootstrap against the options of the variant d1y_b12n (key
             information.accuracy_gain_non_certain_against_variant_d1y_b12n). This value does not decide. That
             variant gives a document with the S1 rule id R1 the rule chain of the D1 decision of the head
             (criteria 7.1 item 5).
  GJ.17      not applicable when the LoRA trigger of the freeze is false (B1-L did not start).
  variant    the variant of the entry decisions: d1<y|n>_b12<y|n>.
  GJ.13      the written block labels of this variant on all blocks: ECE with 10 bins of equal width of p of the
             written option (correct = the written option is the reference option), and the 95 % bound of the
             document bootstrap. MET if ECE <= 0.05 and the 95 % bound <= 0.08.
  GJ.14      R2 after the Platt map on the GJ.14 set: binary q = (p, 1 - p), each p as written (clip and 4
             decimals). MET if the ECE <= 0.05, the Brier score is lower than the Brier score of H without the
             Platt map (as written), and each document of the set has a readout. Without the readouts or the map,
             or with a problem of the map file: NOT MET, R2 is information (criteria chapter 9, note 2). The same
             rule as src/m10_r2_step0b.py measure-gj14 (the second path for GJ.19).
  GJ.21      the measures of criteria 6.2 (m10_calibrate.measures) for each label kind of the variant and of the
             floor converter F1: all units, the non-certain blocks, each reference source, each parliament and
             each language. The gaps without a switch label have the switch probability of the gap (cascade) or
             p_gap_without_label (floor), clipped to [0.005, 0.995]. After phase C, the key recorded_gaps of
             GJ.21 gets the count of documents with the conformance i95_with_recorded_gaps (addendum A, rule A2
             item 6). The run then writes measures.json again and records its new SHA-256.
  GJ.24      R2 on the 44 documents (only with --r2): reference yes if the reference D1 is B or C (criteria 2.6).

5 Records (phase C, GJ.12; addendum A to the criteria, rules A2 and A3; decision M5)
  The decisions of the variant go to daten/gj/decisions_validation/<doc>.json with calibrations.json (the
  calibration file of the variant; the block_slot records that the blocks use get the target status of GJ.13
  and the validation measure set). Then for each document: m10_writer.write_one, m10_rdf.convert_record and
  m10_validate.validate_record into daten/gj/validation/records/<doc>/, base IRI https://parlpdfech.ansv.ch/id/.
  GJ.12 (part validation) is MET if each document is valid (function gj12). A document is valid if:
  1. it has all files (RECORD_FILES);
  2. the writer check passed (manifest key check_passed);
  3. each of the checks C1 to C9 passed (CHECKS: each key of validation.json by its name);
  4. the sum of the linkml errors of C1 is 0;
  5. its conformance is correct (rule A2): "i95" without a recorded gap, or "i95_with_recorded_gaps" with the
     manifest key i95_gaps and a gap rule that passed (C1_linkml.i95_gap_rule.passed).
  The key passed of validation.json does not decide GJ.12 (it is reported). C10 (SHACL) is information: it is
  reported and never decides (rule A3). A valid record with recorded gaps counts as valid. GJ.12 reports the count
  of documents for each conformance and for each gap slot (rule A2 item 6). Such a record does not conform to I95.

6 Outputs and console
  <out>/result.json (all values), <out>/result.md (English STE), <out>/run.json, <out>/run.events.jsonl,
  <out>/run.log (the output of the imported functions). The console shows only counts, aggregate values, file
  paths and SHA-256 values: no value of one document.

7 Check run (--check-run; only for src/m10_validation_run_test.py)
  The same chain on dev documents (--docs) with another freeze file (--freeze, for example a dry run of
  src/m10_freeze.py) into --work (outside daten/gj). It refuses each document that is not a dev document before a
  file of the document is read. The constant m10_calibrate.DESIGN_FREEZE points to the freeze file of the check run
  only for the time of the freeze check. The check run never writes to daten/gj. It does not open the S1 cache files
  of daten/iso/sub/s1_role (they also hold validation documents): --s1-cache gives a folder with synthetic files.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_validation_run.py
      --r2 FILE --r2-calibrations FILE --r2-gj14 FILE [--r2-platt FILE] [--continue-missing] [--reuse-floor]
      [--accept-gj14-not-met]
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_validation_run.py --check-run
      --docs ID [ID ...] --freeze FILE --work DIR [--states DIR] [--gj14-labels FILE] [--s1-cache DIR]
      [R2 options] [--continue-missing] [--no-records]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)
import m10_docs as docs  # noqa: E402  (interface 2)
import m10_design as md  # noqa: E402  (frozen design, cascade mode; not changed)
import m10_calibrate as cal  # noqa: E402  (measures, bootstrap, floor lookup, freeze_check; not changed)
import m10_cascade as casc  # noqa: E402  (floor mode, check_decisions; not changed)
import m10_score as ms  # noqa: E402  (scorer of L9 and of the blocks; not changed)

VERSION = "m10-validation-run-3"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = ROOT / "daten/gj"
SETS = GJ / "sets.json"
RULES = GJ / "rules"
LABELS = GJ / "labels"
DESIGN = GJ / "design"
STATES = GJ / "states/gpu1_labelled"
FREEZE = GJ / "design_freeze.json"
OUT = GJ / "validation"
DECISIONS_OUT = GJ / "decisions_validation"
FLOOR_OUT = GJ / "decisions_floor"
R2_PLATT = GJ / "r2/step0b_platt.json"
R2_INDEX = GJ / "jobs/r2_docling/index.csv"
R2_BUILD = GJ / "jobs/r2_docling.build.json"
R2_DATASET = ROOT / "daten/cls/r2_dataset.csv"
R2_FIT_FILES = ("step0b_platt.json", "step0b_fitset.json", "step0b_fit_run.json")   # key files of the freeze entry
GJ11_RECORDS = ("sets", "labels_build", "docs_build", "rules_run")                 # keys of additions.records
HEX64 = re.compile(r"[0-9a-f]{64}")
PROMPT_JOB = "gpu1_labelled"
SUB_SPLITS = ROOT / "daten/iso/sub/splits.json"
S1_CACHE = {"dev": ROOT / "daten/iso/sub/s1_role/combined_dev.json",
            "eval": ROOT / "daten/iso/sub/s1_role/combined_eval.json"}
BASE_IRI = "https://parlpdfech.ansv.ch/id/"
STATUS = "EXCEPTION (process rule 10, gate GJ); NOT RELEASED"
ACTOR = ("workflow sub-agents (Claude Opus 5.5), stream A of workflow wf_d5120f1f-fd4, stream H of workflow "
         "wf_f92e9354-619 and stream X1 of wave 5, for the main agent")
VARIANTS = (("d1y_b12y", True, True), ("d1y_b12n", True, False), ("d1n_b12y", False, True), ("d1n_b12n", False, False))
OPTIONS = cal.OPTIONS
D1_OPTIONS = cal.D1_OPTIONS
N_BOOT, SEED, N_BINS = cal.N_BOOT, cal.SEED, cal.N_BINS
GJ13_ECE, GJ13_HIGH, GJ14_ECE = 0.05, 0.08, 0.05
EXPECTED = {"validation": {"documents": 44, "d1_c_documents": 10, "switch_documents": 10}}
RECORD_FILES = ("{d}.ech.yaml", "{d}.provenance.yaml", "{d}.labels.yaml", "manifest.json", "{d}.ech.ttl",
                "{d}.ech.rdf.xml", "{d}.gesamt.trig", "{d}.gesamt.rdf.xml", "validation.json")
CHECKS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme", "C7_C8_labels",
          "C9_e19")
MODULES = ("m10_guard", "m10_docs", "m10_design", "m10_calibrate", "m10_cascade", "m10_score", "m10_writer", "m10_rdf",
           "m10_validate", "m10_gaps", "m10_prompts", "m10_convert", "m10_labels", "m10_rules")
RECORD_PACKAGES = ("yaml", "rdflib", "rdflib.compare", "rdflib.namespace", "linkml", "linkml.validator",
                   "linkml.validator.plugins", "linkml.validator.validation_context", "linkml.generators.pythongen",
                   "linkml_runtime", "linkml_runtime.dumpers", "linkml_runtime.loaders", "linkml_runtime.linkml_model",
                   "linkml_runtime.utils.compile_python")
RECORD_MODULES = ("m06_converter", "m10_gaps", "m10_writer", "m10_rdf", "m10_validate")


class RunRefusal(Exception):
    """The run is refused before a value (a check failed, the one-run rule, a wrong document)."""


# ---------------------------------------------------------------- helpers

def now() -> str:
    return md.now()


def sha(p) -> str:
    return guard.sha256_file(Path(p))


def rel(p) -> str:
    return guard.rel(Path(p))


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p, x) -> str:
    return md.write_json(Path(p), x)


def r6(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 6)


def r4(x) -> float:
    """4 decimals for a value of a calibration record (no exponent form in the YAML and RDF files)."""
    return round(float(x), 4)


def by_id(ids) -> list[str]:
    return sorted({str(d) for d in ids}, key=int)


SAY = sys.stdout


def say(msg: str) -> None:
    """Console output of the run: counts, aggregate values, paths and SHA-256 values only."""
    print(f"[{now()}] {msg}", file=SAY, flush=True)


@dataclass
class Config:
    real: bool
    ids: list[str]
    split: str
    freeze: Path
    out: Path
    decisions_out: Path
    floor_out: Path
    records_out: Path
    design: Path = DESIGN
    states: Path = STATES
    r2: Path | None = None
    r2_cal: Path | None = None
    r2_gj14: Path | None = None
    r2_platt: Path | None = None
    gj14_labels: Path | None = None
    s1_cache: dict | None = None
    continue_missing: bool = False
    reuse_floor: bool = False
    records: bool = True
    accept_gj14_not_met: bool = False


# ---------------------------------------------------------------- run record (GJ.2, one-run rule)

class Record:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.path = cfg.out / "run.json"
        self.ev = cfg.out / "run.events.jsonl"
        self.rec: dict = {}

    def event(self, name: str, **kw) -> str:
        t = now()
        with open(self.ev, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": name, "time": t, **kw}, ensure_ascii=False) + "\n")
        return t

    def save(self) -> None:
        """Write run.json through a temp file and a rename. A killed process leaves the old or the new record."""
        tmp = self.path.with_name(self.path.name + ".tmp")
        raw = (json.dumps(self.rec, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def output(self, p: Path, h: str | None = None) -> str:
        h = h or sha(p)
        self.rec.setdefault("outputs", {})[rel(p)] = h
        return h

    def have(self, p: Path) -> bool:
        """True if p exists with the SHA-256 of the run record (continuation after a technical stop)."""
        h = (self.rec.get("outputs") or {}).get(rel(p))
        return h is not None and Path(p).is_file() and sha(p) == h


def module_sha() -> dict:
    out = {rel(SCRIPT): sha(SCRIPT)}
    for name in MODULES:
        p = ROOT / "src" / f"{name}.py"
        if p.is_file():
            out[rel(p)] = sha(p)
    return out


def r2_inputs(cfg: Config) -> dict:
    """The R2 input files of a start: path and SHA-256 of each file. None: the option was not given. The Platt
    map is the file of --r2-platt, or the default file. A continuation must have the values of the first start."""
    def entry(f) -> dict | None:
        return None if f is None else {"path": rel(f), "sha256": sha(f) if Path(f).is_file() else "absent"}
    return {"r2": entry(cfg.r2), "r2_calibrations": entry(cfg.r2_cal), "r2_gj14": entry(cfg.r2_gj14),
            "r2_platt": entry(cfg.r2_platt or R2_PLATT)}


def start_record(cfg: Config) -> Record:
    cfg.out.mkdir(parents=True, exist_ok=True)
    r = Record(cfg)
    script_sha = sha(SCRIPT)
    freeze_sha = sha(cfg.freeze) if cfg.freeze.is_file() else None
    r2_in = r2_inputs(cfg)
    earlier = []
    if r.path.exists():
        old = read_json(r.path)
        if old.get("state") == "refused" and not old.get("first_value") and not cfg.continue_missing:
            # a refusal before the first value made no value: keep its record and start a new run
            stamp = time.strftime("%Y%m%d-%H%M%S")
            keep = cfg.out / f"run.refused-{stamp}.json"
            r.path.rename(keep)
            if r.ev.exists():
                r.ev.rename(cfg.out / f"run.events.refused-{stamp}.jsonl")
            earlier = list(old.get("earlier_refused_runs") or []) + [rel(keep)]
    if r.path.exists():
        old = read_json(r.path)
        if not cfg.continue_missing:
            raise RunRefusal(f"one-run rule (criteria 10.3): {rel(r.path)} exists (state {old.get('state')}); only "
                             "--continue-missing after a technical stop")
        if old.get("state") == "finished":
            raise RunRefusal(f"one-run rule (criteria 10.3): the run of {rel(r.path)} is finished")
        if (old.get("script") or {}).get("sha256") != script_sha:
            raise RunRefusal("--continue-missing: this file differs from the script of the run record")
        if (old.get("freeze") or {}).get("sha256") != freeze_sha:
            raise RunRefusal("--continue-missing: the freeze file differs from the freeze file of the run record")
        if old.get("documents") != cfg.ids:
            raise RunRefusal("--continue-missing: the document list differs from the run record")
        first = old.get("r2_inputs")
        other = sorted(k for k in r2_in if not isinstance(first, dict) or first.get(k) != r2_in[k])
        if other:
            raise RunRefusal("--continue-missing: the R2 inputs differ from the first start of the run (path or "
                             f"SHA-256): {other}")
        r.rec = old
        r.rec.setdefault("continued", []).append(r.event("continued", sha256=script_sha))
        r.save()
        return r
    if cfg.continue_missing:
        raise RunRefusal("--continue-missing needs the run record of a run with a technical stop")
    r.ev.write_text("", encoding="utf-8")
    r.rec = {"schema": "parlpdfech-gj-validation-run/1", "version": VERSION, "status": STATUS, "actor": ACTOR,
             "gate": "GJ (OPEN)", "kind": "validation run (criteria 10.3)" if cfg.real else
             "check run on dev documents (not a measurement of a held-out set)",
             "started": now(), "script": {"path": rel(SCRIPT), "sha256": script_sha},
             "modules": module_sha(), "freeze": {"path": rel(cfg.freeze), "sha256": freeze_sha},
             "split": cfg.split, "documents": cfg.ids, "r2_inputs": r2_in, "records": bool(cfg.records),
             "accept_gj14_not_met": bool(cfg.accept_gj14_not_met), "state": "started",
             "state_text": "the script SHA-256 is recorded; no value exists", "earlier_refused_runs": earlier}
    r.save()
    r.rec["script_sha256_recorded"] = r.event("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    r.save()
    return r


# ---------------------------------------------------------------- checks before the first value (chapter 2)

def guard_ids(cfg: Config, sets: dict) -> dict:
    """GJ.3: the split guard and src/m00_pruefe_testset.py, before a file of a document is read."""
    want = {str(d) for d in sets[cfg.split]}
    other = [d for d in cfg.ids if d not in want]
    if other:
        raise RunRefusal(f"{len(other)} documents are not in the key {cfg.split} of daten/gj/sets.json")
    try:
        g = guard.assert_allowed(cfg.ids, (cfg.split,))
    except guard.GuardRefusal as e:
        raise RunRefusal(f"GJ.3: {e}") from None
    r = subprocess.run([sys.executable, "-I", str(ROOT / "src/m00_pruefe_testset.py"), *cfg.ids],
                       capture_output=True, text=True, timeout=600, cwd=str(ROOT))
    if r.returncode != 0:
        raise RunRefusal("GJ.3: src/m00_pruefe_testset.py found test documents or unknown parliaments")
    return {"guard": {k: g[k] for k in ("items", "distinct", "allowed_splits", "by_split", "refused",
                                        "test_documents")},
            "m00_pruefe_testset": {"rc": r.returncode, "test_documents": 0},
            "guard_code_sha256": sha(ROOT / "src/m10_guard.py")}


@contextlib.contextmanager
def check_freeze_path(cfg: Config):
    """Check run only: m10_calibrate.DESIGN_FREEZE points to the freeze file of the check run (chapter 7)."""
    if cfg.real:
        yield
        return
    old = cal.DESIGN_FREEZE
    cal.DESIGN_FREEZE = Path(cfg.freeze).resolve()
    try:
        yield
    finally:
        cal.DESIGN_FREEZE = old


def freeze_checks(cfg: Config, sets: dict) -> tuple[md.Frozen, dict, dict]:
    if not cfg.freeze.is_file():
        raise RunRefusal(f"no freeze file {rel(cfg.freeze)}: no validation run before the design freeze "
                         "(criteria 10.1)")
    fz = read_json(cfg.freeze)
    res: dict = {"file": rel(cfg.freeze), "sha256": sha(cfg.freeze), "dry_run": bool(fz.get("dry_run")),
                 "problems": fz.get("problems") or []}
    if cfg.real:
        if Path(cfg.freeze).resolve() != FREEZE.resolve() or fz.get("dry_run") or fz.get("problems"):
            raise RunRefusal("the validation run needs the real freeze file daten/gj/design_freeze.json (not a dry "
                             "run, no problems)")
    else:
        if Path(cfg.freeze).resolve() == FREEZE.resolve():
            raise RunRefusal("the check run never uses the real freeze file")
    try:
        frozen = md.load_frozen(cfg.design, cfg.freeze)
    except md.DesignRefusal as e:
        raise RunRefusal(f"m10_design.load_frozen: {e}") from None
    frozen.freeze["_sha256"] = sha(cfg.freeze)
    res["load_frozen"] = "accepted"
    if frozen.synthetic:
        raise RunRefusal("the design is synthetic")
    code = fz.get("code") or {}
    changed = sorted(p for p, h in code.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h)
    used = {rel(SCRIPT), "src/m10_label_schema.yaml"} | {f"src/{m}.py" for m in MODULES}
    if sorted(set(changed) & used):
        raise RunRefusal(f"GJ.11: files of the freeze that this run uses changed: {sorted(set(changed) & used)}")
    missing = sorted(p for p in used if (ROOT / p).is_file() and p not in code)
    if missing:
        raise RunRefusal(f"the freeze file does not name the SHA-256 of {missing}")
    if code.get(rel(SCRIPT)) != sha(SCRIPT):
        raise RunRefusal("the freeze file does not name the SHA-256 of src/m10_validation_run.py")
    loaded = sorted(rel(Path(m.__file__)) for n, m in sys.modules.items()
                    if n.startswith("m10_") and getattr(m, "__file__", None))
    not_named = [p for p in loaded if p not in code]
    if not_named:
        raise RunRefusal(f"imported modules without a SHA-256 in the freeze file: {not_named}")
    res["code_unchanged"] = {"files": len(code), "used_files_changed": 0,
                             "changed_files_not_used_by_this_run": [p for p in changed if p not in used],
                             "imported_m10_modules": loaded}
    if res["code_unchanged"]["changed_files_not_used_by_this_run"]:
        res["gj11_record"] = ("files of the freeze changed after the freeze; this run does not use them; the "
                              "protocol must record them (GJ.11)")
    res["gj11_inputs"] = gj11_inputs_check(fz)
    with check_freeze_path(cfg):
        try:
            res["m10_calibrate_freeze_check"] = cal.freeze_check("validation", cal.FLOOR_FILE)
        except SystemExit as e:
            raise RunRefusal(f"m10_calibrate.freeze_check: {e}") from None
        import m10_convert as conv  # noqa: PLC0415
        try:
            conv.held_out_check("validation", "stored")
            res["m10_convert_held_out_check"] = "accepted"
        except conv.Stop as e:
            raise RunRefusal(f"m10_convert.held_out_check: {e}") from None
    try:
        res["assert_apply_allowed"] = md.assert_apply_allowed(cfg.ids, frozen, sets)
    except md.DesignRefusal as e:
        raise RunRefusal(f"m10_design.assert_apply_allowed: {e}") from None
    ff = md.frozen_files()
    if ff["different"]:
        raise RunRefusal(f"GJ.4: FROZEN_FILES changed: {ff['different']}")
    res["frozen_files"] = {"files": ff["files"], "different": ff["different"], "source_sha256": ff["source_sha256"]}
    crit = sha(md.CRITERIA)
    if crit != md.CRITERIA_SHA:
        raise RunRefusal("the criteria file differs from the protocol value")
    res["criteria"] = {"path": rel(md.CRITERIA), "sha256": crit}
    res["template"] = template_check(fz)
    try:
        res["scorer_reproduction"] = ms.check_reproduction()
    except SystemExit as e:
        raise RunRefusal(f"GJ.6: {e}") from None
    add = fz.get("additions") or {}
    res["freeze_made"] = add.get("made") or fz.get("made")
    res["lora_trigger"] = (fz.get("choices") or {}).get("lora_trigger")
    return frozen, fz, res


def gj11_inputs_check(fz: dict) -> dict:
    """Chapter 2, check GJ.11 inputs: each input file that the freeze file names has the SHA-256 of the freeze
    file now. The files are daten/gj/sets.json, each label file and the build records of the labels and of the
    documents. More files are the rule run record, outputs.json of the GPU-1 states, addendum A and the 3 files of
    the R2 step 0b fit. The function reads file bytes only. A difference or an absent file refuses the run. An
    entry without a SHA-256 in the freeze file is listed and is not compared."""
    add = fz.get("additions") or {}
    recs, r2 = add.get("records") or {}, add.get("r2_step0b") or {}
    entries = [("sets", fz.get("sets")), ("additions.criteria_addendum_a", add.get("criteria_addendum_a")),
               (f"additions.states.{PROMPT_JOB}.outputs_json",
                ((add.get("states") or {}).get(PROMPT_JOB) or {}).get("outputs_json")),
               ("additions.r2_step0b", r2)]
    entries += [(f"additions.records.{k}", recs.get(k)) for k in GJ11_RECORDS]
    entries += [(f"additions.r2_step0b.files.{k}", (r2.get("files") or {}).get(k)) for k in R2_FIT_FILES]
    pairs, not_named = [], []
    for name, e in entries:
        if isinstance(e, dict) and isinstance(e.get("path"), str) and HEX64.fullmatch(str(e.get("sha256"))):
            pairs.append((e["path"], e["sha256"]))
        else:
            not_named.append(name)
    labels = (fz.get("labels") or {}).get("sha256")
    if isinstance(labels, dict) and labels:
        pairs += [(str(k), str(v)) for k, v in labels.items()]
    else:
        not_named.append("labels.sha256")
    now_sha: dict[str, str | None] = {}
    for path, _ in pairs:
        if path not in now_sha:
            now_sha[path] = sha(ROOT / path) if (ROOT / path).is_file() else None
    different = sorted({path for path, h in pairs if now_sha[path] != h})
    if different:
        raise RunRefusal(f"GJ.11: {len(different)} input files differ from the freeze file or are absent: "
                         f"{different[:20]}")
    return {"compared_files": len(now_sha), "label_files": len(labels) if isinstance(labels, dict) else 0,
            "different": 0, "not_named_in_the_freeze_file": not_named}


def template_check(fz: dict) -> dict:
    """Criteria 4 item 7: the items of the prompt job again from the frozen template and the stored block files."""
    import hashlib  # noqa: PLC0415
    import m10_prompts as mp  # noqa: PLC0415
    tpl = mp.template()
    rec = read_json(mp.JOBS / f"{PROMPT_JOB}.build.json")
    guard.assert_allowed(rec["doc_ids"], mp.allowed_of(PROMPT_JOB))
    h = hashlib.sha256()
    for d in rec["doc_ids"]:
        doc = json.loads(docs.doc_path(d).read_text(encoding="utf-8"))
        h.update((json.dumps(mp.item(doc), ensure_ascii=False) + "\n").encode("utf-8"))
    folder = mp.JOBS / PROMPT_JOB
    want = rec["files"][guard.rel(folder / "items.jsonl")]
    frozen_t = (fz.get("template") or {}).get("template_sha256")
    ok = h.hexdigest() == want and tpl["sha256"] == rec["template_sha256"] == frozen_t
    if not ok:
        raise RunRefusal("GJ.8: the items of the prompt job or the template differ from the frozen values")
    return {"job": PROMPT_JOB, "documents": len(rec["doc_ids"]), "items_sha256": want, "rebuild_equal": True,
            "template_sha256": tpl["sha256"], "is_T0": tpl["sha256"] == md.T0}


def states_check(cfg: Config) -> dict:
    """The SHA-256 of each states file against outputs.json (the run reads no value here)."""
    outs = md.outputs_check(cfg.states) or {}
    have, missing, diff, files = [], [], [], {}
    for d in cfg.ids:
        p = md.npz_path(cfg.states, d)
        if not p.is_file():
            missing.append(d)
            continue
        want = outs.get(f"states/{d}.npz")
        files[rel(p)] = sha(p)
        if want is None or files[rel(p)] != want:
            diff.append(d)
        have.append(d)
    if diff:
        raise RunRefusal(f"{len(diff)} states files differ from {rel(cfg.states / 'outputs.json')} or are not in it")
    return {"folder": rel(cfg.states), "outputs_json": {"path": rel(cfg.states / "outputs.json"),
                                                         "sha256": sha(cfg.states / "outputs.json")},
            "with_states": len(have), "without_states": missing, "files_digest": md.digest_lines(files)}


def record_phase_check() -> dict:
    """Chapter 2, check packages: the record phase (phase C) can start. The function imports each package and
    module of the phase. Then it makes the linkml validators and the Python classes of the 3 schemas, and the
    I95 view and the Python classes for a record with the gap slot affair_type (addendum A). These are the same
    cached objects that phase C uses. It reads no file of a document. A failure refuses the run."""
    import importlib  # noqa: PLC0415
    from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415
    bad = []
    for name in RECORD_PACKAGES + RECORD_MODULES:
        try:
            importlib.import_module(name)
        except (Exception, SystemExit) as e:  # noqa: BLE001  (each import error refuses the run)
            bad.append(f"{name} ({type(e).__name__}: {str(e)[:120]})")
    if bad:
        raise RunRefusal(f"the record phase (GJ.12) cannot start: {len(bad)} packages or modules cannot be imported: "
                         f"{bad}; use the command of the docstring (--with linkml==1.11.1)")
    rdf, val, gp = (sys.modules[m] for m in ("m10_rdf", "m10_validate", "m10_gaps"))
    made = {}
    try:
        for schema in (val.I95, val.PROFILE, val.LABEL_SCHEMA):
            val.validator(schema)
            made[f"validator {rel(schema)}"] = True
        for schema in (rdf.WRAPPER, rdf.PROFILE, rdf.LABEL_SCHEMA):
            rdf.bundle(schema)
            made[f"python classes {rel(schema)}"] = True
        gap = gp.GAP_SLOTS[:1]          # affair_type: the gap slot that the export has (addendum A, chapter 1)
        gp.i95_view(())
        gp.i95_view(gap)
        made[f"I95 view with the gap slot {gap[0]} not required"] = True
        rdf.gap_bundle(rdf.WRAPPER, gap)
        made[f"python classes with the gap slot {gap[0]} not required"] = True
    except (Exception, SystemExit) as e:  # noqa: BLE001
        raise RunRefusal(f"the record phase (GJ.12) cannot start: a linkml validator or the Python classes of a schema "
                         f"cannot be made ({type(e).__name__}: {str(e)[:300]})") from None
    if (gp.I95_CONFORMANT, gp.WITH_GAPS) != ("i95", "i95_with_recorded_gaps") or not Path(gp.ADDENDUM).is_file():
        raise RunRefusal("src/m10_gaps.py has other conformance names than addendum A, or the addendum file is absent")
    versions = {}
    for pkg in ("linkml", "linkml-runtime", "rdflib", "PyYAML", "pyshacl"):
        try:
            versions[pkg] = version(pkg)
        except PackageNotFoundError:
            versions[pkg] = None
    return {"packages": list(RECORD_PACKAGES), "modules": list(RECORD_MODULES), "versions": versions, "made": made,
            "c10_shacl": "runs (information only)" if versions["pyshacl"] else "skipped: pyshacl is not installed "
                                                                              "(C10 is information only)",
            "addendum_a": {"path": rel(gp.ADDENDUM), "sha256": sha(gp.ADDENDUM)}}


def r2_files_check(cfg: Config, fz: dict) -> None:
    """Chapter 2, check R2 files: each R2 file that the command names exists. In the real run with --r2-gj14, the
    Platt map is the file of the design freeze. Without this check, such an error ends the one run with GJ.14
    NOT MET. A failure refuses the run before the first value."""
    for name, f in (("--r2", cfg.r2), ("--r2-calibrations", cfg.r2_cal), ("--r2-gj14", cfg.r2_gj14),
                    ("--r2-platt", cfg.r2_platt)):
        if f is not None and not Path(f).is_file():
            raise RunRefusal(f"the file of {name} does not exist: {rel(f)}")
    if cfg.real and cfg.r2_gj14 is not None:
        platt = cfg.r2_platt or R2_PLATT
        frozen_r2 = (fz.get("additions") or {}).get("r2_step0b") or {}
        if not Path(platt).is_file() or frozen_r2.get("sha256") != sha(platt) or frozen_r2.get("path") != rel(platt):
            raise RunRefusal("GJ.14: the Platt map is not the file of the design freeze (criteria 10.1): start the "
                             "run with the map of the freeze file (no option --r2-platt)")


def r2_required_check(cfg: Config, fz: dict, r2: dict) -> dict:
    """Chapter 2, check R2 required (real run only). r2: the loaded file of --r2. If the design freeze names the
    R2 Platt map with a SHA-256 and with 0 fit problems, the run needs all R2 inputs. Without them, the one run
    ends with GJ.14 NOT MET, and criteria 10.3 permits no second run. A failure refuses the run before the first
    value. The messages give counts only, no document id and no value."""
    frozen_r2 = (fz.get("additions") or {}).get("r2_step0b") or {}
    if not cfg.real:
        return {"required": False, "reason": "check run"}
    if cfg.accept_gj14_not_met:
        return {"required": False, "reason": "option --accept-gj14-not-met: the main agent accepts GJ.14 NOT MET; "
                                             "R2 is information (criteria chapter 9, note 2)"}
    if not HEX64.fullmatch(str(frozen_r2.get("sha256"))):
        return {"required": False, "reason": "the design freeze names no R2 Platt map: GJ.14 is NOT MET, R2 is "
                                             "information (criteria chapter 9, note 2)"}
    if frozen_r2.get("fit_problems"):
        return {"required": False, "reason": "the R2 Platt map of the design freeze has fit problems: GJ.14 is "
                                             "NOT MET, R2 is information (decision M4)"}
    hint = ("first run the command apply of src/m10_r2_step0b.py for the validation documents and the GJ.14 set; "
            "the option --accept-gj14-not-met starts the run without this check (GJ.14 is then NOT MET)")
    absent = [name for name, f in (("--r2", cfg.r2), ("--r2-calibrations", cfg.r2_cal), ("--r2-gj14", cfg.r2_gj14))
              if f is None]
    if absent:
        raise RunRefusal(f"the design freeze names the R2 Platt map: the validation run needs the options --r2, "
                         f"--r2-calibrations and --r2-gj14 (not given: {absent}). Without them GJ.14 is NOT MET, "
                         f"and criteria 10.3 permits no second run; {hint}")
    without = sum(1 for d in cfg.ids if d not in r2)
    if without:
        raise RunRefusal(f"the R2 file {rel(cfg.r2)} has no value for {without} of the {len(cfg.ids)} documents of "
                         f"the run; {hint}")
    want_n = ((read_json(R2_BUILD).get("counts") or {}).get("gj14_set") or {}).get("documents") \
        if R2_BUILD.is_file() else None
    ids = gj14_set_ids()
    if not isinstance(want_n, int) or len(ids) != want_n or len(set(ids)) != len(ids):
        raise RunRefusal(f"GJ.14: the set of {rel(R2_INDEX)} has {len(ids)} rows; the build record {rel(R2_BUILD)} "
                         f"gives the count {want_n} (key counts.gj14_set.documents)")
    try:
        labels, _ = gj14_inputs(cfg)
    except guard.GuardRefusal as e:
        raise RunRefusal(f"GJ.14: {e}") from None
    no_label = sum(1 for d in ids if labels.get(d) not in ("yes", "no"))
    if no_label:
        raise RunRefusal(f"GJ.14: {no_label} of the {len(ids)} documents of the set have no label yes or no in "
                         f"{rel(R2_DATASET)}")
    guard.check_path(Path(cfg.r2_gj14))
    raw = read_json(cfg.r2_gj14)
    if isinstance(raw, dict) and isinstance(raw.get("documents"), dict):
        raw = raw["documents"]

    def readout(v) -> bool:
        pr = v.get("p_raw") if isinstance(v, dict) else v
        return isinstance(pr, (int, float)) and 0 <= pr <= 1
    no_readout = sum(1 for d in ids if not isinstance(raw, dict) or d not in raw or not readout(raw[d]))
    if no_readout:
        raise RunRefusal(f"the file of --r2-gj14 ({rel(cfg.r2_gj14)}) has no readout p_raw in [0, 1] for "
                         f"{no_readout} of the {len(ids)} documents of the GJ.14 set; {hint}")
    return {"required": True, "run_documents_with_r2": len(cfg.ids), "gj14_set_documents": len(ids),
            "gj14_set_documents_of_the_build_record": want_n, "gj14_documents_with_a_label": len(ids),
            "gj14_documents_with_a_readout": len(ids)}


def inputs_record(cfg: Config, frozen: md.Frozen) -> dict:
    """The SHA-256 of the inputs of the run (the states files: chapter 2, check states)."""
    def digest(paths) -> dict:
        x = {rel(p): sha(p) for p in paths}
        return {"files": len(x), "digest": md.digest_lines(x)}
    out = {"sets": {"path": rel(SETS), "sha256": sha(SETS)},
           "labels": digest(LABELS / f"{d}.json" for d in cfg.ids),
           "rules": digest(RULES / f"{d}.json" for d in cfg.ids),
           "docs": digest(docs.doc_path(d) for d in cfg.ids),
           "floor_calibration": {"path": rel(cal.FLOOR_FILE), "sha256": sha(cal.FLOOR_FILE)},
           "design_files": frozen.files,
           "records": {rel(p): sha(p) for p in (cal.RULES_RUN, cal.LABELS_BUILD, SUB_SPLITS) if p.is_file()},
           "s1_cache": {rel(p): sha(p) for p in (cfg.s1_cache or {}).values() if Path(p).is_file()}}
    if cfg.real:
        out["gj14_set"] = {rel(p): sha(p) for p in (R2_INDEX, R2_DATASET) if p.is_file()}
    return out


# ---------------------------------------------------------------- inputs of the measures

def load_r2(path: Path | None) -> dict:
    """{doc_id: {"p", "calibration"}}; p as written (clip to [0.005, 0.995], 4 decimals; criteria 8.5)."""
    if path is None:
        return {}
    guard.check_path(Path(path))
    x = read_json(path)
    if isinstance(x, dict) and isinstance(x.get("documents"), dict):
        x = x["documents"]
    out = {}
    for d, v in (x or {}).items():
        if not str(d).isdigit():
            continue
        if not isinstance(v, dict) or not isinstance(v.get("p"), (int, float)) or not 0 <= v["p"] <= 1 \
                or not isinstance(v.get("calibration"), str):
            raise RunRefusal(f"{rel(path)}: an entry has no p in [0, 1] or no calibration id")
        out[str(d)] = {**v, "p": cal.as_written(v["p"])}
    return out


def load_calibration_records(path: Path | None) -> dict:
    if path is None:
        return {}
    guard.check_path(Path(path))
    x = read_json(path)
    recs = x.get("calibrations") if isinstance(x, dict) else None
    if not isinstance(recs, dict):
        raise RunRefusal(f"{rel(path)}: no key calibrations")
    return recs


def floor_inputs() -> dict:
    calib = read_json(cal.FLOOR_FILE)
    fit_p = ROOT / calib["fit_set"]["path"]
    if sha(fit_p) != calib["fit_set"]["sha256"]:
        raise RunRefusal("the fit set file of the floor calibration file has another SHA-256")
    stripped = {}
    for cid, c in calib["calibrations"].items():
        y = {k: v for k, v in c.items() if k != "certain_threshold"}
        y["calibration_note"] = (c.get("calibration_note", "") + ". Floor label of a document without states "
                                 "(criteria 4 item 7): value status unsure").strip()
        stripped[cid] = y
    return {"lookup": cal.FloorLookup(calib), "fit_docs": {str(x) for x in read_json(fit_p)["documents"]},
            "info": {"path": rel(cal.FLOOR_FILE), "sha256": sha(cal.FLOOR_FILE), "version": calib.get("version")},
            "records_without_threshold": stripped,
            "p_gap_without_label": calib["floor_lookup"]["switch"]["p_gap_without_label"]}


def s1_baseline(ids: list[str], rules: dict, cache_files: dict | None) -> dict:
    """Criteria 6.1 item 11: the S1 rule role with the cached CSCS answers where they exist (map P3). cache_files:
    {"dev": file, "eval": file} (key documents, role); None: no cache file (check run without --s1-cache)."""
    sub = read_json(SUB_SPLITS)
    where = {str(d): s for s in ("dev", "eval") for d in sub.get(s) or []}
    need = [d for d in ids if rules[d]["document"]["d1"].get("needs_apertus")]
    cache = {}
    for s in sorted({where[d] for d in need if d in where}) if cache_files else []:
        if s not in cache_files or not Path(cache_files[s]).is_file():
            continue
        guard.check_path(Path(cache_files[s]))
        stored = read_json(cache_files[s])["documents"]
        cache.update({d: stored[d]["role"] for d in need if d in stored})
    out = {}
    for d in ids:
        s1 = rules[d]["document"]["s1"]
        if d in cache:
            out[d] = {"option": cal.D1_OF_ROLE[cache[d]], "source": "cached CSCS answer"}
        else:
            out[d] = {"option": cal.D1_OF_ROLE[s1["rule_role"]], "source": "S1 rule role"}
    return out


# ---------------------------------------------------------------- phase A: decisions

def variant_dir(cfg: Config, name: str) -> Path:
    return cfg.out / "decisions" / name


def floor_fallback(fl: dict, e1: bool, e2: bool) -> dict:
    dec = copy.deepcopy(fl)
    dec["entry"] = {"d1": e1, "b1_b2": e2}
    dec["fallback"] = "no states file (criteria chapter 4 item 7): floor labels with the value status unsure"
    return dec


def decision_checks(w, d: str, doc: dict, rule: dict, fl: dict, decs: dict, floor: dict, cal_v: dict) -> list[str]:
    """The checks of the decisions of one document: m10_cascade.check_decisions and m10_writer.check_decisions on
    the floor decisions and on the decisions of each variant. An empty list: each check passed."""
    bad = [f"floor: {x}" for x in casc.check_decisions(fl, rule)]
    bad += [f"floor: {x}" for x in w.check_decisions(d, doc, fl, floor["records_without_threshold"])]
    for name, _, _ in VARIANTS:
        dec = decs[name]
        bad += [f"{name}: {x}" for x in casc.check_decisions(dec, rule)]
        cals = cal_v[name] | (floor["records_without_threshold"] if dec.get("fallback") else {})
        bad += [f"{name}: {x}" for x in w.check_decisions(d, doc, dec, cals)]
    return bad


def phase_decisions(cfg: Config, r: Record, frozen: md.Frozen, docs_in: dict, floor: dict, r2: dict,
                    cals_extra: dict, dev_ids: set[str]) -> dict:
    """Phase A. A decisions file becomes an output of the run only after its checks passed. A kept file of a
    continuation gets its checks again. A document with a failed check stops the run after the loop."""
    import m10_writer as w  # noqa: PLC0415
    out_floor = cfg.floor_out
    # the files that a killed process of this run was writing (key writing of the run record): they are made again
    pending = set((r.rec.get("writing") or {}).get("files") or [])
    existing = [d for d in cfg.ids if (out_floor / f"{d}.json").exists() and not r.have(out_floor / f"{d}.json")
                and rel(out_floor / f"{d}.json") not in pending]
    reused = {}
    if existing:
        if not cfg.reuse_floor:
            raise RunRefusal(f"{len(existing)} floor decisions of the run documents exist in {rel(out_floor)} without "
                             "this run record: a floor run exists; use --reuse-floor only for the outputs of its run "
                             "record")
        rec_p = cal.CAL_RUNS / f"cascade_floor_{cfg.split}.json"
        fr = read_json(rec_p) if rec_p.is_file() else {}
        for d in existing:
            p = out_floor / f"{d}.json"
            if (fr.get("outputs") or {}).get(rel(p)) != sha(p):
                raise RunRefusal(f"--reuse-floor: {rel(p)} is not an output of {rel(rec_p)}")
            reused[d] = r.output(p)
    cal_v = {}
    for name, e1, e2 in VARIANTS:
        cal_v[name] = md.calibration_file(frozen, e1, e2)["calibrations"] | cals_extra
    fallback_docs, problems, failed, counts = [], [], [], Counter()
    failed_dir = cfg.out / "decisions_failed"
    first = True
    for d in cfg.ids:
        rule = docs_in[d]["rules"]
        doc = md.load_doc(d)
        pf = out_floor / f"{d}.json"
        files = {name: variant_dir(cfg, name) / f"{d}.json" for name, _, _ in VARIANTS}
        floor_have = r.have(pf)             # made by this run, or an output of the floor run (--reuse-floor)
        kept = floor_have and all(r.have(p) for p in files.values())
        if kept:
            fl = read_json(pf)
            decs = {name: read_json(p) for name, p in files.items()}
        else:
            if first:
                r.rec["first_value"] = r.rec.get("first_value") or r.event(
                    "first_value", what="first decisions (floor and cascade)")
                r.save()
                first = False
            fl = read_json(pf) if floor_have else casc.floor_decisions(rule, floor["lookup"], d in floor["fit_docs"],
                                                                       floor["info"])
            decs = {}
            for name, e1, e2 in VARIANTS:
                dec = md.cascade_decisions(d, frozen, cfg.states, e1, e2, r2.get(d), dev_ids)
                decs[name] = floor_fallback(fl, e1, e2) if dec is None else dec
        bad = decision_checks(w, d, doc, rule, fl, decs, floor, cal_v)
        if bad:
            # no file of this document is an output: a continuation makes the files and the checks again
            problems += [f"{d}: {x}" for x in bad]
            failed.append(d)
            counts["documents_kept_with_failed_checks" if kept else "documents_with_failed_checks"] += 1
            if not kept:
                write_json(failed_dir / "floor" / f"{d}.json", fl)
                for name, dec in decs.items():
                    write_json(failed_dir / name / f"{d}.json", dec)
            continue
        if kept:
            counts["documents_kept"] += 1
        else:
            # the record names the files before the first write: a continuation can make them again after a kill
            r.rec["writing"] = {"document": d, "time": now(),
                                "files": sorted(rel(x) for x in [*files.values()] + ([] if floor_have else [pf]))}
            r.save()
            for name, dec in decs.items():
                r.output(files[name], write_json(files[name], dec))
            if not floor_have:
                if pf.exists():            # only a file of the key writing of a killed process reaches this line
                    r.rec.setdefault("orphan_files_made_again", []).append(
                        {"file": rel(pf), "sha256_before": sha(pf), "time": now()})
                r.output(pf, write_json(pf, fl))
            counts["documents_made"] += 1
            r.rec.pop("writing", None)
            r.save()
        if decs["d1y_b12y"].get("fallback"):
            fallback_docs.append(d)
    if problems:
        r.rec.setdefault("decision_check_stops", []).append({
            "time": now(), "documents": failed, "checks_failed": len(problems), "problems": problems[:200],
            **dict(counts), "files_not_outputs": rel(failed_dir)})
        r.save()
        raise RunRefusal(f"{len(problems)} decisions checks failed in {len(failed)} documents: no file of these "
                         f"documents is accepted; the problems are in {rel(r.path)} (key decision_check_stops)")
    for name, e1, e2 in VARIANTS:
        c = cal_v[name] | (floor["records_without_threshold"] if fallback_docs else {})
        p = variant_dir(cfg, name) / "calibrations.json"
        r.output(p, write_json(p, {"calibrations": c, "variant": name, "entry": {"d1": e1, "b1_b2": e2},
                                   "status": STATUS}))
    r.rec.setdefault("phase_decisions", []).append({"documents": len(cfg.ids), **dict(counts),
                                                    "floor_reused": len(reused),
                                                    "decision_checks": "each file of each document passed",
                                                    "documents_without_states_floor_fallback": fallback_docs,
                                                    "finished": now()})
    r.save()
    return {"fallback_docs": fallback_docs}


def load_decisions(cfg: Config) -> tuple[dict, dict]:
    var = {name: {d: read_json(variant_dir(cfg, name) / f"{d}.json") for d in cfg.ids} for name, _, _ in VARIANTS}
    floor = {d: read_json(cfg.floor_out / f"{d}.json") for d in cfg.ids}
    return var, floor


# ---------------------------------------------------------------- phase B: measures

def draw_counts(n_docs: int) -> np.ndarray:
    draws = cal.bootstrap_draws(n_docs, N_BOOT, SEED)
    cnt = np.zeros((len(draws), n_docs))
    for i, row in enumerate(draws):
        cnt[i] = np.bincount(row, minlength=n_docs)
    return cnt


def paired(cnt: np.ndarray, num_m, num_b, den) -> dict:
    """Paired document bootstrap of a ratio (criteria 6.3): method minus baseline on the same resamples."""
    num_m, num_b, den = (np.asarray(x, dtype=float) for x in (num_m, num_b, den))
    tot = float(den.sum())
    dr = cnt @ den
    ok = dr > 0
    diff = (cnt @ num_m)[ok] / dr[ok] - (cnt @ num_b)[ok] / dr[ok]
    return {"units": int(tot), "method": num_m.sum() / tot if tot else None,
            "baseline": num_b.sum() / tot if tot else None,
            "gain": (num_m.sum() - num_b.sum()) / tot if tot else None,
            "low_5": float(np.quantile(diff, 0.05)) if len(diff) else None,
            "high_95": float(np.quantile(diff, 0.95)) if len(diff) else None,
            "resamples": int(ok.sum()), "resamples_without_units": int((~ok).sum()),
            "method_text": f"paired document bootstrap, {N_BOOT} resamples, seed {SEED}, documents in the order of "
                           "the numeric doc id, 5 % and 95 % quantiles (criteria 6.3)"}


def ece_bootstrap(cnt: np.ndarray, p, correct, g, n_docs: int) -> dict:
    p, correct, g = np.asarray(p, dtype=float), np.asarray(correct, dtype=float), np.asarray(g, dtype=int)
    cell = g * N_BINS + cal.bin_index(p)
    shape = (n_docs, N_BINS)
    n = np.bincount(cell, minlength=n_docs * N_BINS).reshape(shape)
    sc = np.bincount(cell, weights=correct, minlength=n_docs * N_BINS).reshape(shape)
    sq = np.bincount(cell, weights=p, minlength=n_docs * N_BINS).reshape(shape)
    tot = (cnt @ n).sum(1)
    ok = tot > 0
    vals = np.abs(cnt @ sc - cnt @ sq).sum(1)[ok] / tot[ok]
    return {"low_5": float(np.quantile(vals, 0.05)), "high_95": float(np.quantile(vals, 0.95)),
            "resamples": int(ok.sum())}


def macro_f1(ref: list[str], hyp: list[str], options) -> float | None:
    """Criteria 6.1 item 2: an option without a reference unit and without a decision is not in the mean."""
    f1s = []
    for o in options:
        tp = sum(1 for a, b in zip(ref, hyp) if a == o and b == o)
        nr, nh = ref.count(o), hyp.count(o)
        if nr == 0 and nh == 0:
            continue
        p, q = (tp / nh if nh else 0.0), (tp / nr if nr else 0.0)
        f1s.append(2 * p * q / (p + q) if p + q else 0.0)
    return float(np.mean(f1s)) if f1s else None


def gap_probs(dec: dict, p_gap_floor: float) -> list[float]:
    ids = [b["block"] for b in dec["blocks"]]
    if dec.get("gap_switch_probabilities") is not None:
        m = {x["after_block"]: float(x["p"]) for x in dec["gap_switch_probabilities"]}
        return [m[b] for b in ids[:-1]]
    lab = {x["after_block"]: float(x["p"]) for x in dec.get("boundaries") or []}
    return [lab.get(b, p_gap_floor) for b in ids[:-1]]


def units(ids: list[str], decs: dict, labels: dict, meta: dict, p_gap_floor: float) -> dict:
    """The measure units of one decisions set (criteria 6.1 and 6.2). Each probability is clipped (8.5)."""
    B = {k: [] for k in ("Q", "y", "g", "pw", "ok", "certain", "src", "parl", "lang", "cal", "p")}
    D = {k: [] for k in ("Q", "y", "g", "pw", "ok", "src", "parl", "lang")}
    S = {k: [] for k in ("pw", "ok", "g")}
    G = {k: [] for k in ("q", "y", "g")}
    for gi, d in enumerate(ids):
        dec, lab = decs[d], labels[d]
        if [b["block"] for b in dec["blocks"]] != [b["block"] for b in lab["blocks"]]:
            raise RunRefusal(f"{d}: the blocks of a decisions file and of the label file differ")
        ref = [b["option"] for b in lab["blocks"]]
        src, parl, lang = lab.get("reference"), meta[d]["parliament"], meta[d]["language"]
        for j, b in enumerate(dec["blocks"]):
            B["Q"].append([b["probs"][o] for o in OPTIONS])
            B["y"].append(OPTIONS.index(ref[j]))
            B["g"].append(gi)
            B["pw"].append(b["probs"][b["option"]])
            B["ok"].append(b["option"] == ref[j])
            B["certain"].append(bool(b.get("certain_pair")))
            B["cal"].append(b["calibration"])
            for k, v in (("src", src), ("parl", parl), ("lang", lang)):
                B[k].append(v)
        d1 = dec["document"]["d1"]
        D["Q"].append([d1["probs"][o] for o in D1_OPTIONS])
        D["y"].append(D1_OPTIONS.index(lab["d1"]))
        D["g"].append(gi)
        D["pw"].append(d1["probs"][d1["option"]])
        D["ok"].append(d1["option"] == lab["d1"])
        for k, v in (("src", src), ("parl", parl), ("lang", lang)):
            D[k].append(v)
        refg = set(cal.switch_gaps(ref))
        pos = {b["block"]: i for i, b in enumerate(dec["blocks"])}
        for x in dec.get("boundaries") or []:
            S["pw"].append(float(x["p"]))
            S["ok"].append(pos[x["after_block"]] in refg)
            S["g"].append(gi)
        for i, q in enumerate(gap_probs(dec, p_gap_floor)):
            G["q"].append(q)
            G["y"].append(0 if i in refg else 1)
            G["g"].append(gi)
    a = np.asarray
    return {"blocks": {"Q": cal.clip(a(B["Q"], dtype=float).reshape(-1, len(OPTIONS))), "y": a(B["y"], dtype=int),
                       "g": a(B["g"], dtype=int), "pw": cal.clip(a(B["pw"], dtype=float)), "ok": a(B["ok"], dtype=bool),
                       "certain": a(B["certain"], dtype=bool), "src": B["src"], "parl": B["parl"], "lang": B["lang"],
                       "cal": B["cal"]},
            "d1": {"Q": cal.clip(a(D["Q"], dtype=float).reshape(-1, len(D1_OPTIONS))), "y": a(D["y"], dtype=int),
                   "g": a(D["g"], dtype=int), "pw": cal.clip(a(D["pw"], dtype=float)), "ok": a(D["ok"], dtype=bool),
                   "src": D["src"], "parl": D["parl"], "lang": D["lang"]},
            "switch": {"pw": cal.clip(a(S["pw"], dtype=float)), "ok": a(S["ok"], dtype=bool),
                       "g": a(S["g"], dtype=int)},
            "gaps": {"Q": cal.binary_q(cal.clip(a(G["q"], dtype=float))), "y": a(G["y"], dtype=int),
                     "g": a(G["g"], dtype=int)}}


def sub(u: dict, mask) -> dict:
    mask = np.asarray(mask, dtype=bool)
    return {k: (v[mask] if isinstance(v, np.ndarray) else [x for x, m in zip(v, mask) if m]) for k, v in u.items()}


def compact(m: dict) -> dict:
    out = {k: m.get(k) for k in ("n", "accuracy_top_label", "ece", "classwise_ece", "brier", "nll")}
    if m.get("written_option"):
        w = m["written_option"]
        out |= {"written_accuracy": w["accuracy"], "written_ece": w["ece_written_option"]}
    return out


def kind_measures(u: dict) -> dict:
    """GJ.21: the measures of criteria 6.2 for each label kind (m10_calibrate.measures)."""
    b, d, s, g = u["blocks"], u["d1"], u["switch"], u["gaps"]
    out = {"block_slot": cal.measures(b["Q"], b["y"], b["g"], True, b["pw"], b["ok"]),
           "document_text_parts": cal.measures(d["Q"], d["y"], d["g"], True, d["pw"], d["ok"]),
           "author_switch_all_gaps": cal.measures(g["Q"], g["y"], g["g"], True),
           "author_switch_written_labels": cal.written_values(s["pw"], s["ok"])}
    nc = sub(b, ~b["certain"])
    out["block_slot_non_certain"] = cal.measures(nc["Q"], nc["y"], nc["g"], False, nc["pw"], nc["ok"])
    ce = sub(b, b["certain"])
    out["block_slot_certain"] = compact(cal.measures(ce["Q"], ce["y"], None, False, ce["pw"], ce["ok"])) \
        if len(ce["y"]) else {"n": 0}
    for key, name in (("src", "reference_source"), ("parl", "parliament"), ("lang", "language")):
        grp = {}
        for v in sorted({x for x in b[key]} | {x for x in d[key]}, key=str):
            mb, mdd = sub(b, [x == v for x in b[key]]), sub(d, [x == v for x in d[key]])
            grp[str(v)] = {"documents": len(mdd["y"]),
                           "block_slot": compact(cal.measures(mb["Q"], mb["y"], None, False, mb["pw"], mb["ok"]))
                           if len(mb["y"]) else {"n": 0},
                           "document_text_parts": compact(cal.measures(mdd["Q"], mdd["y"], None, False, mdd["pw"],
                                                                       mdd["ok"])) if len(mdd["y"]) else {"n": 0}}
        out[f"by_{name}"] = grp
    return out


def l9_compact(v: dict) -> dict:
    a, c, bl, d1 = v["l9_all_documents"], v["l9_claimed"], v["blocks_6"], v["d1"]
    return {"all_documents": {k: a[k] for k in ("documents", "exact", "exact_rate", "exact_lower", "labelled_f1",
                                                 "labelled_f1_lower", "boundaries_ref", "boundaries_hyp", "correct",
                                                 "text_intrusion", "text_omission", "text_class_error",
                                                 "block_omission", "block_intrusion")}
            | {"switch_sr": {k: a["switch_sr"][k] for k in ("documents", "exact")},
               "switch_l9": {k: a["switch_l9"][k] for k in ("documents", "exact")}},
            "claimed": {k: c[k] for k in ("documents_available", "claimed", "documents", "exact", "labelled_f1")},
            "blocks_6": {k: bl[k] for k in ("blocks", "accuracy_6", "correct_6", "accuracy_l9_family",
                                            "macro_f1_6")},
            "d1": {k: d1[k] for k in ("documents", "correct", "accuracy")}}


def score_sets(cfg: Config) -> dict:
    """L9 and the 6 block options through src/m10_score.py (criteria 6.1 items 6 to 9; GJ.6 first)."""
    ids = cfg.ids
    bodies = ms.parliaments(ids)
    split = {d: ms.split_of(d, bodies.get(d), allow_group7=False) for d in ids}
    if any(s != cfg.split for s in split.values()):
        raise RunRefusal(f"m10_score.split_of gives another split than {cfg.split}")
    table = {d: ms.doc_entry(d) for d in ids}
    atom_ref, block_ref, d1_ref, src = {}, {}, {}, Counter()
    for d in ids:
        atom_ref[d], s, _ = ms.atom_reference(table[d], pilots=True)
        src[s] += 1
        block_ref[d], d1, _ = ms.block_reference(table[d], "labels", LABELS, atom_ref[d])
        if d1:
            d1_ref[d] = d1
    out = {"reference_sources": dict(src)}
    for name, kind, folder in (("rules_nos4", "rules", RULES),
                               ("b12_entered", "decisions", variant_dir(cfg, "d1y_b12y")),
                               ("b12_not_entered", "decisions", variant_dir(cfg, "d1y_b12n")),
                               ("floor_f1", "decisions", cfg.floor_out)):
        aset, shas = ms.load_answer_set(kind, folder, ids, table)
        vals = ms.score_set(ids, aset, table, atom_ref, block_ref, d1_ref)
        out[name] = l9_compact(vals) | {"answer_files_sha256_canonical": ms.canonical_sha(shas)}
    return out


def value_status(decs: dict, cals: dict) -> dict:
    c = Counter()
    for dec in decs.values():
        items = [("block_slot", b["probs"][b["option"]], b["calibration"]) for b in dec["blocks"]]
        d1 = dec["document"]["d1"]
        items.append(("document_text_parts", d1["probs"][d1["option"]], d1["calibration"]))
        items += [("author_switch", x["p"], x["calibration"]) for x in dec.get("boundaries") or []]
        for kind, p, cid in items:
            a = (cals.get(cid) or {}).get("certain_threshold")
            c[f"{kind} {'certain' if a is not None and cal.as_written(p) >= a else 'unsure'}"] += 1
    return dict(sorted(c.items()))


def gj14_set_ids() -> list[str]:
    """The doc ids of the GJ.14 set: the rows of the index file with set validation and in_gj14_set 1."""
    with open(R2_INDEX, newline="", encoding="utf-8") as f:
        return [r["doc_id"] for r in csv.DictReader(f) if r["set"] == "validation" and r["in_gj14_set"] == "1"]


def gj14_inputs(cfg: Config) -> tuple[dict, str]:
    """{doc_id: "yes" | "no"} of the GJ.14 set, and the source text."""
    if not cfg.real:
        if cfg.gj14_labels is None:
            return {}, "no labels for the check run"
        x = read_json(cfg.gj14_labels)
        return {str(k): v for k, v in x.items()}, f"{rel(cfg.gj14_labels)} (check run)"
    ids = gj14_set_ids()
    guard.assert_allowed(ids, ("validation",))
    want, lab, conflict = set(ids), {}, set()
    with open(R2_DATASET, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["split"] == "validation" and r["subset"] == "validation" and r["doc_id"] in want:
                if r["doc_id"] in lab and lab[r["doc_id"]] != r["label"]:
                    conflict.add(r["doc_id"])
                lab[r["doc_id"]] = r["label"]
    if conflict:
        raise RunRefusal(f"GJ.14: {len(conflict)} documents have two different labels in {rel(R2_DATASET)}")
    return lab, f"{rel(R2_INDEX)} (set validation, in_gj14_set 1) and {rel(R2_DATASET)} (field label)"


def find_platt(x) -> tuple[float, float, str]:
    """The keys alpha and beta of the Platt map file (the shallowest object that holds both)."""
    found = []

    def walk(o, path, depth):
        if isinstance(o, dict):
            if isinstance(o.get("alpha"), (int, float)) and isinstance(o.get("beta"), (int, float)):
                found.append((depth, path, float(o["alpha"]), float(o["beta"])))
            for k, v in o.items():
                if isinstance(v, dict):
                    walk(v, f"{path}/{k}", depth + 1)
    walk(x, "", 0)
    if not found:
        raise RunRefusal("the Platt map file has no keys alpha and beta")
    top = min(f[0] for f in found)
    vals = {(a, b) for dep, _, a, b in found if dep == top}
    if len(vals) != 1:
        raise RunRefusal("the Platt map file has two different maps at the same depth")
    dep, path, a, b = next(f for f in found if f[0] == top)
    return a, b, path or "/"


def gj14(cfg: Config, fz: dict) -> dict:
    out = {"criterion": "GJ.14: ECE <= 0.05 and a Brier score lower than H without the Platt map (criteria 9)"}
    platt = cfg.r2_platt or R2_PLATT
    frozen_r2 = ((fz.get("additions") or {}).get("r2_step0b") or {})
    if cfg.r2_gj14 is None:
        return out | {"status": "NOT MET", "information_only": True,
                      "reason": "no readouts of H on the GJ.14 set (--r2-gj14): R2 is information (criteria 9 note 2)"}
    if not Path(platt).is_file():
        return out | {"status": "NOT MET", "information_only": True, "reason": f"no Platt map {rel(platt)}"}
    if cfg.real and (frozen_r2.get("sha256") in (None, "absent") or frozen_r2.get("sha256") != sha(platt)
                     or frozen_r2.get("path") != rel(platt)):
        return out | {"status": "NOT MET", "information_only": True,
                      "reason": "the Platt map is not the file of the design freeze (criteria 10.1)"}
    pm = read_json(platt)
    if isinstance(pm, dict) and pm.get("problems"):
        return out | {"status": "NOT MET", "information_only": True,
                      "reason": f"the Platt map file has problems: {pm['problems']}"}
    alpha, beta, where = find_platt(pm)
    labels, lab_src = gj14_inputs(cfg)
    guard.check_path(Path(cfg.r2_gj14))
    raw = read_json(cfg.r2_gj14)
    if isinstance(raw, dict) and isinstance(raw.get("documents"), dict):
        raw = raw["documents"]
    docs_l = by_id(d for d in labels if d in raw)
    missing = len([d for d in labels if d not in raw])
    if not docs_l:
        return out | {"status": "NOT MET", "information_only": True, "reason": "no readout of a document of the set",
                      "set_documents": len(labels)}
    p_raw, p_given = [], []
    for d in docs_l:
        v = raw[d]
        pr = v.get("p_raw") if isinstance(v, dict) else v
        if not isinstance(pr, (int, float)) or not 0 <= pr <= 1:
            return out | {"status": "NOT MET", "information_only": True,
                          "reason": "a readout has no value p_raw in [0, 1] (H without the Platt map)"}
        p_raw.append(float(pr))
        p_given.append(v.get("p") if isinstance(v, dict) else None)
    p_raw = np.array(p_raw)
    p_pl = cal.apply_platt(p_raw, alpha, beta)
    diff = [abs(cal.as_written(a) - float(b)) for a, b in zip(p_pl, p_given) if isinstance(b, (int, float))]
    w_pl = np.array([cal.as_written(x) for x in p_pl])            # as written: clip and 4 decimals (criteria 8.5)
    w_raw = np.array([cal.as_written(x) for x in p_raw])
    y = np.array([0 if labels[d] == "yes" else 1 for d in docs_l])
    g = np.arange(len(docs_l))
    m_pl = cal.measures(cal.binary_q(w_pl), y, g, True)
    m_raw = cal.measures(cal.binary_q(w_raw), y, g, True)
    met = m_pl["ece"] <= GJ14_ECE and m_pl["brier"] < m_raw["brier"] and missing == 0
    build = GJ / "jobs/r2_docling.build.json"
    want_n = ((read_json(build).get("counts") or {}).get("gj14_set") or {}).get("documents") \
        if cfg.real and build.is_file() else None
    return out | {"status": "MET" if met else "NOT MET", "information_only": not met,
                  "set": lab_src, "set_documents": len(labels),
                  "set_documents_of_the_build_record": want_n, "documents_with_readout": len(docs_l),
                  "documents_without_readout": missing, "positives": int((y == 0).sum()),
                  "platt_map": {"path": rel(platt), "sha256": sha(platt), "alpha": alpha, "beta": beta,
                                "keys_at": where},
                  "readouts": {"path": rel(cfg.r2_gj14), "sha256": sha(cfg.r2_gj14)},
                  "given_p_max_difference": r6(max(diff)) if diff else None,
                  "after_platt": {k: m_pl[k] for k in ("n", "accuracy_top_label", "ece", "ece_equal_mass", "brier",
                                                        "nll", "bootstrap")},
                  "h_without_platt": {k: m_raw[k] for k in ("n", "accuracy_top_label", "ece", "brier", "nll")}}


def gj14_safe(cfg: Config, fz: dict) -> dict:
    """GJ.14 never stops the run: an error of its inputs gives NOT MET (information) with the cause."""
    try:
        return gj14(cfg, fz)
    except (RunRefusal, guard.GuardRefusal, KeyError, ValueError, TypeError, OSError) as e:
        return {"criterion": "GJ.14", "status": "NOT MET", "information_only": True,
                "reason": f"the inputs of GJ.14 cannot be used ({type(e).__name__}: {str(e)[:300]})"}


def gj24(r2: dict, ids: list[str], labels: dict) -> dict:
    have = [d for d in ids if d in r2]
    if not have:
        return {"status": "not measured (no --r2 file)"}
    p = cal.clip(np.array([r2[d]["p"] for d in have]))
    y = np.array([0 if labels[d]["d1"] in ("B", "C") else 1 for d in have])
    m = cal.measures(cal.binary_q(p), y, np.arange(len(have)), True)
    return {"status": "information (GJ.24)", "documents": len(have),
            "reference": "yes if the reference D1 is B or C (criteria 2.6 item 1)",
            **{k: m[k] for k in ("n", "accuracy_top_label", "ece", "brier", "nll", "bootstrap")}}


def entry_d1(cnt: np.ndarray, method_ok, baseline_ok, c_idx) -> dict:
    """Criteria 7.1 item 2: the entry decision of D1 from the counts. method_ok and baseline_ok: 1 for each
    document with a correct D1 option (documents in the order of cnt). c_idx: the indices of the documents with
    the reference D1 C. Condition 1: the 5 % quantile of the paired gain in accuracy is more than 0. Condition 2:
    the correct count of the method on the C documents is not lower than the count of the baseline minus 1."""
    m, b = np.asarray(method_ok, dtype=float), np.asarray(baseline_ok, dtype=float)
    c_idx = [int(i) for i in c_idx]
    g = paired(cnt, m, b, np.ones(len(m)))
    c_m, c_b = int(m[c_idx].sum()), int(b[c_idx].sum())
    c1 = g["low_5"] is not None and g["low_5"] > 0
    c2 = c_m >= c_b - 1
    return {"accuracy_gain": g, "c_documents": len(c_idx), "c_correct_method": c_m, "c_correct_baseline": c_b,
            "condition_1_lower_bound_above_0": bool(c1), "condition_2_c_count": bool(c2), "enters": bool(c1 and c2)}


def entry_blocks(cnt: np.ndarray, k_method, k_rules, n_units, l9_method: int, l9_rules: int, switch_method: int,
                 switch_rules: int) -> dict:
    """Criteria 7.2 item 2: the entry decision of B1 and B2 from the counts. k_method and k_rules: the count of
    correct non-certain blocks of each document for the method and for the rule option of src/m10_rules.py.
    n_units: the count of non-certain blocks of each document. Condition 1: the 5 % quantile of the paired gain in
    accuracy is more than 0. Conditions 2 and 3: the count of L9 exact documents and the count of switch-document
    exact of the method are not lower than the count of the rules minus 1."""
    g = paired(cnt, k_method, k_rules, n_units)
    c1 = g["low_5"] is not None and g["low_5"] > 0
    c2 = int(l9_method) >= int(l9_rules) - 1
    c3 = int(switch_method) >= int(switch_rules) - 1
    return {"accuracy_gain_non_certain": g, "l9_exact_method": int(l9_method), "l9_exact_rules": int(l9_rules),
            "switch_exact_method": int(switch_method), "switch_exact_rules": int(switch_rules),
            "condition_1_lower_bound_above_0": bool(c1), "condition_2_l9": bool(c2), "condition_3_switch": bool(c3),
            "enters": bool(c1 and c2 and c3)}


def phase_measures(cfg: Config, frozen: md.Frozen, fz: dict, docs_in: dict, r2: dict, fallback_docs: list[str]) -> dict:
    ids = cfg.ids
    n = len(ids)
    var, floor = load_decisions(cfg)
    labels = {d: docs_in[d]["labels"] for d in ids}
    rules = {d: docs_in[d]["rules"] for d in ids}
    meta = {}
    for d in ids:
        doc = md.load_doc(d)
        meta[d] = {"parliament": doc.get("parliament"), "language": doc.get("language") or "unknown"}
    cnt = draw_counts(n)
    # ---- D1 (GJ.15, criteria 7.1)
    base = s1_baseline(ids, rules, cfg.s1_cache)
    ref = [labels[d]["d1"] for d in ids]
    head = [var["d1y_b12y"][d]["document"]["d1"]["option"] for d in ids]
    s1 = [base[d]["option"] for d in ids]
    m1 = np.array([h == r for h, r in zip(head, ref)], dtype=float)
    b1 = np.array([s == r for s, r in zip(s1, ref)], dtype=float)
    cidx = [i for i, x in enumerate(ref) if x == "C"]
    dec1 = entry_d1(cnt, m1, b1, cidx)
    c_m, c_b, e1 = dec1["c_correct_method"], dec1["c_correct_baseline"], dec1["enters"]
    no_cscs = [cal.D1_OF_ROLE[rules[d]["document"]["s1"]["rule_role"]] for d in ids]
    d1n = [var["d1n_b12y"][d]["document"]["d1"]["option"] for d in ids]
    gj15 = {"criterion": "criteria 7.1", "documents": n, "method": "D1 head (variant d1y_b12y)",
            "baseline": "S1 rule role with the cached CSCS answers (criteria 6.1 item 11, map P3)",
            "baseline_sources": dict(Counter(base[d]["source"] for d in ids)),
            "documents_with_s1_rule_id_r1": sum(1 for d in ids if rules[d]["document"]["d1"].get("needs_apertus")),
            **dec1,
            "c_recall_method": r6(c_m / len(cidx)) if cidx else None,
            "c_recall_baseline": r6(c_b / len(cidx)) if cidx else None,
            "information": {"macro_f1_method": r6(macro_f1(ref, head, D1_OPTIONS)),
                            "macro_f1_baseline": r6(macro_f1(ref, s1, D1_OPTIONS)),
                            "accuracy_s1_rule_without_cscs": r6(np.mean([a == b for a, b in zip(no_cscs, ref)])),
                            "accuracy_variant_d1_not_entered": r6(np.mean([a == b for a, b in zip(d1n, ref)]))}}
    # ---- blocks (GJ.16, criteria 7.2)
    # km: the method; kr: the rule option of src/m10_rules.py (criteria 6.1 item 10, decision M7: it decides);
    # kv: the options of the variant d1y_b12n (information only)
    km, kr, kv, nn = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    cert_same, differ, differ_docs, cert_plain = True, 0, 0, 0
    for i, d in enumerate(ids):
        yv, nv = var["d1y_b12y"][d], var["d1y_b12n"][d]
        rb = [b["option"] for b in labels[d]["blocks"]]
        if [b["block"] for b in rules[d]["blocks"]] != [b["block"] for b in yv["blocks"]]:
            raise RunRefusal(f"{d}: the blocks of the rule file and of a decisions file differ")
        ro = [b["option"] for b in rules[d]["blocks"]]
        flags = [b.get("certain_pair") for b in yv["blocks"]]
        cert_same &= all([b.get("certain_pair") for b in var[name][d]["blocks"]] == flags for name, _, _ in VARIANTS)
        # information: the certain pairs of the design on the plain rule output give the same set (criteria 6.1 item 5)
        cert_plain += sum(bool(f) != ((b["tier"], b["option"]) in frozen.certain)
                          for f, b in zip(flags, rules[d]["blocks"]))
        before = differ
        for j, b in enumerate(yv["blocks"]):
            if b.get("certain_pair"):
                continue
            nn[i] += 1
            km[i] += b["option"] == rb[j]
            kr[i] += ro[j] == rb[j]
            kv[i] += nv["blocks"][j]["option"] == rb[j]
            differ += ro[j] != nv["blocks"][j]["option"]
        differ_docs += differ > before
    if not cert_same:
        raise RunRefusal("the set of certain blocks differs between the variants (criteria 6.1 item 5)")
    sc = score_sets(cfg)
    l9m, l9r = sc["b12_entered"]["all_documents"]["exact"], sc["rules_nos4"]["all_documents"]["exact"]
    swm = sc["b12_entered"]["all_documents"]["switch_sr"]["exact"]
    swr = sc["rules_nos4"]["all_documents"]["switch_sr"]["exact"]
    sw_docs = sc["rules_nos4"]["all_documents"]["switch_sr"]["documents"]
    dec2 = entry_blocks(cnt, km, kr, nn, l9m, l9r, swm, swr)
    e2 = dec2["enters"]
    g2v = paired(cnt, km, kv, nn)
    all_ref = [b["option"] for d in ids for b in labels[d]["blocks"]]
    gj16 = {"criterion": "criteria 7.2 with 6.1 items 5 to 10 (decision M7 of the protocol, 13.10.2026, 00:02)",
            "documents": n,
            "method": "B2 path of the non-certain blocks (variant d1y_b12y)",
            "baseline": "the rule option of each block as src/m10_rules.py gives it (criteria 6.1 item 10): the key "
                        "option of the block in daten/gj/rules, also for a document with the S1 rule id R1; the nos4 "
                        "answers of daten/gj/rules through src/m10_score.py for the 2 count conditions",
            "blocks": len(all_ref), "certain_blocks": int(len(all_ref) - nn.sum()), "non_certain_blocks": int(nn.sum()),
            "certain_set_equal_in_each_variant": cert_same,
            **dec2, "switch_documents": sw_docs,
            "information": {"macro_f1_6_all_blocks_method": r6(macro_f1(
                                all_ref, [b["option"] for d in ids for b in var["d1y_b12y"][d]["blocks"]], OPTIONS)),
                            "macro_f1_6_all_blocks_rules": r6(macro_f1(
                                all_ref, [b["option"] for d in ids for b in rules[d]["blocks"]], OPTIONS)),
                            "macro_f1_6_all_blocks_variant_d1y_b12n": r6(macro_f1(
                                all_ref, [b["option"] for d in ids for b in var["d1y_b12n"][d]["blocks"]], OPTIONS)),
                            "accuracy_gain_non_certain_against_variant_d1y_b12n": g2v | {
                                "decides": False,
                                "note": "information only: the variant d1y_b12n gives a document with the S1 rule "
                                        "id R1 the rule chain of the D1 decision of the head (criteria 7.1 item 5)"},
                            "non_certain_blocks_where_the_two_baselines_differ": int(differ),
                            "documents_where_the_two_baselines_differ": int(differ_docs),
                            "blocks_with_another_certain_flag_for_the_plain_rule_output": int(cert_plain),
                            "certain_flag_note": "0 means: the certain pairs of the design freeze give the same set "
                                                 "of certain blocks on the plain rule output (criteria 6.1 item 5)"}}
    lora = bool((fz.get("choices") or {}).get("lora_trigger"))
    gj17 = ({"status": "not applicable", "reason": "the LoRA trigger of the design freeze is false: B1-L did not "
                                                    "start (criteria 7.3)"} if not lora else
            {"status": "B1-L does not enter", "reason": "no validation value of B1-L (criteria 7.3 item 4)"})
    chosen = f"d1{'y' if e1 else 'n'}_b12{'y' if e2 else 'n'}"
    # ---- GJ.13 on the written block labels of the variant
    floor_in = floor_inputs()
    cals_ch = read_json(variant_dir(cfg, chosen) / "calibrations.json")["calibrations"]
    u = units(ids, var[chosen], labels, meta, floor_in["p_gap_without_label"])
    b = u["blocks"]
    ece = cal.ece_equal_width(b["pw"], b["ok"])
    bs = ece_bootstrap(cnt, b["pw"], b["ok"], b["g"], n)
    m_all = cal.measures(b["Q"], b["y"], None, False, b["pw"], b["ok"])
    design_view = md.written_measures(b["pw"], b["ok"], np.array(ids)[b["g"]])
    met13 = ece <= GJ13_ECE and bs["high_95"] <= GJ13_HIGH
    gj13 = {"criterion": "GJ.13: ECE <= 0.05 and the 95 % bound of the document bootstrap <= 0.08", "variant": chosen,
            "blocks": int(len(b["y"])), "documents": n, "accuracy_written": r6(b["ok"].mean()), "ece": ece,
            "ece_bootstrap": bs, "ece_equal_mass": r6(cal.ece_equal_mass(b["pw"], b["ok"])),
            "brier_6_options": m_all["brier"], "nll_6_options": m_all["nll"], "classwise_ece": m_all["classwise_ece"],
            "reliability_written_option": cal.reliability_table(b["pw"], b["ok"]),
            "status": "MET" if met13 else "NOT MET",
            "information": {"m10_design.written_measures": {k: design_view.get(k) for k in (
                "n", "accuracy", "ece", "ece_low", "ece_high", "brier", "nll")},
                "note": "the bootstrap of m10_design.written_measures orders the documents by the sorted id text; "
                        "the decision uses the numeric order of m10_calibrate"}}
    # ---- GJ.21 for the variant and the floor converter F1
    uf = units(ids, floor, labels, meta, floor_in["p_gap_without_label"])
    gj21 = {"variant": chosen, "variant_measures": kind_measures(u), "floor_f1": kind_measures(uf),
            "l9": {k: sc[k] for k in ("rules_nos4", "b12_entered", "b12_not_entered", "floor_f1")},
            "reference_sources_of_l9": sc["reference_sources"]}
    variants = {}
    for name, ee1, ee2 in VARIANTS:
        uv = u if name == chosen else units(ids, var[name], labels, meta, floor_in["p_gap_without_label"])
        cv = read_json(variant_dir(cfg, name) / "calibrations.json")["calibrations"]
        variants[name] = {"entry": {"d1": ee1, "b1_b2": ee2},
                          "d1_accuracy": r6(uv["d1"]["ok"].mean()),
                          "d1_written_ece": r6(cal.ece_equal_width(uv["d1"]["pw"], uv["d1"]["ok"])),
                          "block_accuracy": r6(uv["blocks"]["ok"].mean()),
                          "block_written_ece": r6(cal.ece_equal_width(uv["blocks"]["pw"], uv["blocks"]["ok"])),
                          "switch_labels": int(len(uv["switch"]["pw"])),
                          "value_status": value_status(var[name], cv)}
    variants["floor_f1"] = {"d1_accuracy": r6(uf["d1"]["ok"].mean()),
                            "block_accuracy": r6(uf["blocks"]["ok"].mean()),
                            "block_written_ece": r6(cal.ece_equal_width(uf["blocks"]["pw"], uf["blocks"]["ok"])),
                            "switch_labels": int(len(uf["switch"]["pw"])),
                            "value_status": value_status(floor, read_json(cal.FLOOR_FILE)["calibrations"])}
    exp = EXPECTED.get(cfg.split) if cfg.real else None
    counts_check = None
    if exp:
        counts_check = {"documents": n == exp["documents"], "d1_c_documents": len(cidx) == exp["d1_c_documents"],
                        "switch_documents": sw_docs == exp["switch_documents"]}
    return {"schema": "parlpdfech-gj-validation-measures/1", "status": STATUS, "made": now(),
            "documents": n, "split": cfg.split, "counts_against_criteria_chapter_3": counts_check,
            "documents_without_states": fallback_docs,
            "entry": {"GJ.15": gj15, "GJ.16": gj16, "GJ.17": gj17,
                      "variant": chosen, "d1_enters": bool(e1), "b1_b2_enter": bool(e2)},
            "GJ.13": gj13, "GJ.14": gj14_safe(cfg, fz), "GJ.21": gj21, "GJ.24": gj24(r2, ids, labels),
            "variants_information": variants,
            "calibration_ids_of_the_variant_blocks": sorted(set(b["cal"])),
            "variant_calibration_records": len(cals_ch)}


# ---------------------------------------------------------------- phase C: records (GJ.12)

def variant_calibrations(cfg: Config, meas: dict) -> dict:
    """The calibration file of the variant; the block_slot records of its blocks get the target status of GJ.13."""
    chosen = meas["entry"]["variant"]
    cals = copy.deepcopy(read_json(variant_dir(cfg, chosen) / "calibrations.json")["calibrations"])
    g = meas["GJ.13"]
    used = set(meas["calibration_ids_of_the_variant_blocks"])
    ms_rec = {"set_name": f"validation ({meas['documents']} documents): written block labels of the variant "
                          f"{chosen} (GJ.13); ECE of p of the written option, Brier score and NLL of the 6 options",
              "set_n": int(g["blocks"]), "ece": r4(g["ece"]), "ece_equal_mass": r4(g["ece_equal_mass"]),
              "classwise_ece": r4(g["classwise_ece"]), "brier": r4(g["brier_6_options"]), "nll": r4(g["nll_6_options"]),
              "ece_low": r4(g["ece_bootstrap"]["low_5"]), "ece_high": r4(g["ece_bootstrap"]["high_95"]),
              "interval_method": f"document bootstrap, {N_BOOT} resamples, seed {SEED}, 5 % and 95 % quantiles"}
    status = "target_met" if g["status"] == "MET" else "target_not_met"
    for cid in used:
        c = cals[cid]
        if c.get("calibrated_kind") != "block_slot":
            continue
        c["target_status"] = status
        c["measure_sets"] = list(c.get("measure_sets") or []) + [ms_rec]
        c["calibration_note"] = (c.get("calibration_note", "") + f". GJ.13 on validation: {g['status']}").strip()
    return {"calibrations": cals}


def phase_records(cfg: Config, r: Record, meas: dict) -> dict:
    import m06_converter as mc  # noqa: PLC0415
    import m10_rdf as rdf  # noqa: PLC0415
    import m10_validate as val  # noqa: PLC0415
    import m10_writer as w  # noqa: PLC0415
    chosen = meas["entry"]["variant"]
    out = cfg.decisions_out
    out.mkdir(parents=True, exist_ok=True)
    for d in cfg.ids:
        src = variant_dir(cfg, chosen) / f"{d}.json"
        p = out / f"{d}.json"
        if not r.have(p):
            p.write_bytes(src.read_bytes())
            r.output(p)
    cp = out / "calibrations.json"
    if not r.have(cp):
        r.output(cp, write_json(cp, variant_calibrations(cfg, meas)))
    r.save()
    cals, cal_info = w.load_calibrations(cp.resolve())
    todo = [d for d in cfg.ids if not r.have(cfg.records_out / d / "validation.json")]
    fails = {}
    try:
        exp = mc.build_export_records(todo) if todo else {}
    except SystemExit:                       # one document without an export row: build each record alone
        exp = {}
        for d in todo:
            try:
                exp |= mc.build_export_records([d])
            except SystemExit as e:
                fails[d] = f"SystemExit: no export record ({str(e)[:200]})"
        todo = [d for d in todo if d not in fails]
    for i, d in enumerate(todo, 1):
        try:
            w.write_one(d, cfg.records_out, None, exp[d], cals, cal_info, BASE_IRI, w.DOCS_DIR, out)
            rdf.convert_record(cfg.records_out / d, d, BASE_IRI)
            val.validate_record(cfg.records_out / d, d)
        except (SystemExit, Exception) as e:  # noqa: BLE001  (a failed record is a GJ.12 finding)
            fails[d] = f"{type(e).__name__}: {str(e)[:300]}"
            continue
        for name in RECORD_FILES:
            p = cfg.records_out / d / name.format(d=d)
            if p.is_file():
                r.output(p)
        r.save()
        if i % 10 == 0:
            say(f"records: {i} of {len(todo)} documents")
    if fails:
        r.rec.setdefault("record_failures", {}).update(fails)
        r.save()
    return gj12(cfg, fails)


def gj12(cfg: Config, fails: dict) -> dict:
    """GJ.12 for the documents of the run (chapter 5). A document is valid if it has all files, the writer check
    passed, each check of CHECKS (C1 to C9) passed, C1 has 0 linkml errors and its conformance is correct (addendum
    A, rule A2). The key passed of validation.json and check C10 (SHACL) do not decide: they are reported."""
    import m10_gaps as gp  # noqa: PLC0415  (conformance names and gap slots of addendum A)
    per, checks, c10, conf, slots = Counter(), Counter(), Counter(), Counter(), Counter()
    linkml_errors = complete = valid = 0
    n = len(cfg.ids)
    for d in cfg.ids:
        f = cfg.records_out / d
        files_ok = all((f / name.format(d=d)).is_file() for name in RECORD_FILES)
        complete += files_ok
        if not (f / "validation.json").is_file() or not (f / "manifest.json").is_file():
            per["without_validation"] += 1
            continue
        v = read_json(f / "validation.json")
        man = read_json(f / "manifest.json")
        writer_ok = man.get("check_passed") is True
        each = {k: (v.get(k) or {}).get("passed") is True for k in CHECKS}
        c1 = v.get("C1_linkml") or {}
        errors = sum(int(x.get("errors") or 0) for x in c1.get("results") or [])
        # conformance (rule A2): the manifest of the writer and the validation result must agree
        try:
            gaps, gap_bad = gp.manifest_gaps(man)
        except (ValueError, TypeError, KeyError):
            gaps, gap_bad = [], ["the manifest keys of the gaps cannot be read"]
        name = v.get("conformance")
        if name == gp.WITH_GAPS:
            conf_ok = bool(gaps) and not gap_bad and (c1.get("i95_gap_rule") or {}).get("passed") is True
        elif name == gp.I95_CONFORMANT:
            conf_ok = not gaps and not gap_bad and "i95_gap_rule" not in c1
        else:
            conf_ok = False
        conf_ok = conf_ok and man.get("conformance", gp.I95_CONFORMANT) == name and (v.get("i95_gaps") or []) == gaps
        ok = files_ok and writer_ok and all(each.values()) and errors == 0 and conf_ok and d not in fails
        valid += ok
        per["writer_check_passed"] += writer_ok
        per["validation_passed"] += v.get("passed") is True
        per["key_passed_equal_to_c1_to_c9"] += (v.get("passed") is True) == all(each.values())
        per["conformance_correct"] += conf_ok
        for k in CHECKS:
            checks[k] += each[k]
        linkml_errors += errors
        conf[str(name)] += 1
        if ok and name == gp.WITH_GAPS:
            per["valid_with_recorded_gaps"] += 1
        for g in gaps if name == gp.WITH_GAPS and not gap_bad else []:
            slots[g["slot"]] += 1
        c10[str((v.get("C10_shacl") or {}).get("status"))] += 1
    met = valid == n and complete == n and not fails
    return {"criterion": "GJ.12 (part validation): each document has all files of the plan chapter 5.3; the writer "
                         "check and each of the checks C1 to C9 pass; linkml 0 errors; conformance by addendum A rule "
                         "A2; C10 (SHACL) is information (rule A3)",
            "documents": n, "documents_valid": valid, "documents_with_all_files": complete,
            **{k: per[k] for k in ("without_validation", "writer_check_passed", "conformance_correct")},
            "checks_passed": {k: checks[k] for k in CHECKS}, "linkml_errors": linkml_errors,
            "conformance": {gp.I95_CONFORMANT: conf[gp.I95_CONFORMANT], gp.WITH_GAPS: conf[gp.WITH_GAPS],
                            **{k: c for k, c in conf.items() if k not in gp.CONFORMANCE}},
            "documents_with_recorded_gaps": conf[gp.WITH_GAPS],
            "valid_documents_with_recorded_gaps": per["valid_with_recorded_gaps"],
            "recorded_gap_slots": {k: slots[k] for k in gp.GAP_SLOTS},
            "gap_note": "a record with recorded gaps does not conform to I95; it is valid by addendum A rule A2 "
                        "(the count is a result about the standard)",
            "information": {"validation_json_key_passed": per["validation_passed"],
                            "key_passed_equal_to_c1_to_c9": per["key_passed_equal_to_c1_to_c9"],
                            "note": "the key passed of validation.json does not decide GJ.12"},
            "c10_shacl": dict(c10), "c10_shacl_information_only": True, "failed_documents": len(fails),
            "failure_kinds": dict(Counter(x.split(":")[0] for x in fails.values())),
            "base_iri": BASE_IRI, "records": rel(cfg.records_out),
            "status": "MET" if met else "NOT MET"}


def gj21_gap_count(cfg: Config, r: Record, meas: dict, g12: dict | None) -> dict:
    """Addendum A, rule A2 item 6: GJ.21 also reports the count of documents with a recorded gap. The count is
    the count of GJ.12 (phase C): the documents with the conformance i95_with_recorded_gaps. The function writes
    measures.json again only if the entry is new. Then the run record gets the new SHA-256 of the file."""
    if g12 is None:
        entry = {"status": "not measured (no record phase)"}
    else:
        entry = {"rule": "addendum A to the criteria, rule A2 item 6", "set": cfg.split,
                 "documents": g12["documents"], "documents_with_recorded_gaps": g12["documents_with_recorded_gaps"],
                 "conformance": dict(g12["conformance"]), "recorded_gap_slots": dict(g12["recorded_gap_slots"]),
                 "source": "GJ.12: the key conformance of validation.json of each record",
                 "note": "a record with recorded gaps does not conform to I95 (a result about the standard)"}
    if meas["GJ.21"].get("recorded_gaps") != entry:
        meas["GJ.21"]["recorded_gaps"] = entry
        mp = cfg.out / "measures.json"
        r.output(mp, write_json(mp, meas))
        r.rec["measures_gap_count_added"] = r.event("measures_gap_count_added")
        r.save()
    return meas


# ---------------------------------------------------------------- result.md (English STE)

def _f(x, n=4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{n}f}"
    return str(x)


def _kv(x: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in x.items()) if x else "none"


def result_markdown(res: dict) -> str:
    m, run = res["measures"], res["run"]
    e = m["entry"]
    g15, g16 = e["GJ.15"], e["GJ.16"]
    L = []
    add = L.append
    kind = "the one validation run" if run["real"] else "a check run on dev documents (not a held-out run)"
    add("# Gate GJ: result of the validation run")
    add("")
    add(f"Run of {run['started']} to {run['finished']} (time from the clock). This file is the result of {kind}. "
        f"Script `src/m10_validation_run.py`, SHA-256 `{run['script_sha256']}`.")
    add("")
    add("Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: workflow sub-agent "
        "(Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    add("## 1 Order of the records and checks")
    add("")
    add(f"1. The script wrote its SHA-256 into `run.json` at {run['script_sha256_recorded']}.")
    add(f"2. The checks passed at {run['checks_passed']}. The first value came at {run['first_value']}.")
    add(f"3. Freeze file: `{run['freeze']['path']}`, SHA-256 `{run['freeze']['sha256']}`, made at "
        f"{run['freeze_made']}.")
    add(f"4. Documents: {m['documents']} of the set `{m['split']}`. Documents without states: "
        f"{len(m['documents_without_states'])}.")
    add("5. Checks before the first value: guard and `m00_pruefe_testset.py` (0 test documents), freeze file, "
        "FROZEN_FILES (0 changes), template items (equal), scorer reproduction (MET), states files (equal).")
    cu = (res["checks"]["freeze"].get("code_unchanged") or {}).get("changed_files_not_used_by_this_run") or []
    if cu:
        add(f"6. GJ.11 record: {len(cu)} files of the freeze changed after the freeze. This run does not use them: "
            f"{', '.join(f'`{x}`' for x in cu)}.")
    if m.get("counts_against_criteria_chapter_3"):
        cc = m["counts_against_criteria_chapter_3"]
        add(f"{7 if cu else 6}. Counts against criteria chapter 3: documents {_f(cc['documents'])}, documents "
            f"with the reference "
            f"D1 C {_f(cc['d1_c_documents'])}, switch documents {_f(cc['switch_documents'])}.")
    add("")
    add("## 2 Entry decisions (criteria chapter 7)")
    add("")
    gd = g15["accuracy_gain"]
    add("| Value | GJ.15 D1 | GJ.16 B1 and B2 |")
    add("|---|---|---|")
    add(f"| Units | {gd['units']} documents | {g16['accuracy_gain_non_certain']['units']} non-certain blocks |")
    add(f"| Accuracy of the method | {_f(gd['method'])} | {_f(g16['accuracy_gain_non_certain']['method'])} |")
    add(f"| Accuracy of the baseline | {_f(gd['baseline'])} | {_f(g16['accuracy_gain_non_certain']['baseline'])} |")
    add(f"| Gain | {_f(gd['gain'])} | {_f(g16['accuracy_gain_non_certain']['gain'])} |")
    add(f"| 5 % quantile of the gain | {_f(gd['low_5'])} | {_f(g16['accuracy_gain_non_certain']['low_5'])} |")
    add(f"| 95 % quantile of the gain | {_f(gd['high_95'])} | {_f(g16['accuracy_gain_non_certain']['high_95'])} |")
    add(f"| Condition 1: 5 % quantile more than 0 | {_f(g15['condition_1_lower_bound_above_0'])} | "
        f"{_f(g16['condition_1_lower_bound_above_0'])} |")
    add(f"| Condition 2 | C documents {g15['c_documents']}: method {g15['c_correct_method']}, baseline "
        f"{g15['c_correct_baseline']}: {_f(g15['condition_2_c_count'])} | L9 exact: method {g16['l9_exact_method']}, "
        f"rules {g16['l9_exact_rules']}: {_f(g16['condition_2_l9'])} |")
    add(f"| Condition 3 | – | switch documents {g16['switch_documents']}: method {g16['switch_exact_method']}, "
        f"rules {g16['switch_exact_rules']}: {_f(g16['condition_3_switch'])} |")
    add(f"| Enters | {_f(g15['enters'])} | {_f(g16['enters'])} |")
    add("")
    add(f"1. GJ.15: D1 {'enters' if g15['enters'] else 'does not enter'}. The baseline is the S1 rule role with the "
        f"cached CSCS answers (documents for each source: {_kv(g15['baseline_sources'])}). Recall of C: method "
        f"{_f(g15['c_recall_method'])}, baseline {_f(g15['c_recall_baseline'])}.")
    add(f"2. GJ.16: B1 and B2 {'enter' if g16['enters'] else 'do not enter'}. Certain blocks: "
        f"{g16['certain_blocks']}. Non-certain blocks: {g16['non_certain_blocks']}.")
    gv = g16["information"]["accuracy_gain_non_certain_against_variant_d1y_b12n"]
    add("3. The baseline of GJ.16 is the rule option of each block from `src/m10_rules.py` (criteria 6.1, item 10). "
        "The L9 counts of the rules use the same rule output.")
    add(f"4. Information only: against the options of the variant `d1y_b12n`, the gain is {_f(gv['gain'])}. Its 5 % "
        f"quantile is {_f(gv['low_5'])}. The two baselines differ in "
        f"{g16['information']['non_certain_blocks_where_the_two_baselines_differ']} non-certain blocks.")
    add(f"5. GJ.17: {e['GJ.17']['status']}. Reason: {e['GJ.17']['reason']}.")
    add(f"6. The variant of the entry decisions is `{e['variant']}`.")
    add("7. The bootstrap uses 2,000 resamples of the documents with the seed 20261013 (criteria 6.3).")
    add("")
    g13 = m["GJ.13"]
    add("## 3 Calibration of the written block labels (GJ.13)")
    add("")
    add("| Variant | Blocks | Accuracy | ECE | 95 % bound | Brier (6 options) | NLL (6 options) | Result |")
    add("|---|---|---|---|---|---|---|---|")
    add(f"| `{g13['variant']}` | {g13['blocks']} | {_f(g13['accuracy_written'])} | {_f(g13['ece'])} | "
        f"{_f(g13['ece_bootstrap']['high_95'])} | {_f(g13['brier_6_options'])} | {_f(g13['nll_6_options'])} | "
        f"{g13['status']} |")
    add("")
    add("The limits are ECE 0.05 or less and a 95 % bound of 0.08 or less. The bins use p of the written option.")
    add("")
    g14 = m["GJ.14"]
    add("## 4 R2 (GJ.14 and GJ.24)")
    add("")
    if g14.get("after_platt"):
        add(f"1. GJ.14: {g14['status']}. Documents with a readout: {g14['documents_with_readout']} of "
            f"{g14['set_documents']}. ECE after the Platt map: {_f(g14['after_platt']['ece'])}. Brier score after "
            f"the Platt map: {_f(g14['after_platt']['brier'])}. Brier score of H without the map: "
            f"{_f(g14['h_without_platt']['brier'])}.")
    else:
        add(f"1. GJ.14: {g14['status']}. Reason: {g14['reason']}.")
    g24 = m["GJ.24"]
    if g24.get("n"):
        add(f"2. GJ.24 (information): R2 on {g24['n']} documents, accuracy {_f(g24['accuracy_top_label'])}, ECE "
            f"{_f(g24['ece'])}, Brier score {_f(g24['brier'])}.")
    else:
        add(f"2. GJ.24 (information): {g24['status']}.")
    add("")
    g12 = res.get("GJ.12") or {}
    add(f"## 5 Validity of the records (GJ.12, part {m['split']})")
    add("")
    if g12:
        add(f"1. Result: {g12['status']}. Valid documents: {g12['documents_valid']} of {g12['documents']}. Documents "
            f"with all files: {g12['documents_with_all_files']}. Linkml errors: {g12['linkml_errors']}. Failed "
            f"documents: {g12['failed_documents']}.")
        add(f"2. Documents for each check C1 to C9 that passed: {_kv(g12['checks_passed'])}. Documents with a "
            f"writer check that passed: {g12['writer_check_passed']}.")
        add(f"3. Documents for each conformance: {_kv(g12['conformance'])}.")
        add(f"4. Documents with recorded I95 gaps (addendum A, rule A2): {g12['documents_with_recorded_gaps']}. "
            f"Valid documents of these: {g12['valid_documents_with_recorded_gaps']}. Documents for each gap slot: "
            f"{_kv(g12['recorded_gap_slots'])}.")
        add("5. A record with recorded gaps does not conform to I95. It has no invented value.")
        add(f"6. Check C10 (SHACL) is information only. Documents for each status: {_kv(g12['c10_shacl'])}.")
        add(f"7. Base IRI: `{g12['base_iri']}`. Records: `{g12['records']}`.")
    else:
        add("1. The run did not write the records (option --no-records).")
    add("")
    add("## 6 Measures for each label kind (GJ.21)")
    add("")
    g21 = m["GJ.21"]
    gaps = g21.get("recorded_gaps") or {}
    if "documents_with_recorded_gaps" in gaps:
        add(f"Documents with recorded I95 gaps (addendum A, rule A2): {gaps['documents_with_recorded_gaps']} of "
            f"{gaps['documents']}.")
        add("")
    add("| Label kind | Converter | n | Accuracy | ECE | Brier | NLL | Written accuracy | Written ECE |")
    add("|---|---|---|---|---|---|---|---|---|")
    for conv_name, vm in (("variant", g21["variant_measures"]), ("floor F1", g21["floor_f1"])):
        for k in ("document_text_parts", "block_slot", "block_slot_non_certain", "author_switch_all_gaps"):
            c = compact(vm[k])
            add(f"| `{k}` | {conv_name} | {c['n']} | {_f(c['accuracy_top_label'])} | {_f(c['ece'])} | "
                f"{_f(c['brier'])} | {_f(c['nll'])} | {_f(c.get('written_accuracy'))} | {_f(c.get('written_ece'))} |")
    add("")
    add("L9 values through `src/m10_score.py` on all documents (no abstention):")
    add("")
    add("| Answer set | Documents | L9 exact | Switch exact | Labelled boundary F1 | Text intrusion | Block accuracy |")
    add("|---|---|---|---|---|---|---|")
    for name, x in g21["l9"].items():
        a = x["all_documents"]
        add(f"| `{name}` | {a['documents']} | {a['exact']} | {a['switch_sr']['exact']} of "
            f"{a['switch_sr']['documents']} "
            f"| {_f(a['labelled_f1'])} | {_f(a['text_intrusion'])} | {_f(x['blocks_6']['accuracy_6'])} |")
    add("")
    add("Block labels of the variant for each parliament and each language:")
    add("")
    add("| Group | Value | Documents | Blocks | Written accuracy | Written ECE |")
    add("|---|---|---|---|---|---|")
    for grp in ("by_parliament", "by_language", "by_reference_source"):
        for v, x in g21["variant_measures"][grp].items():
            bsl = x["block_slot"]
            add(f"| {grp.replace('by_', '').replace('_', ' ')} | `{v}` | {x['documents']} | {bsl.get('n')} | "
                f"{_f(bsl.get('written_accuracy'))} | {_f(bsl.get('written_ece'))} |")
    add("")
    add("## 7 Limits")
    add("")
    add("1. The reference is the AI reference. It has no human acceptance.")
    add("2. The set is small: the intervals are wide.")
    if run["real"]:
        add("3. The rules saw 42 of the 44 validation documents. This favours the rules (criteria chapter 3).")
    else:
        add("3. A check run uses dev documents. The heads and the maps saw these documents: in-sample values.")
    add("4. All values have the status EXCEPTION and NOT RELEASED. A second AI agent must calculate them again "
        "(GJ.19).")
    add("5. No value of this run changes a frozen file, a threshold, a limit or a choice (criteria 10.3 item 6).")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- the run

def run(cfg: Config) -> dict:
    global SAY
    t0 = time.perf_counter()
    if cfg.real and not cfg.records:
        raise RunRefusal("the validation run always writes the records (GJ.12, one run: criteria 10.3): the option "
                         "--no-records is only for a check run; the run writes no file")
    if cfg.real and not Path(cfg.freeze).is_file():
        raise RunRefusal(f"no freeze file {rel(cfg.freeze)}: no validation run before the design freeze "
                         "(criteria 10.1); the run writes no file")
    cfg.out.mkdir(parents=True, exist_ok=True)
    r = start_record(cfg)
    log = open(cfg.out / "run.log", "a", encoding="utf-8")
    SAY = sys.stdout
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            res = _run(cfg, r, t0)
    except BaseException as e:
        # before the first value: state refused for each error (no value exists, a new start is possible);
        # after the first value: state stopped (only --continue-missing continues the run)
        refusal = isinstance(e, RunRefusal)
        reason = str(e) if refusal else f"{type(e).__name__}: {str(e)[:1500]}"
        r.rec["state"] = "stopped" if r.rec.get("first_value") else "refused"
        r.rec["state_text"] = ("stopped after the first value: only --continue-missing continues the run"
                               if r.rec.get("first_value") else
                               "stopped before the first value: no value exists; a new start is possible")
        r.rec["stop"] = {"time": r.event("stopped", reason=reason[:500] if refusal else type(e).__name__),
                         "reason": reason[:2000], "kind": "refusal" if refusal else "error"}
        r.save()
        raise
    finally:
        log.close()
    return res


def _run(cfg: Config, r: Record, t0: float) -> dict:
    sets = md.load_sets()
    checks = {"guard": guard_ids(cfg, sets)}
    say(f"guard: {len(cfg.ids)} documents of the split {cfg.split}, 0 test documents")
    if cfg.records:
        # before the freeze checks: they also examine each imported m10 module against the freeze file
        checks["record_phase"] = record_phase_check()
        say(f"record phase: {len(RECORD_PACKAGES)} packages and {len(RECORD_MODULES)} modules imported, "
            f"{len(checks['record_phase']['made'])} validators and class sets of the schemas made; C10 (SHACL): "
            f"{checks['record_phase']['c10_shacl']}")
    frozen, fz, fc = freeze_checks(cfg, sets)
    checks["freeze"] = fc
    checks["states"] = states_check(cfg)
    r2_files_check(cfg, fz)
    r2 = load_r2(cfg.r2)
    r2_cals = load_calibration_records(cfg.r2_cal)
    floor = floor_inputs()
    if cfg.r2 is not None and not any(d in r2 for d in cfg.ids):
        raise RunRefusal(f"the R2 file {rel(cfg.r2)} has no value for a document of the run")
    if r2:
        missing = sorted({v["calibration"] for v in r2.values()} - set(r2_cals))
        if missing:
            raise RunRefusal(f"the R2 calibration ids have no record (--r2-calibrations): {missing}")
    checks["r2"] = {"file": None if cfg.r2 is None else {"path": rel(cfg.r2), "sha256": sha(cfg.r2)},
                    "required": r2_required_check(cfg, fz, r2),
                    "documents_with_r2": sum(1 for d in cfg.ids if d in r2),
                    "calibrations": None if cfg.r2_cal is None else {"path": rel(cfg.r2_cal),
                                                                      "sha256": sha(cfg.r2_cal)}}
    docs_in = cal.load_documents(cfg.ids, with_labels=True)
    try:
        # the same call as in phase B: an error of the S1 cache files refuses the run before the first value
        base = s1_baseline(cfg.ids, {d: docs_in[d]["rules"] for d in cfg.ids}, cfg.s1_cache)
    except (KeyError, TypeError, ValueError, OSError, guard.GuardRefusal) as e:
        raise RunRefusal(f"the S1 baseline of GJ.15 cannot be made ({type(e).__name__}: {str(e)[:200]})") from None
    checks["s1_baseline"] = {"documents": len(base), "sources": dict(Counter(v["source"] for v in base.values()))}
    checks["inputs"] = inputs_record(cfg, frozen)
    if r.rec.get("checks"):
        r.rec.setdefault("checks_of_the_continuations", []).append(checks)
    else:
        r.rec["checks"] = checks
        r.rec["checks_passed"] = r.event("checks_passed")
    r.save()
    say(f"checks passed: freeze {rel(cfg.freeze)} ({fc['sha256'][:12]}...), FROZEN_FILES 0 changes, "
        f"template equal, states {checks['states']['with_states']} files equal to outputs.json")
    # ---- phase A (a continuation makes only the missing files)
    dev_ids = {str(d) for d in sets["dev"]}
    pa = phase_decisions(cfg, r, frozen, docs_in, floor, r2, r2_cals, dev_ids)
    say(f"decisions: {len(cfg.ids)} documents, 4 variants and floor F1; without states: {len(pa['fallback_docs'])}")
    # ---- phase B
    mp = cfg.out / "measures.json"
    if r.have(mp):
        meas = read_json(mp)
    else:
        meas = phase_measures(cfg, frozen, fz, docs_in, r2, pa["fallback_docs"])
        r.output(mp, write_json(mp, meas))
        r.rec["measures_made"] = r.event("measures_made")
        r.save()
    e = meas["entry"]
    say(f"entry decisions: GJ.15 D1 enters {e['d1_enters']}, GJ.16 B1 and B2 enter {e['b1_b2_enter']}, "
        f"GJ.17 {e['GJ.17']['status']}; variant {e['variant']}")
    # ---- phase C
    g12 = None
    if cfg.records:
        g12 = phase_records(cfg, r, meas)
        say(f"GJ.12 (part {cfg.split}): {g12['status']}, valid documents {g12['documents_valid']} of "
            f"{g12['documents']}, with all files {g12['documents_with_all_files']}, failed {g12['failed_documents']}, "
            f"with recorded I95 gaps {g12['documents_with_recorded_gaps']} (addendum A, rule A2)")
    meas = gj21_gap_count(cfg, r, meas, g12)
    # ---- end checks
    ff = md.frozen_files()
    mods = module_sha()
    if mods != r.rec["modules"]:
        raise RunRefusal("a script changed during the run")
    loaded = sorted(rel(Path(m.__file__)) for n, m in list(sys.modules.items())
                    if n.startswith("m10_") and getattr(m, "__file__", None))
    not_frozen = [p for p in loaded if (fz.get("code") or {}).get(p) != sha(ROOT / p)]
    if not_frozen:
        raise RunRefusal(f"GJ.11: imported modules without their SHA-256 in the freeze file: {not_frozen}")
    if ff["different"]:
        raise RunRefusal(f"GJ.4: FROZEN_FILES changed during the run: {ff['different']}")
    r.rec["finished"] = r.event("finished")
    run_info = {"real": cfg.real, "started": r.rec["started"], "finished": r.rec["finished"],
                "script_sha256": r.rec["script"]["sha256"], "script_sha256_recorded": r.rec["script_sha256_recorded"],
                "checks_passed": r.rec["checks_passed"], "first_value": r.rec.get("first_value"),
                "freeze": r.rec["freeze"], "freeze_made": checks["freeze"].get("freeze_made"),
                "continued": r.rec.get("continued") or [], "seconds": round(time.perf_counter() - t0, 1)}
    res = {"schema": "parlpdfech-gj-validation-result/1", "status": STATUS, "run": run_info,
           "checks": checks, "measures": meas, "GJ.12": g12,
           "frozen_files_at_the_end": {"files": ff["files"], "different": ff["different"]}}
    rp = cfg.out / "result.json"
    r.output(rp, write_json(rp, res))
    mdp = cfg.out / "result.md"
    mdp.write_text(result_markdown(res), encoding="utf-8")
    r.output(mdp)
    r.rec["state"] = "finished"
    r.rec["state_text"] = "the run is finished (one run: criteria 10.3)"
    r.rec["seconds"] = run_info["seconds"]
    r.save()
    g13, g14 = meas["GJ.13"], meas["GJ.14"]
    summary = {"run": rel(r.path), "result_json": {"path": rel(rp), "sha256": sha(rp)},
               "result_md": {"path": rel(mdp), "sha256": sha(mdp)},
               "GJ.15": {"enters": e["d1_enters"], "gain": r6(e["GJ.15"]["accuracy_gain"]["gain"]),
                         "low_5": r6(e["GJ.15"]["accuracy_gain"]["low_5"]),
                         "c_method": e["GJ.15"]["c_correct_method"], "c_baseline": e["GJ.15"]["c_correct_baseline"]},
               "GJ.16": {"enters": e["b1_b2_enter"], "gain": r6(e["GJ.16"]["accuracy_gain_non_certain"]["gain"]),
                         "low_5": r6(e["GJ.16"]["accuracy_gain_non_certain"]["low_5"]),
                         "l9_method": e["GJ.16"]["l9_exact_method"], "l9_rules": e["GJ.16"]["l9_exact_rules"],
                         "switch_method": e["GJ.16"]["switch_exact_method"],
                         "switch_rules": e["GJ.16"]["switch_exact_rules"]},
               "GJ.17": e["GJ.17"]["status"], "variant": e["variant"],
               "GJ.13": {"status": g13["status"], "ece": r6(g13["ece"]),
                         "high_95": r6(g13["ece_bootstrap"]["high_95"])},
               "GJ.14": g14["status"], "GJ.12": None if g12 is None else g12["status"],
               "GJ.12_documents": None if g12 is None else {
                   k: g12[k] for k in ("documents", "documents_valid", "documents_with_recorded_gaps")},
               "seconds": run_info["seconds"]}
    return summary


# ---------------------------------------------------------------- command line

def config_of(args) -> Config:
    if not args.check_run:
        if args.docs or args.work or args.freeze or args.gj14_labels or args.s1_cache or args.states:
            raise RunRefusal("--docs, --work, --freeze, --states, --gj14-labels and --s1-cache are only for "
                             "--check-run")
        if args.no_records:
            raise RunRefusal("--no-records is only for --check-run: the validation run always writes the records "
                             "(GJ.12; one run, criteria 10.3)")
        sets = md.load_sets()
        return Config(real=True, ids=by_id(sets["validation"]), split="validation", freeze=FREEZE, out=OUT,
                      decisions_out=DECISIONS_OUT, floor_out=FLOOR_OUT, records_out=OUT / "records",
                      r2=Path(args.r2).resolve() if args.r2 else None,
                      r2_cal=Path(args.r2_calibrations).resolve() if args.r2_calibrations else None,
                      r2_gj14=Path(args.r2_gj14).resolve() if args.r2_gj14 else None,
                      r2_platt=Path(args.r2_platt).resolve() if args.r2_platt else None,
                      s1_cache=dict(S1_CACHE), continue_missing=args.continue_missing,
                      reuse_floor=args.reuse_floor, records=True,
                      accept_gj14_not_met=bool(getattr(args, "accept_gj14_not_met", False)))
    if not (args.docs and args.work and args.freeze):
        raise RunRefusal("--check-run needs --docs, --work and --freeze")
    work = Path(args.work).resolve()
    if work.is_relative_to(GJ.resolve()):
        raise RunRefusal("the check run never writes to daten/gj: --work must be another folder")
    guard.check_path(work)
    ids = by_id(i for a in args.docs for i in guard.read_items(a))
    return Config(real=False, ids=ids, split="dev", freeze=Path(args.freeze).resolve(), out=work / "validation",
                  decisions_out=work / "decisions_validation", floor_out=work / "decisions_floor",
                  records_out=work / "validation" / "records",
                  states=Path(args.states).resolve() if args.states else STATES,
                  r2=Path(args.r2).resolve() if args.r2 else None,
                  r2_cal=Path(args.r2_calibrations).resolve() if args.r2_calibrations else None,
                  r2_gj14=Path(args.r2_gj14).resolve() if args.r2_gj14 else None,
                  r2_platt=Path(args.r2_platt).resolve() if args.r2_platt else None,
                  gj14_labels=Path(args.gj14_labels).resolve() if args.gj14_labels else None,
                  s1_cache=None if not args.s1_cache else {
                      s: Path(args.s1_cache).resolve() / f"combined_{s}.json" for s in ("dev", "eval")},
                  continue_missing=args.continue_missing, records=not args.no_records)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--r2")
    ap.add_argument("--r2-calibrations")
    ap.add_argument("--r2-gj14")
    ap.add_argument("--r2-platt")
    ap.add_argument("--continue-missing", action="store_true")
    ap.add_argument("--reuse-floor", action="store_true")
    ap.add_argument("--accept-gj14-not-met", action="store_true",
                    help="real run: start without the check R2 required (GJ.14 is then NOT MET, R2 is information)")
    ap.add_argument("--no-records", action="store_true", help="check run only: no record phase (no GJ.12)")
    ap.add_argument("--check-run", action="store_true")
    ap.add_argument("--docs", nargs="*")
    ap.add_argument("--work")
    ap.add_argument("--freeze")
    ap.add_argument("--states")
    ap.add_argument("--gj14-labels")
    ap.add_argument("--s1-cache", help="check run: a folder with combined_dev.json and combined_eval.json")
    args = ap.parse_args()
    try:
        cfg = config_of(args)
        summary = run(cfg)
    except RunRefusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
