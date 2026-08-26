# Public-data foundation: harmonized variable dictionary

All counts are institution-year aggregates. Missing values remain missing; the pipeline
does not impute them or convert them to zero. Monetary fields retain the units in their
names.

## GSS labor measures

| Harmonized variable | Definition | Availability / caveat |
|---|---|---|
| `graduate_students` | All graduate students in S&E and health fields reported by the institution's GSS organizational units. | 2008–2024. Master's and doctoral students are combined before 2017. |
| `doctoral_students` | Doctoral students only. | 2017–2024; structurally missing earlier. |
| `full_time_doctoral_students` | Full-time doctoral students. | 2017–2024; structurally missing earlier. |
| `research_assistants` | Full-time graduate students whose primary support mechanism is a research assistantship. | 2008–2024. |
| `doctoral_research_assistants` | Doctoral subset of research assistants. | 2017–2024; structurally missing earlier. |
| `teaching_assistants` | Full-time graduate students whose primary support mechanism is a teaching assistantship. | 2008–2024; retained separately from research labor. |
| `fellowship_trainee_students` | Fellowship-supported plus traineeship-supported full-time graduate students. | 2008–2024. |
| `postdocs` | Postdoctoral appointees across support sources. | 2008–2024; the 2010 postdoc frame expansion is a comparability warning. |
| `federally_supported_postdocs` | Postdocs whose support source is federal. | 2008–2024, subject to annual source availability. |
| `research_labor_core` | `research_assistants + postdocs`. | Primary labor definition. |
| `research_labor_broad` | `research_assistants + fellowship_trainee_students + postdocs`. | Planned sensitivity definition. |

The source-column mapping for each collection era is versioned in
`config/gss_variable_crosswalk.yml`. `data/metadata/gss_variable_availability.csv`
records source columns and nonmissing institution counts by year.

## HERD research resources

| Harmonized variable | Definition | Unit |
|---|---|---|
| `total_rd_nominal_thousands` | Total separately accounted-for higher-education R&D expenditures. | Current-year $1,000s. |
| `federal_rd_nominal_thousands` | R&D funded by the federal government. | Current-year $1,000s. |
| `state_local_rd_nominal_thousands` | R&D funded by state and local government. | Current-year $1,000s. |
| `business_rd_nominal_thousands` | R&D funded by business. | Current-year $1,000s. |
| `nonprofit_rd_nominal_thousands` | R&D funded by nonprofit organizations. | Current-year $1,000s; not a separate pre-2010 row. |
| `institution_rd_nominal_thousands` | R&D funded by the reporting institution. | Current-year $1,000s. |
| `*_real_2017_thousands` | Corresponding nominal measure multiplied by `100 / GDP_deflator`. | Constant 2017 $1,000s. |
| `total_rd_real_2017_thousands_change` | Within-HERD-identifier first difference in total real R&D. | Constant 2017 $1,000s. |

Status columns preserve NCSES flags such as imputed and not available. The pipeline
uses BEA NIPA table 1.1.9, series `A191RD`, matching NCSES's published constant-dollar
method. The 2010 HERD redesign expanded reporting beyond the older academic S&E R&D
concept and is a material time-series break.

## IPEDS covariates

| Harmonized variable | Complete-file source / definition | Caveat |
|---|---|---|
| `control` | HD control of institution. | Public/private classification code. |
| `degree_granting`, `graduate_offering`, `highest_degree_offered` | HD institutional characteristics. | Annual status. |
| `carnegie_basic_2005_or_2021`, `carnegie_2000` | HD Carnegie fields when supplied. | Classification editions change; not a stable R1 flag by itself. |
| `total_enrollment` | EF-A `EFALEVEL=1`, grand total. | Fall enrollment. |
| `graduate_enrollment` | EF-A `EFALEVEL=12`, graduate total. | First-professional treatment differs in early years. |
| `full_time_instruction_research_staff` | 2008–11: full-time primary instruction, combined instruction/research/public service, and primary research totals; 2012+: EAP category 20000 full-time. | Definition break in 2012. |
| `full_time_instruction_research_faculty` | Same activity scope, restricted to faculty status. | Not equivalent to tenure-track research faculty. |
| `full_time_tenured_or_tenure_track_ir_staff` | Tenured plus on-tenure-track categories within the instruction/research scope. | 2008–11 source labels are less precise; use as sensitivity covariate. |
| `full_time_primarily_research_staff` | Primary-research category, full-time. | Occupational redesign in 2012. |
| `graduate_assistants_*` | Modern EAP total/teaching/research graduate-assistant aggregates. | Available under the 2012+ schema; used for directional validation, not as the primary GSS measure. |
| `total_revenue_nominal` | F1A total revenues and additions for public institutions; F2 total revenues and investment return for private nonprofits. | Accounting forms differ; retain `finance_form`. |
| `tuition_revenue_nominal` | Net tuition and fees on F1A; total tuition and fees on F2. | Form definitions are not identical. |
| `*_appropriations_nominal` | Federal, state, and local appropriations. | Often zero/not applicable for private institutions. |
| `research_expense_nominal` | Research functional expense. | Validation/covariate only; HERD is primary R&D source. |
| `endowment_assets_end_nominal` | End-of-fiscal-year endowment assets. | Missing for institutions that report through affiliated entities or systems. |

The IPEDS cleaner prefers final/revised CSV members (`*_RV`) when historical archives
contain both provisional and revised releases. It records the release choice and
annual nonmissing counts in `data/metadata/ipeds_variable_availability.csv`.

## Planned OpenAlex outcomes (not yet analysis-ready)

The raw downloader is implemented but full acquisition is gated on the institution
crosswalk and an investigator-supplied API key. Planned institution-year outcomes are
unique research works, fractional institutional work counts, full counts, normalized
citation-weighted output, fixed-window citations where feasible, author-team size,
international collaboration, multi-institution collaboration, and open-access share.
Document-type inclusion/exclusion rules are predeclared in `config/analysis.yml`.
