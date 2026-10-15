# SPDX-License-Identifier: Apache-2.0
"""make run-earlier: convert the samples from their stored input, validate the output, print the stored results.

Written in English to the STE rules (ASD-STE100, Issue 9).

The converter code in src/converter/ is a copy of the code of the private project (SOURCES.md). That code
reads its files from a fixed folder layout below one project folder (src/, daten/, quellen/). This script
makes that layout in build/layout/ from the files of this repository and runs the copied code there. It
changes no copied file.

Steps:
  1. Check the downloads of `make setup`: the two eCH-0295 schema files (SHA-256 of the pinned commit).
  2. Make build/layout/:
     - src/: the files of src/converter/ (code, profile) and the prompts of src/prompts/ without their first
       line (the license line), so that the S1 prompt has the SHA-256 that the runner examines;
     - daten/: for each sample, the stored atoms and the stored Docling output; the export records; the
       method files of src/converter/method/; guard files with a header only (no development list, no
       test list, no reference answers);
     - quellen/: the two schema files.
  3. Stage 1 (rule stage, method nos4, isolation level L9): src/m05_iso_runner.py run, CSCS mode
     cache-only, on a sealed selection of the sample ids (selection file and its SHA-256 file).
  4. Stage 2 (eCH-0295 writer): src/m06_converter.py convert --validate.
  5. Validator: src/validate_ech.py on each instance (I95, class Container) and each provenance side file
     (profile, class ExtractionRecord).
  6. Compare the output with samples/<doc>/expected/ (the values of the runner and the two YAML files; the
     time of the run is not compared).
  7. Print the stored results table (results/stored_results.json).
Exit code 0 only if each step passes.

Usage (from track_2a/): uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python src/run_samples.py
  Option --write-expected: write the output to samples/<doc>/expected/ (only for the maintainer).
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # track_2a/src
TRACK = HERE.parent                               # track_2a
SAMPLES = TRACK / "samples"
LAYOUT = TRACK / "build" / "layout"
CACHE = TRACK / ".cache" / "ech-0295"
RESULTS = TRACK / "results" / "stored_results.json"
SPDX = "# SPDX-License-Identifier: Apache-2.0\n"
S1_PROMPT_SHA256 = "a458b4258d86c895b52e781b60c738e2c2cd81db9ca257d503aa09440386298f"

sys.path.insert(0, str(HERE))
import fetch_schema as fs  # noqa: E402

# header lines of the guard files of the private layout (the files hold no row here)
GUARD_HEADERS = {
    "daten/iso/gruppen.csv": "group,doc_id,body_key,split,ebene,sprache,scan,dokumentrolle,seiten,sha256,url",
    "daten/iso/pool.csv": "part,home,doc_id,body_key,ebene,sprache,scan,dokumentrolle,seiten,sha256",
    "daten/iso/triage.csv": "doc_id,batch,final,verdict_a,categories_a,atoms_a,verdict_b,categories_b,atoms_b,actor,criteria,date",
    "daten/analyse/synthese/split.csv": "body_key,name_de,ebene,sprache,rolle,begruendung,geschaefte,"
                                        "geschaefte_mit_pdf_text,anteil_scan_verdacht,texts_datei,texts_zu_vorstoessen,"
                                        "pilot_kandidaten,typ_label_pdf,empfehlung_pdf,entscheid_pdf,dok_vorstoss,dok_antwort",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def say(text: str) -> None:
    print(text, flush=True)


def sample_ids() -> list[str]:
    return sorted((p.name for p in SAMPLES.iterdir() if (p / "source.json").exists()), key=int)


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ layout
def make_layout(ids: list[str]) -> None:
    if LAYOUT.exists():
        shutil.rmtree(LAYOUT)
    src = LAYOUT / "src"
    src.mkdir(parents=True)
    for p in sorted((HERE / "converter").iterdir()):
        if p.is_file():
            shutil.copyfile(p, src / p.name)
    (src / "prompts").mkdir()
    for p in sorted((HERE / "prompts").glob("s*_*.txt")):
        raw = p.read_text(encoding="utf-8")
        if not raw.startswith(SPDX):
            raise SystemExit(f"{p.name}: the first line is not the license line")
        (src / "prompts" / p.name).write_text(raw[len(SPDX):], encoding="utf-8")
    got = sha256(src / "prompts" / "s1_role.txt")
    if got != S1_PROMPT_SHA256:
        raise SystemExit(f"S1 prompt without the license line has SHA-256 {got}, frozen value {S1_PROMPT_SHA256}")

    d = LAYOUT / "daten"
    for doc in ids:
        inp = SAMPLES / doc / "input"
        for kind, name in (("atome", "atoms.json"), ("docling", "docling.json")):
            (d / "iso" / kind).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(inp / name, d / "iso" / kind / f"{doc}.json")
        (LAYOUT / "export").mkdir(exist_ok=True)
        shutil.copyfile(inp / "export.json", LAYOUT / "export" / f"{doc}.json")
    (d / "analyse" / "pdf").mkdir(parents=True)
    (d / "analyse" / "pdf" / "docs_pdf_index.csv.gz").write_bytes(
        gzip.compress((SAMPLES / "pdf_index.csv").read_bytes(), mtime=0))
    (d / "analyse" / "lehrer_stichprobe").mkdir(parents=True)
    shutil.copyfile(SAMPLES / "languages.csv", d / "analyse" / "lehrer_stichprobe" / "auswahl_lehrer.csv")
    for rel, header in GUARD_HEADERS.items():
        (LAYOUT / rel).parent.mkdir(parents=True, exist_ok=True)
        (LAYOUT / rel).write_text(header + "\n", encoding="utf-8")
    (d / "gold" / "records" / "review").mkdir(parents=True)
    method = HERE / "converter" / "method"
    (d / "iso" / "ladder" / "scratch").mkdir(parents=True)
    shutil.copyfile(method / "ladder.json", d / "iso" / "ladder" / "ladder.json")
    for split in ("dev", "eval"):
        write_json(d / "iso" / "ladder" / "scratch" / f"err_recompose_nos4_{split}.json", {})
    sel = json.loads((method / "s1_selection.json").read_text(encoding="utf-8"))
    s1 = d / "iso" / "sub" / "s1_role"
    for name in ("rule", "apertus", "combined"):
        for split in ("dev", "eval"):
            body = {"documents": {}}
            if (name, split) == ("combined", "dev"):
                body = {k: sel[k] for k in ("chosen", "sure_ids", "apertus_prompt_sha256")} | body
            write_json(s1 / f"{name}_{split}.json", body)
    q = LAYOUT / "quellen" / "political-affairs-ech-group"
    for rel in fs.FILES:
        (q / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CACHE / rel, q / rel)

    selection = LAYOUT / "selection"
    selection.mkdir()
    with open(selection / "selection.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doc_id", "final"])
        for doc in ids:
            src_rec = json.loads((SAMPLES / doc / "source.json").read_text(encoding="utf-8"))
            w.writerow([doc, src_rec["triage_personal_data"]])
    (selection / "selection.sha256").write_text(f"{sha256(selection / 'selection.csv')}  selection/selection.csv\n",
                                                encoding="utf-8")


# ------------------------------------------------------------------ stages
def run(cmd: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(cmd, cwd=LAYOUT, capture_output=True, text=True, env=env, timeout=1800)


def stage(name: str, cmd: list[str]) -> bool:
    say(f"\n== {name}")
    p = run(cmd)
    for line in p.stdout.splitlines():
        if line.strip():
            say("   " + line)
    if p.returncode != 0:
        say(f"   FAIL (exit code {p.returncode})")
        for line in p.stderr.strip().splitlines()[-15:]:
            say("   " + line)
        return False
    return True


# ------------------------------------------------------------------ comparison with the stored output
def runner_core(rec: dict) -> dict:
    return {"nos4": rec["nos4"], "l9": rec["l9"]["answers"],
            "claims": {k: [v["claimed"], v["abstention_reason"]] for k, v in rec["claims"].items()},
            "s1": [rec["s1"]["rule_role"], rec["s1"]["rule_id"], rec["s1"]["combined_role"], rec["s1"]["source"]],
            "s2": rec["s2"], "converter_role": rec["converter_role"], "ids": rec["ids"],
            "atoms_sha256": rec["inputs"]["atome"]["sha256"]}


def without_run_time(text: str) -> str:
    return "\n".join(z for z in text.splitlines() if not z.strip().startswith("datetime_generated:"))


def outputs(doc: str) -> dict[str, str]:
    rec = json.loads((LAYOUT / "out" / "run" / "records" / f"{doc}.json").read_text(encoding="utf-8"))
    return {"runner_core.json": json.dumps(runner_core(rec), indent=1, ensure_ascii=False) + "\n",
            "instance.yaml": (LAYOUT / "out" / "ech" / "instances" / f"{doc}.yaml").read_text(encoding="utf-8"),
            "provenance.yaml": (LAYOUT / "out" / "ech" / "provenance" / f"{doc}.yaml").read_text(encoding="utf-8")}


def compare(ids: list[str], write: bool) -> bool:
    say("\n== Comparison with the stored output (samples/<doc>/expected/)")
    ok = True
    for doc in ids:
        exp_dir = SAMPLES / doc / "expected"
        got = outputs(doc)
        if write:
            exp_dir.mkdir(exist_ok=True)
            for name, text in got.items():
                (exp_dir / name).write_text(text, encoding="utf-8")
            say(f"   {doc}: written")
            continue
        res = []
        for name, text in got.items():
            p = exp_dir / name
            same = p.exists() and without_run_time(p.read_text(encoding="utf-8")) == without_run_time(text)
            res.append(f"{name} {'equal' if same else 'DIFFERENT'}")
            ok &= same
        say(f"   {doc}: " + ", ".join(res))
    return ok


# ------------------------------------------------------------------ stored results
def print_results() -> None:
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    say(f"\n== Stored results ({RESULTS.relative_to(TRACK)}, state of {r['state_date']})")
    say(f"   History of {r['state_date']}, not the product of this version (see results/README.md). No value below")
    say(f"   comes from this run. On {r['state_date']}, both gates were OPEN.")
    for part in r["parts"]:
        say(f"\n   {part['title']}  [gate: {part['gate_status']}]")
        w = max(len(x["item"]) for x in part["rows"])
        for x in part["rows"]:
            say(f"   - {x['item'].ljust(w)}  {x['value']}")
        say(f"     Source: {part['source']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write-expected", action="store_true")
    a = ap.parse_args()
    ids = sample_ids()
    say(f"ParlPDFeCH, make run-earlier: {len(ids)} samples ({', '.join(ids)}); no GPU, no model, no network")
    bad = fs.check()
    if bad:
        say("Missing or changed schema files: " + "; ".join(bad) + ". Run `make setup` first.")
        return 2
    make_layout(ids)
    say(f"Layout: {LAYOUT.relative_to(TRACK)} (copied code, stored inputs, schema files)")
    py = sys.executable
    ok = stage("Stage 1: rule stage (runner, method nos4, isolation level L9)",
               [py, "src/m05_iso_runner.py", "run", "--out", "out/run", "--selection", "selection/selection.csv",
                "--selection-sha256", "selection/selection.sha256", "--cscs", "cache-only"])
    ok = ok and stage("Stage 2: eCH-0295 writer with validation (I95 and profile)",
                      [py, "src/m06_converter.py", "convert", "--run", "out/run", "--export", "export",
                       "--out", "out/ech", "--validate"])
    if ok:
        files = sorted((LAYOUT / "out" / "ech" / "instances").glob("*.yaml"))
        files += sorted((LAYOUT / "out" / "ech" / "provenance").glob("*.yaml"))
        ok = stage("Validator (src/validate_ech.py)", [py, str(HERE / "validate_ech.py"), *map(str, files)])
    if ok:
        ok = compare(ids, a.write_expected)
    print_results()
    say(f"\nResult of make run-earlier: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
