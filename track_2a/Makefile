# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a. Run the targets from this folder (track_2a/, the project root of the template).
#
# The app (folder app/): a PDF of a Swiss parliament goes in, an eCH-0295 record comes out.
#   make setup          downloads (network): Python 3.12 and the Python packages of the app into .venv/, the
#                       Rust crates of app/Cargo.lock (only if cargo is on the computer), and the packages and
#                       the 2 schema files of the earlier converter. 'make run' does not need 'make setup'
#   make run            needs Docker: builds the image (target slim) from app/ (docker compose build), starts it
#                       on 127.0.0.1:8080 and waits for /healthz. Then open http://127.0.0.1:8080/app/
#   make stop           stops the container of 'make run'. 'make logs' shows its log
#   make run-native     no container: builds the Rust server and the WebAssembly bundle with cargo, then starts
#                       the app with the Python of .venv/ (or APP_PYTHON=<command>) on 127.0.0.1:$(PORT)
#                       (default 8080). Needs cargo with the target wasm32-unknown-unknown and the command
#                       wasm-bindgen 0.2.127 (cargo install wasm-bindgen-cli --version 0.2.127). Stop it with
#                       Ctrl-C. This is the way that ran on 14.10.2026; 'make run' did not run
#   make test           checks with no network and no Rust compiler, after one 'make setup' (it needs the 2 schema
#                       files of 'make setup'): the copied files against SOURCES.json, the prompt files, the
#                       validator, the file list and the code layout of app/
#   make test-app       the tests of app/ (cargo tests of the 2 crates, the example view, a start of the seed
#                       script). Needs cargo and the crates of 'make setup'
#   make clean          removes build/ and the build outputs of app/ (target-server/, target-wasm/, ui/pkg/, work/)
#
# The earlier converter of 12.10.2026 (its metadata values come from the export record, not from the PDF):
#   make run-earlier    converts the 3 samples from their stored input, validates the output, prints the stored
#                       results (no network, no GPU, no model). Before 14.10.2026 this target had the name 'run'
#   make head-selftest  synthetic self-test of the Apertus head code of path 2 (numpy, scipy; no network; no model)
#
# Requirement: uv (https://docs.astral.sh/uv/), version 0.11 or later. README.md gives the details.

UV_RUN  = uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python
UV_HEAD = uv run --offline --no-project --python 3.12 --with numpy==2.5.3 --with scipy==1.18.1 python -B

PORT ?= 8080
APP_VENV := .venv
APP_PYTHON ?= $(if $(wildcard $(APP_VENV)/bin/python),$(abspath $(APP_VENV)/bin/python),python3)
# The versions of app/Cargo.lock, with no network: 'make setup' downloads the crates before.
APP_CARGO_FLAGS ?= --offline --locked

.PHONY: setup run stop logs run-native test test-app clean run-earlier head-selftest

setup:
	uv python install 3.12
	uv venv --allow-existing --python 3.12 $(APP_VENV)
	uv pip install --python $(APP_VENV)/bin/python -r app/container/requirements-slim.txt
	@if command -v cargo >/dev/null 2>&1; then $(MAKE) -C app fetch; \
	else echo "NOTE: no cargo on this computer. The Rust crates are not downloaded. make run-native and make test-app need cargo; make run and make test do not."; fi
	uv run --no-project --python 3.12 --with pyyaml==6.0.3 --with numpy==2.5.3 --with scipy==1.18.1 python -c "import yaml, numpy, scipy"
	uvx --from linkml==1.11.1 linkml-validate --version
	uv run --no-project --python 3.12 python src/fetch_schema.py

run:
	$(MAKE) -C app run

stop:
	$(MAKE) -C app stop

logs:
	$(MAKE) -C app logs

run-native:
	$(MAKE) -C app run-native PORT=$(PORT) PYTHON=$(APP_PYTHON) CARGO_FLAGS="$(APP_CARGO_FLAGS)"

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
