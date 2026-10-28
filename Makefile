PY ?= python

.PHONY: test simulate edgar sample texts models probe analysis all

test:
	$(PY) -m pytest -q tests

simulate:
	$(PY) -m simulate.run_simulation --firms 1500

edgar:
	$(PY) -m data.fetch_edgar index
	$(PY) -m data.fetch_edgar events

sample:
	$(PY) -m data.build_sample

texts:
	$(PY) -m data.fetch_edgar texts

models:
	$(PY) -m coding.run_models

probe:
	$(PY) -m probes.reidentify

analysis:
	$(PY) -m analysis.leakage_index
	$(PY) -m analysis.figures

all: edgar sample texts models probe analysis
