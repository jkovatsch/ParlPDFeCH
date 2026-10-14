# parlpdfech-server

The web server of the ParlPDFeCH package. Status of all results of the package: EXCEPTION, NOT RELEASED.

The server gives the pages, the API and the files of a record. It starts one worker process for each conversion. It converts nothing itself. It opens no connection to another host. The reference for each interface is `../CONTRACT.md` (chapters 2 to 5).

## Build and test

All commands run from the folder `package/`, with no network.

```
cargo build --offline --locked --release -p parlpdfech-server
cargo test --offline --locked -p parlpdfech-server
cargo clippy --offline -p parlpdfech-server --all-targets -- -D warnings
```

The binary is `<target>/release/parlpdfech-server`. The tests need `python3` on the `PATH` (standard library only) for the fake worker. The tests open no port.

## Configuration

The server reads these environment variables at its start. An invalid value stops the start with the exit code 2.

| Variable | Default | Meaning |
|---|---|---|
| `PARLPDFECH_PROFILE` | `native` | `slim`, `full` or `native` |
| `PARLPDFECH_BIND` | `127.0.0.1:8080` | listen address |
| `PARLPDFECH_UI_DIR` | `ui` | folder that `/app/` serves |
| `PARLPDFECH_DATA_DIR` | `data` | holds `samples/index.json` |
| `PARLPDFECH_WORK_DIR` | `work` | holds `records/` and `jobs/`; must be writable |
| `PARLPDFECH_WORKER_CMD` | `["python3","worker/serve_convert.py"]` | JSON array of strings |
| `PARLPDFECH_WORKER_CWD` | not set | working folder of the worker |
| `PARLPDFECH_SITE_DIR` | not set | a folder with a built static site, given below `/` (CONTRACT.md chapter 15); a folder with no `index.html` is dropped with a warning |
| `PARLPDFECH_MAX_BYTES` | `20971520` | largest PDF |
| `PARLPDFECH_MAX_PAGES` | `25` | passed to the worker and shown by `/api/health` |
| `PARLPDFECH_JOB_TIMEOUT` | `600` | seconds for one worker process |
| `PARLPDFECH_COMMIT` | `unknown` | text for `/api/health` |
| `PARLPDFECH_READONLY` | not set (off) | `1` = a public site: no PDF file is taken and each `DELETE` is refused with the code `read_only` (CONTRACT.md chapter 14) |
| `PARLPDFECH_SAMPLE_RUNS` | `on` | `off` = no run for a sample whose record is in the work folder (code `sample_runs_off`) |
| `PARLPDFECH_HOSTED` | not set (off) | `1` = the server is not on the computer of the reader: `/api/health` says `hosted: true` and the page uses its texts for a hosted site (CONTRACT.md chapter 15) |

At its start the server makes `records/` and `jobs/` and deletes what an earlier process left in `jobs/`.

## Addresses

| Method and address | Answer |
|---|---|
| `GET /healthz` | 200, `text/plain`, body `ok` |
| `GET /api/health` | version, profile, modes (also `read_only` and `sample_runs`), limits, `busy`, `job_id`, `wasm`, `site`, `hosted` |
| `GET /api/samples` | the content of `samples/index.json`; each sample gets `ready: {auto, rules}` |
| `POST /api/jobs` | starts a job; 202 with `job_id`, `state`, `events`, `status` |
| `GET /api/jobs/{id}` | the job object |
| `GET /api/jobs/{id}/events` | `text/event-stream` |
| `DELETE /api/jobs/{id}` | stops a running job; 200 with the job object |
| `GET /api/records/{record_id}` | the bytes of `view.json` |
| `GET /api/records/{record_id}/files/{name}` | the bytes of one file, not changed; `?download=1` adds `Content-Disposition` |
| `GET /api/records/{record_id}/bundle.zip` | the files of the record and `SHA256SUMS` |
| `DELETE /api/records/{record_id}` | deletes the record folder; 204 |
| `GET /app/...` | files of `PARLPDFECH_UI_DIR`; `/app` gives 308 to `/app/` |
| `GET /...` | files of `PARLPDFECH_SITE_DIR` (a folder address gives its `index.html`; a path with no file gives `404.html` of the site with the status 404); with no site, `/` gives 307 to `/app/` |

### POST /api/jobs

Two body forms:

- `multipart/form-data` with the fields `file` (one PDF) or `sample` (a document number), `doc_id` (optional, with `file` only) and `mode` (`auto` or `rules`; default `auto`).
- `application/json` for a sample: `{"sample": "26171", "mode": "auto"}`.

Checks before the worker starts, in this sequence:

1. A job runs: 409 `busy` with `detail.job_id`.
2. The declared length is above `max_bytes` plus 64 KB: 413 `too_large`.
3. While the body streams: more than `max_bytes` in the field `file` gives 413 `too_large`. The mark `%PDF-` is not in the first 1024 bytes: 415 `not_pdf`. The other fields together have a limit of 64 KB.
4. The server writes the bytes to `jobs/<job id>/input.pdf` and calculates the SHA-256 while they arrive. The name on the disk is fixed. The name that the client sent is for display only (no path, no control character, 120 characters).
5. Field checks: 400 `bad_request` with `detail.field`; 404 `sample_unknown`.

A request that does not become a job leaves no file.

### The worker

The server adds these arguments to `PARLPDFECH_WORKER_CMD`:

```
--sample <doc id> --mode auto|rules --out <WORK_DIR>/jobs/<job id>/out --data-dir <DATA_DIR>
--pdf <WORK_DIR>/jobs/<job id>/input.pdf [--doc-id N] --mode auto|rules --out ... --data-dir ...
```

It adds `PARLPDFECH_PROFILE`, `PARLPDFECH_MAX_PAGES`, `PARLPDFECH_DATA_DIR` (absolute path) and `PYTHONUNBUFFERED=1` to the environment of the worker.

- The worker runs in its own process group.
- Each line of standard output that is a stage line of the protocol becomes one event `stage`. The data of the event is the line, not changed.
- A line that is not a JSON object of the protocol (not JSON, an unknown event, an unknown stage id or state, a line above 1 MiB) goes to no client. The log gets the number of such lines.
- Standard error goes to the log of the server only.
- Exit code 0 or 2 with the last line `done`: the server moves `out/` to `records/<record id>/` (rename of the full folder) and sets `valid`. The record id of the worker must be the id that the server calculated. The folder must hold `view.json`. An entry that is not one of the 11 record file names is deleted before the move.
- Exit code 3 or 4 with the last line `failed`: the job gets the error of the worker. Only short scalar values of `detail` pass (letters, digits and `_ . : -`).
- Each other end: `converter_stopped` with `detail.note` = `exit_<code>`, `exit_signal`, `protocol`, `record_id`, `no_view`, `no_output`, `record_move`, `spawn` or `wait`.
- Timeout: the signal TERM to the process group, the signal KILL after 3 s, then `failed` with `timeout`.
- `DELETE /api/jobs/{id}` and the stop of the server use the same stop sequence. The job gets the state `stopped`.
- The server deletes `jobs/<job id>/` at the end of each job.

### Events

`event: stage`, then one of `event: done`, `event: failed`, `event: stopped` (data = the job object). A client that connects late gets each earlier event again. A comment line `: ping` comes after each 15 s with no event. The server closes the stream after the last event.

### Path safety

- A record id must match `^(s-[0-9]{1,12}|u-[0-9a-f]{16})(-rules)?$`. Each other value gives 404 `record_unknown` before a file access.
- A file name must be one of the 11 names of CONTRACT.md chapter 3 (prefix: a document number or `local`). Each other value gives 404 `file_unknown` before a file access.
- A job id must be a UUID in lower case.
- A value that fails a pattern is not copied into the answer.
- Static files: `tower-http` `ServeDir` refuses each path that leaves the folder.

### Headers

Each answer has `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy: same-origin` and `Permissions-Policy: camera=(), microphone=(), geolocation=()`.

- Below `/api/` and for `/healthz`: `Cache-Control: no-store`.
- Below `/app/`: the `Content-Security-Policy` of the app (CONTRACT.md chapter 5.4) and `Cache-Control: no-cache`. Each other page address (the static site): the policy of the site (no WebAssembly, no font, no form) and `Cache-Control: no-cache`.
- A static file whose name holds a content hash (8 or more hex digits between two separators, for example `app.0123abcd.js`) gets `Cache-Control: public, max-age=31536000, immutable`. The UI of this stage has no such file.
- A static text file gets `charset=utf-8` in its media type.

The server sets no cookie. Each answer with a status of 400 or more below `/api/` is the error object of CONTRACT.md chapter 5.1. The texts come from `../contract/errors.json`, which the build includes. No answer holds a stack trace, a local path or a line of standard error.

## Limits

| Limit | Value |
|---|---|
| Jobs at one time | 1 |
| Jobs kept in memory | 20 |
| PDF size | `PARLPDFECH_MAX_BYTES` (default 20 MB) |
| Upload body | `max_bytes` plus 64 KB |
| Each other request body (declared length) | 64 KB |
| One line of the worker | 1 MiB |
| Run time of the worker | `PARLPDFECH_JOB_TIMEOUT` (default 600 s) |
| Time between TERM and KILL | 3 s |
| Time for the stop of the server | at most 10 s after the signal |

## Stop

The signals TERM and INT stop the server: the worker stops first, then the server closes its connections and exits with the code 0.

## Log

One line for each request and for each step of a job, on standard error, with `key=value` fields: `method`, `path`, `status`, `ms`, `job_id`, `record_id`, `exit_code`.

## What is measured

Measured on the build host (macOS, arm64, cargo 1.97.1), 13.10.2026:

- Release build with no network: passed; 35.5 s for the first build with all dependencies; binary 2.9 MB (2,876,832 bytes, stripped).
- `cargo test`: 12 unit tests and 22 integration tests passed. The integration tests use the fake worker `tests/fake_worker.py` with the cases valid, not valid, refused, internal stop, crash, hang (timeout; also a worker that ignores TERM), garbage on standard output, a wrong record id, an absent view and an extra file.
- `cargo clippy ... -D warnings`: no finding. The crate forbids `unsafe` code.
- A trial with `curl` on port 8895 with the fake worker and the fixture index `tests/fixtures/data/samples/index.json`: health, samples, a sample job with the event stream, `busy`, the files, the archive (12 entries; `shasum -c SHA256SUMS` passed for the 11 files), an upload of a synthetic PDF (`not_in_package` from the fake worker), `too_large`, `not_pdf`, 8 path traversal requests (all 404), the stop of a running job, the deletion of a record, and the stop with the signal TERM during a job (exit code 0, no worker process left).

Not measured:

- No run with the real worker `worker/serve_convert.py`. All job results above come from the fake worker.
- No run on Linux and no run in a container.
- No run in a browser.
- No load test. No test with two uploads at the same instant.
