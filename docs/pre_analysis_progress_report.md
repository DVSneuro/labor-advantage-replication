# Pre-analysis feasibility and progress report

**Status (2026-08-26): Phases 1–4 foundation complete; Phases 5–6 incomplete; modeling
is not approved.** This report is the required checkpoint before substantive analysis.

## 1. Sources, years, and acquisition

| Source | Exact public source | Years acquired / represented | Scripted method |
|---|---|---:|---|
| Zhang et al. replication | Zenodo record 7126263, `code-and-data.tar.gz` | Study period 2008–17; released tables are cross-sectional | Zenodo record API, upstream MD5 and local SHA256 verification, safe extraction |
| GSS | NCSES annual public-use archives and 2024 guide/appendices | 2008–2024 | Stable annual ZIP URL; SAS member read directly from each ZIP |
| HERD | NCSES annual full archives, short-form archives, and 2024 guide | 2008–2024; short form 2012–2024 | Stable annual ZIP URLs; full and short files combined only after overlap check |
| IPEDS | NCES complete data files: HD, EF-A, EAP, F1A, F2, plus matching dictionaries | 2008–2023 | Stable annual ZIP URLs; final/revised member preferred when present |
| GDP deflator | BEA NIPA flat files, table 1.1.9 series `A191RD` | 2008–2024 extracted | Keyless official `FlatFiles.ZIP`; converted to constant 2017 dollars |
| OpenAlex | Works API and institution/ROR records | Planned 2008–2024; not acquired at scale | Cursor-paginated API cache implemented; requires `OPENALEX_API_KEY` |

Every acquired file appears in `data/metadata/download_manifest.csv` with source
organization, exact URL, file name, release year, UTC retrieval time, byte size,
SHA256, upstream checksum when available, access notes, and documentation URL. Raw
files are ignored and are not silently replaced.

## 2. Data dictionaries and definition breaks

The harmonized definitions are in `docs/data_dictionary.md`. Machine-readable
availability tables are:

- `data/metadata/gss_variable_availability.csv` (source columns by era and year);
- `data/metadata/herd_variable_availability.csv` (Source rows and counts by year);
- `data/metadata/ipeds_variable_availability.csv` (nonmissing counts by year); and
- `data/metadata/bea_gdp_deflator_2017_dollars.csv`.

Material breaks are not smoothed away: doctoral counts become separately available in
GSS in 2017; GSS has postdoc-frame and 2014-frame warnings; HERD is redesigned in
2010; and IPEDS employees change occupational schema in 2012. The longest current
deterministic GSS–HERD panel begins in 2010. The fully covariate-covered core period is
2010–2023 because the selected IPEDS collection is not yet complete for 2024.

## 3. Identity resolution and match rates

The crosswalk uses UNITID whenever an annual GSS/HERD record supplies exactly one
valid campus identifier. A reviewed override is allowed only from
`institution_crosswalk.csv`. Sixty-three unresolved or multi-campus cases are in
`institution_matches_to_review.csv` and are excluded from automatic linkage.

Seven required high-profile mappings pass automated tests: Temple, Rutgers–New
Brunswick, UIC, UCLA, Michigan–Ann Arbor, Wisconsin–Madison, and Ohio State main
campus. Rutgers has no accepted OpenAlex/ROR identifier because the candidate found is
a system aggregate. Six of the seven seed records have reviewed OpenAlex and ROR IDs.

| Year | GSS institutions | HERD institutions | Matched | Share of GSS | Share of HERD |
|---:|---:|---:|---:|---:|---:|
| 2010 | 574 | 744 | 457 | 79.6% | 61.4% |
| 2014 | 706 | 889 | 566 | 80.2% | 63.7% |
| 2018 | 715 | 911 | 589 | 82.4% | 64.7% |
| 2023 | 687 | 911 | 567 | 82.5% | 62.2% |
| 2024 | 635 | 925 | 537 | 84.6% | 58.1% |

Rates use all reporting source institutions as denominators, including records without
UNITIDs. Among the matched GSS–HERD rows for 2010–2023, IPEDS joins to 99.37%. Zhang's
public archive cannot be institution-matched because it contains no institution ID or
name. A meaningful full OpenAlex match rate is not yet available.

## 4. Retained panel

- GSS source panel: 778 reporting IDs and 11,108 institution-years (2008–2024).
- HERD source panel: 1,146 reporting IDs and 14,800 institution-years (2008–2024).
- IPEDS source panel: 9,845 UNITIDs and 113,659 institution-years (2008–2023).
- Matched labor/resource foundation: **650 UNITIDs and 8,196 institution-years**
  (2010–2024), including 7,611 IPEDS-matched rows.

The foundation is unbalanced by design. Annual retained counts range from 457 in 2010
to 589 in 2018, with 537 in 2024. No default imputation is performed.

## 5. Candidate labor/resource measures

Primary labor is `research_labor_core = research_assistants + postdocs`. The broad
sensitivity measure adds fellowship/traineeship-supported students. RA, TA,
fellowship/traineeship, and postdoc counts remain separate. HERD total and source-
specific R&D are retained in nominal thousands and constant 2017 thousands. Derived
resource measures include trainees per $1 million real R&D, real R&D per research
trainee, and within-institution change in real R&D. IPEDS supplies enrollment,
instruction/research workforce, control, classification, and finance covariates.

## 6. Candidate publication outcomes

The predeclared primary OpenAlex outcomes are fractional institution-attributed unique
research works, field-normalized work production, and normalized or fixed-window
citation-weighted output. Full counts are a sensitivity analysis. Secondary outcomes
are team size, international collaboration, multi-institution collaboration, and open
access. Editorials, corrections, letters, reviews, and other non-research types are
excluded or separated according to `config/analysis.yml`. Total works will be called
production, never productivity.

## 7. Validation completed

- Zhang archive MD5 and SHA256 verified; two central public-data figures and six
  Poisson specifications regenerated without editing upstream `labor.R`.
- GSS 2024 reproduces exactly 635 institutions, 818,078 graduate students, 312,148
  doctoral students, and 69,877 postdocs in the referenced NCSES total.
- HERD 2024 combines 681 full-form and 244 short-form institutions and sums to
  $117,718,608,000 nominal R&D, consistent with the published $117.7 billion headline.
- Crosswalk tests prohibit the known Rutgers system aggregate and verify the seven
  named campuses.
- Schema, uniqueness, category-aggregation, and published-total tests pass.
- Source-year-variable missingness is regenerated at
  `outputs/tables/missingness_by_source_year.csv`.

## 8. Problems and decisions requiring investigator approval

1. **OpenAlex access and cost:** systematic acquisition should use an investigator-
   supplied free API key via `OPENALEX_API_KEY`. Decide API versus the much larger
   public snapshot after a measured pilot; do not commit the key.
2. **Crosswalk review:** review the 63 held-out campus/system candidates before a full
   OpenAlex pull. Auburn and the University of Colorado illustrate GSS records that
   span multiple UNITIDs and must not be assigned to the first listed campus.
3. **Rutgers boundary:** select or construct a campus-level OpenAlex attribution rule;
   the current system aggregate is intentionally blank.
4. **UC finance boundary:** campus-level GSS/HERD/IPEDS identity does not guarantee
   campus-level IPEDS finance. UCLA's 2023 finance value is missing rather than copied
   from the UC system. Approve a consistent system/campus policy before finance models.
5. **Primary window:** approve 2010–2023 as the main fully harmonized window, retaining
   2024 for labor/R&D-only updates and future IPEDS refreshes.
6. **IPEDS workforce sensitivity:** approve the documented 2012 schema bridge; it is a
   defensible workforce denominator but not a claim to measure tenure-track research
   faculty exactly.
7. **IPEDS manual checks:** schema and cross-source checks pass, but the requested
   independent Data Center comparison for ten high-profile institutions remains a
   Phase 6 task.
8. **Field panel:** the tracked field crosswalk is intentionally empty. Panel B should
   wait until institution-level OpenAlex validation passes.
9. **Zhang benchmark scope:** the public archive lacks raw annual and institution-
   identified data; the reproduced public relationships cannot validate longitudinal
   institution matches or replicate restricted AARC results.

## 9. Gate decision

Do not run Figures 2–4, fixed-effects models, nonlinear marginal-return models, or
quasi-experimental analyses yet. The next defensible milestone is a small OpenAlex
pilot covering the reviewed institutions, manual validation of at least ten
institution-years, completion of the broader institution crosswalk, and then the full
Phase 6 validation report.
