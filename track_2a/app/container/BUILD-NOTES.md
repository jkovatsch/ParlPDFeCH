# Build notes of the container part

State of the container files on 13.10.2026: written and read. No image was built. No container was started. Each mark in this file is one of: measured, read, estimate.

Later state (15.10.2026). On 14.10.2026 a private build pipeline on Linux built the image of the target `slim` from the source tree of the package; nobody started that image. On the same day, `make run` built an image of the target `slim` on one Mac and started the container. It used the copy of the source tree in a clone of GitHub at commit `10e07b4`. The 3 samples in the 2 modes gave 6 valid records. The target `full` and `make check-offline` were not run.

## 1 What was run and what was not

Run on the build host (no network, no Docker daemon):

| Step | Result |
|---|---|
| `make -n` for the targets `run`, `run-full`, `check-offline`, `run-native`, `test` | The command lists print with no make error (GNU Make 3.81). |
| `docker compose config` (the client reads the file; it needs no daemon) | The file is accepted. The output shows the target `slim`, the port `127.0.0.1:8080`, `read_only`, the two tmpfs lines, `cap_drop ALL`, `no-new-privileges`, the user `10001:10001` and the context `converter`. |
| `container/seed_records.py` with a stand-in worker (a test script, not the worker of the package) | 3 cases passed: one sample with `--limit 1`; all samples and modes; a worker that ends with exit code 4 gives exit code 1 and leaves no half record. |
| `container/entrypoint.py` with a stand-in server | 2 cases passed: the seed records are copied and the server command starts; with no seed folder the server command starts. |
| Calculation of the two requirements files | See chapter 4. |

Not run:

- `docker build`, for each target and each architecture.
- `docker compose up`, the health check, `make run`, `make run-full`, `make check-offline`, `make stop`, `make remove`.
- `make run-native` and `make test` were not run by the container part. Later steps ran them with no container on one Mac (`../STATE.md`).
- An install of a requirements file on Linux.

## 2 Structure of the Dockerfile

| Stage | Base | Content |
|---|---|---|
| `rust-base` | `rust:1-bookworm` | target `wasm32-unknown-unknown`, the two crates, `cargo fetch --locked` |
| `server-build` | `rust-base` | `cargo build --release --locked -p parlpdfech-server` |
| `wasm-tools` | `rust:1-bookworm` | `cargo install --locked wasm-bindgen-cli --version 0.2.127` |
| `wasm-build` | `rust-base` | version check against `Cargo.lock`, the WebAssembly build, `wasm-bindgen --target web` |
| `py-slim` | `python:3.12-slim-bookworm` | all environment variables, user 10001, `requirements-slim.txt`, `pip check`, HEALTHCHECK, CMD |
| `py-full` | `py-slim` | 3 Debian packages, torch and torchvision from the CPU index, `requirements-full.txt`, the Docling models |
| `layout` | `py-slim` | `worker/layout.py --check` on the named context `layout` (the folder `build/layout`, made on the build host by `make layout`). Changed by the integration step; not run. |
| `appfiles` | `scratch` | all files of `/app` |
| `full` | `py-full` | `/app`, the sample records (`RUN --network=none`) |
| `slim` (default) | `py-slim` | `/app`, the sample records (`RUN --network=none`) |

Decisions of this part:

- wasm-opt is not run. Read on packages.debian.org: Debian 12 has binaryen 108. It is not known if this version reads the output of the present Rust compiler.
- The file has no `# syntax=` line. Thus the build pulls no frontend image. The file needs BuildKit (named context, `RUN --network=none`), which is the default of Docker Engine 23 and later.
- `rust-toolchain.toml` is not copied into the image. With it, rustup downloads a second toolchain. Thus the Rust version of the image is the version of the tag `rust:1-bookworm` at build time, not the version of the build host (measured there: 1.97.1).
- The work folder `/work` is a memory file system; it is empty at each start. The image build makes the records of the samples (`container/seed_records.py`) and keeps them in `/app/seed/records`. The start command (`container/entrypoint.py`) copies them to `/work/records` and then becomes the server. `PARLPDFECH_SEED_DIR` is a variable of this part; the contract does not have it.
- The sample step of the build is a check: the build stops if one sample does not convert to a valid record in the image, with no network.
- `HOME` and `XDG_CACHE_HOME` point into `/tmp`, because the root file system is read-only.

## 3 Downloads at build time

Sizes are estimates if not said differently. None was measured in a build.

### 3.1 Target slim (`make run`)

| Id of the plan | What | Source | Size |
|---|---|---|---|
| D-1 | image `rust:1-bookworm` | Docker Hub | estimate 0.5 GB compressed |
| D-2 | image `python:3.12-slim-bookworm` | Docker Hub | estimate 30 to 50 MB compressed |
| new | Rust standard library for `wasm32-unknown-unknown` (`rustup target add`) | static.rust-lang.org | estimate 20 to 40 MB |
| D-7 | the crates of `Cargo.lock` (163 package entries, read) | crates.io | estimate 30 to 80 MB |
| new | `wasm-bindgen-cli` 0.2.127 and its dependencies (`cargo install --locked`) | crates.io | estimate 20 to 60 MB |
| D-4 | 87 Python packages of `requirements-slim.txt` | pypi.org | estimate 100 to 200 MB |

No Debian package is installed in the target `slim`. Thus D-3 is not a download of this target.

D-8 (the 2 eCH-0295 schema files) is not a download of this Dockerfile. They are in the code layout (`build/layout/quellen/`).

The plan named a way with no crate download (`cargo vendor`). This Dockerfile does not use it.

### 3.2 Target full (`make run-full`) in addition

| Id of the plan | What | Source | Size |
|---|---|---|---|
| D-3 | Debian packages `poppler-utils`, `libgl1`, `libglib2.0-0` and their dependencies | deb.debian.org | estimate less than 100 MB |
| D-5 | `torch` 2.14.1 and `torchvision` 0.29.1, CPU build | download.pytorch.org/whl/cpu | estimate 0.2 to 0.3 GB |
| D-5 | 71 more Python packages of `requirements-full.txt` | pypi.org | estimate 0.3 GB |
| D-6 | Docling layout model and table model (`docling-tools models download`) | huggingface.co | 506 MB (measured in a local cache: 164 MB and 342 MB) |

### 3.3 Not downloaded

No weights of Apertus. No CUDA package: 19 packages of the lock file (`nvidia-*`, `cuda-*`, `triton`) are not in the requirements files. No OCR model. No onnxruntime.

## 4 The requirements files

- `requirements-slim.txt`: 87 lines. Method: the dependency closure of `linkml`, `rdflib`, `pyyaml`, `numpy` and `scipy`, calculated from the `Requires-Dist` data of the installed packages of the project environment with `--with linkml==1.11.1`, with the markers evaluated for Linux, Python 3.12; the list is the union for x86_64 and aarch64. Versions: numpy 2.5.3, scipy 1.18.1 and pyyaml 6.0.3 are equal to `uv.lock` (read). linkml 1.11.1 and rdflib 7.6.0 are not in `uv.lock`; their versions come from the environment.
- `requirements-full.txt`: 73 lines plus the include of the slim file. Method: the dependency closure of `docling`, `torch` and `torchvision` in `uv.lock`, markers evaluated in the same way (x86_64 and aarch64 gave the same list), without the extra `ocrmac`, minus the 19 CUDA packages, minus the lines of the slim file. No package has two different versions in the two files (checked by the script).
- scipy: read in the converter code: `scipy` is imported inside two fit functions of the calibration module only. The trace of the worker was not available. scipy stays in the slim file until the trace shows that no step calls these functions.
- The linkml closure holds packages that the converter does not import (for example sphinx, pytest, sqlalchemy). They are requirements of linkml 1.11.1.

## 5 Assumptions about the other parts

The folders `worker/` and `data/` did not exist when these files were written. The files assume:

1. (Not true; changed by the integration step: the script is `worker/layout.py`, it reads files of `src/`, `daten/`, `quellen/` and `crisp-dm/`, and it runs on the build host. The image only checks the copies.) `python package/worker/build_layout.py`, started in the project folder with no option, reads the converter modules from `<project>/src`, writes `<project>/package/build/layout`, checks the SHA-256 of each copy and ends with an exit code that is not 0 if a check fails. The Dockerfile mirrors these paths below `/project`.
2. `python package/worker/make_samples.py`, started in the project folder with no option, writes `package/data/`.
3. `data/` (samples) is in the build context. `data/layout/` and `data/SOURCES.json` do not exist; the shared files are in the code layout. The image does not make it.
4. The worker reads `PARLPDFECH_CODE_DIR`, `PARLPDFECH_VIEW_DIR` and `PARLPDFECH_DATA_DIR` and writes only below `--out` and the temporary folder.
5. `data/samples/index.json` has the keys `samples[].doc_id`, `record_id` and `modes` (form of `contract/examples/samples.json`).

If one assumption is false, the integration step must change the lines that the Dockerfile and the Makefile mark with the script names.

## 6 Open risks

1. No build was run. A syntax error or a wrong path in the Dockerfile is possible.
2. The build context. The converter modules are outside the package folder. The build gets byte-equal copies through the named context `layout` (default `build/layout`, made by `make layout` in the project environment). A clean checkout that holds only the package folder cannot build. The place of the converter modules in a public repository is not decided.
3. Read in the contract: 4 converter files hold a name or a home path. The image holds byte-equal copies of the converter modules in `/app/code`. A public image thus holds these texts.
4. `COPY ui/ /app/ui/` copies each file of `ui/`, also the folders `ui/fixtures` and `ui/tools` that exist now. The server serves the folder below `/app/`.
5. `pip check` can stop the build if a Linux wheel has a requirement that the calculation did not see. A Linux wheel can be absent for one of the pinned versions and one of the two architectures; then pip compiles from source or stops.
6. The requirements files have no hash values. A package index could give other bytes for the same version.
7. The tag `rust:1-bookworm` moves. A new Rust version can give a compile error or a larger WebAssembly file. The two base images are not pinned by digest.
8. Architecture: nothing in the files names an architecture. Not one of the two architectures was built.
9. The health check and `docker compose up --wait` are not examined. `--wait` needs Compose 2.1.1 or later, `additional_contexts` needs 2.17 or later.
10. Read-only root: it is not known if a Python package of the worker writes outside `/tmp` and `/work`. The sample step of the build runs with a writable file system; only `make check-offline` runs the worker with `--read-only`.
11. Linux was never a platform of the converter (read in the plan). The sample step of the build is the first Linux run of the worker.
12. Target `full`: not examined in any way. `opencv-python` needs system libraries; `libgl1` and `libglib2.0-0` are an estimate of the list. `rapidocr` is a dependency of docling; with torch present, Docling can select it as an OCR engine (read in the plan, chapter 5). The worker of stage P0b must set the OCR option to off. The command `docling-tools models download` and its model names were not run.
13. Memory: no limit is set, and no memory value was measured in a container.
14. Build time and image size are estimates. A long build can stop a juror before the first page.
15. `make run` prints the output of the build and then one line with the address. The address line is the last line.

## 7 Target `full` against the fresh branch of the worker (stage P0b)

State: read and compared on 13.10.2026. No image was built and no container was started. The fresh branch (`worker/fresh.py`, `worker/pdf_only.py`) ran on macOS only (profile `native`).

### 7.1 What the fresh branch needs in the image

| Need of the branch | State of the Dockerfile target `full` (read) |
|---|---|
| `PARLPDFECH_PROFILE=full` in the environment of the server (the server gives it to the worker) | `ENV PARLPDFECH_PROFILE=full` in the final stage `full` (read). With the value `slim` the worker refuses each PDF that is not a sample. |
| `DOCLING_ARTIFACTS_PATH` names a folder with the layout model and the table model | `ENV DOCLING_ARTIFACTS_PATH=/app/docling-models`, filled by `docling-tools models download ... layout tableformer`. Read in docling 2.133.0: the pipeline takes the path from the setting `DOCLING_ARTIFACTS_PATH` and stops if the folder is not valid. Not run. The branch stops with the note `docling_models` if the variable has no value. |
| `HF_HUB_OFFLINE=1` | set in `py-slim`; the branch also sets it if it has no value |
| the command `pdftotext` | `poppler-utils`; the branch takes the command from the search path, else `/usr/bin/pdftotext` |
| the code layout with the files of mode 3 (45 files) in `/app/code` | `COPY --from=layout`; the build host must run `make layout` with the list of this stage (72 files) |
| `worker/fresh_tables.json`, `worker/fresh.py`, `worker/pdf_only.py`, `worker/states_provider.py` in `/app/worker` | `COPY worker/ /app/worker/` |
| a writable folder for the scratch root (the parent of `--out`, below `/work`) | `/work` and `/tmp` are memory file systems of 256 MB each (`compose.yaml` and `Makefile`, read). One run writes the copies of 45 code files (2.0 MB), the PDF, the Docling output and the record. Not measured in a container. |
| memory | measured on macOS: peak 1.2 to 1.3 GB for a PDF of 1 page (Docling with 2 models on MPS). No limit is set in the files; the value on a Linux CPU is not measured. |

### 7.2 Imports of the fresh branch against the requirements files

Measured with one traced fresh run on macOS (the modules that the process loaded, mapped to distributions): 108 distributions.

| Group | Count | In a requirements file |
|---|---|---|
| in `requirements-slim.txt`, same version | 55 | yes |
| in `requirements-full.txt` only, same version | 44 | yes |
| `ocrmac`, `pyobjc-core`, `pyobjc-framework-cocoa`, `pyobjc-framework-coreml`, `pyobjc-framework-quartz`, `pyobjc-framework-vision` | 6 | no, by design: Apple OCR exists on macOS only |
| `mlx`, `mlx-metal` | 2 | no: packages for Apple silicon. Which package loads them in the run was not examined. |
| `sentencepiece` | 1 | no. It was loaded on macOS. It is not known if the import is optional on Linux. |

Direct imports of the new code and of the converter files of mode 3, and their place:

| Import | Used by | Requirements file |
|---|---|---|
| `pypdfium2` | `fresh.pdf_check` (page count, password, text layer) | full (`pypdfium2==5.14.0`) |
| `docling` (`document_converter`, `datamodel`, `backend.pypdfium2_backend`) | `m03_docling_zerlegen` | full (`docling==2.133.0` and its parts) |
| `torch` | `m03_docling_zerlegen.mps_speicher` (inside a try block), Docling | full (`torch==2.14.1`, CPU index) |
| `ocrmac` | `m03_docling_zerlegen.baue_konverter` (inside a try block; not reached with `--ocr aus`) | none, by design |
| `yaml`, `rdflib`, `linkml`, `linkml_runtime`, `numpy`, `scipy` | rule chain, floor decisions, `pdf_only.py` | slim |
| the commands `pdftotext -layout` and `pdftotext -bbox -cropbox` | `m03_docling_zerlegen`, `m03_atome` | Debian package `poppler-utils` |

The traced run also started the commands `uname` and `file` (2 of 6 subprocesses; the 4 others are pdftotext). Which package starts them was not examined. `python:3.12-slim-bookworm` has `uname`; it is not known if it has `file`.

### 7.3 What differs from the measured conversion in the target `full`

Read in the code and, for the first two rows, measured on macOS with `PARLPDFECH_FRESH_OCR=none` and `PARLPDFECH_FRESH_DEVICE=cpu`:

1. No OCR (`--ocr aus`). Measured on macOS for the 3 sample PDF files: 1 of 3 block files is equal to the stored block file (26171: 13 of 13 blocks; 879163: 4 of 24; 714840: 6 of 8). The stored text of 879163 is all from OCR, and 1 block of 714840 is from OCR.
2. Device `cpu` in place of MPS. Measured on macOS: for 26171 (no OCR in the stored output) the blocks, the lines and the labels are equal with the device `cpu`.
3. Poppler of Debian 12 (read in the plan: 22.12) in place of 26.04. `m03_atome` takes the word frames of the lines from `pdftotext -bbox`. Not measured.
4. torch from the CPU index for Linux in place of the macOS build. Not measured.
5. `rapidocr` is installed as a dependency of docling. With `--ocr aus` Docling builds no OCR model (read: `do_ocr` is false). Not run.

### 7.4 What the first Linux trial must measure

In this sequence. Each point gives a number for the README, also if it is low.

1. The build of the target `full` ends: `pip check` passes for the two architectures that are built; the size of the image; the build time.
2. `docling-tools models download --output-dir /app/docling-models layout tableformer` gives a folder that Docling accepts through `DOCLING_ARTIFACTS_PATH` with `HF_HUB_OFFLINE=1` and `--network none` (the first conversion reads the 2 models and opens no connection).
3. `PARLPDFECH_PROFILE` is `full` in the worker (`convert.json` key `profile`), and `/api/health` gives `modes.upload` true and `ocr` `none`.
4. `python /app/worker/serve_convert.py --pdf <a PDF> --mode auto --out /work/x/out` with a PDF that has a text layer: the last line is `done`; `convert.json` key `fresh.docling.settings_equal_to_stored` shows only `ocr`, `ocr_engine`, `ocr_sprachen` and `geraet`; key `tools_equal_to_stored` shows which tool versions differ (`ocrmac` null, `pdftotext`).
5. The equality measurement: `python /app/worker/check_fresh.py --pdf-dir <folder with the 3 sample PDF files> --code-dir /app/code` (the PDF files are not in the image; the script needs a writable `--work` folder). Report for each sample: blocks equal, lines equal, block file equal, labels equal, and the causes. Compare the numbers with chapter 7.3 point 1 (macOS, same two arguments): a difference between the two is the effect of Poppler, of torch on Linux and of the CPU.
6. The modules that the run loads: `sentencepiece`, `mlx` and the commands `uname` and `file` (chapter 7.2). A missing optional import must not stop the run.
7. The stage times and the peak memory (`convert.json` keys `seconds` and `resources.max_rss_bytes`; the unit of `ru_maxrss` is kilobytes on Linux, the worker converts it) for a PDF of 1 page and of about 20 pages, with the CPU count of the container. Compare with `PARLPDFECH_JOB_TIMEOUT` (600 s) and with the size of the memory file system `/work`.
8. The read-only root file system: Docling, torch and the LinkML generators write nothing outside `/tmp` and `/work` (the scratch root is below `/work`; `HOME` and `XDG_CACHE_HOME` are in `/tmp`).
9. The cases: a PDF with a password (`protected_pdf`), more than 25 pages (`too_long`), a page that is one picture (`no_text_layer`), a file with the PDF mark only (`converter_stopped`, note `pdf_unreadable`). `check_fresh.py` writes 5 of these files itself.
10. The byte-equal copies: `python /app/worker/layout.py --check --out /app/code` gives 0 differences for 72 files, and the worker reports no module outside the scratch root (note `layout`). One converter file names a fixed folder of its author for the module search path; in the image this folder does not exist.

Cut rule of the plan (chapter 9.2): if the trial does not convert the 3 samples, the package has the profile `slim` only. Then `/api/health` gives `modes.upload` false and the screen S2 shows the line `s0.mode.slim`.

## 8 Notes of the examination step (13.10.2026)

Nothing of this chapter was run in a container.

1. Host names. The server answers only for the host names `localhost`, `127.0.0.1` and `[::1]`. A browser on the host that opens `http://localhost:<port>/app/` passes. Another name (for example a name of a reverse proxy) needs the variable `PARLPDFECH_ALLOWED_HOSTS`. `/healthz` has no host rule, so a health check with no host name passes.
2. Start through compose. `compose.yaml` publishes the port on `127.0.0.1`. The image sets the listen address `0.0.0.0:8080`; the server writes a warning for this address at the start. A start with `docker run -p 8080:8080` opens the API on all interfaces.
3. Work volume. `/work` is a memory file system of 256 MB. One upload holds at most 20 MB there, and the server takes one upload at one time. Before this rule, 13 open uploads of 20 MB filled the volume (read by the examiner, not run).
4. The UI folder in the image. The image copies the full folder `ui/`. The server gives the page files only; `ui/README.md`, `ui/tools/` and `ui/fixtures/` are in the image and have no address.
5. Compiled files of the layout. The worker uses a compiled file of the layout only if `layout_manifest.json` holds its SHA-256 (key `compiled`). A layout stage that compiles the files again in the image (another Python build) gives other compiled files than the manifest names: the worker then compiles each source file in each run. The first Linux trial must measure the time of this, or the layout stage must write the manifest key again.
6. The lock file `.lock` in the work folder: one container uses one work volume.

## 9 Notes of the correction round (13.10.2026)

Nothing of this chapter was run in a container.

1. Home folder and temporary files. The worker itself sets `PYSTOW_HOME` and `TMPDIR` to folders below the scratch folder of each job (`PARLPDFECH_SCRATCH_DIR`, else the parent of `--out`). The image needs no `PYSTOW_HOME`; `HOME=/tmp` can stay. Effect to check on Linux: the temporary files of Docling and of torch go to the scratch folder of the job, which is in the memory file system `/work` (256 MB), not to `/tmp`.
2. The target `full` must keep `DOCLING_ARTIFACTS_PATH`: the image has no hub cache. With no container, the profile `native` reads the Docling models from the hub cache of the user account.
3. Paths of the build host. `Dockerfile` has `ENV RUSTFLAGS` with `--remap-path-prefix` in the stage `rust-base` and one search step in each of the stages `server-build` and `wasm-build`. The lines were written and NOT run. The search step uses patterns for the cargo folder, the rustup folder, the build folder and the home folders of the image, and for the start of a home folder on macOS. If a binary holds one of these strings for another reason, the stage stops and the pattern list must be cut. With no container the same mapping is in `Makefile` (`make native-server`) and `rdfcheck/build.sh`; measured there: 0 paths of the build host in the server binary and in the 2 bundle files.
4. The WebAssembly bundle of the image. Read and not changed: the stage `wasm-build` calls `wasm-bindgen` with no `--no-typescript` and with no profile values of `rdfcheck/build.sh`. The bundle of the image thus differs from the bundle of the run with no container. The first build must compare the two or use the build script.
5. Compiled files of the layout. `worker/layout.py --check` ends with exit code 1 if the layout holds a compiled file that the manifest does not record. An image must not copy such files; run the check in the layout stage.

## 10 The self-contained source tree and the deploy kit (13.10.2026)

No image was built in this step. No Docker command ran.

1. `make dist-src` (script `worker/make_dist.py`, standard library only) writes `dist-src/`: the sources of the package, the code layout as plain files in `layout/` (the bytes of `build/layout` after `layout.py --check`, with `layout_manifest.json`, with no compiled file), `data/samples/` and `DIST-MANIFEST.json`. Measured: 184 files and the manifest, 15.7 MB; `layout/` 11.4 MB, `data/` 3.0 MB.
2. The tree has its own build files. `Dockerfile` and `compose.yaml` are made from the files of the package with fixed text changes: the layout stage has `COPY layout/ ...` and no named build context; compose has no key `additional_contexts`. `Makefile`, `.dockerignore`, `.gitignore` and `DIST.md` come from `container/dist/`. The tool stops if a fixed place is not found exactly one time. Thus a change of the head comment of the `Dockerfile` or of `compose.yaml` can need a change of `worker/make_dist.py`.
3. Not in the tree: the tools that read the project folder (list in `container/dist/DIST.md`). The tree has no target `gate`, `layout` or `native-data`.
4. Measured from a copy of the tree in a folder outside the project (one Mac, no network, no container): `make native-server` and `make native-wasm` built (16 s and 19 s with the crates on the computer); `make test` passed (16 + 29 server tests, 7 module tests, the example view valid); the server of the copy converted the 3 samples in the mode `auto` in 3.3 to 4.0 s each; each decisions SHA-256 was equal to the reference run; the trace of the 3 worker processes showed 0 opened, listed or imported paths below the project folders `src`, `daten`, `package`, `web`, `public`, `crisp-dm` and `quellen`. The interpreter was the Python environment of the project (632 paths of its package folder in each trace). An install of `requirements-slim.txt` with pip was not run.
5. The layout of the tree has no compiled file. The worker then compiles the converter files in each run. Measured: no clear difference of the time for one sample (3.3 to 4.0 s against 3.4 to 3.8 s with compiled files).
6. Measured with no container, profile `slim`: `container/seed_records.py` made the 6 sample records in 20 s (peak memory of one worker process 214 to 244 MB); `container/entrypoint.py` copied them to an empty work folder and started the server; `/api/samples` then gave `ready` true for each sample and mode. `container/check_seed.py` (new) compares the decisions SHA-256 of seed records with the reference values of the sample data: 3 of 3 equal in the mode `auto`.
7. Two settings of the server for a public site: `PARLPDFECH_READONLY=1` (no PDF file is taken, each DELETE is refused; error code `read_only`) and `PARLPDFECH_SAMPLE_RUNS=off` (no run for a sample whose record is in the work folder). The image sets neither. `deploy/k8s/deployment.yaml` sets the two. `CONTRACT.md` chapter 14 has the rule; `deploy/README.md` has the details and the measured answers. Later additions (`CONTRACT.md` chapter 15): the setting `PARLPDFECH_HOSTED=1` (the page uses its texts for a hosted site; `deployment.yaml` sets it), the error code `sample_runs_off` for the refusal of a sample run, and the static site: the image sets `PARLPDFECH_SITE_DIR=/app/site`, and the Dockerfile of a source tree that was made with `SITE_DIR` has the line `COPY site/ /app/site/` in the stage `appfiles`. An image with no folder `/app/site` redirects `/` to `/app/`. These lines were written and not run.
8. `deploy/` is a kit for a hosted sample site: a pipeline with Kaniko and manifests. Nothing of it was run. `make dist-src` copies only the pipeline file; the folder `deploy/` is not in the tree. The pipeline calls Kaniko with `--skip-unused-stages=true` (the stages `py-full` and `full` stand before the stage `slim` in the Dockerfile); read in the Kaniko documentation, not run. Not known: if Kaniko accepts `RUN --network=none` (the pipeline builds from a copy of the Dockerfile with no such flag); if the owner of `/app/seed` stays the user 10001 after `COPY --from=appfiles /app/ /app/` in a Kaniko build.
9. The package `.dockerignore` now also leaves out `dist-src/` and `deploy/`.
