# ParlPDFeCH package, self-contained source tree (made by 'make dist-src' of the package).
# Run the targets from the folder of this file. No target reads a file outside this folder.
#
#   make run            builds the image (target slim) from this folder, starts it, waits for /healthz
#   make run-full       the same with the target full (stage P0b; NOT YET EXAMINED)
#   make stop           stops the container; all results of the session are lost
#   make logs           shows the log of the container
#   make check-offline  converts one sample in a container that has no network
#   make remove         stops the container and removes the images of this package
#   make fetch          downloads the crates of Cargo.lock (the only native step that needs a network)
#   make run-native     no container: builds and starts the server on this computer. Needs cargo with the
#                       target wasm32-unknown-unknown, the command wasm-bindgen 0.2.127 and a Python 3.12
#                       with the packages of container/requirements-slim.txt (PYTHON=<command>).
#                       PORT=8894 sets the port (default 8080). Stop it with Ctrl-C or the signal TERM.
#                       If this tree has the folder site/ (a static site), the server gives it below /;
#                       SITE_DIR=<folder> sets another folder, SITE_DIR= (empty) gives no site.
#   make check-layout   compares the SHA-256 of each file of layout/ with layout/layout_manifest.json
#   make check-dist     compares the SHA-256 of each file of this tree with DIST-MANIFEST.json
#   make test           tests with no container (cargo tests, the view example, the layout check)
#
# STATE: the container targets (run, run-full, check-offline) were written and not run.
# Not in this tree: the gate tools and the build tools that read the project folder (DIST.md lists them).
# Variables: PARLPDFECH_PORT (default 8080), PYTHON (default python3), CARGO_FLAGS (default --locked),
# WORKER_CMD (a JSON array; default: PYTHON with worker/serve_convert.py).

SHELL := /bin/sh

PARLPDFECH_PORT ?= 8080
export PARLPDFECH_PORT

COMPOSE := docker compose
WAIT_SECONDS ?= 120

# The tmpfs and security options of compose.yaml, for 'docker run'.
RUN_HARDENED := --rm --read-only --tmpfs /tmp:size=256m,mode=1777 --tmpfs /work:size=256m,mode=1777 \
	--user 10001:10001 --cap-drop ALL --security-opt no-new-privileges:true

# --- native run (no container) ------------------------------------------------------------------
PACKAGE_DIR := $(abspath .)
CARGO ?= $(shell command -v cargo 2>/dev/null || echo cargo)
WASM_BINDGEN ?= $(shell command -v wasm-bindgen 2>/dev/null || echo $(HOME)/.cargo/bin/wasm-bindgen)
PYTHON ?= python3
# '--locked': the versions of Cargo.lock. Add '--offline' if the crates are on this computer.
CARGO_FLAGS ?= --locked
PORT ?= 8080
NATIVE_BIND ?= 127.0.0.1:$(PORT)
WORKER_CMD ?= ["$(PYTHON)","$(PACKAGE_DIR)/worker/serve_convert.py"]
WORK_DIR ?= $(PACKAGE_DIR)/work
# The static site of this tree, if it has one (made with 'make dist-src SITE_DIR=...' of the package).
SITE_DIR ?= $(if $(wildcard site/index.html),$(PACKAGE_DIR)/site)

# No path of this computer goes into the server binary (panic messages hold the paths of the source files:
# the home folder with the name of the user account). The folders get fixed names. The last flag that fits a
# path applies, so the home folder comes first. rdfcheck/build.sh and the Dockerfile use the same names.
CARGO_HOME_DIR := $(or $(CARGO_HOME),$(HOME)/.cargo)
RUSTUP_HOME_DIR := $(or $(RUSTUP_HOME),$(HOME)/.rustup)
RUST_REMAP := --remap-path-prefix=$(HOME)=/build-home --remap-path-prefix=$(PACKAGE_DIR)=/package \
	--remap-path-prefix=$(CARGO_HOME_DIR)=/cargo --remap-path-prefix=$(RUSTUP_HOME_DIR)=/rustup

.PHONY: run run-full up stop logs check-offline remove preflight fetch \
        run-native native-server native-wasm check-layout check-dist test

# --- container ----------------------------------------------------------------------------------

run: PARLPDFECH_TARGET := slim
run: up

run-full: PARLPDFECH_TARGET := full
run-full: up

preflight:
	@command -v docker >/dev/null 2>&1 || { echo "ERROR: the command 'docker' is not on this computer."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker does not run. Start Docker, then run make again."; exit 1; }
	@test -f layout/layout_manifest.json || { echo "ERROR: layout/layout_manifest.json is absent. This folder is not a full source tree."; exit 1; }
	@test -f data/samples/index.json || { echo "ERROR: data/samples/index.json is absent. The sample data are not in this folder."; exit 1; }

up: preflight
	PARLPDFECH_TARGET=$(PARLPDFECH_TARGET) $(COMPOSE) build
	PARLPDFECH_TARGET=$(PARLPDFECH_TARGET) $(COMPOSE) up --detach --wait --wait-timeout $(WAIT_SECONDS) \
		|| { echo "ERROR: the server gave no answer on /healthz in $(WAIT_SECONDS) s. Run 'make logs'."; exit 1; }
	@echo "ParlPDFeCH runs. Open http://localhost:$(PARLPDFECH_PORT)/app/ in a browser. Stop it with 'make stop'."

stop:
	$(COMPOSE) down --volumes --remove-orphans

logs:
	$(COMPOSE) logs --follow --tail 200

# One sample, mode auto, in a container with no network interface except loopback.
# The command builds the image of the target slim if it is absent.
check-offline: preflight
	PARLPDFECH_TARGET=slim $(COMPOSE) build
	docker run $(RUN_HARDENED) --network none parlpdfech:slim \
		python /app/container/seed_records.py --out /work/offline-check --limit 1 --modes auto
	@echo "PASS: one sample converted in a container with --network none."

remove:
	-$(COMPOSE) down --volumes --remove-orphans --rmi all
	-docker image rm parlpdfech:slim parlpdfech:full 2>/dev/null
	@echo "Removed: the container and the images parlpdfech:slim and parlpdfech:full."
	@echo "Not removed: the base images and the build cache. README.md gives the commands."

# --- native -------------------------------------------------------------------------------------

fetch:
	$(CARGO) fetch --locked

native-server:
	RUSTFLAGS="$(RUST_REMAP)" CARGO_TARGET_DIR=target-server $(CARGO) build $(CARGO_FLAGS) --release -p parlpdfech-server
	@N=$$(LC_ALL=C grep -a -o -e "$(HOME)/" -e "/[U]sers/" target-server/release/parlpdfech-server | wc -l | tr -d ' '); \
	 echo "paths of this computer in the server binary: $$N"; test "$$N" -eq 0

# If this step fails, the server runs and the RDF panel of the page is absent.
# rdfcheck/build.sh: cargo (wasm32-unknown-unknown, with --offline: run 'make fetch' or 'make native-server'
# first), wasm-bindgen --target web, wasm-opt if present.
native-wasm:
	PATH="$(dir $(CARGO)):$(dir $(WASM_BINDGEN)):$$PATH" CARGO="$(CARGO)" sh rdfcheck/build.sh

check-layout:
	$(PYTHON) -B worker/layout.py --check --out layout

check-dist:
	$(PYTHON) -B container/check_dist.py

run-native: check-layout native-server
	@$(MAKE) native-wasm || echo "NOTE: the WebAssembly bundle was not built. The RDF panel of the page is absent."
	@mkdir -p "$(WORK_DIR)"
	@echo "ParlPDFeCH starts (profile native). Open http://$(NATIVE_BIND)/app/ in a browser. Stop it with Ctrl-C."
	PARLPDFECH_PROFILE=native \
	PARLPDFECH_BIND=$(NATIVE_BIND) \
	PARLPDFECH_UI_DIR="$(PACKAGE_DIR)/ui" \
	PARLPDFECH_DATA_DIR="$(PACKAGE_DIR)/data" \
	PARLPDFECH_WORK_DIR="$(WORK_DIR)" \
	PARLPDFECH_CODE_DIR="$(PACKAGE_DIR)/layout" \
	PARLPDFECH_VIEW_DIR="$(PACKAGE_DIR)/view" \
	PARLPDFECH_WORKER_CMD='$(WORKER_CMD)' \
	PARLPDFECH_WORKER_CWD="$(PACKAGE_DIR)" \
	$(if $(SITE_DIR),PARLPDFECH_SITE_DIR="$(abspath $(SITE_DIR))") \
	exec target-server/release/parlpdfech-server

# --- tests (no container) -----------------------------------------------------------------------

test: check-layout
	RUSTFLAGS="$(RUST_REMAP)" CARGO_TARGET_DIR=target-server $(CARGO) test $(CARGO_FLAGS) -p parlpdfech-server
	RUSTFLAGS="$(RUST_REMAP)" CARGO_TARGET_DIR=target-server $(CARGO) test $(CARGO_FLAGS) -p parlpdfech-rdfcheck
	$(PYTHON) -B contract/tools/validate_view.py contract/view.schema.json contract/examples/view_26171.json
	$(PYTHON) -B container/seed_records.py --help >/dev/null
	@echo "PASS: make test"
