# Self-contained source tree of the ParlPDFeCH package

This folder is made by `make dist-src` of the package (script `worker/make_dist.py`). It holds each file that a computer with no copy of the project needs to build and run the package. Do not change a file here: make the tree again.

## 1 Content

| Folder or file | Content |
|---|---|
| `server/`, `rdfcheck/`, `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` | the Rust web server and the Rust module for WebAssembly |
| `ui/` | the page. The folder `ui/pkg/` (the WebAssembly bundle) is not here: the build makes it. |
| `worker/`, `view/` | the Python worker and the view function |
| `contract/` | the error catalog (the server includes it at compile time), the view schema, the examples |
| `container/` | the requirements files, the start command of the image, the script that makes the sample records |
| `layout/` | the code layout: byte-equal copies of the converter files as plain files, with `layout_manifest.json` (SHA-256 of each file). No compiled file. |
| `data/samples/` | the stored inputs of the 3 sample documents, and the PDF and the page image of each sample (`source.pdf`, `page-1.png`; not inputs of the conversion) |
| `site/` (only if the tree was made with `make dist-src SITE_DIR=<folder>`) | a built static site: the pages about the project. The server gives it below `/`, the app stays below `/app/`. The Dockerfile of such a tree copies the folder to `/app/site` of the image; `make run-native` gives it too. A tree with no `site/` redirects `/` to `/app/`. The manifest key `site` has the count of its files. |
| `Dockerfile`, `compose.yaml`, `Makefile`, `.dockerignore` | the build files of this tree. They differ from the files of the package: the layout comes from `./layout`, and no line names a folder outside this tree. |
| `.gitlab-ci.yml` | the pipeline file of the deploy kit (if the package has one) |
| `DIST-MANIFEST.json` | each file with its bytes and SHA-256, the git commit of the project, the time |
| `README.md`, `CONTRACT.md`, `STATE.md`, `EXAMINATION.md` | the documents of the package. They describe the package inside the project: commands that start with `cd` to the project folder, `make layout`, `make native-data`, `make gate` and the worker checks do not apply to this tree. |

## 2 What is not in this tree

- The project: the converter sources outside the layout list, the document data, the reference run.
- The tools that read the project folder: `worker/make_samples.py`, `worker/make_layout_list.py`, `worker/make_fresh_tables.py`, `worker/make_dist.py`, `worker/check_worker.py`, `worker/check_fresh.py`, `worker/check_values.py`, `worker/layout_add.py`, `view/check_view.py`, `contract/tools/gate_compare.py`, `contract/tools/gate_api.sh`, `contract/tools/gate_values.py`, `contract/tools/make_example_view.py`, `contract/tools/make_test_pdf.py`. Thus this tree has no target `gate`, `layout` or `native-data`.
- Build outputs: `target*/`, `ui/pkg/`, `work/`, compiled Python files.
- PDF files (except the PDF of each of the 3 samples), model weights, settings with values.

## 3 Build and run

With a container:

```
make run
```

On 14.10.2026, `make run` (target `slim`) ran one time on one Mac, from the copy of this tree in a clone of GitHub (commit `10e07b4`). The 3 samples in the 2 modes gave 6 valid records. `make run-full` and `make check-offline` were not run.

The image build needs a network: 2 base images, the Rust target for WebAssembly, the crates of `Cargo.lock`, the command `wasm-bindgen`, the Python packages of `container/requirements-slim.txt`.

With no container:

```
make fetch
make run-native PORT=8080 PYTHON=python3
```

Needs: cargo with the target `wasm32-unknown-unknown`; the command `wasm-bindgen` 0.2.127 (the version of the crate in `Cargo.lock`); `wasm-opt` (optional); a Python 3.12 that has the packages of `container/requirements-slim.txt`. `make fetch` downloads the crates; all other native steps use no network. With the crates on the computer: `CARGO_FLAGS="--offline --locked"`.

`PYTHON` is one command with no blank. For an interpreter that needs arguments, set `WORKER_CMD` to a JSON array, for example `WORKER_CMD='["uv","run","--project","<folder>","python","worker/serve_convert.py"]'`, and give the same interpreter to the targets `check-layout` and `test` through a small script.

The profile `native` of this tree converts the 3 samples. The conversion of another PDF needs more on the computer (README.md).

## 4 Checks

```
make check-dist
make check-layout
make test
```

`make check-dist` compares each file with `DIST-MANIFEST.json`. `make check-layout` compares each file of `layout/` with its manifest. `make test` runs the layout check, the cargo tests of the two crates, the schema check of the example view and one start of the seed script.

The real worker with the 3 samples, with no server (the pipeline of the deploy kit runs these two lines):

```
PARLPDFECH_PROFILE=slim PARLPDFECH_CODE_DIR="$PWD/layout" python -B container/seed_records.py --out work/seed
python -B container/check_seed.py --records work/seed
```

`container/check_seed.py` compares the SHA-256 of the decisions file of each record with the value of the reference run (`data/samples/<document>/reference.json`).

The layout has no compiled Python file. The worker compiles the converter files in each run. The manifest of the layout keeps the SHA-256 values of the compiled files of the build host; the worker uses a compiled file only if it has such a value.

## 5 Words in the layout files

The files below `layout/` are byte-equal copies of converter code. The converter compares their SHA-256, so they are not changed. They hold working names and internal notes of the project. The layout also holds ids and block labels of 193 development documents: a list of the documents with the file names of their rule and label files (`layout/daten/gj/calibration/floor_v1_fitset.json`) and an array file with document ids, block ids and one label for each block (`layout/daten/gj/design_b1s/oof/b1s_oof.npz`); it holds no text of these documents and no PDF. `STATE.md` (chapter 9, decision 1) gives the question of 13.10.2026 on their publication. Since 14.10.2026 the public repository holds this tree (folder `track_2a/app`).
