# Image of the ParlPDFeCH package (CONTRACT.md chapter 2.1; package plan chapters 3 and 8).
#
# STATE: this file was written and read. No build of it was run. See container/BUILD-NOTES.md.
#
# Targets:
#   slim  converts the sample documents from their stored inputs. No Docling, no torch, no model.
#   full  prepared for stage P0b (an unknown PDF). NOT YET EXAMINED: no build, no run.
#
# Build (from the folder of this file; Docker Engine 23 or later with BuildKit):
#   docker compose build                      target slim, see compose.yaml
#   docker build --target slim -t parlpdfech:slim .
#
# This is the file of the self-contained source tree. The code layout is the folder layout/ of the
# tree (plain files). The layout stage checks the SHA-256 of each copy.
#
# The file has no '# syntax=' line. Thus the build pulls no frontend image.
# No instruction names a processor architecture. The base images exist for linux/amd64 and linux/arm64.

ARG RUST_IMAGE=rust:1-bookworm
ARG PYTHON_IMAGE=python:3.12-slim-bookworm

# ---------------------------------------------------------------------------------------------
# Rust base: the sources of the two crates and all crates of Cargo.lock.
# rust-toolchain.toml is not copied: the toolchain of the image is used, and no second toolchain
# is downloaded. The WebAssembly target is one download from static.rust-lang.org.
# ---------------------------------------------------------------------------------------------
FROM ${RUST_IMAGE} AS rust-base
WORKDIR /build
RUN rustup target add wasm32-unknown-unknown
COPY Cargo.toml Cargo.lock ./
COPY server/ server/
COPY rdfcheck/ rdfcheck/
# The server includes this file at compile time (CONTRACT.md chapter 5.1).
COPY contract/errors.json contract/errors.json
RUN cargo fetch --locked
# No path of the build stage goes into the server binary or into the WebAssembly module (panic
# messages hold the paths of the source files). The folders of cargo, of rustup and of the build
# get fixed names; rdfcheck/build.sh and the Makefile use the same names for a native build.
ENV RUSTFLAGS="--remap-path-prefix=/build=/package --remap-path-prefix=/usr/local/cargo=/cargo --remap-path-prefix=/usr/local/rustup=/rustup"

# ---------------------------------------------------------------------------------------------
# Stage 1: the web server.
# ---------------------------------------------------------------------------------------------
FROM rust-base AS server-build
RUN cargo build --release --locked -p parlpdfech-server \
 && install -D target/release/parlpdfech-server /out/parlpdfech-server \
 && N="$(LC_ALL=C grep -a -o -e '/usr/local/cargo/' -e '/usr/local/rustup/' -e '/build/' -e '/root/' -e '/home/' -e '/[U]sers/' /out/parlpdfech-server | wc -l)" \
 && echo "paths of the build stage in the server binary: ${N}" && test "${N}" -eq 0

# ---------------------------------------------------------------------------------------------
# Stage 2: the WebAssembly bundle.
# The wasm-bindgen command MUST have the version of the wasm-bindgen crate in Cargo.lock.
# With two different versions the JavaScript file and the .wasm file do not fit together.
# ---------------------------------------------------------------------------------------------
FROM ${RUST_IMAGE} AS wasm-tools
ARG WASM_BINDGEN_VERSION=0.2.127
RUN cargo install --locked wasm-bindgen-cli --version ${WASM_BINDGEN_VERSION}

FROM rust-base AS wasm-build
ARG WASM_BINDGEN_VERSION=0.2.127
COPY --from=wasm-tools /usr/local/cargo/bin/wasm-bindgen /usr/local/cargo/bin/wasm-bindgen
RUN set -eu; \
    LOCK_VERSION="$(awk '/^name = "wasm-bindgen"$/{f=1; next} f && /^version = /{gsub(/"/,"",$3); print $3; exit}' Cargo.lock)"; \
    test "${LOCK_VERSION}" = "${WASM_BINDGEN_VERSION}" \
      || { echo "wasm-bindgen: Cargo.lock has ${LOCK_VERSION}, the command has ${WASM_BINDGEN_VERSION}"; exit 1; }
RUN cargo build --release --locked -p parlpdfech-rdfcheck --target wasm32-unknown-unknown \
 && wasm-bindgen --target web --out-dir /out/pkg \
      target/wasm32-unknown-unknown/release/parlpdfech_rdfcheck.wasm \
 && N="$(cat /out/pkg/* | LC_ALL=C grep -a -o -e '/usr/local/cargo/' -e '/usr/local/rustup/' -e '/build/' -e '/root/' -e '/home/' -e '/[U]sers/' | wc -l)" \
 && echo "paths of the build stage in the WebAssembly bundle: ${N}" && test "${N}" -eq 0
# wasm-opt is not run. Debian 12 has binaryen 108 (read on packages.debian.org). It is not known
# if this version reads the WebAssembly features that the present Rust compiler writes. The crate
# is compiled with opt-level "s" (Cargo.toml).

# ---------------------------------------------------------------------------------------------
# Stage 3a: Python run time of the target slim. All settings of the contract are here;
# the final stages inherit them.
# ---------------------------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS py-slim
ARG PARLPDFECH_COMMIT=unknown
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    TMPDIR=/tmp \
    PARLPDFECH_BIND=0.0.0.0:8080 \
    PARLPDFECH_UI_DIR=/app/ui \
    PARLPDFECH_DATA_DIR=/app/data \
    PARLPDFECH_WORK_DIR=/work \
    PARLPDFECH_WORKER_CMD='["python","/app/worker/serve_convert.py"]' \
    PARLPDFECH_WORKER_CWD=/app \
    PARLPDFECH_CODE_DIR=/app/code \
    PARLPDFECH_VIEW_DIR=/app/view \
    PARLPDFECH_SEED_DIR=/app/seed/records \
    PARLPDFECH_MAX_BYTES=20971520 \
    PARLPDFECH_MAX_PAGES=25 \
    PARLPDFECH_JOB_TIMEOUT=600 \
    PARLPDFECH_COMMIT=${PARLPDFECH_COMMIT} \
    PARLPDFECH_SITE_DIR=/app/site
# PARLPDFECH_SITE_DIR: the server gives a static site below / only if this folder holds index.html. An image
# with no such folder redirects / to /app/ (the server writes one warning line at the start).
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /tmp --shell /usr/sbin/nologin app \
 && install -d -o 10001 -g 10001 /work /app/seed
COPY container/requirements-slim.txt /opt/requirements/requirements-slim.txt
RUN python -m pip install --no-compile -r /opt/requirements/requirements-slim.txt \
 && python -m pip check
WORKDIR /app
EXPOSE 8080
# The image has no curl. Python asks the server.
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=6 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"]
# entrypoint.py copies the records of the samples to the work folder and then becomes the server.
CMD ["python", "/app/container/entrypoint.py"]

# ---------------------------------------------------------------------------------------------
# Stage 3b: Python run time of the target full. NOT YET EXAMINED (stage P0b).
# Adds Poppler (pdftotext), Docling, the CPU build of torch and the Docling models.
# ---------------------------------------------------------------------------------------------
FROM py-slim AS py-full
RUN apt-get update \
 && apt-get install -y --no-install-recommends poppler-utils libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*
COPY container/requirements-full.txt /opt/requirements/requirements-full.txt
# torch and torchvision come from the CPU index only, with no dependency resolution.
# Then pip installs all other lines from PyPI; the two packages are then present.
RUN python -m pip install --no-compile --no-deps --index-url https://download.pytorch.org/whl/cpu \
      $(grep -E '^(torch|torchvision)==' /opt/requirements/requirements-full.txt) \
 && python -m pip install --no-compile -r /opt/requirements/requirements-full.txt \
 && python -m pip check
# The layout model and the table model of Docling (huggingface.co). This is the only step that
# sets HF_HUB_OFFLINE to 0. At run time the value is 1.
RUN HF_HUB_OFFLINE=0 docling-tools models download --output-dir /app/docling-models layout tableformer
# pdftotext is at /usr/bin/pdftotext. The worker of stage P0b sets this path (package plan chapter 4.4).
ENV DOCLING_ARTIFACTS_PATH=/app/docling-models

# ---------------------------------------------------------------------------------------------
# The code layout: copies of the converter files (code, schemas, shared data), equal to the
# originals byte for byte. They are in the folder layout/ of this source tree, with no compiled
# file. This stage compares the SHA-256 of each copy with the layout manifest
# and stops the build if one is different. STATE: written, not run.
# ---------------------------------------------------------------------------------------------
FROM py-slim AS layout
WORKDIR /project
COPY layout/ /project/package/build/layout/
COPY worker/ /project/package/worker/
RUN python package/worker/layout.py --check \
 && test -n "$(ls -A /project/package/build/layout)"

# ---------------------------------------------------------------------------------------------
# All files of /app that the two targets share.
# ---------------------------------------------------------------------------------------------
FROM scratch AS appfiles
COPY --from=server-build /out/parlpdfech-server /app/parlpdfech-server
COPY ui/ /app/ui/
COPY --from=wasm-build /out/pkg/ /app/ui/pkg/
COPY worker/ /app/worker/
COPY view/ /app/view/
COPY data/ /app/data/
COPY --from=layout /project/package/build/layout/ /app/code/
COPY container/entrypoint.py container/seed_records.py /app/container/
# This tree has no folder site/: the address / redirects to /app/.

# ---------------------------------------------------------------------------------------------
# Target full (stage P0b; NOT YET EXAMINED).
# ---------------------------------------------------------------------------------------------
FROM py-full AS full
COPY --from=appfiles /app/ /app/
ENV PARLPDFECH_PROFILE=full
USER 10001:10001
# The records and views of the samples are made now, with no network.
# The build stops if a sample does not convert or is not valid.
RUN --network=none python /app/container/seed_records.py --out /app/seed/records

# ---------------------------------------------------------------------------------------------
# Target slim. It is the last stage, thus it is the default target.
# ---------------------------------------------------------------------------------------------
FROM py-slim AS slim
COPY --from=appfiles /app/ /app/
ENV PARLPDFECH_PROFILE=slim
USER 10001:10001
# The records and views of the samples are made now, with no network.
# The build stops if a sample does not convert or is not valid.
RUN --network=none python /app/container/seed_records.py --out /app/seed/records
