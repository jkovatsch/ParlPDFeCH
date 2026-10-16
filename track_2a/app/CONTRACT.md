# Contract of the ParlPDFeCH package (stages P0a and P0b)

Version 1, with the corrections of 13.10.2026.

How to read this file: the chapters 1 to 5 and 8 are the text of stage P0a; the chapters 9 and 11 correct them, and where they differ, the chapters 9 and 11 apply. The chapters 5.1, 5.2, 5.4, 6, 7 and 10 are edited in place and describe the package of now. Chapter 12 lists the changes of the correction round. Chapter 13 lists the changes after the second skeptic check. Chapter 14 has the two settings of a hosted sample site, chapter 15 the static site below `/`, the setting `PARLPDFECH_HOSTED` and the texts of a hosted site.

This file fixes the interfaces between the parts of the package. Where this file and the package plan differ, this file applies. Each value has one of three marks where it is not a rule: measured, read or estimate.

Words: MUST is a rule. "Sample" is one of the document numbers 26171, 879163 and 714840. "Record" is the output of one conversion. "Project folder" is the folder that holds `package/`.

Files of the contract:

| File | Content |
|---|---|
| `CONTRACT.md` | this file |
| `contract/view.schema.json` | JSON Schema of the view `parlpdfech-site-view/3` (chapter 16 adds `head_values`, `values[]` and `slots[]`) |
| `contract/errors.json` | all error codes with title, text and action in English and German |
| `contract/strings.contract.json` | the UI texts that this contract fixes; form `{key: {en, de}}` |
| `contract/examples/view_26171.json` | a real view of record 26171 in the earlier record form (head values from the export); it is valid against the schema (measured) |
| `contract/examples/view_879163.json`, `view_26171_values.json`, `view_unknown_pdf.json` | three real views with values that are read from the PDF (chapters 16 and 17): sample 879163 (mode `auto`), sample 26171 (mode `rules`, with a weak candidate) and the synthetic file `head_author.pdf` with no export record |
| `contract/examples/health.json`, `samples.json`, `job.json`, `error.json` | one example of each API answer |
| `contract/examples/events_sample.jsonl`, `events_refused.jsonl` | the standard output of the worker for two cases |
| `contract/tools/make_schema.py`, `make_example_view.py`, `validate_view.py` | tools of the contract; `validate_view.py` is also the check tool of the gate |

## 1 Folder layout and owners

One agent owns each path. An agent writes only below its own paths.

| Path | Owner | Content |
|---|---|---|
| `CONTRACT.md`, `contract/**` | contract | this contract |
| `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `.gitignore` | contract | Rust workspace. Another agent MUST NOT change them. A missing crate is a report to the integration agent. |
| `server/**` | server | crate `parlpdfech-server` (binary `parlpdfech-server`) |
| `rdfcheck/**` | wasm | crate `parlpdfech-rdfcheck` (WebAssembly) |
| `ui/rdfpanel.js`, `ui/rdfpanel.strings.json` | wasm | the panel module and its texts |
| `ui/pkg/**` | wasm (generated, ignored by git) | output of `wasm-bindgen --target web`: `parlpdfech_rdfcheck.js`, `parlpdfech_rdfcheck_bg.wasm` |
| `ui/**` except the three wasm paths | ui | `index.html`, `app.css`, `app.js`, `strings.json`, `favicon.svg` |
| `worker/**` | worker | `serve_convert.py`, `build_layout.py`, `make_samples.py`, requirements files |
| `view/**` | view | `site_view.py` and its check script |
| `data/samples/**`, `data/layout/**`, `data/SOURCES.json` | worker (made by `worker/make_samples.py`) | stored inputs of the samples, the sample index, shared input files |
| `Dockerfile`, `compose.yaml`, `Makefile`, `.dockerignore`, `README.md`, `container/**` | container | image and run commands |
| `build/**`, `work/**`, `target*/` | generated, ignored by git | `build/layout/` = byte-equal copies of converter code; `work/` = records and jobs of local trials |

Rules:

- No file below `package/` that git tracks holds a personal name, a path that starts with a home folder, a key or an internal note.
- The copies of the converter code go to `build/layout/` only. Read: 4 converter files hold a name or a home path. The copies must stay byte-equal. Thus they are not tracked files of this stage.
- `data/samples/**` holds text of 3 parliament documents. Its publication is a decision of the owner (plan decision D9 and D10).

## 2 Run time

### 2.1 Environment variables of the server

| Variable | Default | Meaning |
|---|---|---|
| `PARLPDFECH_PROFILE` | `native` | `slim`, `full` or `native`. `native` = server on the host with the project Python. The image sets `slim` or `full`. |
| `PARLPDFECH_BIND` | `127.0.0.1:8080` | listen address. The image sets `0.0.0.0:8080`; compose binds the host port to `127.0.0.1`. |
| `PARLPDFECH_UI_DIR` | `ui` | folder that `/app/` serves |
| `PARLPDFECH_DATA_DIR` | `data` | holds `samples/index.json`, `samples/<doc>/`, `layout/` |
| `PARLPDFECH_WORK_DIR` | `work` | holds `records/` and `jobs/`. The server makes the folders. It MUST be writable. |
| `PARLPDFECH_WORKER_CMD` | `["python3","worker/serve_convert.py"]` | JSON array. The server adds the arguments of chapter 4.1. |
| `PARLPDFECH_WORKER_CWD` | not set (the folder of the server process) | working folder of the worker process |
| `PARLPDFECH_SITE_DIR` | not set | a folder with a built static site. The server gives its files below `/` (chapter 15). A folder with no file `index.html` is dropped at the start with one warning line. |
| `PARLPDFECH_MAX_BYTES` | `20971520` | 20 MB |
| `PARLPDFECH_MAX_PAGES` | `25` | |
| `PARLPDFECH_JOB_TIMEOUT` | `600` | seconds for one worker process |
| `PARLPDFECH_COMMIT` | `unknown` | text for `/api/health` |
| `PARLPDFECH_ALLOWED_HOSTS` | empty | list with commas: host names that a request can name in addition to the loopback names (chapter 11.1 point 2) |
| `PARLPDFECH_UPLOAD_TIMEOUT` | `120` | seconds for the read of the body of `POST /api/jobs` (chapter 11.1 point 10) |
| `PARLPDFECH_READONLY` | not set (off) | `0` or `1`. `1` = a public site: the server takes no PDF file and refuses each `DELETE` (chapter 14). Another value stops the server at the start. |
| `PARLPDFECH_SAMPLE_RUNS` | `on` | `on` or `off`. `off` = the server starts no run for a sample whose record of that mode is in the work folder (chapter 14). Another value stops the server at the start. |
| `PARLPDFECH_HOSTED` | not set (off) | `0` or `1`. `1` = the operator says that the server is not on the computer of the reader. The server reports the value in `/api/health` (key `hosted`) and changes nothing else; the page then uses the texts for a hosted site (chapter 15). Another value stops the server at the start. |

The server passes its full environment to the worker and adds `PARLPDFECH_PROFILE`, `PARLPDFECH_MAX_PAGES` and `PARLPDFECH_DATA_DIR` with their effective values (absolute paths).

Environment variables of the worker only:

| Variable | Default | Meaning |
|---|---|---|
| `PARLPDFECH_CODE_DIR` | `<package>/build/layout` | root of the code layout (chapter 4.4) |
| `PARLPDFECH_VIEW_DIR` | `<package>/view` | folder that holds `site_view.py` |

Native command on the host (profile `native`), from the project folder:

`PARLPDFECH_WORKER_CMD='["uv","run","--offline","--frozen","--no-sync","--with","linkml==1.11.1","python","package/worker/serve_convert.py"]'` with `PARLPDFECH_WORKER_CWD` = the project folder.

Paths in the image: `/app/parlpdfech-server`, `/app/ui`, `/app/worker`, `/app/view`, `/app/data`, `/app/code` (= `build/layout`), `/work` (temporary volume). User 10001. The root file system is read-only.

### 2.2 URL layout

| Address | Content |
|---|---|
| `/healthz` | 200, `text/plain`, body `ok` |
| `/app/` | `index.html` of `PARLPDFECH_UI_DIR`. `/app` redirects (308) to `/app/`. |
| `/app/<file>` | static files of `PARLPDFECH_UI_DIR` (also `/app/pkg/*.wasm` with `application/wasm`) |
| `/api/...` | the API of chapter 5 |
| `/` and each other address | if `PARLPDFECH_SITE_DIR` is set and the folder holds `index.html`: the files of that folder (chapter 15). Else `/` gives 307 to `/app/` (a query stays) and each other address 404. |

The app has one HTML file. The screens are hash routes (chapter 7.2). The language is the query `?lang=en` or `?lang=de` before the hash. The addresses `/app`, `/app/...`, `/api/...` and `/healthz` always belong to the server: a file of the site folder with such a path is never given.

No request goes to another host. The pages load no font, script or image from another host.

## 3 Record ids and record folders

- Sample, mode `auto`: `s-<doc id>`, for example `s-26171`.
- Sample, mode `rules`: `s-<doc id>-rules`. This is an addition to the order of the main agent. Reason: the two modes give different files, and the page can show the two.
- Upload: `u-<first 16 hex characters of the PDF SHA-256>`; mode `rules` adds `-rules` in the same way. An upload whose SHA-256 is in the sample index gets the id of the sample.
- Pattern: `^(s-[0-9]+|u-[0-9a-f]{16})(-rules)?$`. The server MUST refuse each other value with `record_unknown` before a file access.
- Job id: a UUID version 4 in lower case.

`<WORK_DIR>/records/<record_id>/` holds exactly these files (`<doc>` = the document number; for an unknown PDF of stage P0b = `local`):

| Name | Media type | Written by |
|---|---|---|
| `<doc>.gesamt.trig` | `application/trig` | converter |
| `<doc>.ech.ttl` | `text/turtle; charset=utf-8` | converter |
| `<doc>.gesamt.rdf.xml` | `application/rdf+xml` | converter |
| `<doc>.ech.rdf.xml` | `application/rdf+xml` | converter |
| `<doc>.ech.yaml` | `application/yaml` | converter |
| `<doc>.labels.yaml` | `application/yaml` | converter |
| `<doc>.provenance.yaml` | `application/yaml` | converter |
| `manifest.json` | `application/json` | converter |
| `validation.json` | `application/json` | converter |
| `view.json` | `application/json` | worker, through the view function |
| `convert.json` | `application/json` | worker |

The 9 converter files are the bytes of the converter, not changed. The folder `export/` of the converter output is not copied. `<WORK_DIR>/jobs/<job_id>/` holds `input.pdf` (upload only) and `out/` during a job. The server deletes it at the end of the job.

A new conversion with the same record id replaces the folder (rename of a complete folder; no half record is visible).

`convert.json`: `{"schema":"parlpdfech-convert/1","record_id","doc_id","pdf_sha256","input":{"kind":"sample|upload","file_name"},"mode","converter_mode","apertus","origin","profile","status":"EXCEPTION, NOT RELEASED","valid","exit_code","started_utc","finished_utc","seconds":{},"stages":[],"counts":{},"files":[{"name","bytes","sha256"}],"decisions_sha256","reference":{"decisions_sha256_equal":true|false}|null,"tools":{},"worker_version"}`. `files` lists the 9 converter files and `view.json`. `reference` is null if the sample folder has no `reference.json`.

## 4 The worker

### 4.1 Command

```
serve_convert.py --sample <doc id> --mode auto|rules --out <dir> [--data-dir D]
serve_convert.py --pdf <file> [--doc-id N] --mode auto|rules --out <dir> [--data-dir D]
```

- `--out` is a folder that does not exist or is empty. The worker writes the 11 files of chapter 3 into it and nothing else. The server gives `<WORK_DIR>/jobs/<job_id>/out` and moves it to `records/<record_id>/` after the line `done`.
- `--data-dir` default: `PARLPDFECH_DATA_DIR`, else `<package>/data`.
- `--mode auto`: the best mode that the package has for the input. For a sample: the decisions of candidate B1-S from the stored Apertus states (`apertus: stored`). For another PDF: code rules (`apertus: none`).
- `--mode rules`: code rules with the floor probabilities, no Apertus state (`apertus: none`).
- One process makes one conversion. The server never starts 2 workers at one time.

### 4.2 Standard output: JSON lines

Each line is one JSON object in UTF-8 with no line break inside. The worker flushes after each line. Standard error is a log. It never goes to the browser.

Stage event:

```
{"event":"stage","id":"read_pdf|lines|rules|apertus|write|check","state":"running|done|skipped|failed",
 "origin":"stored|new","seconds":0.0,"counts":{},"reason":"..."}
```

- `event`, `id`, `state` are always there. `seconds` and `counts` come with `done`. `reason` comes with `skipped` and `failed`. `origin` comes with `done`: `stored` = the step read a stored input of the package; `new` = the step ran now.
- The stages come in the sequence `read_pdf`, `lines`, `rules`, `apertus`, `write`, `check`. Each stage gets `running` and then one end state, or only `skipped`.
- Counts: `read_pdf` `{pages}`; `lines` `{lines, blocks}`; `rules` `{blocks}`; `apertus` `{labels}` (labels with the source `apertus_head` or `code_step`); `write` `{labels, triples}`; `check` `{passed, total, skipped}`.
- `reason` of `skipped` for the stage `apertus`: `mode_rules` or `not_in_package`.
- `write` = the writer and the RDF step. `check` = the validator and the view function.

Last line, one of:

```
{"event":"done","record_id":"s-26171","doc_id":"26171","valid":true,"mode":"auto","apertus":"none|stored",
 "origin":"stored|new","pdf_sha256":"...","seconds":{"read_pdf":0,"lines":0,"rules":0,"apertus":0,"write":0,"check":0,"total":0},
 "counts":{"pages":0,"lines":0,"blocks":0,"labels":0},"files":["..."]}
{"event":"failed","code":"<error code>","detail":{}}
```

Exit codes:

| Code | Meaning | Last line |
|---|---|---|
| 0 | the record is written and valid | `done` with `valid: true` |
| 2 | the record is written; one or more checks failed | `done` with `valid: false` |
| 3 | refused before a conversion | `failed` with one of `protected_pdf`, `too_long`, `no_text_layer`, `pdf_unreadable`, `not_in_package`, `doc_id_unknown`, `pdf_differs_from_doc_id`, `sample_unknown`, `bad_request` |
| 4 | internal stop | `failed` with `converter_stopped`; `detail.note` is a short word with no path and no trace, for example `writer`, `rdf`, `validator`, `view`, `layout`, `self_check`, `out` (the record, `view.json` or `convert.json` cannot be written, or the parent folder of `--out` cannot be made), `scratch` (the scratch folder that `PARLPDFECH_SCRATCH_DIR` names cannot be written) |

`detail` keys: `too_long` `{pages, max_pages}`; `doc_id_unknown` and `pdf_differs_from_doc_id` `{doc_id}`; `not_in_package` `{pdf_sha256, profile}`; `sample_unknown` `{doc_id}`; `converter_stopped` `{note}`.

If the process ends with no last line, or with another exit code, the server makes `converter_stopped` with `detail.note = "exit_<code>"`.

Examples: `contract/examples/events_sample.jsonl`, `contract/examples/events_refused.jsonl`.

### 4.3 Cases of `--pdf`

1. The worker calculates the SHA-256 of the file.
2. The SHA-256 is in `samples/index.json`: the worker continues as `--sample <doc id>`. A `--doc-id` that is not this document gives `pdf_differs_from_doc_id`.
3. The SHA-256 is not in the index: the worker calls `convert_fresh(pdf_path, doc_id, mode, out_dir, emit) -> int` of `serve_convert.py`. In stage P0a this function writes the stage `read_pdf` as `failed` with the reason `not_in_package`, writes the line `failed` with the code `not_in_package` and returns 3, for each profile. Stage P0b replaces this one function. The function is NOT a converter. Reports MUST name it as "not implemented in stage P0a".

### 4.4 How the worker makes a sample record

Read in `src/m10_fullrun2.py` (function `work_one`): the decisions of the candidate (`decisions_of`, which calls `m10_b1s.b1s_decisions` through the candidate object), then `m10_writer.write_one`, `m10_rdf.convert_record`, `m10_validate.validate_record`. Inputs of one document, as project paths: `daten/gj/docs/<doc>.json` (blocks), `daten/gj/rules/<doc>.json` (rule record), `daten/iso/docling/<doc>.json`, `daten/iso/atome/<doc>.json`, the export record, `daten/gj/states/gpu1_labelled/states/<doc>.npz` (states), the R2 value, the calibration file of the run, the heads and the design files.

Rules for the worker:

- The worker imports the step functions. It does not run a check script, a build command or a batch command of the project.
- The writer puts project-relative paths of its inputs and their SHA-256 values into the output files. Thus the worker MUST build a scratch root that mirrors the project paths (code from `PARLPDFECH_CODE_DIR`, inputs from `PARLPDFECH_DATA_DIR`) and MUST write the converter output to `<root>/daten/gj/fullrun_b1s_dev/` for the mode `auto`. Then it copies the 9 files to `--out`.
- The worker uses the real clock. It does not set the run time to the time of a stored record.
- `data/samples/<doc>/` holds: `docling.json`, `atoms.json`, `blocks.json`, `rules.json`, `export.json`, `states.npz`, `r2.json`, `sample.json` (the index entry) and `reference.json` (`{"decisions_sha256","outputs":{...}}`, copied from the run record of the reference run, key `results.<doc>`). `data/layout/` holds the shared inputs under their project-relative paths. `data/SOURCES.json` lists each data file with its project-relative path and SHA-256.
- `data/samples/index.json` has the form of `contract/examples/samples.json` without the key `ready`. `in_sample` comes from the data: true if 1 or more block decisions or document decisions of the reference decisions file have `in_sample: true`. No script writes the value as a constant.
- Mode `rules`: the floor decisions (`m10_pipeline.decide` with the mode `floor`), then the same three steps.

### 4.5 The view function

File: `view/site_view.py`. The worker puts `PARLPDFECH_VIEW_DIR` on `sys.path` and calls:

```python
import site_view
view: dict = site_view.make_view(record_dir, inputs_dir, run_info)
```

- `record_dir` (`pathlib.Path`): a folder with the 9 converter files.
- `inputs_dir` (`pathlib.Path`): a folder with `docling.json`, `atoms.json`, `blocks.json` (required) and `decisions.json` (optional). The worker makes this folder (copies or links).
- `run_info` (`dict`): `{"record_id": str, "origin": "stored"|"new", "mode": "auto"|"rules", "apertus": "none"|"stored", "profile": "slim"|"full"|"native", "seconds": {...}}`. `seconds` is optional.
- Return value: a `dict` that is valid against `contract/view.schema.json`. The function reads only the two folders. It writes no file. It uses the Python standard library and PyYAML only. It raises `site_view.ViewError` (a `ValueError`) with a short text if a file is absent or a link between the files is broken.
- The worker writes the return value to `view.json` with `json.dumps(view, ensure_ascii=False, indent=1) + "\n"`.
- `site_view.py` also has a command line: `python site_view.py --record DIR --inputs DIR --run-info FILE --out FILE`.
- The view of record 26171 from `make_view` MUST be equal to `contract/examples/view_26171.json` as JSON data, except `run.seconds` and `run.profile`. A difference that the view agent finds to be an error of the example is a report, not a silent change.

## 5 The HTTP API

All addresses are below the same origin. Each answer below `/api/` is `application/json; charset=utf-8` if not said differently. Each answer below `/api/` has `Cache-Control: no-store`.

### 5.1 Error object

Each answer with a status of 400 or more below `/api/` is:

```json
{"error": {"code": "busy", "title": {"en": "", "de": ""}, "text": {"en": "", "de": ""},
           "action": {"en": "", "de": ""}, "exits": ["retry", "sample"], "detail": {}}}
```

- `code`, `title`, `text`, `action`, `exits` and the HTTP status come from `contract/errors.json`. The server includes this file at compile time (`include_str!("../../contract/errors.json")`).
- The server replaces each placeholder `{name}` in `text` with `detail.name`. A placeholder with no value stays as an empty string.
- No answer holds a stack trace, a path of the server or a line of standard error.
- Example: `contract/examples/error.json`.

Error codes (18 in this table; 22 with `forbidden` and `pdf_unreadable` of chapter 11.1, `read_only` of chapter 14 and `sample_runs_off` of chapter 15; texts in `contract/errors.json`):

| Code | HTTP | Made by | Case |
|---|---|---|---|
| `not_pdf` | 415 | server | the file does not start with `%PDF-` in its first 1024 bytes |
| `too_large` | 413 | server | more than `max_bytes` |
| `bad_request` | 400 | server | no `file` and no `sample`; the two together; a `mode` that is not `auto` or `rules`; a `doc_id` that is not a number; `detail.field` names the field |
| `sample_unknown` | 404 | server | `sample` is not in the index |
| `busy` | 409 | server | a job is `queued` or `running`; `detail.job_id` |
| `timeout` | 504 | server | the worker ran longer than the limit; `detail.seconds` |
| `job_unknown` | 404 | server | |
| `record_unknown` | 404 | server | `detail.record_id` |
| `file_unknown` | 404 | server | `detail.record_id`, `detail.name` |
| `not_found` | 404 | server | each other address below `/api/` |
| `internal` | 500 | server | `detail.note` is a short word |
| `protected_pdf` | 422 | worker | |
| `too_long` | 422 | worker | `detail.pages`, `detail.max_pages` |
| `no_text_layer` | 422 | worker | stage P0b |
| `not_in_package` | 422 | worker | `detail.pdf_sha256`, `detail.profile` |
| `doc_id_unknown` | 422 | worker | `detail.doc_id` |
| `pdf_differs_from_doc_id` | 422 | worker | `detail.doc_id` |
| `converter_stopped` | 500 | worker or server | `detail.note` |

An error of the worker does not change the HTTP status of `POST /api/jobs` (the job is accepted with 202). It is the key `error` of the job and the data of the event `failed`. The HTTP value of the table is for information.

### 5.2 Addresses

`GET /api/health` (example: `contract/examples/health.json`)

```json
{"schema": "parlpdfech-health/1", "version": "0.1.0", "commit": "unknown", "profile": "slim",
 "status": "EXCEPTION, NOT RELEASED",
 "modes": {"samples": true, "rules": true, "apertus_stored": true, "upload": false, "apertus_gpu": false,
           "read_only": false, "sample_runs": true,
           "reason": {"upload": "profile_slim", "apertus_gpu": "not_implemented"}},
 "ocr": "none", "limits": {"max_bytes": 20971520, "max_pages": 25, "job_timeout_seconds": 600},
 "busy": false, "job_id": null, "wasm": true, "site": false, "hosted": false}
```

- `modes.samples`: the index has 1 or more samples. `modes.apertus_stored`: 1 or more samples have `apertus: stored`. `modes.upload`: true in the profiles `native` and `full` if `PARLPDFECH_READONLY` is not `1` (then `modes.reason.upload` is null); false in the profile `slim` (reason `profile_slim`) and in each profile with `PARLPDFECH_READONLY=1` (reason `read_only` in a profile that is not `slim`). `modes.apertus_gpu`: always false. `modes.read_only`: true if `PARLPDFECH_READONLY=1`. `modes.sample_runs`: false if `PARLPDFECH_SAMPLE_RUNS=off` (chapter 14).
- `wasm`: the file `pkg/parlpdfech_rdfcheck_bg.wasm` exists in the UI folder.
- `site`: true if the server gives a static site below `/` (chapter 15). `hosted`: true if `PARLPDFECH_HOSTED=1`.
- `job_id`: the running job or null.

`GET /api/samples` (example: `contract/examples/samples.json`): the content of `samples/index.json`, and for each sample `ready: {"auto": bool, "rules": bool}` = the record folder exists.

`POST /api/jobs`: `multipart/form-data` with the fields `file` (one PDF) or `sample` (a document number), `doc_id` (optional, with `file` only), `mode` (`auto` or `rules`; default `auto`). The server reads at most `max_bytes` of `file`, calculates its SHA-256 and writes it to `jobs/<job_id>/input.pdf`. Answer 202:

```json
{"job_id": "<uuid>", "state": "queued", "events": "/api/jobs/<uuid>/events", "status": "/api/jobs/<uuid>"}
```

`GET /api/jobs/{id}` (example: `contract/examples/job.json`)

```json
{"schema": "parlpdfech-job/1", "job_id": "", "state": "queued|running|done|failed|stopped",
 "input": {"kind": "sample|upload", "doc_id": null, "file_name": null, "bytes": null, "pdf_sha256": null},
 "mode": "auto", "stages": [{"id": "", "state": "", "origin": null, "seconds": null, "counts": {}, "reason": null}],
 "elapsed_seconds": 0.0, "record_id": null, "valid": null, "apertus": null, "error": null,
 "events": "", "status": ""}
```

- `stages` always has the 6 stage ids in their sequence. A stage with no event has the state `pending`.
- `state` `done`: the record exists. `valid` is true (exit code 0) or false (exit code 2). A record with `valid: false` is a result. The page shows it with the notice `not_valid`.
- `error`: null or the error object of chapter 5.1 (the inner object, without the key `error`).
- `file_name` is the name that the browser sent, cut to 120 characters, with no path.
- The server keeps the last 20 jobs in memory. A start of the server loses them. Records stay.

`GET /api/jobs/{id}/events`: `text/event-stream`.

- At the connection the server sends each earlier event of the job again, then the new events. Thus a late connection gets the full sequence.
- `event: stage`, `data:` = the stage line of the worker, not changed.
- `event: done`, `data:` = the job object of `GET /api/jobs/{id}`.
- `event: failed`, `data:` = the job object (with `error`).
- `event: stopped`, `data:` = the job object.
- A comment line `: ping` each 15 s. After `done`, `failed` or `stopped` the server closes the stream.
- If the stream fails, the page asks `GET /api/jobs/{id}` each 2 s.

`DELETE /api/jobs/{id}`: a running job: the server stops the worker process, deletes `jobs/<job_id>/`, sets the state `stopped`. Answer 200 with the job object. A job that ended: no change, 200 with the job object. No record is deleted.

`GET /api/records/{record_id}`: the bytes of `view.json`.

`DELETE /api/records/{record_id}`: deletes the record folder. Answer 204. This address is an addition to the plan. The button "Delete this result from this computer" needs it.

`GET /api/records/{record_id}/files/{name}`: the bytes of the file, not changed, with the media type of chapter 3. `name` MUST be one of the 11 names of the folder; each other value gives `file_unknown` before a file access. `?download=1` adds `Content-Disposition: attachment; filename="<name>"`; for `source.pdf` the name is `parlpdfech-<record_id>.pdf` (14.10.2026).

`GET /api/records/{record_id}/bundle.zip`: `application/zip`, `Content-Disposition: attachment; filename="parlpdfech-<record_id>.zip"`. Content, in this sequence, all below the folder `parlpdfech-<record_id>/`: the 11 files of chapter 3, then `SHA256SUMS` (one line for each of the 11 files: `<sha256>  <name>`, sorted by name; the form of `sha256sum`). The server makes the archive in memory with the crate `zip` (4.6.1, feature `deflate`; read: it is in the local crate cache; measured: the lock file resolves and the server skeleton compiles with it). The worker makes no archive.

### 5.3 The one-job rule

One job is `queued` or `running` at one time. `POST /api/jobs` in this time gives 409 `busy`. `GET` requests are always possible. A job that reaches `PARLPDFECH_JOB_TIMEOUT` is stopped and gets `failed` with `timeout`.

### 5.4 Headers

Each answer:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `X-Frame-Options: DENY`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

Each answer below `/app/`:

- `Content-Security-Policy: default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`
- `Cache-Control: no-cache`

Each other answer that is not below `/api/` and is not `/healthz` (the static site, the redirect of `/`, a 404):

- `Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` (no WebAssembly, no font file, no form; chapter 15)
- `Cache-Control: no-cache`

Each answer below `/api/` and `/healthz`: `Content-Security-Policy: default-src 'none'; sandbox; frame-ancestors 'none'` and `Cache-Control: no-store` (chapter 11.1).

The page has no inline script, no inline style attribute that the policy refuses and no `eval`. `index.html` repeats the policy in a `meta` element (without `frame-ancestors`). The server sets no cookie.

The upload body limit of `POST /api/jobs` is `max_bytes` plus 64 KB for the form fields. Each other request body is refused above 64 KB.

## 6 The view `parlpdfech-site-view/3`

The schema file is `contract/view.schema.json`. Each object of the schema is closed (`additionalProperties: false`) except `counts.record`, `run.seconds`, `notices[].params`, `document.named_graphs` and the maps of counts. The names below come from the real record files of 26171, 879163 and 714840 (read). "Optional" = the value can be `null`; the key is always there, except `run.candidate` and `run.model`.

Top level: `schema`, `record_id`, `doc_id` (null for a PDF with no document number), `run`, `notices`, `document`, `pages`, `blocks`, `labels`, `calibrations`, `counts`, `checks`, `files`.

`run`:

| Key | Source |
|---|---|
| `origin` | `run_info` |
| `mode` | `run_info` (the mode of the request) |
| `converter_mode` | `manifest.json` key `mode` (`cascade` or `floor`) |
| `apertus` | `run_info` |
| `profile` | `run_info` |
| `status` | the constant `EXCEPTION, NOT RELEASED`. A machine field. The pages do not show it. |
| `record_status` | `manifest.json` key `status`, not changed |
| `human_checked` | the constant `false` |
| `in_sample` | three states: true if 1 or more labels have `in_sample: true`; false if none is true and 1 or more are false; else null (not known). It is null for each record with `origin` `new`: the package cannot tell if an own PDF is a development document. |
| `valid` | `manifest.json` key `validation.passed` |
| `generated_at` | labels file, `label_run.datetime_generated` |
| `seconds` | `run_info.seconds`, else `manifest.json` key `seconds` |
| `candidate` | optional; decisions file key `candidate` |
| `model` | optional; `manifest.json` key `model.model` |

`notices[]`: `{code, params}`. The text of a notice is the string `notice.<code>` of the strings file. The view function adds a code by these rules, in this sequence:

| Code | Rule |
|---|---|
| `proposal` | always |
| `no_human_check` | always |
| `in_sample_heads` | `run.in_sample` is true and `run.apertus` is `stored` |
| `in_sample_rules` | `run.in_sample` is true and `run.apertus` is `none` |
| `stored_apertus` | `run.apertus` is `stored` |
| `no_apertus` | `run.apertus` is `none` and no label has the group `apertus_values` |
| `apertus_values` | one or more labels have the group `apertus_values` (`make convert` with the Apertus step; fix step of 16.10.2026); `params.n` (the key with the ending `.one` for 1) |
| `chosen_not_top` | `counts.labels.chosen_not_top` is above 0; `params.n` |
| `no_text_block` | `document.text_blocks` is empty |
| `no_export` | `document.has_export` is false (stage P0b) |
| `not_a_sample`, `not_examined_pipeline` | `run.origin` is `new` (stage P0b). `not_a_sample` replaces the earlier code `outside_fit_population`, which said more than the package knows. |
| `ocr_apple` or `ocr_none` | `run.origin` is `new`; by `run_info.ocr` |
| `shacl_not_run` | the check `C10_shacl` did not run |
| `not_valid` | `run.valid` is false |
| `rdfxml_not_readable` | the parse check did not read 1 or more RDF/XML files; `params.n` |

`document`: `source_iri`, `record_iri`, `container_iri` (optional), `named_graphs` (`manifest.json`), `pdf_sha256`, `page_count`, `language` (optional), `parliament` (optional; block file key `parliament`), `parliament_name` (optional; export record key `body.name`), `title`, `affair_number`, `affair_type` (optional; the first head value whose `ech_slot` ends with `.title.text`, `.affair_number`, `.affair_type`), `has_export`, `conformance`, `head[]`, `text_blocks[]`.

- `head[]`: one entry for each entry of `value_records` of the provenance file, in its sequence: `instance_path`, `ech_slot`, `value` (the value of the eCH-0295 YAML file at `instance_path`, as a string; for a text block this is the full text with its markup), `derivation` (not changed), `origin` (`export`, `pdf_copy`, `code_rule`, `identifier`, `schema`; the map of view 1: `extracted_from_pdf` gives `pdf_copy`; the four `*_from_metadata` values give `export`; `detected_by_rule` gives `code_rule`; `identifier_minted` gives `identifier`; `fixed_by_schema` gives `schema`), `pdf_consistency`, `mapping_match` (optional), `atom_ids` (from `pdf_evidence`), `label_id` (optional; the label of the kind `export_value`, `constant_value` or `text_wording` with the same `instance_path`; for `text_wording` the label path plus `.text`).
- `text_blocks[]`: one entry for each entry of `text_block_records`: `id` (`textblock-<n>`), `iri`, `ech_slot`, `text_type`, `instance_path`, `block_ids` (the `unit_id` values), `atom_ids`, `char_count`, `extent_value_status`, `label_id` (optional).

`pages[]`: `number`, `width`, `height` (PDF points; stored Docling output keys `seiten[].breite` and `hoehe`), `text_source` (`pdf`, `ocr`, `mixed`), `lines[]`. A line is one atom of the atoms file: `atom_id`, `block_id`, `frame` (`[left, top, right, bottom]`, origin top left; the line frame, else the block frame), `frame_source`, `text`, `char_start`, `char_end`, `from_ocr`. The lines of a page are in the sequence of the atoms file.

`blocks[]`: one entry for each block of the block file: `id`, `page`, `docling_label`, `char_start`, `char_end`, `atom_ids`, `text`, `label_id` (optional; the label of the kind `block_slot` of this block).

`labels[]`: one entry for each entry of `label_assertions` of the labels file, in its sequence (the sequence of the document).

| Key | Source and rule |
|---|---|
| `id` | last part of `global_uri`, for example `d1`, `r2`, `B3-slot`, `value-affairs-0-local_id`, `textblock-1-text` |
| `iri` | `global_uri` |
| `kind` | `label_kind` |
| `slot` | local name of `label_predicate`, for example `textType` |
| `predicate`, `subject` | `label_predicate`, `label_subject` |
| `target.type` | `block` for `block_slot` and `author_switch`; `document` for `document_text_parts` and `executive_response`; `text_block` for `text_wording`; else `value` |
| `target.block_id` | optional; last part of the subject if it is a block IRI |
| `target.atom_ids` | the atoms of the block, or of the text block; else empty |
| `target.page`, `target.last_page`, `target.char_start`, `target.char_end` | optional; `page`, `last_page`, `span_start`, `span_end` |
| `target.instance_path`, `target.about_entity` | optional |
| `value` | `label_object` as a string (the selected option) |
| `options[]` | `{value, probability}` for each entry of `option_probabilities`, in its sequence; empty if the label has no probability |
| `probability` | optional; `label_probability` (the stored decimal, not rounded) |
| `value_status` | `certain` or `unsure` from the record; `none` if the label has no probability |
| `chosen_is_top` | optional; true if no option has a higher probability than the selected option; null if no probability |
| `top_option` | optional; the option with the highest probability, only if `chosen_is_top` is false |
| `source.kind` | `label_source`, not changed: `rule`, `apertus_head`, `code_step`, `export`, `constant`, `copy` |
| `source.group` | `rule`, `apertus_readout`, `apertus_values`, `export`, `constant`, `copy`. `apertus_head` gives `apertus_readout`; `apertus_head` with a value tier `apertus_q1` or `apertus_q2_<field>` (a value of an Apertus value head, `make convert` with the Apertus step) gives `apertus_values`, and the source line of such a `pdf_value` is `source.apertus_values`. `code_step` gives `apertus_readout` if `run.apertus` is `stored`, else `rule`. |
| `source.tier`, `source.rule_id` | optional; `tier` (for example `s2_start_default`, `fixed:R3`), `rule_id` (for example `P1`) |
| `source.head` | optional; `R2` for `executive_response` with the source `apertus_head`; `B1` for `block_slot` with the source `code_step` if the decisions file has the key `b1_s`; `D1` for `document_text_parts` with the source `apertus_head`; else null |
| `calibration_id` | optional; last part of `calibration` |
| `in_sample` | optional; the value of the label; if absent: decisions file `document.d1.in_sample` for `document_text_parts`, `r2.in_sample` for `executive_response`; else null. Read in the 3 sample records: the labels `d1` and `r2` have no `inSample` statement in the label graph (bytes of the converter), so for these 2 labels the value of the view comes from the decisions file and not from the label graph. For `origin` `new` the value is null for each label. |
| `note_code` | optional; the note of the label (`label_note`) as a code, if the view function knows the note: `switch_between_blocks`, `value_derivation`, `wording_copy`, `final_check`, `unsure_final_check_differs` |
| `note_params` | the values of the note: `before` and `after` (block ids) for `switch_between_blocks`; `derivation` for `value_derivation`; `agrees` (true or false) for `final_check` |
| `note` | optional; only a note that the view function does not know, in English, after a filter that removes paths, numbers of 5 or more digits and working words of the project (mark `[…]`). null if `note_code` has a value. The view passes no raw `label_note`. |

Read in the three sample records of the reference run: the block labels have the source `code_step` (the sequence step on the values of the read-out head B1), not `apertus_head`. Only the label `r2` has the source `apertus_head`. The pages MUST keep this difference (chapter 7.5).

`calibrations[]`: one entry for each entry of `calibrations` of the labels file: `id` (last part of `global_uri`), `iri`, `method`, `kind`, `fit_n` (optional), `in_sample` (optional; the constant of the calibration record, chapter 10.3: it says nothing about the document of the record; null for a record of an own PDF), `target_status`, `certain_threshold` (optional; read: floor records have none), `basis` (optional; `{n, agreed, documents}` from the calibration parameters `dev_blocks`, `dev_correct`, `dev_documents`; read: only the floor records have them; chapter 11.3 point 2 names the other forms), `reference_code` (optional; `model_labels_not_human_checked`, `other` or null; it replaces the earlier key `reference_source`, so that the view holds no text of the calibration file), `measure_sets[]` (`name`, `n`, `ece`, `ece_low`, `ece_high`, `brier`, `nll`; each optional), `note` (optional). `calibrations[].note` and `measure_sets[].name` are the English texts of the converter, not changed; they hold working words of the project. The page does not print the note.

`counts`: `pages`, `lines`, `blocks`; `labels` = `{total, with_probability, certain, unsure, none, chosen_not_top, by_source, by_group, by_kind}` (counted on `labels[]`); `triples` (`manifest.json` key `rdf.triples`); `record` (`manifest.json` key `counts`, not changed).

`checks[]`: `{id, state, reason}`. Ids in this sequence: `writer_check` (`manifest.json` key `check_passed`), `C1_linkml`, `C2_parse`, `C3_isomorphism`, `C4_parts`, `C5_leaf_values`, `C6_iri_scheme`, `C7_C8_labels`, `C9_e19` (`validation.json` key `<id>.passed`), `C10_shacl` (`skipped` with the reason `shacl_tool_absent` if `validation.json` says `skipped`).

`files[]`: `{name, role, media_type, bytes, sha256, url}` for the 9 converter files in this sequence of roles: `gesamt_trig`, `ech_ttl`, `gesamt_rdfxml`, `ech_rdfxml`, `ech_yaml`, `labels_yaml`, `provenance_yaml` (bytes and SHA-256 from `manifest.json` key `outputs`), `manifest`, `validation` (calculated). `url` = `/api/records/<record_id>/files/<name>`.

Measured on `contract/examples/view_26171.json`: 33 labels (15 with a probability: 9 certain, 6 unsure; 18 with none), 36 lines, 13 blocks, 20 head values, 3 calibrations, 10 checks (9 passed, 1 skipped), 9 files; 79,888 bytes. `contract/tools/make_example_view.py` makes the example; the tool and the view function give equal data for the record under the rule of gate G4 (measured).

## 7 The UI contract

### 7.1 Files and rules

- `ui/index.html`, `ui/app.css`, `ui/app.js` (one script, no framework, no library), `ui/strings.json`.
- `ui/strings.json` has the form `{"<key>": {"en": "...", "de": "..."}}`. It MUST hold each key of `contract/strings.contract.json` with the same texts (108 keys; `ui/strings.json` has 463 keys, of these 20 with the ending `.hosted`; `ui/rdfpanel.strings.json` 83). The UI agent adds keys. The page does not use each contract key: chapter 7.7 lists the contract keys that `app.js` does not use and the keys that it uses in their place. No text of the page is in `app.js` or `index.html`, except the text for the case that the strings file does not load.
- Placeholders have the form `{name}`.
- A key with the ending `.hosted` is the text of its base key on a hosted site: the page takes it in place of the base key if `hosted` of `/api/health` is true (chapter 15). It has the same placeholders, and it does not say "on this computer".
- The page sets no cookie and stores nothing in the browser.
- A count shows with the thousands mark of the language (`en`, `de-CH`). The key with the ending `.one` is the form for the count 1.
- No text uses the word "live". No colour red or green carries a meaning. A probability shows as the stored decimal with no percent sign.
- The page MUST work with a keyboard. Each screen sets the focus to its heading.

### 7.2 Routes

| Route | Screen |
|---|---|
| `/app/#/` | S0 Start |
| `/app/#/samples` | S1 Samples |
| `/app/#/upload` | S2 Upload |
| `/app/#/job/<job_id>` | S3 Stages |
| `/app/#/record/<record_id>` | S4 Result |
| `/app/#/record/<record_id>/label/<label_id>` | S4 with one label selected and shown on the page |

An unknown route shows S0. A route `#/record/<id>` whose id has not the form of chapter 3 shows a case that the page makes (keys `case.no_record.*`, exits to the samples and to the start, no request). `?lang=de` or `?lang=en` before the hash sets the language; with no query the page takes `de` if `navigator.language` starts with `de`, else `en`.

### 7.3 Screens

- A site that takes no file (`modes.read_only`), a hosted site (`hosted`) and a server with a static site (`site`) change the texts and the entries of S0, S1, S2 and of the navigation: chapters 14 and 15. The points below describe the page with none of them.
- S0: title, line, 3 buttons, the mode line, the first two notices and the list "Words used on these pages" (keys `words.*`). The mode line is a set of sentences that the page selects by `modes.upload`, `ocr` and `modes.apertus_stored` of `GET /api/health` (keys `mode.upload.*`, `mode.ocr.*`, `mode.samples.stored`). The button for an own PDF goes to S2.
- S1: one card for each sample of `GET /api/samples`: title, kind of affair (a word from the map `affair_type.<value>`), public body (`parliament_name` with the key `parliament` in parentheses), language as a word, pages, the stored inputs (`s1.card.inputs`), a line for a development document only if `in_sample` is true (`s1.card.dev`), and one button for each mode of `modes` with the mode name `mode.name.*`. If the two records of a sample exist, the card shows the counts of the two results (`cmp.line`). A button sends `POST /api/jobs` with `sample` and `mode` and goes to S3.
- S2: the file control (the native file input is out of sight and in the keyboard sequence; its label is the button), a drop zone as an addition, the limits line with the values of `/api/health`, the optional document number, the button `s2.convert`. The line of the selected file gives the size in MB from 0.1 MB, in KB from 1 KB and in bytes below (`fmt.size.*`). The mode line above the form is the same set of sentences as on S0. The page compares the size of the file with the limit and asks `/api/health` for a running job before it sends the file. If `modes.upload` is false, the form stays usable, and a PDF that is not a sample gives the case `not_in_package`.
- S3: the 6 stages with their states from the event stream. For a sample the first two stages have the names `s3.stage.read_pdf.sample` ("Read the stored pages of the PDF") and `s3.stage.lines.sample` ("Read the stored lines of the PDF"): the package holds no PDF of a sample, and the worker reads stored inputs. The fourth stage has a name by the input: `s3.stage.model.sample` for a sample, `s3.stage.model.own` with the state text `s3.skip.no_model` for an own PDF. The line `s3.time`; the button `s3.stop` (`DELETE /api/jobs/{id}`). `done` goes to S4. `failed` shows the case.
- S4: the head line (`s4.headline.<origin>` with the mode name), the notices, the count line `s4.count` (`n` = `counts.labels.total`, `a` = `with_probability`, `c` = `certain`, `u` = `unsure`, `b` = `none`), a list of the parts of the result, the pages with their lines, the label cards in the sequence of `labels[]`, the head data with the source of each value, the downloads (`dl.trig`, `dl.ttl`, `dl.rdfxml`, `dl.zip`), the checks with plain names (`check.*`), the RDF panel, the delete button (`DELETE /api/records/{id}`, then S0). The notice about the text recognition of an own PDF shows the counts of the pages by `pages[].text_source` (`ocr.apple.pages`), not the text of `notice.ocr_apple`.
- Cases: each error object shows `title`, `text`, `action` in the language of the page and one button for each entry of `exits` (`exit.other_pdf` to S2 with no file selected, `exit.sample` to S1, `exit.retry` sends the request again, `exit.start` to S0). The page has cases of its own for answers that are not an error object (`case.*`).

### 7.4 The RDF panel (WebAssembly)

- `index.html` holds `<section id="rdf-panel" hidden></section>` inside S4. It has no `script` element for the panel: `app.js` loads the module with `import('./rdfpanel.js')` when S4 opens. The panel also loads `rdfpanel.css`.
- `ui/rdfpanel.js` sets `window.ParlRdfPanel = { mount, unmount }` and then sends the event `parl-rdfpanel-ready` on `document`.
- `mount(element, {trigUrl, manifestUrl, lang, hasExport}) -> Promise<{ok: boolean}>`. `trigUrl` and `manifestUrl` are addresses of the files endpoint. `lang` is `en` or `de`. `hasExport` is `document.has_export` of the view: if it is false, the panel does not show the example of the eCH-0295 head values and says why. A language switch on S4 does not read the TriG file and the manifest again. The panel fills `element` and removes its attribute `hidden`. `unmount(element)` empties it. A second `mount` on the same element replaces the content.
- The panel loads `pkg/parlpdfech_rdfcheck.js` (output of `wasm-bindgen --target web`), gets the TriG bytes, parses them with the Rust code, counts the statements of each named graph and the labels of each source, compares the counts with `manifest.json` (`rdf.triples`, `counts.label_assertions`, `counts.label_assertions_by_source`), and runs fixed SPARQL examples and one free query. The tables show the plain words of a source and of a count; the stored name (for example `code_step` or `counts.certain_labels`) is in the `title` attribute of the cell text, not in the text. If no label of the file has a statement `plb:inSample`, the row of that count shows `rdf.summary.not_known`, not the number 0.
- The texts of the panel are in `ui/rdfpanel.strings.json` (same form as the strings file; not merged into `ui/strings.json`).
- The UI MUST work when the panel is absent: `app.js` calls `mount` if `window.ParlRdfPanel` exists, else it waits for the event. If the module, the WebAssembly file or the promise fails, only the section shows the text `rdf.absent`. No other function changes.
- Measured: `wasm-bindgen` 0.2.127 is installed on the build host; the crate skeleton compiles for `wasm32-unknown-unknown`.

### 7.5 Plain words in place of status words

The pages do NOT show the words `EXCEPTION` or `NOT RELEASED`, and no status banner. They do not print `run.status`, `run.record_status`, `run.candidate` and `run.converter_mode`, and no working name of the project (a name of a step, of a calibration record or of a variant of the converter). They show the notices of the view as plain sentences at the top of S4 (and the first two on S0):

- `notice.proposal`: "Each label that a code rule or a read-out decided is a proposal with a probability. The probability is the calculated probability that the label agrees with the AI reference of the project. No stored value is below 0.005 or above 0.995: the converter cuts each value to this range."
- `notice.no_human_check`: "Each label and each value of a result can be wrong."
- `notice.in_sample_heads` (only if the data flag says so): "This sample is a development document. The project set the read-outs with it. Its probabilities are not a result on a new document."
- `notice.not_a_sample` (an own PDF): "This PDF is not one of the samples of this package. The package cannot tell if it is one of the development documents. The probabilities were not checked on this PDF."

The German texts are in `contract/strings.contract.json`. The machine field `run.status`, `/api/health` key `status`, `convert.json` and the README keep the words `EXCEPTION, NOT RELEASED`. This replaces the status line of plan chapter 7.1.

The page takes "development document" from `run.in_sample` and from `samples[].in_sample`. It has no list of document numbers. For `in_sample` null the page makes no statement about it.

Limit: the download files are the files of the converter. They hold the status words, working names of the project and project-relative paths (`STATE.md` chapter 6). An IRI with the path part `/gj/` shows in the technical details and in the panel.

### 7.6 Display of the uncertainty (plan chapter 7.3)

1. A label with a probability shows: the status word (`status.certain` or `status.unsure`), then the stored decimal. No percent sign. No red or green.
2. A label with `value_status: none` shows its source and no number.
3. If `chosen_is_top` is false, the card names the selected answer, its number and who selected it: `unc.why.rule` for a label of a code rule (the rule does not use the numbers), `unc.other_higher.readout` or `unc.other_higher` else, with `top_option.value` and `top_option.probability`.
4. All options show as a list with their numbers, in the sequence of `options[]`.
5. The source line: `source.rule` for the group `rule` (`source.rule.readout_number` if the calibration has the method `verifier_platt`: a rule selected the answer, and the number is a read-out); `source.readout.*` for the group `apertus_readout`, by `source.kind`; `source.stored_value` for the label `executive_response` with the source `apertus_head` in a record with `apertus: stored` (the worker copies the stored value and does not calculate it); `source.export`, `source.constant`, `source.copy`.
6. If the calibration of a label of the group `rule` has `basis`, the card shows the basis line (`unc.rule.basis.blocks` with `n` = `basis.n` and `k` = `basis.agreed`, or `unc.basis.documents`). For a record with `document.has_export` false the document label adds `unc.basis.no_export`: the counts come from runs of the rule with export values.
7. The card shows `unc.target.<target_status>` of the calibration of the label.
8. The default sequence of the cards is the sequence of `labels[]`.
9. The name of an option is the string `option.<kind>.<value>` if it exists, else the value as it is.
10. A note of a label shows only as the text `note.<note_code>` (with `note_params`). The code `final_check` has no text of its own: the card shows the final check from `counts.record.r2_agrees_with_block_path`. A view with no key `note_code` shows no note. A new code needs a key `note.<code>`.
11. A mode with no limit for the word "certain" (`certain_threshold` null) says so on the card.

### 7.7 Contract keys that the page does not use

The texts of these keys stay in `contract/strings.contract.json` and in `ui/strings.json` (the check tool compares them), and `app.js` does not use them: `s1.card.stored`, `s1.card.in_sample`, `s1.mode.auto`, `s1.mode.rules`, `unc.basis`, `s3.stage.apertus`, `s3.stage.apertus.stored`, `s4.head.stored.auto`, `s4.head.stored.rules`, `s4.head.new.rules`, `source.apertus_readout.apertus_head`, `source.apertus_readout.code_step`. `s3.skip.not_in_package` is used only for another stage than the fourth. The page uses in their place: `s1.card.inputs`, `s1.card.dev`, `mode.name.*`, `mode.inline.*`, `unc.rule.basis.blocks`, `s3.stage.model.sample`, `s3.stage.model.own`, `s3.skip.no_model`, `s4.headline.stored`, `s4.headline.new`, `source.readout.*`, `source.stored_value`. Open for the contract owner: remove the 12 keys from the contract file or make them the keys of the page. The texts of `notice.stored_apertus`, `notice.in_sample_heads`, `notice.in_sample_rules`, `notice.not_a_sample`, `notice.not_examined_pipeline`, `notice.shacl_not_run`, `notice.proposal`, `s3.time` and `unc.target.*` were written again in the words of the list of words (chapter 13).

## 8 The gate of stage P0a

The integration agent checks each point and reports the measured result. A point that is not met is reported as not met.

G0 Build. `cargo build --offline --locked --release -p parlpdfech-server` passes. `cargo build --offline --locked --release -p parlpdfech-rdfcheck --target wasm32-unknown-unknown` and `wasm-bindgen --target web` pass, or the report says that the panel is absent.

G1 Conversion through the server. With the profile `native`, for each of the 3 samples and the mode `auto`: `POST /api/jobs` with `sample`, the event stream ends with `done`, `valid` is true, `apertus` is `stored`, and `GET /api/records/s-<doc>` answers.

G2 Equality with the direct call. The reference is the stored record of the reference run of candidate B1-S (project path `daten/gj/fullrun_b1s_dev/<doc>/`) and its run record (`runs/run_1.json`, key `results.<doc>`).

- G2.0: the SHA-256 of each reference file is the value of the run record key `results.<doc>.outputs`. This shows that the reference is the recorded output.
- G2.1: `convert.json` key `decisions_sha256` is the value of the run record key `results.<doc>.decisions_sha256` (exact).
- G2.2: the three YAML files, the TriG file and the Turtle file from `GET /api/records/s-<doc>/files/<name>` are byte-equal to the reference files after one replacement: the run time of each file set (`label_run.datetime_generated`; the two written forms `...Z` and `...+00:00`) becomes the text `RUN_TIME`.
- G2.3: the two RDF/XML files are isomorphic to the reference files after the same replacement (rdflib `to_isomorphic`). Read: the RDF/XML files hold random blank node names. Thus byte equality is not a rule for them.
- `manifest.json` and `validation.json` hold times and seconds. They are not in the comparison. Their keys `counts`, `validation.checks` and `conformance` MUST be equal to the reference.
- If G2.2 is not met for a file but the graphs are isomorphic, the report says "isomorphic, not byte-equal" for this file. This is not a pass of G2.2.

G3 Rules mode. For each sample and the mode `rules`: the job ends with `done`, `valid` is true, `apertus` is `none`, `counts.labels.by_source` has no `apertus_head` and no `code_step`. Information only: the comparison with a stored floor record, if the worker agent names one.

G4 View. `python contract/tools/validate_view.py contract/view.schema.json <view files>` passes for the 6 views (3 samples, 2 modes). The view of `s-26171` is equal to `contract/examples/view_26171.json` as JSON data, except `run.seconds`, `run.profile`, `run.generated_at`, and `bytes`, `sha256` of the files that hold a time.

G5 API. Each address of chapter 5.2 gives the form of its example. A second `POST /api/jobs` during a job gives 409 `busy` (if a job is too short to test this, the report says so). An upload of a file that is not a PDF gives `not_pdf`. An upload of a PDF that is not a sample gives a job that ends with `failed` and `not_in_package`. `bundle.zip` holds 12 entries, and each line of `SHA256SUMS` is correct. The headers of chapter 5.4 are there.

G6 UI. The screens S0, S1, S3 and S4 work for one sample in a browser, in English and in German. The page shows no status word of chapter 7.5. With `ui/pkg/` removed, S4 works and the panel shows `rdf.absent`.

G7 Offline and hygiene. The server and the worker open no connection to another host (read of the code; a run with no network if the host permits it). `grep` on the tracked files of `package/` finds no personal name, no home path, no key and none of the words of the hygiene rule.

Not in this gate: a container build, a Linux run, an unknown PDF (stage P0b).

## 9 Corrections of the integration step (13.10.2026)

These points correct the text above. Each one is measured or read in the built package.

1. Chapter 1 and 4.4: the layout builder is `worker/layout.py`, not `worker/build_layout.py`. `data/layout/` and `data/SOURCES.json` do not exist. The shared input files are in the code layout `build/layout/` under their project paths. `worker/layout_files.json` lists each file with its path, bytes and SHA-256. The worker reads code and shared data from `PARLPDFECH_CODE_DIR` only.
2. Chapter 4.2: a stage line of the stage `check` can hold the added key `note` (`view_absent` or `view_failed`). A record with no `view.json` is not installed by the server (`converter_stopped`, note `no_view`).
3. Chapter 5.2: `POST /api/jobs` also accepts `application/json` with `{"sample", "mode"}` for a sample (measured). Each sample of `GET /api/samples` has the added key `source_url`.
4. Chapter 8, G2.2: one file set can hold 2 run times that differ by 1 s (labels file and provenance file). The comparison replaces each value of the key `datetime_generated` of the two files. `contract/tools/gate_compare.py` does this.
5. Chapter 6 and chapter 8, G2.3: the cause of the byte difference of the RDF/XML files is the sequence of the XML elements, not the blank node names (measured by the worker part). The rule (isomorphic graphs) is not changed.
6. Chapter 7.4: `index.html` has no `script` element for `rdfpanel.js`. `app.js` loads the module with `import('./rdfpanel.js')` when S4 opens. The panel also loads `rdfpanel.css`.
7. Chapter 7.5: the page does not print `run.status`. The row was removed from the technical details of S4.
8. The gate tools are `contract/tools/gate_api.sh` (curl pass through the API) and `contract/tools/gate_compare.py` (comparisons).

## 10 Stage P0b: a PDF that is not a sample (13.10.2026)

This chapter adds to the chapters above. Where it differs from them, this chapter applies for a PDF whose SHA-256 is not in the sample index. It is edited in place for the corrections of chapter 11 and chapter 12. Each point is measured or read in the built package on one Mac, profile `native`. Nothing of this chapter was run on Linux.

### 10.1 The worker

- `convert_fresh()` of `serve_convert.py` calls `fresh.convert_fresh(host, pdf_path, doc_id, mode, out_dir)` of `worker/fresh.py`. The command line and the hook of chapter 4.3 do not change. `serve_convert.py` puts the data folder of the run into `PARLPDFECH_DATA_DIR` before the call.
- Code rules only. The modes `auto` and `rules` give the same labels. The record id is `u-<first 16 hex of the PDF SHA-256>`, with `-rules` for the mode `rules`.
- Stage events: `read_pdf` (PDF checks and Docling; counts `{pages}`), `lines` (`{lines, blocks}`), `rules` (`{blocks}`), `apertus` only as `skipped` with the reason `not_in_package` (mode `auto`) or `mode_rules`, `write` (`{labels, triples}`), `check` (`{passed, total, skipped}`). Each stage that runs has `origin: new`.
- Last line `done`: `doc_id` is `null`, `apertus` is `none`, `origin` is `new`. Exit code 0 or 2 as in chapter 4.2.
- Refusals (exit code 3): `not_in_package` (profile `slim`), `doc_id_unknown` (a `--doc-id` that is not a sample), `pdf_differs_from_doc_id` (a `--doc-id` of a sample), `bad_request` with the field `file` (no PDF mark), `protected_pdf`, `too_long` (`detail.pages`, `detail.max_pages`; the limit is `PARLPDFECH_MAX_PAGES`), `no_text_layer` (no page has a text layer and no OCR engine runs; or Docling gives no block with text), `pdf_unreadable` (the PDF does not open or has 0 pages).
- Internal stop (exit code 4, `converter_stopped`): new notes `pdf_reader_absent`, `docling_absent`, `docling_models` (profile `full` with no `DOCLING_ARTIFACTS_PATH`), `docling_status`, `docling_input`, `pdftotext_absent`, `lines`, `in_sample`, `states`, `copy`, `out`, `scratch` (chapter 4.2).
- Environment variables of the fresh branch: `PARLPDFECH_MAX_PAGES` (read by the worker now), `DOCLING_ARTIFACTS_PATH` (profile `full`), `HF_HUB_OFFLINE` (set to `1` if it has no value), `PARLPDFECH_CALIBRATION_BASE` (base IRI of the calibration records; default `https://parlpdfech.ansv.ch/id/`, the base of the sample records), `PARLPDFECH_FRESH_OCR=none` and `PARLPDFECH_FRESH_DEVICE=cpu` (profile `native` only; a measurement aid), `PARLPDFECH_SCRATCH_DIR` (scratch folder of the job; default: the parent of `--out`). The worker sets `PYSTOW_HOME` and `TMPDIR` to folders below the scratch folder of the job before the first import of a converter file (sample path and fresh path), so that no file goes to the home folder.
- The fresh branch takes a foreign entry with the name `src` out of the module search path before an import reads it (one converter copy adds such an entry). `convert.json` key `fresh.search_path_entries_removed` has the count.
- The code layout has a third mode (number 3 in `worker/layout_files.json`): 45 files, 2,026,544 bytes. `worker/layout.py --update` adds files to a layout that is in use. A build and `--update` remove compiled files that the manifest does not record; `--check` reports such files and ends with exit code 1.

### 10.2 OCR and device by profile

| Profile | OCR | Device | Docling arguments |
|---|---|---|---|
| `slim` | no conversion | | |
| `native` on macOS with the package `ocrmac` | Apple OCR | `auto` (MPS for the layout model) | the stored settings of the converter, not changed |
| `native` with no `ocrmac` | none | `auto` | the stored settings with `--ocr aus` |
| `full` | none | `cpu` | the stored settings with `--ocr aus` and `--geraet cpu` |

### 10.3 The record of a PDF with no export record

The 11 files of chapter 3, with the prefix `local`. The 9 converter-form files are written by `worker/pdf_only.py` (new code that calls converter functions), not by the writer of the converter.

IRIs:

| Thing | IRI |
|---|---|
| Document | `urn:parlpdfech:local:sha256:<64 hex of the PDF bytes>` |
| Record | `<document>/record` |
| Named graphs | `<record>/ech-0295`, `<record>/provenance`, `<record>/atoms`, `<record>/labels` |
| Container (eCH-0295) | `<record>/i95` |
| Provenance record, label record, run | `<record>/extraction`, `<record>/label-record`, `<record>/run` |
| Block, line, boundary | `<record>/block/B<n>`, `<record>/atom/<line id>`, `<record>/boundary/after-B<n>` |
| Text block | `<record>/textblock/<k>` |
| Label | `<record>/label/d1`, `/B<n>-slot`, `/switch-after-B<n>`, `/textblock-<k>-text`, `/value-global_uri` |
| Calibration record | `https://parlpdfech.ansv.ch/id/calibration/<id>` (the IRI of the same calibration record in a sample record) |

No IRI and no file name of the record holds a document number.

Graphs:

- eCH-0295 graph: one statement. The Container has its IRI and no affair. eCH-0295 has a text block only below a step of an affair, and the PDF gives no affair. This differs from the first order for this stage ("the eCH-0295 part holds the text blocks"): a text block in the eCH-0295 part needs an affair with an invented type and number.
- Provenance graph: the source document (SHA-256 of the PDF, page count, language from the stop-word rule, no document number, no URL), one TextBlockRecord for each author block (`mapping_status: profile_only`, `text_content` = the text, `section_key` = the text type, the lines as evidence, the text changes), one ValueRecord (the Container IRI), the NotMappedRecords (the affair; each title block; each text block).
- Atoms graph: each Docling block with its lines (the function `layout_record` of the RDF step).
- Label graph: `d1`; one `block_slot` label for each block; one `author_switch` label for each switch; one `text_wording` label (source `copy`) for each text block; one `constant_value` label (the Container IRI). Each label of a rule has `label_probability`, `option_probabilities`, `value_status`, `page`, `span_start`, `span_end` and `calibration`; no label has the slot `in_sample` (the slot is optional in the label schema; the record does not say if the PDF is a development document); a block label also has `tier`, the label `d1` also `rule_id` and `last_page`. The label run has `run_mode: floor` and lists the input files (the PDF, the block file, the decisions file, the atoms, the Docling output, the calibration file) with paths of the scratch root.
- Calibration records: each one is the record of the calibration file with two changes. Change 2: the slot `in_sample` is left out (the slot is optional in the label schema). In the calibration file, `plb:inSample` on a calibration record is a constant of the calibration: it says that the measures of the calibration were taken on its own fit set. It says nothing about the PDF of a record. In the record of an own PDF a reader could take it for a statement about that PDF, so the record does not hold it: the TriG file and the RDF/XML file of such a record hold no statement `plb:inSample`, and `calibrations[].in_sample` of the view is null. `manifest.json` key `calibration_in_sample` (`{left_out, why}`) records this. The calibration records of a SAMPLE record keep the slot (converter bytes); there it has the meaning of this point, not "this document is a development document". Change 1: the slot `reference_source` holds the neutral text "reference labels of the development documents, made by a language model and not checked by a human" in place of the text of the calibration file (that text names document numbers and folders of the project). `manifest.json` key `calibration_reference_source` records the replacement. No file of the record holds a document number of another document or the words of the reference text (gate rows of stage P0b). Paths relative to the code layout and to the scratch root of the run stay: they name the files that the worker read.

`manifest.json` (schema `parlpdfech-pdf-only-record/1`): `doc_id` `local`; `source_iri`; `pdf_sha256`; `record_iri`; `container_iri`; `named_graphs`; `mode` `floor`; `split` null; `writer` (`worker/pdf_only.py`, version, SHA-256); `reused_files` (SHA-256 of 7 converter files); `schemas`; `inputs`; `calibration_ids`; `counts` (the keys of a converter manifest that apply; `textblocks_by_slot` is 0 and 0, `textblock_records_profile_only` counts the text blocks); `outputs`; `rdf`; `validation`; and:

- `conformance`: `pdf_only_with_recorded_gaps`. The record is not a full eCH-0295 record.
- `apertus`: `none`, with `apertus_note`. `sample_of_the_package`: false. `development_document`: null (not known), with `development_document_note`. `probabilities_checked_on_other_documents`: false, with `probabilities_note`. `calibration_reference_source`: `{replaced, text, why}`. `calibration_in_sample`: `{left_out, why}`.
- `recorded_gaps`: `{"cause", "export_record": null, "absent_slots": [{"slot", "required_in_i95"}], "text_blocks", "not_a_full_ech_0295_record": true}`. `absent_slots` is `Container.affairs` and each slot of the class Affair of the I95 schema (21 entries; 3 of them are required in I95: `Affair.global_uri`, `Affair.affair_number`, `Affair.affair_type`). The list is read from the schema at run time.
- The manifest has no key `i95_gaps`. That key names gap slots of an affair that exists.

`validation.json`: `conformance` (same value), `conformance_note`, `recorded_gaps`, the checks `C1_linkml` to `C9_e19` and `C10_shacl` with the keys of a converter record, `passed` (C1 to C9), and `skipped_checks`.

| Check | State for a PDF-only record |
|---|---|
| `writer_check` (`manifest.json` key `check_passed`) | runs: check E19 of each text block at write time |
| `C1_linkml` | runs: the eCH-0295 file against I95 (class Container; I95 permits a Container with no affair; the check does not show a full record), the provenance file, the label file, the atom layout |
| `C2_parse`, `C3_isomorphism`, `C4_parts`, `C5_leaf_values`, `C6_iri_scheme`, `C7_C8_labels` | run, through the functions of the validator |
| `C9_e19` | runs in another form: the text is the key `text_content` of each TextBlockRecord; also: the lines of the record are the lines of its blocks, and the copy label holds the SHA-256 of the text |
| `C10_shacl` | `skipped` (no pyshacl), as for a sample |
| `metadata_values` | `skipped`, reason `no_export_record` |
| `i95_gap_rule` | `skipped`, reason `no_affair` |
| `independent_wording_comparison` | `skipped`, reason `no_text_block_in_ech_instance` |

`convert.json`: the keys of chapter 3 with `doc_id` null, `origin` `new`, `apertus` `none`, `reference` null, and the added key `fresh`: `{version, document_iri, export_record: null, pdf_check{pages, pages_with_text_layer, ...}, ocr, docling{settings, tools, settings_equal_to_stored, tools_equal_to_stored, backend, page_text_sources, seconds_initialize, seconds_convert, ...}, atoms, language, rules, reduced_tables, states_provider{kind}, search_path_entries_removed, sample_of_the_package, development_document, not_measured}` (`sample_of_the_package` is false, `development_document` is null).

The LinkML dumper stops for an IRI of the scheme `urn`. The RDF step of `pdf_only.py` adds the prefix `urn` to the prefix map of the schema views in memory. No schema file changes.

### 10.4 The view

- `run_info` has the optional key `ocr` (`apple` or `none`). `run.origin` is `new`, `run.apertus` is `none`, `run.in_sample` is null and `labels[].in_sample` is null for each label (not known), `doc_id` is null, `document.has_export` is false, `document.conformance` is `pdf_only_with_recorded_gaps`, `document.title`, `affair_number`, `affair_type` and `parliament` are null.
- Notices of an own PDF, in this sequence: `proposal`, `no_human_check`, `no_apertus`, `chosen_not_top` (if it applies), `no_text_block` (if it applies), `no_export`, `not_a_sample`, `not_examined_pipeline`, then `ocr_apple` or `ocr_none`, then `shacl_not_run`, `not_valid` (if it applies).
- `contract/view.schema.json` has the codes `ocr_apple`, `ocr_none`, `not_a_sample` and `rdfxml_not_readable` (list `NOTICE_CODES` of `contract/tools/make_schema.py`). A view of an own PDF is valid against the schema (measured in the gate).
- The order for this stage named the codes `no_export_record` and `new_conversion_not_measured`. The view uses `no_export`, and `not_a_sample` with `not_examined_pipeline`. Their texts are fixed in `contract/strings.contract.json`.
- `calibrations[].reference_code` is `model_labels_not_human_checked`.
- `document.head[]` has one entry (the Container IRI, origin `identifier`).
- `document.text_blocks[]` of a text block with the mapping status `profile_only`: `ech_slot` and `instance_path` are empty strings (the schema requires a string), `text_type` is the section key, `label_id` is the copy label of the text block.
- A label of the kind `author_switch` (each record, also a sample): `target.block_id` is null (the subject is a boundary IRI), and `target.atom_ids` holds the last line before the boundary and the first line after it. Before this change the view function stopped for such a label (measured with a PDF that has a switch; no sample of the modes `auto` and `rules` has a switch label).

### 10.5 The server and the page

- `GET /api/health`: `modes.upload` is true for the profiles `native` and `full` and false for `slim`. `modes.reason.upload` is null or `profile_slim`. `ocr` is `apple` for the profile `native` on macOS, else `none`. The server does not test if the package `ocrmac` is present; the worker does.
- Screens S0 and S2: the mode line follows `modes.upload`, `ocr` and `modes.apertus_stored` (chapter 7.3). The keys `s0.mode.slim`, `s0.mode.full` and `s2.mode.upload` do not exist.
- Strings of this stage in `ui/strings.json` (English and German): `mode.upload.*`, `mode.ocr.*`, `notice.ocr_apple`, `notice.ocr_none`, `notice.not_a_sample`. The sentence `mode.ocr.apple` says that the conversion decides for each page if it reads the text layer or uses Apple OCR (measured: Apple OCR also gave the text of pages that have a text layer).

### 10.6 The states provider (interface only)

`worker/states_provider.py`: kinds `none`, `stored`, `remote`. Only `none` exists; the two other kinds stop with `NotImplementedError`. `worker/README.md` names what a provider must deliver. `convert.json` key `fresh.states_provider.kind` is `none`. A later stage can add a kind with no change of the HTTP API: the stage `apertus` then gets `running` and `done`, and the last line gets another value of `apertus`.

## 11 Corrections of the examination step (13.10.2026)

Three examiners examined the stage P0a, and one builder made the stage P0b. This chapter fixes what changed after that. Where it differs from a chapter above, this chapter applies. Each point is built; the measured results are in `STATE.md`, and `EXAMINATION.md` lists each finding.

### 11.1 The server

1. Start. The server binds the port, then takes an exclusive lock on the file `<WORK_DIR>/.lock`, then deletes what an earlier process left in `jobs/`. A second process with the same port or the same work folder stops with exit code 2 and changes no file.
2. Host and origin (chapter 5.4). The server answers a request only if the `Host` header (and the authority of an absolute request target) names `localhost`, `127.0.0.1`, `[::1]` or a name of the new variable `PARLPDFECH_ALLOWED_HOSTS` (a list with commas; default empty). The port is not compared. `/healthz` has no host rule. A request with another method than GET or HEAD is refused if it has an `Origin` header that is not `http://<Host>` or `https://<Host>`, or a header `Sec-Fetch-Site` with another value than `same-origin` or `none`. The answer is 403: below `/api/` the error object with the new code `forbidden`, else the text `forbidden`.
3. Error codes (chapter 5.1): 20 codes at that step (22 now: chapter 5.1). New: `forbidden` (403, server) and `pdf_unreadable` (422, worker, exit code 3: the file does not open as a PDF or has no page).
4. A path below `/api/` that is not UTF-8 after the percent decoding gives 404 with the error object `not_found`.
5. Each answer below `/api/` and `/healthz` has the header `Content-Security-Policy: default-src 'none'; sandbox; frame-ancestors 'none'`. Chapter 5.4 said that the policy is only on the answers below `/app/` and `/`.
6. Static files (chapter 2.2). Below `/app/` the server gives only: `/app/` (the file `index.html`), a regular file at the top level of the UI folder with one of the extensions `html`, `js`, `css`, `json`, `svg`, `ico`, `png`, `woff2`, `txt`, and a regular file below `pkg/` with the extension `js` or `wasm`. A name has only letters, digits, `.`, `_` and `-`, has at most 100 characters and does not start with a dot. Each other address below `/app/` gives 404 with no redirect: a folder, `README.md`, `tools/`, `fixtures/`, a dot file, a symbolic link. For `PARLPDFECH_SITE_DIR` the server refuses a path part that starts with a dot or has more than 255 bytes, and an error of the file system gives 404.
7. The cache rule for a file name with a content hash: the part has 8 or more hex digits and 1 or more of the letters a to f, or 16 or more hex digits. A part of decimal digits only (a date) is not a content hash.
8. Stage events (chapter 5.2 said "the stage line of the worker, not changed"). The data of an event `stage` is an object that the server builds from checked values of the worker line: `event`, `id`, `state`; `origin` only `stored` or `new`; `seconds` only a number that is 0 or more; `counts` only a flat map of numbers with keys of at most 32 letters, digits and `_` (at most 12 keys); `reason` and `note` only one word of at most 64 characters from `[A-Za-z0-9_.:-]`. No other key passes. The keys of the object are in the sequence of the alphabet. One job keeps at most 64 stage events; a later stage line is dropped and counted in the log.
9. A job that ends with no record (`failed`, `stopped`) has no stage with the state `running` in its job object: such a stage gets the state `failed` with the reason `timeout`, `stopped` or `job_failed`.
10. `POST /api/jobs` with a file: one request sends a file at one time. A second upload in that time gets 409 `busy`; `detail.job_id` is the running job or an empty string. The read of the form has a time limit (new variable `PARLPDFECH_UPLOAD_TIMEOUT`, default 120 s; the answer is `bad_request` with the field `body`). Before an early answer (`busy`, `too_large` from the declared length, an error of a form field) the server reads and drops the rest of the body, at most `max_bytes` plus 4 MB and 5 s.
11. A worker output is a record only if it holds the 11 files of chapter 3 with one document prefix and no other file; else the job ends with `converter_stopped`, note `output`.
12. The file name of an upload for the display (`input.file_name`): no Unicode format character (for example U+202E), and a name of dots only becomes an empty string.
13. A line of the standard error of the worker goes to the log with at most 2,000 characters and with no control character. The request line of the log holds at most 200 characters of the path. The server writes a warning at the start if the listen address is not a loopback address, or if `index.html` or `samples/index.json` is absent.
14. Not changed, stated as limits: a known address with another method gives 404 `not_found` with an `Allow` header (no code for 405). A request that the HTTP parser refuses gets an answer with no header of chapter 5.4. The server has no time limit for the request header and no limit for open connections. A worker whose child process holds the standard output open keeps the job slot until the job time limit.

### 11.2 The worker and the code layout

1. `layout_manifest.json` has the key `compiled`: the SHA-256 of each compiled Python file. The worker uses a compiled file only with this SHA-256. `layout.py --check` also compares these files.
2. `convert.json` key `checks`: `true`, `false` or `null` (the validator did not run the check). The count `skipped` of the stage `check` holds the checks that did not run. New key `validation_paths_made_relative`.
3. `validation.json` is the file of the validator with one change: the text of the scratch root is removed from error texts of the parser. Chapter 3 said "the bytes of the converter, not changed"; this applies to the other 8 converter files.
4. The inputs folder of the view function can hold `export.json` (chapter 4.5). The worker puts the export record of a sample there.
5. A PDF that does not open or has 0 pages: `failed` with `pdf_unreadable`, exit code 3 (chapter 10.1 has this form now).

### 11.3 The sample index and the view

1. Each sample of `samples/index.json` and of `GET /api/samples` has the key `parliament_name` (export record key `body.name`). `worker/make_samples.py` writes it.
2. View (chapter 6): `document.parliament_name` (optional). `calibrations[].basis.n` is optional (null if the record counts documents only); `basis` also comes from the parameters `blocks` and `precision`, and from `dev_correct` with `dev_documents`. `labels[].source.head` is `D1` also for the document label with the source `rule` and a calibration of the method `verifier_platt`. `checks[].state` `skipped` has the reason `shacl_tool_absent` or `earlier_check_failed`. The notice `shacl_not_run` comes only if `C10_shacl` did not run.
3. Notice codes: the schema has `ocr_apple`, `ocr_none`, `not_a_sample` (chapter 10.4) and the new code `rdfxml_not_readable` (`params.n`: the number of RDF/XML files that the parse check did not read). A view of an own PDF is valid against `contract/view.schema.json` (measured in the gate).
4. The examples `contract/examples/view_26171.json` and `samples.json` hold these changes. `ui/fixtures/` holds copies.

### 11.4 The page

1. Contract strings (chapter 7.5 and `contract/strings.contract.json`), new texts: `notice.proposal` ("Each label that a code rule or a read-out decided is a proposal with a probability. The probability is the calculated probability that the label agrees with the AI reference of the project. The stored values have the limits 0.005 and 0.995."), `notice.no_human_check` ("No person checked these results."), `notice.stored_apertus`, `notice.chosen_not_top`, `s2.limits`, `s2.doc_id`, `s0.button.upload`, `s3.stage.apertus`, `kind.block_slot`, `source.apertus_readout.*`, `unc.other_higher`, `unc.basis`, `unc.target.target_not_met`. The keys `s0.mode.slim`, `s0.mode.full` and `s2.mode.upload` are gone. Chapter 7 has the state of now.
2. S0 and S2 (chapter 7.3): the mode line is a set of sentences that the page selects by `modes.upload`, `ocr` and `modes.apertus_stored` of `/api/health` (keys `mode.*` of `ui/strings.json`).
3. S1 and S4: the name of the body with its key in parentheses, the kind of affair from the map `affair_type.<value>`, the name of the language, and the counts of the two results of a sample if the two records exist.
4. Chapter 7.6, point 3: the sentence for a label whose selected answer has not the highest number names the selected answer and its number, and says who selected the answer (`unc.other_higher`, `unc.other_higher.rule`, `unc.other_higher.readout`). Point 5: a label of the group `rule` whose calibration has the method `verifier_platt` shows `source.rule.readout_number`. Point 6: the basis line shows for a label of the group `rule` (now `unc.rule.basis.blocks` or `unc.basis.documents`, chapter 7.6).
5. The fixture mode (`?fixture=1`) is a mode for the development of the page. The server does not serve `ui/fixtures/`.

### 11.5 The gate

`contract/tools/gate_api.sh` and `contract/tools/gate_compare.py` also run the checks of stage P0b (gate name `P0b`: health, the upload of a synthetic PDF with a text layer, the view against the schema, the 11 files, the archive, the mode `rules`, 6 refusals, DELETE) and the checks of the points 2, 4 and 6 of chapter 11.1. `contract/tools/make_test_pdf.py` writes the synthetic PDF files. The gate point G5 "an upload of a PDF that is not a sample gives `not_in_package`" applies to the profile `slim` only; for the profiles `native` and `full` a PDF with one empty page gives `no_text_layer`. The work folder of the server must hold no record at the start of the gate.

## 12 Changes of the correction round (13.10.2026)

Two fixers changed the package after the skeptic check (findings V-01 to V-14 and the full list of the examiner of the page). `EXAMINATION.md` lists each finding. The chapters 6, 7 and 10 above hold these changes in place; this chapter is the list.

1. Chapter 4.2: the notes `out` and `scratch` of `converter_stopped`; `pdf_unreadable` in the list of the refusals.
2. Chapter 6, view: `labels[].note_code`, `note_params` and a filtered `note` (no raw note of the converter); `calibrations[].reference_code` replaces `reference_source`; `in_sample` has three states and is null for `origin` `new`; the notice code `not_a_sample` replaces `outside_fit_population`; the value `in_sample` of the labels `d1` and `r2` of a sample comes from the decisions file.
3. Chapter 7, page: the screens as they are now (7.3), the words that the page does not print (7.5), the card rules (7.6 points 3, 5, 6, 10, 11), the contract keys that the page does not use (7.7), the mount option `hasExport` (7.4), the case for a record address with a wrong form (7.2).
4. Chapter 10, record of an own PDF: no label has the slot `in_sample`; the calibration records carry a neutral reference text; new keys of `manifest.json` (`apertus`, `apertus_note`, `sample_of_the_package`, `development_document`, `development_document_note`, `probabilities_checked_on_other_documents`, `probabilities_note`, `calibration_reference_source`) and of `convert.json` key `fresh` (`sample_of_the_package`, `development_document`, `search_path_entries_removed`, a changed text `not_measured`). The eCH-0295 graph of the record keeps its 1 statement; the record of the gate has 1,311 statements (before: 1,322; the `in_sample` statements are gone).
5. Worker: `PYSTOW_HOME` and `TMPDIR` below the scratch folder of the job; the search path entry `src` of a converter copy is taken out; `layout.py` removes and reports compiled files that the manifest does not record.
6. Build: the server binary and the WebAssembly bundle are built with `--remap-path-prefix` for the home folder, the package folder, the cargo home and the rustup home (`Makefile`, `rdfcheck/build.sh`); the two build steps search the output for a path of the build host and fail on a hit. The same lines of the `Dockerfile` were written and not run.
7. Chapter 8 and 11.5, gate: `contract/tools/gate_api.sh` also saves the 11 files of the upload record of the mode `rules`. The gate has 100 rows with a reference run: 7 new rows of the gate name `P0b` (the search list of document numbers; for each of the 2 upload records: no document number of another document, no absolute path or project path outside the code layout and no words of the reference text, no slot `in_sample` and the new manifest keys) and 1 new row of G4 (no document number of another document, no project path, no words of the reference text and no raw note in `view.json` of each record). Gate point G4: the view of `s-26171` equals the example under the rule of chapter 8.
8. `rdfcheck/tools/check_wasm.mjs` reads `manifest.json` key `conformance`: for `pdf_only_with_recorded_gaps` it requires 0 rows for the example of the head values and no label with the statement `plb:inSample`; it also searches the two bundle files for a path of a build host.

Not changed and open for the contract owner: the 12 unused contract keys (chapter 7.7); a code for HTTP 405 (chapter 11.1 point 14); `/api/health` does not test that the states file of a sample exists; the text of the neutral reference sentence needs the confirmation of the owner (`STATE.md` chapter 9).

## 13 Changes after the second skeptic check (13.10.2026)

The second skeptic check made the list S2-01 to S2-10 (`EXAMINATION.md` chapter 9). The chapters 6, 7 and 10 above hold these changes in place; this chapter is the list. The quotes of contract texts in chapter 11.4 point 1 are the texts of that step; where they differ from `contract/strings.contract.json`, the file applies.

1. Contract strings, 13 keys with a new text in `contract/strings.contract.json` and `ui/strings.json`: `app.title` and `s0.title` ("A PDF of a Swiss parliament or government becomes data. On this computer."; one sample is a resolution of a government), `notice.proposal` (the last sentence), `notice.in_sample_heads`, `notice.in_sample_rules`, `notice.stored_apertus`, `notice.not_a_sample` (the last sentence), `notice.not_examined_pipeline`, `notice.shacl_not_run`, `s3.time`, `unc.target.target_not_met`, `unc.target.target_met`, `unc.target.not_met_on_unseen_parliaments`. No key was added or removed (108 keys).
2. Page keys (`ui/strings.json`, 430 keys; 6 new: `fmt.size.mb`, `fmt.size.kb`, `fmt.size.bytes`, `s3.stage.read_pdf.sample`, `s3.stage.lines.sample`, `s4.card.nochars`). Changed texts: `s0.sample.note`, `about.p1`, `about.steps.note`, `s2.selected` (placeholder `size`), `consistency.not_found`, `fmt.name_id`, `group.apertus_readout`, `unc.other_higher.readout`, `method.*` (3 keys), `detail.slot`, `detail.value`, `s4.head.slot`, `slot.localId`, `words.reference`, `words.readout` (German), `check.C6_iri_scheme`.
3. `consistency.not_found` is "not found with the same letters in the text of the PDF". Read in the converter code: the comparison is a search for the exact letters of the value in the text of the lines; white space is merged and a value can go over a line end. It does not find a value with another first letter or another word division.
4. Chapter 7.3: the names of the first two stages for a sample; the size of the selected file. A block with an empty character range shows `s4.card.nochars` in place of "characters 0 to 0". The one tab stop of the drawn page starts on the first line with text.
5. Chapter 7.4: the stored names of the panel tables are in `title` attributes (panel key `rdf.stored_name`; `ui/rdfpanel.strings.json` has 83 keys); the row for labels with no `plb:inSample` statement shows "not known".
6. Chapter 10.3: the calibration records of the record of an own PDF have no slot `in_sample`; `manifest.json` has the new key `calibration_in_sample`. The record of the synthetic test PDF has 1,307 statements (before: 1,311; 4 calibration records; measured on one upload through the server).

## 14 A hosted sample site: the settings `PARLPDFECH_READONLY` and `PARLPDFECH_SAMPLE_RUNS` (13.10.2026)

The package can run as a public site that shows the sample documents only (`deploy/`). Two settings of the server make this possible. With no setting the server behaves as the chapters above say. Each point is built; the measured results are in `STATE.md` chapter 10.4.

1. `PARLPDFECH_READONLY=1`. `POST /api/jobs` with a field `file` gets 403 with the code `read_only` and `detail.note` `upload`; the server writes no byte of the file and starts no job. Each `DELETE` below `/api/` gets 403 `read_only` with `detail.note` `delete`, also for an id that does not exist; a `DELETE` of another address gets 403 with the text `forbidden`. The host and origin rules of chapter 11.1 come first (code `forbidden`).
2. `PARLPDFECH_SAMPLE_RUNS=off`. `POST /api/jobs` with `sample` gets 403 with the code `sample_runs_off` and `detail.record_id` (chapter 15 point 6; before that chapter: the code `read_only` with `detail.note` `sample_run`) when the record of that sample and mode is in the work folder (the file `view.json` of the record folder exists; in an image the start command copies the seed records there). No job starts. If the record is absent, the run is accepted. The checks of the request (`bad_request`, `sample_unknown`) and the rule `busy` come first.
3. Error code `read_only` (403, server; `contract/errors.json`, 21 codes at that step, 22 with chapter 15): title "This site shows the samples only", text "This site shows the samples only. It takes no file and deletes no result.", action "Open the result of a sample.", exits `sample` and `start`.
4. `GET /api/health`: the two new keys `modes.read_only` (true or false) and `modes.sample_runs` (true or false). `contract/examples/health.json` has them. `modes.upload` is false if `modes.read_only` is true; `modes.reason.upload` is `profile_slim` in the profile `slim` and `read_only` in another profile.
5. The page (chapter 7.3), as it was at that step; chapter 15 point 5 replaces the entries for an own PDF. If `modes.read_only` is true: S0 shows the line `s0.line.read_only` and the note `s0.upload.note.read_only` (this key is gone); the mode line of S0 starts with `mode.read_only` in place of `mode.upload.yes` or `mode.upload.no`; S2 shows the text `s2.read_only` and a link to the samples in place of the form (the button of S0 and the navigation entry still lead to S2); S3 has no stop button; S4 has no part "Delete the result"; the link to a ready record on S1 has the text `s1.open.site`. If `modes.sample_runs` is false: a card of S1 shows for a mode whose record is ready one link `s1.open.site` and no convert button; a mode with no record keeps the convert button. 5 new keys of `ui/strings.json` (435 keys); no contract key changed.
6. The size of a file and each other number with one decimal (S2, the downloads) has the number form of the page language (`en`, `de-CH`), as the counts have. The two forms have a point before the decimal.
7. At that step: the contract texts `app.title`, `s0.title` and the text of the code `forbidden` say "on this computer" or name `localhost`, and the page showed them also on a public site. Chapter 15 point 4 gives the page other texts for a hosted site; the contract texts themselves are not changed.

## 15 One site: the static pages below `/`, the setting `PARLPDFECH_HOSTED`, the texts of a hosted site (13.10.2026)

Each point is built. The measured results are in `STATE.md` chapter 10.5. The contract owner did not confirm the new keys, the new code and the new texts.

1. **The address plan of one server.** The app lives at `/app/` (language: the query `?lang=de` or `?lang=en` before the hash; a result: `/app/#/record/s-<document number>` or `/app/?lang=de#/record/s-<document number>`; the id of the mode `rules` ends with `-rules`). The static pages live at `/`, the German pages at `/de/`. `/api/...` and `/healthz` are the API. A page of the site can link to these addresses with an absolute path. The app links to `/` (to `/de/` in German) only if the server gives a site.
2. **The site folder** (`PARLPDFECH_SITE_DIR`). The server gives each regular file of the folder at its path; a folder address with a slash at the end gives its `index.html`; a folder address with no slash gives 307 to the address with the slash (a relative `Location`); a path with no file gives the file `404.html` of the folder with the status 404, or the plain text `not found` if the folder has no such file; a path part that starts with a point gives 404. A method that is not GET or HEAD gets 405 and no file. Media types by the file extension, text types with `charset=utf-8`: `html`, `css`, `js` (`text/javascript`), `json`, `svg`, `txt`; `yaml` and `yml` give `application/yaml` (as the record files, chapter 3); the file name `SHA256SUMS` gives `text/plain`; another name with no extension gives `application/octet-stream` (read in the file service library; not run). The answers have `Last-Modified`, and a request with `If-Modified-Since` gets 304. The server follows a symbolic link of the site folder; the build tool of the source tree refuses a site folder with a link.
3. **Headers and rules of the site.** The headers of chapter 5.4 with the policy of the site: it permits one script file, one style sheet and pictures of this server and requests to this server (the pages read their data files), and nothing more: no inline script, no WebAssembly, no font file, no form, no frame. A `script` element with the type `application/json` is data and needs no permission. The `Host` rule and the origin rule of chapter 11.1 apply to each address of the site as to `/app/`. With `PARLPDFECH_READONLY=1` a `DELETE` of a site address gets 403 with the text `forbidden` before the file service.
4. **`GET /api/health`: the keys `site` and `hosted`** (top level, true or false). `site` is true if the server gives a site folder. `hosted` is true if and only if `PARLPDFECH_HOSTED=1`. The rule for `hosted` is a statement of the operator and not a guess from the profile: a read-only server of the profile `slim` can run on the computer of the reader (the container of `make run` with the setting), and a hosted server can have another profile. If `hosted` is true, the page takes for each text the key with the ending `.hosted` if the strings file has it (20 keys: `s0.title`, `s0.line`, `s0.upload.note`, `notice.stored_apertus`, `s3.time`, `s4.delete`, `s4.delete.note`, `foot.line`, `about.p4`, `about.steps.note`, `s1.lead`, `s1.open`, `s2.sending`, `case.network.text`, `case.network.action`, `mode.upload.yes`, `cmp.line`, `words.apertus`, `source.stored_value`, `s4.headline.new`), and for the server codes `forbidden` and `internal` the page texts `err.hosted.forbidden.text`, `err.hosted.forbidden.action` and `err.hosted.internal.action` in place of the texts of the error object. The texts say "on the server of this site" in place of "on this computer"; for example `about.p4.hosted`: "The conversion runs on the server of this site. Your browser sends its requests to this site and to no other site." The page asks `/api/health` before it shows its first text. The error object of the API keeps the texts of `contract/errors.json` on each server.
5. **No entry promises an upload on a site that takes no file** (`modes.read_only`). The second way of S0 has the text `s0.button.local` ("Run it on your computer") with the note `s0.local.note` ("This site takes no file. With the package on your computer, you convert a PDF of your own."); the navigation entry has the text `nav.local` ("On your computer"); the two lead to `#/upload`. S2 has the headline `s2.title.read_only` ("Convert your own PDF on your computer"), the text `s2.read_only` ("This site shows the samples only. It takes no file and deletes no result. To convert a PDF of your own, start the package on your computer. The file README.md in the source of the package gives the commands and says what the computer needs."), a button to the samples and, if `site` is true, the link `nav.site` to the pages about the project. If `modes.sample_runs` is false, S1 has the lead `s1.lead.ready` (a result that is ready opens; no new run starts for it).
6. **Error code `sample_runs_off`** (403, server; `contract/errors.json` has 22 codes): the refusal of a sample run for a ready record with `PARLPDFECH_SAMPLE_RUNS=off`, with `detail.record_id`. Title "The result of this sample is ready", text "The result of this sample is ready. This server starts no new run for it.", action "Open the result of the sample.", exits `sample` and `start`. The text is true with and without `PARLPDFECH_READONLY`: with the setting `off` alone the server still takes a file and deletes a record, and the code `read_only` is no longer used for this refusal.
7. **The link from the app to the site.** If `site` is true, the navigation of the app has the entry `nav.site` ("About this project" / «Über das Projekt») with the address `/` (German page: `/de/`). With `site` false the entry is hidden.
8. **The source tree and the image.** `make dist-src SITE_DIR=<folder>` copies a built site to `site/` of the tree; `DIST-MANIFEST.json` lists its files (key `site`: the count and the bytes), and `container/check_dist.py` compares them. The Dockerfile of such a tree has the line `COPY site/ /app/site/`; each image sets `PARLPDFECH_SITE_DIR=/app/site`, and an image with no such folder redirects `/` to `/app/`. `make run-native SITE_DIR=<folder>` gives a site with no container. The Dockerfile lines were written and not run.
9. Page keys: `ui/strings.json` has 463 keys (435 before; 1 key removed, 9 new keys of the page, 20 keys with the ending `.hosted`). No contract key changed. Not changed and open for the contract owner: the contract texts `s0.title` and `notice.stored_apertus` and the texts of the codes `forbidden` and `internal` stay as they are for a local run; the unused contract key `s4.head.new.rules` says "on this computer" and is not shown. The German texts of this chapter use the word «Website» for the site and «Seite» for one page; the German text of the code `read_only` (a text of `contract/errors.json`) still says «Diese Seite» for the site.

## 16 Values that are read from the PDF (13.10.2026)

This chapter describes the record form of now. Where it differs from the chapters 3 to 15, this chapter applies. The chapters 4.4, 8 and 10.3 describe the earlier record form. That form stays in the package behind one switch (16.2).

### 16.1 The rule

1. Code rules with tiers (the value readers) read 7 fields from the text of the PDF: the affair type, the title, the affair number, the submission date, the response date, the responder and the first author.
2. Each value has the wording of the PDF, the value of the record, a rule tier and a probability. It also has a page and a span in the document text.
3. The probability of a value is the share of the development documents in which a value of its rule tier was equal to the OpenParlData value (Jeffreys mean). The reference of that measurement is the OpenParlData export.
4. No value of the eCH-0295 part comes from the export. A value that the rules do not find is absent, and the record gives the slot the state `not_found_in_pdf` with a reason. No value is invented. Chapter 17 adds: the value as the document prints it, the floor, and the check that makes each value again.
5. The export record of a sample is the cross-check only. A value of the export stands in the comparison of one value, in the provenance file and in the label of that value. It never stands in the eCH-0295 part.
6. eCH-0295 (version I95) requires the affair type and the affair number. If the rules find none (or only a weak candidate, chapter 17), the slot is absent and the record states a recorded gap. The conformance name is `i95` with no gap, else `i95_with_recorded_gaps`.
7. A PDF with no export record gets the same record form: one affair, the two steps with their text blocks, the value labels and the manifest. It has no cross-check.

### 16.2 The worker

| Part | Rule |
|---|---|
| Record path | `worker/values_record.py` calls 3 converter files of the code layout: the value readers (`m11_values_base` and the 4 rule modules), `m11_writer` (`write_record`, `rdf_step`) and `m11_validate` (`validate_record`). |
| Inputs of the readers | the block file and the rule file only. The readers read no export record and no model state. An error of one reader does not stop the conversion: the field gets the reason `reader_error`. |
| Sample | the stages `rules` and `apertus` are not changed. The block labels of the mode `auto` and of the mode `rules` are the labels of the earlier record form (checked: equal). The export record of the sample goes to the writer for the cross-check. |
| PDF that is not a sample | the same record path runs after the fresh steps (Docling, lines, block file, rules, floor decisions). It has no export record. The record IRI is `urn:parlpdfech:local:sha256:<hash>/record`. |
| Files | the 9 converter-form files of chapter 3 keep their names. `manifest.json` has the schema `parlpdfech-pdf-values-record/1`. `validation.json` has the checks `C1_linkml` to `C9_e19`, `C10_shacl` (information) and `C11_wording_at_span` to `C19_value_forms`. |
| `valid` | true if the writer check passed and each check of the validator that ran passed. |
| `convert.json` | the new key `values`: `state`, the calibration file with `measured`, the counts of the values and of the slot states, the conformance name, the recorded gaps. |
| Switch | `PARLPDFECH_VALUES=off` gives the earlier record form (`m10_writer` for a sample, `worker/pdf_only.py` for another PDF). The gate of chapter 8 needs it. |
| Hold list | `worker/values_hold.json` names samples (document number and SHA-256 of the PDF) that keep the earlier record form. No value reader runs on them. Their view has `head_values.state` `held` and the notice `head_from_export`. The list is a hold, not a result. |
| Code layout | `worker/layout_add.py --values` adds the 10 files of the values and the calibration file to `worker/layout_files.json`. Then `worker/layout.py` makes the layout. |

The calibration file of the values: `daten/gj_values/calibration_values_dev.json` of the code layout, if the layout holds it. Else the worker uses the stand-in file of the layout. The numbers of the stand-in file are synthetic. They are not a measurement.

### 16.3 The view (`parlpdfech-site-view/3`)

The view has 3 new keys at the top. Each key is always there.

| Key | Content |
|---|---|
| `head_values` | `source` (`pdf`, `export` or `none`), `state` (`pdf`, `off` or `held`), `cross_check`, `probabilities_measured`, `i95_gaps`, `fields_not_read`, `counts`, `slot_counts` |
| `values[]` | one entry for each value that is read from the PDF: `field`, `slot`, `name_key`, `value_printed`, `value`, `probability`, `value_status`, `measured`, `tier`, `rule_id`, `normalisation_rule`, `page`, `last_page`, `char_start`, `char_end`, `block_id`, `atom_ids`, `spans[]`, `export_check`, `export_value`, `label_id`, `calibration_id`, `instance_path` |
| `slots[]` | one entry for each of the 52 slots of `Affair`, `Submission` and `ResponseStep`: `slot`, `state`, `reason`, `field`, `label_id`, `gap_id`, `export_has_value`, `name_key` |

1. The 4 slot states are `read_from_pdf`, `not_found_in_pdf`, `not_in_this_document_type` and `register_only`.
2. The 4 results of the cross-check are `equal_to_export`, `differs_from_export`, `no_export_value` and `not_compared`.
3. `export_value` is the value of the export for the first two results. The page must show it in the comparison only.
4. `export_has_value` says if the export has a value for a field that the PDF does not print. The value of the export is not in the view.
5. If `probabilities_measured` is false, each value has `probability` null, `value_status` `none` and `measured` false. A calibration record of the kind `pdf_value` then has no count. The view holds no number of the stand-in file.
6. `document.title`, `document.affair_number` and `document.affair_type` are the values that were read from the PDF, or null.
7. `document.head[].origin` has the new value `pdf_rule`. `labels[].kind` has the new value `pdf_value`. A label of that kind has no options.
8. `calibrations[]` has the new keys `tier` and `measured`, and the new reference code `export_register_value`.
9. For the earlier record form `values[]` and `slots[]` are empty, and `head_values.source` is `export` or `none`.

New notice codes: `values_from_pdf`, `values_from_pdf_no_check`, `values_measured`, `values_not_measured`, `recorded_gaps`, `head_from_export`. The notice `no_export` is only for the earlier record form of a PDF with no export record.

### 16.4 The page

1. The result page starts with the part "The eCH-0295 record", if `head_values.source` is `pdf`.
2. The line above the tables is the string `s4.record.lead.check` (with a cross-check) or `s4.record.lead.no_check`.
3. The part has 3 tables: the affair, the submission and the response step. A row is one slot with its state.
4. A value row shows the wording as printed, and the value of the record if it differs. It shows the probability as the stored decimal and the word certain or unsure. The button "Show on the page" marks the line and draws a frame around the span.
5. With `probabilities_measured` false the page must show the string `s4.record.not_measured` and no number for a value.
6. The technical details of a value row give the rule tier, the rule id, the place and the name of the slot.
7. With a cross-check the table has the column "OpenParlData": equal, different (with the value of the export), no value there, not compared.
8. A row with no value shows the state and the reason in plain words. Each slot with no row of its own is in the list of the other entries of its group.
9. The block cards stay below, with the heading "The text parts".
10. The start page, the text "What is this?" and the list of words say that the head values are read from the PDF.

### 16.5 Checks

| Check | Command | What it covers |
|---|---|---|
| Worker | `python package/worker/check_values.py` | the switch and the hold list; one sample in the two modes; the same sample with the switch off; a trace of one run; 3 synthetic PDF files |
| API | `python package/contract/tools/gate_values.py --port <port>` | a server with the values path on: one sample in the two modes and 3 synthetic PDF files; view, files, bundle |
| View | `python package/view/check_view.py` | the 4 stored records of the earlier form, and each example view of `contract/examples/` |
| Earlier gate | `make gate` on a server with `PARLPDFECH_VALUES=off` | the gate of chapter 8 and of chapter 10, with no change of its reference |

The table shows the state before chapter 17; chapter 17.6 has the checks of now. No check tool counts how often values equal export values over a set of documents.

## 17 Corrections after the skeptic check of the values (13.10.2026)

This chapter changes chapter 16. Where the two differ, this chapter applies. The findings and decisions are in `EXAMINATION.md` chapter 12. The record form is `daten/gj_values/record_form.md` (version 2) of the project.

### 17.1 The rules

1. The value of the record is what the document prints. The first author, the responder, the title and the affair number are the wording at the span on one line (white space as one space; a hyphen at a line end joined). The affair type is the value of the eCH-0295 list for the printed type word. A date is the printed date as a calendar day (ISO 8601).
2. The folded form that a value reader makes for a comparison (for example a family name in lower case) is the comparison value. It is used for the cross-check and the calibration only. It is in `manifest.json` (key `comparison_values`), in the note of the label and in the value record. It is never in the eCH-0295 part.
3. The validator makes each value again from the document text at the span of its label (check `C20_value_follows_from_wording`). It needs no export record. A record whose value does not follow from its wording fails.
4. REPLACED (chapter 18). Earlier text: The first author is written only if the block labels give a submitted text. Else the slot has the state `not_in_this_document_type`: the rules do not search it there. Writer and validator use this one rule.
5. The floor. A value of a rule tier whose stored probability (calibration file, field and tier, all folds) is below 0.5 is not written to the eCH-0295 part. It stays in the label file as a candidate: label id `candidate-<field>`, value status `unsure`, no path of the record, a note that starts with "not written: the tier is more often different from the reference than equal". The slot has the state `not_found_in_pdf` with the reason `weak_candidate_only`. For the affair type and the affair number the gap rule of 16.1 item 6 applies. Check `C21_floor` enforces it.
6. REPLACED (chapter 18). Earlier text: The calibration file of the product is `daten/gj_values/calibration_open.json` of the code layout, until a later file replaces it. The layout holds no stand-in file. The worker stops if the file is absent. The view function gives no view of a record with stand-in numbers.
7. `worker/values_hold.json` is empty. The 3 samples get the record with values from the PDF in the two modes.
8. REPLACED (chapter 18). Earlier text: A development document of the open part gets, as the probability of a label, the value without the fold of the document. The floor uses the value of all folds, so that one PDF gives one eCH-0295 part as a sample and as an upload. Thus a written value of a sample can have a label probability below 0.5 (sample 879163, affair type: 0.2143; tier 0.6071).

### 17.2 Where the probabilities come from

REPLACED (chapter 18). Earlier text: The probabilities come from the development documents of the open part: 1,486 documents of 36 parliaments (`daten/gj_values/calibration_open.json` of the project). The project record `daten/gj_values/closed_table.md` gives the values on 8 parliaments that the authors of the rules did not read (307 documents). There the share of equal values was lower than the stated probability for two fields: affair number (94 values, mean stated probability 0.856, share equal 0.606) and submission date (126 values, 0.639 and 0.460). For the affair type, the title, the responder and the first author the difference was between -0.013 and +0.011. For the response date it was +0.085 with 19 values. That measurement was made before the floor: its counts include values of rule tiers that the package does not write now.

### 17.3 The worker

1. REPLACED (chapter 18). Earlier text: `values_record.CHECK_IDS`: C1 to C9 and C11 to C21 (19 ids). `convert.json` key `checks` has them and `writer_check`.
2. REPLACED (chapter 18). Earlier text: `convert.json` key `values`: `calibration.path` is `daten/gj_values/calibration_open.json`, `calibration.measured` true, `calibration.stand_in` false; new keys `floor` and `author_rule`.
3. The state `held` of `values_record.state` stays in the code. No sample has it.

### 17.4 The view (`parlpdfech-site-view/3`, additions)

| Key | Content |
|---|---|
| `values[]` | one entry for each label of the kind `pdf_value`: the values of the record and the weak candidates |
| `values[].written` | true: the value is in the eCH-0295 part. false: a weak candidate |
| `values[].value_form` | `printed`, `list_value` or `iso_day` |
| `values[].differs_from_printed` | true: `value` and `value_printed` differ after white space is one space |
| `values[].comparison_value` | the comparison value of the reader, or null |
| `values[].probability`, `value_status` | always a stored decimal and `certain` or `unsure` |
| `values[].tier_probability` | the stored probability of the rule tier from all folds |
| `values[].probability_source` | REPLACED (chapter 18). Earlier text: `all_folds`, `without_own_fold`, or null for a weak candidate |
| `values[].export_match` | for `equal_to_export`: `exact` or `after_normalisation`; else null |
| `values[].instance_path` | null for a weak candidate |
| `slots[].reason` | new value `weak_candidate_only`; `slots[].label_id` then names the candidate label |
| `head_values.document_kind` | REPLACED (chapter 18). Earlier text: the kind of the document that the rules chose (`s1_rule_role`) |
| `head_values.submitted_text` | REPLACED (chapter 18). Earlier text: true if the block labels give a submitted text |
| `head_values.floor` | `threshold` and `not_written` (fields) |
| `head_values.probabilities_measured` | true for the source `pdf`; never false |
| `notices[]` | new code `weak_candidates` (parameter `n`); the code `values_not_measured` is removed |
| `labels[].note_code` | REPLACED (chapter 18). Earlier text: new codes `comparison_value`, `weak_candidate`, `fold_value` |
| `checks[]` | REPLACED (chapter 18). Earlier text: new ids `C20_value_follows_from_wording`, `C21_floor`; 21 entries for a record with values from the PDF |

The schema name stays `parlpdfech-site-view/3`: the keys were added in the same step as the record form, before a release of the view.

### 17.5 The page

1. Each value row: the stored word and the stored decimal, and the count "equal in k of n development documents". One paragraph above the tables says what the number is: the share of development documents in which a value of this rule tier was equal to the OpenParlData value.
2. A value whose form in the record differs from the printed wording shows the two strings: "printed: ...; in the record: ...".
3. A weak candidate shows as such, with the words "not in the record".
4. The cross-check word for a tolerant match is "equal by the comparison rule" / "nach der Vergleichsregel gleich". The cell shows the string of OpenParlData and the rule.
5. A gap text says "the rules found no value in this PDF". No text says "the PDF does not print".
6. The state `not_in_this_document_type` is worded as a decision of the rules: "Not searched in this kind of document" / "In dieser Dokumentart nicht gesucht".
7. The notice `head_from_export` shows only for a record of the earlier form (`PARLPDFECH_VALUES=off`).
8. The RDF panel shows the example query for the head values for each record with an affair.

### 17.6 Checks

| Check | Command | What it covers |
|---|---|---|
| Worker | `python package/worker/check_values.py` | the switch, the empty hold list, the calibration file; the 3 samples in the two modes, each one also with the switch off; a trace of one run; 5 synthetic PDF files |
| API | `python package/contract/tools/gate_values.py --port <port>` | a server with the values path on: the 3 samples in the two modes and 5 synthetic PDF files; view, checks, files, bundle, truth rows; for a sample, a second run of the validator in its own process |
| WebAssembly | `node rdfcheck/tools/check_wasm.mjs <records folder> <doc id>` | knows the two record forms by `manifest.json`; for a record with values from the PDF: the conformance name, one affair, no register address, no statement for the slot of a gap or of a weak candidate, rows for the example `ech_head` |
| View | `python package/view/check_view.py` | the 4 stored records of the earlier form, and each example view of `contract/examples/` |
| Earlier gate | `make gate` on a server with `PARLPDFECH_VALUES=off` | the gate of chapter 8 and of chapter 10 |
| `make test` | | the cargo tests, the 4 example views, the layout check, `check_ui.mjs` if node is there, `check_view.py` |

`worker/check_worker.py`, `worker/check_fresh.py` and `make gate` run with `PARLPDFECH_VALUES=off`: they compare the records with the reference run of the earlier record form (SHA-256 of files, label counts). The record with values from the PDF has other files, so these comparisons do not apply to it.

## 18 The cascade reader and the decisions D1 to D7 (13.10.2026)

This chapter changes the chapters 16 and 17. Where they differ, this chapter applies. Each replaced sentence of chapter 17 has the mark REPLACED. The findings F-1 to F-6 and their decisions are in `EXAMINATION.md` chapter 13. The record form is `daten/gj_values/record_form.md` (version 3) of the project. The cascade is `crisp-dm/04-modeling/ech-cascade.md` (version 2), `src/m11_cascade.yaml` (`m11-cascade-2`) and `src/m11_cascade.py` of the project.

### 18.1 The rules

1. D1. The reader of a record is the cascade reader (`src/m11_values_cascade.py`, `read_document`). The kind of the document selects which of the 7 values are searched. The kind comes from the rule chain (the rule role and the rule id of the rule file) for a sample and for an unknown PDF. A value that the cascade does not search has the slot state `not_in_this_document_type` with the result "not searched in this kind of document", the kind and the ids of the cascade rules.
2. The selection of the 7 values by the kind (the affair type changes no row of this table):

| Kind | Affair type, title, affair number | Submission date, first author | Response date, responder |
|---|---|---|---|
| `proposal`, `executive_proposal` | searched | searched | not searched |
| `response`, `combined` | searched | searched | searched |
| `committee_report`, `minutes`, `other` | searched | not searched | not searched |

3. D2. A response document that prints the authors and the date of the proposal in its head states them. The first author and the submission date are searched for the kinds `response` and `combined`. The record then has a submission step with the sponsorship and the date and with no text block. Cascade rule R30 says so. R30 is a choice of the project. It is not a rule of the standard.
4. D3. A document of the kind `proposal` or `executive_proposal` gets no response step. The body that its text addresses is a candidate label (`candidate-responder`, no path of the record). A text block with a response label in such a document is not written to the eCH-0295 part; it stays in the provenance file.
5. D4. The probability that a record shows for a value is the value of its rule tier over all folds of the calibration file (key `p_all_folds`), for every document, also a development document. No fold value is shown. The floor of 0.5 uses the same number.
6. D5. The calibration file of the product is `daten/gj_values/round3/calibration_dev_all.json` of the code layout. Origin: Development documents of 44 parliaments that the rule authors read. The values on 8 parliaments before the authors read them are lower for the affair number and the submission date: see the numbers of `daten/gj_values/closed_table.md`. A last run on documents that nobody read is planned. Each place that names the origin of the file says this. SUPERSEDED (chapter 19.1 point 1 and `STATE.md` chapter 18): the origin text of 14.10.2026 names the one fixed run of 13.10.2026; AI agents had read a part of its documents before the run.
7. D6. The validator runs the cascade reader again on the block file and the rule file and compares each field with the record: value, span, tier and slot state (check `C22_values_from_the_readers`). A record whose span or tier does not come from the readers fails. The kind of this check comes from the rule chain, never from the manifest.
8. D7. The selection for the kinds `committee_report`, `minutes` and `other` stays as the cascade says. The cost on the development documents is in `ech-cascade.md` chapter 6.3.1: 29 submission dates would be read (20 equal to the export, 9 different) and 32 first authors (20 equal, 3 different, 9 with no export value).
9. The text blocks stay as the block labels give them (the earlier decision W-5), with the one exception of point 4. Thus a record of a kind with no submission step can hold a submission step with a text block. The page says so in the row of that text.

### 18.2 The code layout

`worker/layout_add.py --values` puts 14 paths into `worker/layout_files.json`: `src/m11_writer.py`, `src/m11_validate.py`, `src/m11_values_cascade.py`, `src/m11_cascade.py`, `src/m11_cascade.yaml`, `src/m11_label_schema.yaml`, `src/m11_values_base.py`, the 4 rule modules of round 3, `src/m11_value_norm.py`, `src/m11_value_reference.py` and the calibration file of 18.1 point 6. It removes the entry of `daten/gj_values/calibration_open.json`. The layout has 86 files.

### 18.3 The worker

1. `worker/values_record.py` version `parlpdfech-values/0.3.0`. It calls `m11_writer.read_values`, `write_record` and `m11_validate.validate_record` with `kind="from_rule_chain"`. It stops if the calibration path or the origin text of the writer is not that of the package.
2. `values_record.CHECK_IDS`: C1 to C9 and C11 to C22 (20 ids). `convert.json` key `checks` has them and `writer_check`.
3. `convert.json` key `values`, new keys: `cascade` (`version`, `reader`, `kind`, `kind_from`, `affair_type`, `not_searched`), `calibration.origin`, `addressee_candidates`. `calibration.path` is the path of 18.1 point 6.

### 18.4 The view (`parlpdfech-site-view/3`, additions and changes)

| Key | Content |
|---|---|
| `head_values.cascade` | the cascade of the record, or null if `head_values.source` is not `pdf` |
| `head_values.cascade.kind`, `kind_from` | the kind of the document (one of 7, or null) and where it comes from: `rule_chain`, `argument`, `none` |
| `head_values.cascade.affair_type` | the affair type of stage 1: a value of the eCH-0295 list, or `none` |
| `head_values.cascade.steps[]` | `submission` and `response`: `applies` and the rule ids |
| `head_values.cascade.entries[]` | the 7 values: `field`, `slot`, `group` (`affair`, `submission`, `response`), `state`, `searched`, `rules`, `reason`, `label_id` |
| `entries[].state` | `read_from_pdf`, `not_found_in_pdf`, `weak_candidate`, `not_searched`, `addressee_candidate` |
| `head_values.cascade.texts[]` | the text slot of each step: `applies`, `cut`, `rules`, `blocks` (text blocks in the eCH-0295 part) |
| `head_values.cascade.text_blocks_not_written`, `register_only` | counts |
| `head_values.document_kind` | the kind of the cascade (before: the rule role) |
| `head_values.addressee_candidates` | the fields with a candidate of the kind addressee |
| `head_values.submitted_text` | removed |
| `values[].candidate` | null (written), `weak` or `addressee` |
| `values[].probability_source` | `all_folds`, `no_unit` (the calibration file has no document for the pair of field and tier), or null for a candidate; `without_own_fold` is removed |
| `values[].in_sample` | true: the document is one of the development documents that the number counts |
| `slots[].result`, `kind`, `cascade_rules` | `not_searched` with the kind and the rule ids, for a slot that the cascade cuts; else null, null and an empty list |
| `notices[]` | new codes `cascade_selection` (each record with values from the PDF) and `addressee_candidate` |
| `labels[].note_code` | new code `addressee_candidate`; the code `fold_value` is removed |
| `checks[]` | new id `C22_values_from_the_readers`; 22 entries for a record with values from the PDF |

The view function refuses a record whose probability source is a fold value, a record with no cascade, and a slot of a value with the state `not_in_this_document_type` and no kind. The link checks of `contract/tools/validate_view.py` compare the 7 entries of the cascade with `values[]` and `slots[]`.

The schema name stays `parlpdfech-site-view/3`. A consumer that pins the key set of chapter 17.4 must read this chapter: 2 keys are removed and 1 enum value is removed.

### 18.5 The page

1. The top of the eCH-0295 part has the part "What this document can state": two sentences on the idea; "Kind of this document: <kind> (decided by code rules)"; "Affair type: ..."; the 3 groups (affair, submission, response) with the sentence if a document of this kind can state the step; each of the 7 entries with its state; the text slot of each step; the count of entries that are only in a register; the details part "The whole cascade" with the 5 stages (one line each, from the key `stages` of the cascade file).
2. The texts of the 5 states of an entry: "Read from the PDF" with the value, "probability <stored decimal> · certain or unsure" and the button "Show on the page"; "Searched. The rules found no value."; "Searched. The rules found a weak candidate that is not written to the record."; "Not searched in this kind of document (<kind>)."; for the addressed body the sentence "The text addresses this body. It is a candidate that is not written to the record."
3. The line that says what a probability of a value is (string key `s4.record.measured`) and the notice `values_measured` follow rule 18.1 point 6, in English and in German.
4. No line shows a fold value. A value of a development document that the number counts has the line "This document is one of the development documents that this number counts."
5. The strings keys `values.prob.fold`, `note.fold_value`, `slot_reason.not_in_this_document_type.author` and `doc_kind.committee` are removed.

### 18.6 Checks

| Check | Command | What it covers in addition to chapter 17.6 |
|---|---|---|
| Worker | `python package/worker/check_values.py` | for each record: the cascade (kind from the rule chain, the selection table of 18.1, kind and rule ids of each value that is not searched), rule D3, rule D4 against the calibration file of the layout, the origin text; 6 synthetic PDF files (new: `response_head.pdf`, rule D2) |
| API | `python package/contract/tools/gate_values.py --port <port>` | 6 synthetic PDF files; the row `cascade`; 22 checks of the view; the validator of the project in its own process must be `m11-validate-3` with C22 passed |
| WebAssembly | `node rdfcheck/tools/check_wasm.mjs <records folder> <doc id>` | the manifest has the cascade with 7 values; no statement for a value that is not searched; no response step if the kind cannot state it; the addressed body is a label only; each value that is read is a label; the probabilities come from all folds |

### 18.7 Examples

`contract/examples/view_26171_values.json` (sample 26171, mode `rules`, kind `proposal`, an addressed body), `view_879163.json` (mode `auto`, kind `response`, rule D2) and `view_unknown_pdf.json` (the synthetic file `head_author.pdf`, kind `proposal`) are views of the instance of `STATE.md` chapter 13. `view_26171.json` is the view of the earlier record form of that step (`head_values.cascade` null).

## 19 Rule V5, the reason `reader_scope`, the signs of a response and the calibration file of round 4 (13.10.2026)

This chapter changes chapter 18. Where they differ, this chapter applies. The findings S3-01 to S3-10 are in `EXAMINATION.md` chapter 14. The project side has the writer `m11-writer-4`, the validator `m11-validate-4` and the reader `m11-values-cascade-3`.

### 19.1 The rules

1. The calibration file of the product is `daten/gj_values/round4/calibration_dev_all.json` of the code layout. This replaces the path of 18.1 point 6 and of 18.2. Origin (text of 14.10.2026, constant `CALIBRATION_ORIGIN` of `src/m11_writer.py` and `ORIGIN` of `worker/values_record.py`): Development documents of 44 parliaments that the rule authors read; the rule files of the reader are made from the PDF alone. The one fixed run of 13.10.2026 used 872 documents of 26 other parliaments. There the share correct (correct / documents with an export value) was 0.2214 for the affair number and 0.2729 for the submission date. Before the run, AI agents had read 116 or more of these documents in earlier work. The text before 14.10.2026 named a last run as future work; that run took place on 13.10.2026 (`STATE.md` chapter 18).
2. Rule V5 (this adds to 18.1 point 1). The kind comes from the rule chain. If the rule chain made no decision (rule id D0), the reader uses 2 facts of the PDF. Fact 1: the type rule reads a type word of a proposal of a member. Fact 2: the responder rule finds a body by a rule tier that is not the tier of an addressed body. The 2 facts give `combined`. Fact 1 gives `proposal`. Fact 2 gives `response`. With no fact, or with the type `draft_decree`, the kind stays `other`.
3. Finding S3-01. A value that the cascade searches has a state of a search. If the rule of the value gives the reason `not_in_document_type`, the manifest slot has the state `not_found_in_pdf` and the reason `reader_scope`. It has no result, no kind and no cascade rule. Only a value that the cascade does not search has the state `not_in_this_document_type`.
4. Finding S3-02. The validator opens the calibration file of the product by its own path below the root. It does not open the path that the manifest names. The worker gives no calibration file to the validator. It stops if the key `calibration_file` of the result does not say `the product file`.
5. The text blocks (this replaces 18.1 point 9). The cascade gives each kind its text slots. A text block of another text slot is not written to the eCH-0295 part. It stays in the provenance file, and the manifest key `cascade.text_blocks_not_written` lists it. The main agent must confirm this rule of the project side.
6. Finding S3-03. For a record of the kind `proposal` or `executive_proposal`, `values_record.response_signs` runs the responder rule one more time on the block file and the rule file. It keeps the rule tiers of the candidates that are not the tier of an addressed body. The record does not change. The worker gives the result to the view function in the optional key `response_signs` of `run_info`.

### 19.2 The worker

1. `worker/values_record.py` version `parlpdfech-values/0.4.0`.
2. `convert.json` key `values` has new keys. `cascade.kind_rule` and `cascade.rule_chain_id` name the rule of the kind. `cascade.v5` is the key `v5` of the kind source, or null. `cascade.searched_out_of_scope` lists the fields with the reason `reader_scope`. `cascade.text_blocks_not_written` is a count. `response_signs` is null, or it holds `responder_tiers` and `text_blocks`.
3. `run_info` of the view function, new optional key `response_signs`: an object with the list `responder_tiers`.

### 19.3 The view (`parlpdfech-site-view/3`, additions)

| Key | Content |
|---|---|
| `head_values.cascade.kind_from` | new value `rule_v5`: rule V5 decided the kind |
| `head_values.cascade.kind_facts` | null if the rule chain made a decision. Else `kind_of_the_rule_chain`, `type_word` (a list value or null), `response_cue` (true or false) and `changed` |
| `head_values.cascade.entries[].state` | new value `reader_scope`: searched, no value, the rule of the value does not read this document |
| `head_values.cascade.texts[].not_written` | the count of text blocks of the family that are in the provenance file only |
| `head_values.response_signs` | null for each kind but `proposal` and `executive_proposal`. Else `responder_candidates` (a count, or null if the worker gave none), `responder_tiers` and `text_blocks` |
| `slots[].reason` | new value `reader_scope` (state `not_found_in_pdf`) |
| `notices[]` | new code `response_signs` with the values `candidates` and `blocks` |

The 3 keys `kind_facts`, `not_written` and `response_signs` are required keys. A consumer that pins the key set of chapter 18.4 must read this chapter. The link checks of `contract/tools/validate_view.py` compare the kind with the 2 facts, the counts of the text blocks and the notice with the signs. They fail a text block in a text slot that the cascade does not give to the kind.

The view function refuses a manifest whose kind source and facts of rule V5 do not agree.

### 19.4 The page

1. The part "What this document can state" has the row "Where the kind comes from". Its text is one of 3: the rule chain decided; rule V5 decided ("the rule chain made no decision; the type word and a response cue of the PDF decide"); the rule chain made no decision and rule V5 changed nothing.
2. For a document with no decision of the rule chain the part shows 3 more rows: fact 1 (found with the type word, or not found), fact 2 (found or not found) and the result of rule V5.
3. An entry with the state `reader_scope` has the text "Searched. The rules found no value: the rule of this entry does not read a document of this form." and the cause for its field (string keys `slot_reason.reader_scope.affair_type`, `.sponsor`, `.response_date`; `slot_reason.reader_scope` for another field).
4. The notice `response_signs` is in the list of notices and below the kind in the cascade part: "The rules found signs of a response in this document; the kind may be wrong." with the 2 counts.
5. The card of the body that a proposal addresses has the heading "Addressed body (not in the record)" (string key `kind.pdf_addressee`).
6. The text slot of a step shows the count of text blocks that are not written. The string key `cascade.texts.kept` is removed, and `cascade.kind.value` is removed.
7. The sentences on the mode "code rules only" (`about.p3`, `unc.no_threshold`) say: the labels of the blocks have no limit; a value that is read from the PDF has its own limit in each mode.

### 19.5 Checks

| Check | Command | What it covers in addition to chapter 18.6 |
|---|---|---|
| Worker | `python package/worker/check_values.py` | for each record: finding S3-01 (each searched value has a state of a search), the text slots against the eCH-0295 file, the signs of a response; 11 synthetic PDF files (new: `petition_head.pdf`, `response_no_author.pdf`, `v5_proposal.pdf`, `v5_response.pdf`, `proposal_signed.pdf`) |
| API | `python package/contract/tools/gate_values.py --port <port>` | 11 synthetic PDF files; the row `new file`; the validator of the project in its own process must be `m11-validate-4`, with no calibration argument, and must say that it used the product file |
| WebAssembly | `node rdfcheck/tools/check_wasm.mjs <records folder> <doc id>` | the example of the head values gives rows only for a record with a value or a text block in its eCH-0295 part |

### 19.6 Examples

The 4 files of `contract/examples/view_*.json` are views of the instances of `STATE.md` chapter 14.

## 20 The limit of rule V5 on the page and the product calibration file of the validator (13.10.2026)

This chapter changes chapter 19. Where they differ, this chapter applies. The findings V4-01 to V4-07 are in `EXAMINATION.md` chapter 15. The project side has the writer `m11-writer-4`, the validator `m11-validate-5` and the reader `m11-values-cascade-3`. The view and its schema are not changed.

### 20.1 The rules

1. The validator opens the product calibration file below the code root. A file at the product path below the root of the caller is used only if the code root has none. If the two files have different SHA-256 values, check C16 fails. In the package the code root and the root are the same folder (`build/layout`).
2. Check C22 of the validator has the key `information`: a list of lines that are no problems. The package does not show them.

### 20.2 The page

1. A record with `head_values.cascade.kind_from` `rule_v5` and the kind `response` shows one more paragraph in the cascade part (string key `cascade.kind.v5.response_limit`). It says that the response cue can be a signature of the executive, the head of minutes or a decision of the executive. It gives 2 numbers of the development documents (40 documents, 22 of them with the type `draft_decree` in the export). The numbers are fixed text of round 4.
2. A record with `kind_from` `rule_v5` shows one more sentence in the card of the document label (string key `unc.doclabel.v5`, with the name of the kind).
3. The German text of `slot_reason.reader_scope.response_date` is: "Die Regeln haben diesen Eintrag gesucht. Für die Regelkette ist dieses Dokument keine Antwort, und die Labels der Blöcke ergeben keinen Text einer Antwort. Die Datumsregel liest dann kein Datum einer Antwort."

### 20.3 Checks

`python package/contract/tools/gate_values.py --port <port>`: the validator of the project in its own process must be `m11-validate-5`. The other checks are those of chapter 19.5.

## 21 Rule V5 made narrower, the key `response_sign` and the rule files of the samples (13.10.2026)

This chapter changes the chapters 19 and 20. Where they differ, this chapter applies. The project side has the writer `m11-writer-4`, the validator `m11-validate-5` and the reader `m11-values-cascade-4`. `STATE.md` chapter 16 has what was run.

### 21.1 The rules

1. Rule V5 of the reader. A document with the rule id `D0` gets the kind response only if the responder rule gives the tier `rsp_response_cue`: a heading or a phrase of the first lines says that the executive answers. A type word with each responder tier but `rsp_addressee_cue` and `rsp_response_text` gives the kind combined. A type word alone gives the kind proposal. Each other case changes nothing.
2. The product calibration file is `daten/gj_values/round4/calibration_dev_all.json` of round 4 with reader version 4 (SHA-256 `e48e7a8d8efdd1e10b68071df85275dc0c5b69e004bb8051b2aecd2a1d4229d7`). The layout holds a byte-equal copy.
3. The rule file of a sample (`data/samples/<doc>/rules.json`) is the file that is made from the PDF alone (`daten/gj/rules_pdf/<doc>.json` of the project). It names no export record. The worker puts it at the path `daten/gj/rules/<doc>.json` of its scratch root, as before.

### 21.2 The view

`head_values.cascade.kind_facts` (an object, or null if the rule chain made a decision) has 5 required keys.

| Key | Value |
|---|---|
| `kind_of_the_rule_chain` | the kind before rule V5 |
| `type_word` | the list value of the type word, or null |
| `response_cue` | true only if the responder tier is `rsp_response_cue` |
| `response_sign` | NEW. true if the responder tier is another tier that is not `rsp_addressee_cue` and not `rsp_response_text` (for example a signature of the executive) |
| `changed` | true if rule V5 gave another kind |

Not more than one of `response_cue` and `response_sign` is true. The link check of `contract/tools/validate_view.py` makes the kind again from these keys. The schema name stays `parlpdfech-site-view/3`.

### 21.3 The page

1. Chapter 20.2 item 1 does not apply: the paragraph of the limit and the string `cascade.kind.v5.response_limit` are removed.
2. The row of fact 2 has 3 texts: found (`response_cue`), another sign of the executive (`response_sign`, string `cascade.kind.fact.response.sign`), not found.
3. The row of the result has one more text for a document with a sign and no type word (string `cascade.kind.fact.result.sign`): the kind stays.

### 21.4 `sample.json`

The entry of `rules.json` in the list `files` has 3 more keys: `source_path` (the project file that was copied), `no_export_record` (true) and `keys_that_differ_from_the_stored_rule_file`. `project_path` stays the path in the scratch root. The key `run_record.path` names `daten/gj_values/round4/rules_pdf_build.json`. An entry with no key `source_path` was copied from its `project_path`.

### 21.5 Checks

`python package/contract/tools/gate_values.py --port <port>` converts the 3 samples in 2 modes and 13 synthetic PDF files (19 jobs). New files: `v5_signature.pdf` (the kind must stay other document, with no response step and no responding body) and `v5_combined.pdf`. `v5_response.pdf` must have `response_cue` true. `python package/worker/check_values.py` has the same 13 files.

## 22 The response cue of rule V5 on the page and the file `v5_report.pdf` (13.10.2026)

This chapter changes chapter 21. Where they differ, this chapter applies. The reader, the writer, the validator and the view did not change. `STATE.md` chapter 17 has what was run.

### 22.1 The rule as it is

1. Chapter 21.1 item 1 says too little about the tier `rsp_response_cue`. The pattern of this tier names the executive with a word for an answer, a statement or a report. It also takes a verb such as answers or submits.
2. Such a phrase is also printed in a report or a proposal of the executive that answers no proposal. Then the kind response by rule V5 is wrong, and the record states a response step that the PDF does not state.
3. Rule V5 does not divide the text. For the kind combined by rule V5 each text block is submitted text, also the answer of the executive.

### 22.2 The page

1. The strings `cascade.kind.fact.response` and `cascade.kind.fact.result.changed` state item 1 and item 2 of 22.1.
2. New string `cascade.texts.v5_roles` (with the form `.one`): one sentence below the text entry of the submission step. It shows if the kind is combined by rule V5 and the entry has 1 text block or more.
3. New string `unc.card.v5_unsure`: one sentence in the card of the responding body or of the response date. It shows if the kind is from rule V5, the word is «unsure» and the probability is at the limit of the calibration or above.
4. The view did not change. The page reads the keys `head_values.cascade.kind_from`, `kind`, `texts[]` and `calibrations[].certain_threshold`.

### 22.3 Checks

`python package/contract/tools/gate_values.py --port <port>` converts the 3 samples in 2 modes and 14 synthetic PDF files (20 jobs). New file: `v5_report.pdf`, a report of the executive with the line "Bericht des Stadtrates" and no type word. Its row states a known limit: the kind is response by rule V5, `response_cue` is true and the record has 1 response step. A later reader must give the kind other document; the row must change then. `python package/worker/check_values.py` has the same 14 files.

## 23 The start page, the result view and the record files for it (14.10.2026)

This chapter adds to the chapters 3, 5.2, 6 and 7. Where they differ, this chapter applies.

### 23.1 The record files

1. A record with values from the PDF (`values_record.state` `pdf`) has 3 more kinds of file in its folder: `<doc>.values.ttl` (text/turtle; charset=utf-8), `source.pdf` (application/pdf) and `page-<n>.png` (image/png; `n` from 1 to 999 with no leading zero). A record of the earlier form (`PARLPDFECH_VALUES=off`) has none of them.
2. `<doc>.values.ttl` is a converter file: `src/m11_writer.py` (`m11-writer-6` since the correction of 14.10.2026; function `values_graph`) writes it in `rdf_step`. The manifest has it in `outputs.values_ttl` and the facts in `rdf.values_ttl` (`form`, `namespace`, `triples`, `readings`). The form `parlpdfech-values-ttl/2` has one node `<record IRI>` of the class `pvl:ValueSet`. It has `pvl:document`, `pvl:form` and one `pvl:reading` for each value node. A label of the kind `pdf_value` with a path of the record gives one node `<record IRI>/value/<field>` of the class `pvl:ValueReading`. Its properties: `pvl:field`, `pvl:resource` (`label_subject`) and `pvl:property` (`label_predicate`): the pair is the subject and the predicate of a statement of `<doc>.ech.ttl`; `pvl:entity` (`about_entity`, only if it is another resource: the actor whose `aff:name` holds the value of a sponsor or of a responder), `pvl:value` (`label_object`), `pvl:printed` (`value_wording`). Also: `pvl:probability` (xsd:decimal, `label_probability`), `pvl:status`, `pvl:tier`, `pvl:page`, `pvl:lastPage` (only for another page), `pvl:charStart`, `pvl:charEnd`, `pvl:label` and `pvl:calibration`. Prefix `pvl:` = `https://schema.parlpdfech.example/values/`. A weak candidate and an addressed body have no node. Form 1 (`m11-writer-5`, 14.10.2026, superseded) gave `about_entity` as `pvl:resource`; for a sponsor and a responder that pair was no statement of the eCH-0295 record (finding F1). The 4 comment lines at the top of the file say what the properties mean and that the domain of `pvl:` is a placeholder.
3. If the manifest names the file, the validator (`m11-validate-7`) parses it in check C2. Check C3 compares it with the label file and checks that each pair resource and property is a statement of `<doc>.ech.ttl` (key `values_ttl_equals_label_file`). No new check id.
4. `source.pdf` and `page-<n>.png`: for a sample the worker copies them from `data/samples/<doc>/` (made by `worker/make_samples.py` with pypdfium2, scale 2, entries with the roles `source_pdf` and `page_image` in `sample.json`). For an own PDF it copies the PDF of the job and makes the images with pypdfium2 (scale 2, at most `PARLPDFECH_MAX_PAGES` pages). A failure of the renderer gives no image and no failure of the record. `convert.json` has the new key `page_images` (`state` `images`, `no_renderer` or `renderer_error`, `renderer`, `made`). The key `files` of `convert.json` lists the new files.
5. The server (`server/src/ids.rs`): `file_media_type` and `file_rank` know the 3 kinds; `is_complete_record` accepts the 11 files and these files only. `bundle.zip` holds them, after `convert.json`, and `SHA256SUMS` has a line for each. The Host and Origin rules of the file route do not change.
6. Superseded: the sentence of chapter 7.3 "the package holds no PDF of a sample". The worker still reads the stored pages and lines of a sample; the PDF is for the page image and the download only.

### 23.2 The view

`files[]` has the roles `values_ttl`, `source_pdf` and `page_image` for these files. `pages[]` has the optional key `image` (the address of the image below `/api/records/<id>/files/`); only a page with an image has it. The schema name stays `parlpdfech-site-view/3`; the schema file was made again with `contract/tools/make_schema.py`. The 4 example views are valid with no change.

### 23.3 The page

| Route | Screen |
|---|---|
| `/app/#/` | the new start: one sentence, the flow, the 3 sample cards, the box "How often correct?", the own PDF, the links "more" |
| `/app/#/about`, `/app/#/about/<part>` | the long texts: `method`, `numbers`, `limits`, `technical` |
| `/app/#/view/<record_id>` | the result view: the PDF, the values with their probability, the RDF (chapter "Corrections of 14.10.2026" of `ui/README.md`) |
| `/app/#/record/<record_id>` | the technical view (the earlier S4, no part removed) |

The numbers of the fixed run come from `ui/run_numbers.json` (chapter 7.1 of `ui/README.md`). The page loads no file from another host.
