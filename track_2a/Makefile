# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a. Run the targets from this folder (track_2a/, the project root of the template).
#
#   make setup          downloads (network): Python 3.12, PyYAML 6.0.3, linkml 1.11.1, the two eCH-0295 schema files
#   make run            converts the 3 samples from their stored input, validates the output, prints the stored
#                       results (no network, no GPU, no model)
#   make test           examines the copied files against SOURCES.json and the validator on a known invalid instance
#   make head-selftest  synthetic self-test of the Apertus head code of path 2 (numpy, scipy; no network; no model)
#   make clean          removes build/ (output of make run)
#
# Requirement: uv (https://docs.astral.sh/uv/), version 0.11 or later. README.md gives the details.

UV_RUN  = uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python
UV_HEAD = uv run --offline --no-project --python 3.12 --with numpy==2.5.3 --with scipy==1.18.1 python -B

.PHONY: setup run test head-selftest clean

setup:
	uv python install 3.12
	uv run --no-project --python 3.12 --with pyyaml==6.0.3 --with numpy==2.5.3 --with scipy==1.18.1 python -c "import yaml, numpy, scipy"
	uvx --from linkml==1.11.1 linkml-validate --version
	uv run --no-project --python 3.12 python src/fetch_schema.py

run:
	$(UV_RUN) src/run_samples.py

test:
	$(UV_RUN) src/check_sources.py
	$(UV_RUN) src/validate_ech.py samples/*/expected/instance.yaml samples/*/expected/provenance.yaml
	@if $(UV_RUN) src/validate_ech.py tests/invalid_instance.yaml; then \
		echo "FAIL: the validator accepted tests/invalid_instance.yaml"; exit 1; \
	else echo "PASS: the validator rejected tests/invalid_instance.yaml"; fi

head-selftest:
	cd src/apertus_head && $(UV_HEAD) m05_cls_it2_head.py selftest

clean:
	rm -rf build
