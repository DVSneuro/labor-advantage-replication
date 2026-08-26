# Marginal Returns to Research Labor

This repository builds a reproducible public-data extension of Zhang et al. (2022),
"Labor advantages drive the greater productivity of faculty at elite universities."
The central question is whether an additional graduate research assistant or postdoc
is associated with more subsequent research output at institutions that begin with
relatively little, versus abundant, research labor and resources.

The project is observational unless and until a defensible identification strategy is
validated. Total publication counts are called **production**; ratios to faculty,
research spending, or trainees are called **productivity**.

## Current milestone

The public labor/resource foundation (Phases 1–4) is complete. It contains 650 matched
institutions and 8,196 institution-years for 2010–2024, with IPEDS covariates through
2023. Modeling remains gated until OpenAlex acquisition, identity review, and full
Phase 6 validation pass. See `docs/pre_analysis_progress_report.md` for the exact
coverage and open decisions.

1. Reproduce the public Zhang archive.
2. Acquire and document GSS, HERD, and IPEDS.
3. Resolve institutional identities.
4. Build and validate the institution-year labor/resource panel.
5. Add fractionally attributed OpenAlex outcomes.
6. Issue the pre-analysis feasibility report.

The previous exploratory work is preserved under `legacy/initial_exploration/`. It is
not part of the reproducible pipeline.

## Quick start

Requires Python 3.11 or newer. `requirements-lock.txt` records the exact resolved
environment; `pyproject.toml` records compatible dependency ranges.

```bash
make setup
make download-zhang
make reproduce-zhang
make test
```

The larger public-data downloads are explicit because they take time and disk space:

```bash
make download-core
make data
make validate
```

The OpenAlex stage is deliberately separate. After the reviewed crosswalk and access
plan are approved, provide a key outside the repository and run:

```bash
export OPENALEX_API_KEY="..."
make download-openalex
```

All source definitions live in `config/sources.yml`. Every downloader records the
source, URL, release year, retrieval timestamp, byte size, SHA256, access notes, and
documentation URL in `data/metadata/download_manifest.csv`. Existing raw files are
never silently replaced.

## Data policy

- `data/raw/`, `data/interim/`, and `data/processed/` are generated and ignored.
- Raw files are immutable after download; a checksum mismatch is a hard failure.
- Small metadata manifests, crosswalk decisions, schemas, and test fixtures are
  versioned.
- Deterministic identifiers are preferred. Fuzzy matches are candidates only and must
  be written to `institution_matches_to_review.csv`.
- No proprietary Academic Analytics individual-level data are used.
- The legacy NIH RePORTER extracts contain public award and PI metadata. They are
  retained for provenance but will be replaced by scripted acquisition.

The complete privacy and repository-history audit is in
`docs/privacy_and_data_governance.md`.

## Repository map

```text
config/                         source and analysis configuration
data/crosswalks/                reviewed identity and field mappings
data/metadata/                  source and variable manifests
docs/                           technical decisions and progress reports
legacy/initial_exploration/     preserved pre-project analyses
src/research_labor_returns/     acquisition, cleaning, panel, and validation code
tests/                          deterministic unit tests and small fixtures
outputs/                        regenerable figures, tables, and model artifacts
manuscript/                     manuscript-ready material
```

## Citation

Please cite Zhang et al. (2022) and the Zenodo replication archive when using their
materials. Project citation metadata are in `CITATION.cff`.
