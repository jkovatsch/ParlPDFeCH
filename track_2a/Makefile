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
#                       (only if they are absent)
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
#                       validator, the file list and the code layout of app/
#   make test-app       the tests of app/ (cargo tests of the 2 crates, the example view, a start of the seed
#                       script). Needs cargo and the crates of 'make setup'
#   make clean          removes build/ and the build outputs of app/ (target-server/, target-wasm/, ui/pkg/, work/)
#
# Own PDFs in the terminal: code rules only (no GPU, no Apertus), as for an upload in the app. The targets need
# 'make setup' and 'make setup-pdf' one time, and the commands jq and curl. The results go to out/ (git ignores it).
# On 15.10.2026 the 3 targets ran on one Mac (Apple silicon), in a clone: 3 samples and 5 development PDFs.
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

PORT ?= 8080
APP_VENV := .venv
APP_PYTHON ?= $(if $(wildcard $(APP_VENV)/bin/python),$(abspath $(APP_VENV)/bin/python),python3)
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
	PDFTOTEXT_PLACES='$(PDFTOTEXT_PLACES)' sh tools/convert.sh
WASM_BUNDLE := app/ui/pkg/parlpdfech_rdfcheck_bg.wasm
WASM_SOURCES := app/rdfcheck app/Cargo.toml app/Cargo.lock app/rust-toolchain.toml

.PHONY: setup setup-pdf run stop logs run-native test test-app clean run-earlier head-selftest convert list view

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
	uv pip check --python $(APP_VENV)/bin/python
	@for m in $(DOCLING_MODELS); do repo=$${m%@*}; rev=$${m#*@}; \
	if HF_HUB_OFFLINE=1 $(APP_VENV)/bin/hf download $$repo --revision $$rev --quiet >/dev/null 2>&1; then \
	echo "model $$repo ($$rev): in the Hugging Face cache"; \
	else echo "model $$repo ($$rev): not in the Hugging Face cache, download (network)"; \
	HF_HUB_OFFLINE=0 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1 \
	$(APP_VENV)/bin/hf download $$repo --revision $$rev --quiet >/dev/null || exit 1; fi; done
	$(APP_VENV)/bin/python -c "from importlib.metadata import version as v; import docling, pypdfium2; print('docling', v('docling'), '/ pypdfium2', v('pypdfium2'))"
	@echo "PASS: make setup-pdf. Start the app with 'make run-native'. Then open http://127.0.0.1:$(PORT)/app/ and drop your PDF on the page."

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
	@echo "PASS: make test"

test-app:
	$(MAKE) -C app test PYTHON=$(APP_PYTHON) CARGO_FLAGS="$(APP_CARGO_FLAGS)"

clean:
	rm -rf build app/target-server app/target-wasm app/ui/pkg app/work

run-earlier:
	$(UV_RUN) src/run_samples.py

head-selftest:
	cd src/apertus_head && $(UV_HEAD) m05_cls_it2_head.py selftest
