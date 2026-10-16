# Map of the folder track_2a

This table gives each folder of `track_2a/`, what it holds, its source in the private project and its state from 14.10.2026 to 16.10.2026. `SOURCES.json` and `SOURCES.md` give the source and the SHA-256 of each copied file and each edit.

## Folders

| Folder | What it holds | Source in the private project | State |
|---|---|---|---|
| `track_2a/` (files) | `README.md`, `technical_report.md`, `numbers.json` and `numbers.md`, `SOURCES.json` and `SOURCES.md`, `Makefile`. History: `technical_report_numbers.json`, the numbers file of the report of 12.10.2026 (earlier converter); `numbers.json` replaces it for the numbers of the texts. | written for the submission; `numbers.json` from the tool `src/m11_numbers.py` | written |
| `app/` | The app: a PDF of a Swiss parliament goes in, an eCH-0295 record comes out. A self-contained source tree: Rust server, page, Python worker, view, contract, container files. 230 files: the 229 files of the list `DIST-MANIFEST.json` and the list. Since 16.10.2026 the worker also has the Apertus step of `make convert` (`worker/apertus_*.py`, `worker/values_apertus.py`). The page has the start page (`#/`), the page "About" (`#/about/<part>`), the result view (`#/view/<record_id>`) and the technical view (`#/record/<record_id>`). `docs/run-locally.md` tells how to start it. | `package/` of commit `5153118` with 18 changed files (`DIST-MANIFEST.json`), made by `make dist-src` (`package/worker/make_dist.py`) and copied by `src/m11_public_app.py` | copied on 14.10.2026, and again on 16.10.2026 (last at 02:32 UTC). 3 files of `app/layout/src/` have an edit (next row). The 3 sample PDF files are an addition (row `app/data/samples/`). |
| `app/layout/` | The code layout: 98 files that the worker runs or examines (converter code, schemas, calibration and design files), with `layout_manifest.json`. Since 16.10.2026 it also has the files of the Apertus step: the prompt code and the read-out engine of the fixed run, the value heads and the combined reader. It also has new versions of the writer and the validator (`src/m12_*.py`). | `package/build/layout/`, byte-equal copies of files of `src/`, `daten/`, `quellen/` and `crisp-dm/` | copied. `m03_atome.py`, `m03_docling_zerlegen.py`, `m03_sub_assemble.py`: line 1 is the licence line, and a path of the private computer and an internal role name are replaced. The 2 file lists of the tree have the new SHA-256 of these 3 files. |
| `app/data/samples/` | The stored inputs of the 3 samples, the PDF (`source.pdf`) and one image of each page (`page-<n>.png`). `index.json` gives the URL of the publisher of each PDF. | `package/data/samples/` | copied. The tool `make dist-src` does not copy a PDF file; `src/m11_public_app.py` adds the 3 PDF files and records them in the key `publication_additions` of `DIST-MANIFEST.json`. The worker puts a copy of the PDF into each sample result. |
| `src/converter_gj/` | The reader of the values from the PDF: rules, value normalisation, the cascade over eCH-0295, the combined reader, the calibration, the writer, the validator, the questions to Apertus. 32 files. | `src/m11_*`, `src/m10_*`, `src/m03_ech_export_schema.yaml` | copied on 14.10.2026, with the licence line. `src/converter_gj/README.md` gives the files and their imports. |
| `src/prompts/gj_values_v1_de/` | The template of the value questions Q0, Q1 and Q2: 6 text files and `template.json` | output of `python src/m11_prompts_values.py write` (`daten/gj_values/prompts/gj_values_v1_de/`) | copied on 14.10.2026 |
| `src/prompts/gj_jev_v1_de/` | The template of the block role questions D1 and B1 | the job records of the project | written on 13.10.2026 |
| `src/prompts/` (files) | History: the prompts of the earlier converter (S1 to S5) and of the earlier Apertus head of task R2 (12.10.2026) | `src/prompts/`, `src/m05_cls_apertus.py` | copied on 12.10.2026 |
| `src/converter/` | The earlier converter of 12.10.2026 (path 1). The reader in `src/converter_gj/` imports 21 of its modules and 1 schema file. | `src/m02_*` to `src/m06_*` | copied on 12.10.2026 |
| `src/converter/method/` | 2 method files of the earlier converter, reduced | `daten/iso/ladder/`, `daten/iso/sub/s1_role/` | copied on 12.10.2026 |
| `src/apertus_head/` | The earlier Apertus head of task R2 (path 2, 12.10.2026). The R2 head is not a part of the product. The reader in `src/converter_gj/` imports 5 of its modules. | `src/m02_*` to `src/m07_*` | copied on 12.10.2026 |
| `src/` (files) | The tools of stages 1 to 3 of the first public version (06.10.2026), and the check tools of this folder: `check_sources.py`, `check_prompts.py`, `validate_ech.py`, `fetch_schema.py`, `run_samples.py` | `src/` | stage tools: copied on 06.10.2026; check tools: copied or written from 12.10.2026 to 14.10.2026 |
| `samples/` | History: the 3 samples of the earlier converter (stored input, expected output, 2 reduced tables), `NOTICE.md` and `README.md` | `daten/iso/`, the export, `daten/analyse/` | copied on 12.10.2026; `README.md` written on 15.10.2026 |
| `results/` | History: `stored_results.json`, the stored results of 12.10.2026 that `make run-earlier` prints, and `README.md` | the earlier converter | written on 12.10.2026; `README.md` on 15.10.2026 |
| `docs/` | The limits, the long report, figure 1, the stages 1 to 3; how to run the app on your computer (`run-locally.md`); the GPU for the Apertus step (`apertus-gpu.md`); this map | written for the submission | written |
| `tests/` | `invalid_instance.yaml`: an instance that the validator must refuse | written | written on 12.10.2026 |
| `tools/` | The scripts of `make convert`, `make list` and `make view` (`convert.sh`); of `make setup-apertus` (`setup_apertus.sh`, `text_branch.py`, `apertus/` with the MLX packages and the pinned SHA-256 of the heads and of the text branch); of `make serve-apertus` (`serve_apertus.sh`); the OCR packages of macOS (`requirements-macos-ocr.txt`) | written for the submission | `convert.sh` written on 15.10.2026 and changed on 16.10.2026; the other files written on 16.10.2026 |
| `data/` | The default data folder of the earlier converter (empty). `make setup-apertus` writes `data/apertus/` here: the text branch of the model, the 3 head files and `setup.json` | none | written on 12.10.2026; `data/apertus/` is not in the repository (`.gitignore`) |
| `.cache/`, `.venv/`, `build/` | Downloads of `make setup`, the Python of the app, the output of `make run-earlier` | none | not in the repository (`.gitignore`) |
| `technical_report.pdf` | The PDF of `technical_report.md` (6 pages), for the submission form | made from `technical_report.md` with `src/m11_report_pdf.py` of the private project | not in the repository (`.gitignore`). `technical_report.md` has the same text. |

## Files that are not in this folder

| File or folder | Reason |
|---|---|
| `src/m11_values_sponsor.py` (the rule for the first author) | Left out. This rule is only in `app/layout/src/`. The copy tool cannot make the edit that its copy in `src/converter_gj/` needs. |
| `src/m11_values_run.py`, `src/m11_values_job.py` | Left out. They run the readers on the data folder of the project. They are not a part of the reader. |
| the files `src/m11_*_test.py` | Left out. They read the data folder of the project. |
| `src/m11_heads2_convert.py`, a tool of the fit of the value heads | Not copied. Since 16.10.2026, `app/layout/src/` has the code of the value heads (`m11_value_heads2.py`, `m11_value_heads2_data.py`), because the Apertus step applies the heads with it. |
| the document data, the export, the PDF files, the hidden states | Not published. The app holds the stored inputs, the PDF and the page images of the 3 samples only. |

## The commands

| Command | What it does |
|---|---|
| `make setup` | Downloads (network): Python 3.12, the Python packages of the app into `.venv/`, the packages and schema files of the earlier converter. If cargo is on the computer, it also downloads the Rust crates. `make run` does not need it. |
| `make setup-pdf` | Only for your own PDF (`make run-native`, `make convert`), after `make setup`. Needs `pdftotext` and the network. Installs the packages of `app/container/requirements-full.txt` (`docling`, `pypdfium2`, torch) into `.venv/`, on macOS also `ocrmac` (OCR of Apple Vision), and downloads the 2 Docling models. It ran on one Mac on 15.10.2026. |
| `make convert`, `make list`, `make view` | Own PDFs in the terminal, the table of their IDs, one result in the browser. They ran on one Mac on 15.10.2026. |
| `make setup-apertus` | Only for the Apertus step of `make convert`, after `make setup-pdf`. Needs a GPU, the network and your own Hugging Face account. Downloads Apertus-v1.5-8B and the 3 head files at pinned revisions ([apertus-gpu.md](apertus-gpu.md)). It ran on one Mac on 16.10.2026: the heads came from Hugging Face, the model from the local Hugging Face cache. |
| `make serve-apertus` | On a computer with a GPU: the read-out service for `make convert APERTUS_URL=...` ([apertus-gpu.md](apertus-gpu.md)). It ran on one Mac on 16.10.2026, with the client on the same computer. |
| `make run` | Needs Docker. Builds the image of `app/` and starts it on `127.0.0.1:8080`. Then open `http://127.0.0.1:8080/app/`. On 14.10.2026 it ran one time on one Mac (commit `10e07b4`), with the 3 samples only. |
| `make run-native` | Builds the server and the WebAssembly bundle with cargo. Starts the app with no container on `127.0.0.1:8080` (`PORT=` sets the port). It ran on one Mac on 14.10.2026. |
| `make test` | Examines the copied files, the prompt files, the validator, the file list and the code layout of `app/`. It also examines the rules of the Apertus read-out service and its client (a backend that loads no model). No network, no Rust compiler. |
| `make test-app` | The cargo tests of the 2 crates of `app/`, the example view and a start of the seed script. |
| `make run-earlier` | The earlier converter of 12.10.2026 on the 3 samples. Before 14.10.2026 this command had the name `make run`. |

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 14.10.2026. In the afternoon of the same day, it changed the rows of `app/`, the PDF row and the commands. In the evening, an AI agent changed the states of `make run` and `make run-native`. On 15.10.2026 an AI agent added `make setup-pdf` and corrected rows after an audit. In the evening, an AI agent shortened the start of the file. On 16.10.2026 an AI agent added the files and the commands of the Apertus step.
