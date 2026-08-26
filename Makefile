BOOTSTRAP_PYTHON ?= python3
PYTHON ?= .venv/bin/python
YEARS ?= 2008:2024

.PHONY: setup download download-zhang download-core download-openalex reproduce-zhang data validate analysis figures test lint clean-generated

setup:
	$(BOOTSTRAP_PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-lock.txt
	.venv/bin/python -m pip install -e . --no-deps

download: download-zhang download-core

download-zhang:
	$(PYTHON) -m research_labor_returns.download.zhang

download-core:
	$(PYTHON) -m research_labor_returns.download.deflators
	$(PYTHON) -m research_labor_returns.download.gss --years $(YEARS)
	$(PYTHON) -m research_labor_returns.download.herd --years $(YEARS)
	$(PYTHON) -m research_labor_returns.download.ipeds --years 2008:2023

download-openalex:
	$(PYTHON) -m research_labor_returns.download.openalex

reproduce-zhang:
	$(PYTHON) -m research_labor_returns.analysis.zhang_replication

data:
	$(PYTHON) -m research_labor_returns.clean.deflators
	$(PYTHON) -m research_labor_returns.clean.gss
	$(PYTHON) -m research_labor_returns.clean.herd
	$(PYTHON) -m research_labor_returns.clean.ipeds
	$(PYTHON) -m research_labor_returns.crosswalk.candidates
	$(PYTHON) -m research_labor_returns.build_panel.labor_resources
	$(PYTHON) -m research_labor_returns.validation.missingness

validate:
	$(PYTHON) -m research_labor_returns.validation.schemas
	$(PYTHON) -m research_labor_returns.validation.institution_crosswalk
	$(PYTHON) -m research_labor_returns.validation.published_totals

analysis:
	@echo "Analysis is gated until docs/pre_analysis_progress_report.md records Phase 6 approval."

figures: reproduce-zhang

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests

clean-generated:
	@echo "Generated data are intentionally not deleted automatically; raw inputs are immutable."
