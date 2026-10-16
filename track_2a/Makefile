# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a. Run the targets from this folder (track_2a/, the project root of the template).
#
# The app (folder app/): a PDF of a Swiss parliament goes in, an eCH-0295 record comes out.
#   make setup          downloads (network): Python 3.12 and the Python packages of the app into .venv/, the
#                       Rust crates of app/Cargo.lock (only if cargo is on the computer), and the packages and
#                       the 2 schema files of the earlier converter. 'make run' does not need 'make setup'
#   make setup-pdf      for your own PDF with 'make run-native', after 'make setup'. Needs the command pdftotext.
#                       Downloads (network): the packages of app/container/requirements-full.txt (docling 2.133.0,
#                       pypdfium2 5.14.0, torch) into .venv/, and the 2 Docling models into the Hugging Face cache
#                       (only if they are absent). On macOS also ocrmac 1.0.1 (OCR of Apple Vision for Docling,
#                       tools/requirements-macos-ocr.txt), as for the stored Docling files of the project
#   make setup-apertus  for the Apertus step of 'make convert', after 'make setup-pdf'. Needs a GPU: a Mac with Apple
#                       silicon and 32 GB memory (MLX), or an NVIDIA GPU with 24 GB or more (torch CUDA). Downloads
#                       (network): on macOS MLX 0.32.3; the model swiss-ai/Apertus-v1.5-8B at the revision
#                       APERTUS_REVISION (about 17.3 GB; needs your own Hugging Face account: accept the conditions
#                       of the model on its page, then 'hf auth login'); tools/text_branch.py cuts its text branch
#                       (16.1 GB) into APERTUS_MODEL_DIR; the 3 head files from HEADS_REPO at HEADS_REVISION (or from
#                       HEADS_DIR). Disk: about 40 GB free. With no GPU it stops and names the ways out (a GPU in the
#                       cloud, docs/apertus-gpu.md; or APERTUS=0). APERTUS_MODEL=none sets up the heads only (and
#                       on macOS ocrmac, no MLX). A text branch that is already there gets a full SHA-256 check
#                       (APERTUS_VERIFY=0 skips it). HEADS_DIR=<folder> takes the 3 head files from a local
#                       folder in place of the download.
#                       Tested only on one Mac (Apple M4, 32 GB) on 16.10.2026; Linux and Windows are not tested
#   make serve-apertus  on a computer with a GPU (this one, another one, or a rented GPU in the cloud), after
#                       'make setup-apertus' there: the read-out service of the Apertus step (docs/apertus-gpu.md).
#                       It loads the model one time and answers with the layer-20 states for the prompt texts of
#                       one PDF at a time. HOST and PORT on the command line set the address (default
#                       127.0.0.1:8090: this computer only; another address needs the environment variable
#                       APERTUS_TOKEN, 32 characters or more). APERTUS_IDLE_EXIT=<s> and APERTUS_MAX_REQUESTS=<n>
#                       end it by itself. Ctrl-C ends it. On your own computer: an ssh tunnel to it, then
#                       'make convert APERTUS_URL=http://127.0.0.1:8090 PDF=...' (the text of the PDF goes to that
#                       computer). Tested only on one Mac on 16.10.2026, service and client on this one computer
#   make run            needs Docker: builds the image (target slim) from app/ (docker compose build), starts it
#                       on 127.0.0.1:8080 and waits for /healthz. Then open http://127.0.0.1:8080/app/
#   make stop           stops the container of 'make run'. 'make logs' shows its log
#   make run-native     no container: builds the Rust server and the WebAssembly bundle with cargo, then starts
#                       the app with the Python of .venv/ (or APP_PYTHON=<command>) on 127.0.0.1:$(PORT)
#                       (default 8080). Needs cargo with the target wasm32-unknown-unknown and the command
#                       wasm-bindgen 0.2.127 (cargo install wasm-bindgen-cli --version 0.2.127). Stop it with
#                       Ctrl-C. On 14.10.2026 'make run' and 'make run-native' ran on one Mac
#   make test           checks with no network and no Rust compiler, after one 'make setup' (it needs the 2 schema
#                       files of 'make setup'): the copied files against SOURCES.json, the prompt files, the
#                       validator, the file list and the code layout of app/, and the rules of the Apertus
#                       read-out service and its client (app/worker/check_apertus.py: a test backend on 127.0.0.1,
#                       no model)
#   make test-app       the tests of app/ (cargo tests of the 2 crates, the example view, a start of the seed
#                       script). Needs cargo and the crates of 'make setup'
#   make clean          removes build/ and the build outputs of app/ (target-server/, target-wasm/, ui/pkg/, work/)
#
# Own PDFs in the terminal. The targets need 'make setup' and 'make setup-pdf' one time, and the commands jq and
# curl. The results go to out/ (git ignores it). On 15.10.2026 the 3 targets ran on one Mac (Apple silicon), in a
# clone, with code rules only: 3 samples and 5 development PDFs.
#   The Apertus step: APERTUS=auto (default): Apertus-v1.5-8B reads out the PDF if 'make setup-apertus' is done
#   and a GPU is there; else a NOTE, and the code rules only. APERTUS=1: Apertus or stop with a message.
#   APERTUS=0: code rules only (no GPU, no Apertus), as for an upload in the app. APERTUS_BACKEND=auto|mlx|cuda|mps|cpu
#   (auto never takes the CPU; cpu is very slow, for checks only). APERTUS_TIMEOUT: seconds for one PDF (1800).
#   APERTUS_URL=http://127.0.0.1:8090: the read-out runs on the GPU of another computer ('make serve-apertus'
#   there, an ssh tunnel here; the token of that service in the environment variable APERTUS_TOKEN). With
#   APERTUS_URL, auto takes that GPU first. This computer then needs only the heads ('make setup-apertus
#   APERTUS_MODEL=none'). docs/apertus-gpu.md gives the steps.
#   make convert PDF=<file or URL>   converts one PDF. A relative path starts in track_2a/. A URL must be http or
#                       https. A download has a limit of 20 MB and 120 s. As in the app, the first 1024 bytes
#                       must have the mark %PDF-. Each PDF gets an ID (0001, 0002, ...). The same PDF (same
#                       SHA-256) keeps its ID. The terminal shows the ID, valid yes or no, the values with their
#                       probability and status, and the folder out/<ID>/. A PDF with a stored result is not
#                       converted again. AGAIN=1 converts it again. Only one 'make convert' can run at a time
#   make convert DIR=<folder>        converts each file of the folder whose name ends with .pdf (no subfolder).
#                       A file name with a line break is not read
#   make convert LIST=<file>         converts each line of the file: a path or an http(s) URL. A relative path
#                       starts in the folder of the file. A line that starts with # is a comment
#   make list           shows the IDs as a table. The data of an ID are in out/<ID>/source.txt. The file
#                       out/catalog.tsv is made from these files after each conversion
#   make view ID=0002   opens this one result in the browser. A local server of the app shows it (read-only,
#                       127.0.0.1). The port is 8080 or the next free port. PORT=<n> sets the port. OPEN=no
#                       shows the address only. Stop the server with Ctrl-C. The online website does not have
#                       this view. Before the start, 'make view' does the build steps of 'make run-native'.
#                       cargo builds only the parts that changed. The WebAssembly bundle is built only if it
#                       is absent or older than its source files
#
# The earlier converter of 12.10.2026 (its metadata values come from the export record, not from the PDF):
#   make run-earlier    converts the 3 samples from their stored input, validates the output, prints the stored
#                       results (no network, no GPU, no model). Before 14.10.2026 this target had the name 'run'
#   make head-selftest  synthetic self-test of the earlier Apertus head of task R2 (12.10.2026; numpy, scipy; no
#                       network; no model)
#
# Requirement: uv (https://docs.astral.sh/uv/), version 0.11 or later. README.md gives the details.

UV_RUN  = uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python
UV_HEAD = uv run --offline --no-project --python 3.12 --with numpy==2.5.3 --with scipy==1.18.1 python -B
UV_NUMPY = uv run --offline --no-project --python 3.12 --with numpy==2.5.3 python -I -B

PORT ?= 8080
APP_VENV := .venv
APP_PYTHON ?= $(if $(wildcard $(APP_VENV)/bin/python),$(abspath $(APP_VENV)/bin/python),python3)

# The Apertus step ('make setup-apertus', 'make convert'). The model and the heads are pinned: the revision of the
# model repository, and the commit of the heads repository with the SHA-256 of tools/apertus/heads.sha256.
APERTUS ?= auto
APERTUS_BACKEND ?= auto
APERTUS_TIMEOUT ?= 1800
APERTUS_PYTHON ?= $(APP_PYTHON)
APERTUS_REPO := swiss-ai/Apertus-v1.5-8B
APERTUS_REVISION := ef4bbc54d6fe658bc782280ff9f3b53a10a9758f
# The text branch folder.
APERTUS_MODEL_DIR ?= data/apertus/apertus-v1.5-8b-text-bf16
APERTUS_MODEL ?= auto
APERTUS_SOURCE_DIR ?=
HEADS_REPO ?= JonathanKovatsch/parlpdfech-heads
# The commit of the heads repository (40 hex characters; upload of 16.10.2026).
HEADS_REVISION ?= 64ba850a119f5b9dcee3761a60d25b4ad670cd1c
# Optional: a local folder with the 3 head files, in place of the download.
HEADS_DIR ?=
APERTUS_VERIFY ?= 1
# 'make serve-apertus': HOST and PORT count only on the command line (PORT of 'make run-native' is 8080).
APERTUS_HOST := $(if $(filter command line,$(origin HOST)),$(HOST),127.0.0.1)
APERTUS_PORT := $(if $(filter command line,$(origin PORT)),$(PORT),8090)
APERTUS_IDLE_EXIT ?=
APERTUS_MAX_REQUESTS ?=
# The versions of app/Cargo.lock, with no network: 'make setup' downloads the crates before.
APP_CARGO_FLAGS ?= --offline --locked

# 'make setup-pdf': the 2 models that Docling loads for a PDF (layout model and table model), as <repository>@<revision>.
# The worker (app/worker/fresh.py) looks for pdftotext with the search path, then in these 3 places.
DOCLING_MODELS := docling-project/docling-layout-heron@main docling-project/docling-models@v2.3.0
PDFTOTEXT_PLACES := /usr/bin/pdftotext /opt/homebrew/bin/pdftotext /usr/local/bin/pdftotext

# 'make convert', 'make list', 'make view': only a value on the command line counts. The targets do not read
# a variable PDF, DIR or ID of the shell environment. $(value ...) keeps the value as it is: make does not
# expand a '$' in a path or a URL. A value with a line break stops make with a message. shq puts a value in
# single quotes for sh.
define line_break


endef
cmdline = $(if $(filter command line,$(origin $(1))),$(if $(findstring $(line_break),$(value $(1))),$(error \
	$(1) has a line break. Give a path or a URL with no line break),$(value $(1))))
shq = '$(subst ','\'',$(1))'
CONVERT_SH = PYTHON=$(call shq,$(APP_PYTHON)) DOCLING_MODELS='$(DOCLING_MODELS)' \
	PDFTOTEXT_PLACES='$(PDFTOTEXT_PLACES)' APERTUS=$(call shq,$(APERTUS)) APERTUS_BACKEND=$(call shq,$(APERTUS_BACKEND)) \
	APERTUS_TIMEOUT=$(call shq,$(APERTUS_TIMEOUT)) APERTUS_PYTHON=$(call shq,$(APERTUS_PYTHON)) sh tools/convert.sh
WASM_BUNDLE := app/ui/pkg/parlpdfech_rdfcheck_bg.wasm
WASM_SOURCES := app/rdfcheck app/Cargo.toml app/Cargo.lock app/rust-toolchain.toml

.PHONY: setup setup-pdf setup-apertus serve-apertus run stop logs run-native test test-app clean run-earlier head-selftest \
	convert list view

setup:
	uv python install 3.12
	uv venv --allow-existing --python 3.12 $(APP_VENV)
	uv pip install --python $(APP_VENV)/bin/python -r app/container/requirements-slim.txt
	@if command -v cargo >/dev/null 2>&1; then $(MAKE) -C app fetch; \
	else echo "NOTE: no cargo on this computer. The Rust crates are not downloaded. make run-native and make test-app need cargo; make run and make test do not."; fi
	uv run --no-project --python 3.12 --with pyyaml==6.0.3 --with numpy==2.5.3 --with scipy==1.18.1 python -c "import yaml, numpy, scipy"
	uvx --from linkml==1.11.1 linkml-validate --version
	uv run --no-project --python 3.12 python src/fetch_schema.py

setup-pdf:
	@[ -x $(APP_VENV)/bin/python ] || { echo "ERROR: $(APP_VENV)/ is absent. Run 'make setup' first."; exit 1; }
	@found=$$(command -v pdftotext 2>/dev/null); \
	for p in $(PDFTOTEXT_PLACES); do [ -n "$$found" ] || { [ -x "$$p" ] && found="$$p"; }; done; \
	if [ -n "$$found" ]; then echo "pdftotext: $$found"; \
	else echo "ERROR: the command pdftotext is absent. Install it, then run 'make setup-pdf' again:"; \
	echo "  macOS (Homebrew):  brew install poppler"; \
	echo "  Debian or Ubuntu:  sudo apt install poppler-utils"; exit 1; fi
	uv pip install --python $(APP_VENV)/bin/python -r app/container/requirements-full.txt
	@if [ "$$(uname -s)" = Darwin ]; then echo "macOS: ocrmac (OCR of Apple Vision for Docling, as for the stored Docling files)"; \
	uv pip install --python $(APP_VENV)/bin/python -r tools/requirements-macos-ocr.txt || exit 1; fi
	uv pip check --python $(APP_VENV)/bin/python
	@for m in $(DOCLING_MODELS); do repo=$${m%@*}; rev=$${m#*@}; \
	if HF_HUB_OFFLINE=1 $(APP_VENV)/bin/hf download $$repo --revision $$rev --quiet >/dev/null 2>&1; then \
	echo "model $$repo ($$rev): in the Hugging Face cache"; \
	else echo "model $$repo ($$rev): not in the Hugging Face cache, download (network)"; \
	HF_HUB_OFFLINE=0 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1 \
	$(APP_VENV)/bin/hf download $$repo --revision $$rev --quiet >/dev/null || exit 1; fi; done
	$(APP_VENV)/bin/python -c "from importlib.metadata import version as v; import docling, pypdfium2; print('docling', v('docling'), '/ pypdfium2', v('pypdfium2'))"
	@echo "PASS: make setup-pdf. Start the app with 'make run-native'. Then open http://127.0.0.1:$(PORT)/app/ and drop your PDF on the page."

setup-apertus:
	@PYTHON=$(call shq,$(APERTUS_PYTHON)) APERTUS_REPO='$(APERTUS_REPO)' APERTUS_REVISION='$(APERTUS_REVISION)' \
	APERTUS_MODEL_DIR=$(call shq,$(APERTUS_MODEL_DIR)) APERTUS_MODEL=$(call shq,$(APERTUS_MODEL)) \
	APERTUS_SOURCE_DIR=$(call shq,$(APERTUS_SOURCE_DIR)) APERTUS_BACKEND=$(call shq,$(APERTUS_BACKEND)) \
	HEADS_REPO=$(call shq,$(HEADS_REPO)) HEADS_REVISION=$(call shq,$(HEADS_REVISION)) HEADS_DIR=$(call shq,$(HEADS_DIR)) \
	APERTUS_VERIFY=$(call shq,$(APERTUS_VERIFY)) sh tools/setup_apertus.sh

serve-apertus:
	@PYTHON=$(call shq,$(APP_PYTHON)) APERTUS_PYTHON=$(call shq,$(APERTUS_PYTHON)) \
	APERTUS_MODEL_DIR=$(call shq,$(APERTUS_MODEL_DIR)) APERTUS_BACKEND=$(call shq,$(APERTUS_BACKEND)) \
	APERTUS_HOST=$(call shq,$(APERTUS_HOST)) APERTUS_PORT=$(call shq,$(APERTUS_PORT)) \
	APERTUS_IDLE_EXIT=$(call shq,$(APERTUS_IDLE_EXIT)) APERTUS_MAX_REQUESTS=$(call shq,$(APERTUS_MAX_REQUESTS)) \
	sh tools/serve_apertus.sh

run:
	$(MAKE) -C app run

stop:
	$(MAKE) -C app stop

logs:
	$(MAKE) -C app logs

run-native:
	$(MAKE) -C app run-native PORT=$(PORT) PYTHON=$(APP_PYTHON) CARGO_FLAGS="$(APP_CARGO_FLAGS)"

convert:
	@$(CONVERT_SH) convert --pdf $(call shq,$(call cmdline,PDF)) --dir $(call shq,$(call cmdline,DIR)) \
		--list $(call shq,$(call cmdline,LIST)) --again $(call shq,$(call cmdline,AGAIN))

list:
	@$(CONVERT_SH) list

# First the check of the ID, then the build steps of 'make run-native' (cargo builds only the parts that changed;
# the WebAssembly bundle only if it is absent or older than a file of WASM_SOURCES), then the start.
view:
	@$(CONVERT_SH) view-check --id $(call shq,$(call cmdline,ID))
	@$(MAKE) --no-print-directory -s -C app check-layout native-server PYTHON=$(APP_PYTHON) \
		CARGO_FLAGS="$(APP_CARGO_FLAGS)" || { echo "ERROR: the server of the app was not built (the steps of 'make run-native')."; exit 1; }
	@if [ ! -f $(WASM_BUNDLE) ] || [ -n "$$(find $(WASM_SOURCES) -newer $(WASM_BUNDLE) 2>/dev/null | head -n 1)" ]; then \
		$(MAKE) --no-print-directory -s -C app native-wasm \
		|| echo "NOTE: the WebAssembly bundle was not built. The RDF panel of the page is absent."; \
	fi
	@$(CONVERT_SH) view --id $(call shq,$(call cmdline,ID)) --port $(call shq,$(call cmdline,PORT)) \
		--open $(call shq,$(call cmdline,OPEN))

test:
	$(UV_RUN) src/check_sources.py
	$(UV_RUN) src/check_prompts.py
	$(UV_RUN) src/validate_ech.py samples/*/expected/instance.yaml samples/*/expected/provenance.yaml
	@if $(UV_RUN) src/validate_ech.py tests/invalid_instance.yaml; then \
		echo "FAIL: the validator accepted tests/invalid_instance.yaml"; exit 1; \
	else echo "PASS: the validator rejected tests/invalid_instance.yaml"; fi
	$(MAKE) -C app check-dist PYTHON=$(APP_PYTHON)
	$(MAKE) -C app check-layout PYTHON=$(APP_PYTHON)
	$(UV_NUMPY) app/worker/check_apertus.py
	@echo "PASS: make test"

test-app:
	$(MAKE) -C app test PYTHON=$(APP_PYTHON) CARGO_FLAGS="$(APP_CARGO_FLAGS)"

clean:
	rm -rf build app/target-server app/target-wasm app/ui/pkg app/work

run-earlier:
	$(UV_RUN) src/run_samples.py

head-selftest:
	cd src/apertus_head && $(UV_HEAD) m05_cls_it2_head.py selftest
