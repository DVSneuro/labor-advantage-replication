# Zhang et al. (2022) Replication & Extensions

## Replication of "Labor advantages drive the greater productivity of faculty at elite universities"

### Files

**Notebooks (executed, with embedded outputs):**
- `01_replication.ipynb` — Core replication: Figures 1A-D, 2A-C, Poisson regressions, matching, key stats
- `02_critical_review_extensions.ipynb` — Critical review + blueprints for 4 extensions
- `05_temple_impact_analysis.ipynb` — Temple-focused training grant and impact analysis

**R analyses:**
- `06_under_overperformers.R` — Named NIH training-output over/underperformer scorecard, Temple labor-obligation profile, and anonymized Zhang productivity residuals

**Python source files (for editing):**
- `01_replication.py` — Same as notebook 1, in script format (convert with `jupytext --to notebook`)
- `02_extensions.py` — Same as notebook 2

**Data (from Zenodo 10.5281/zenodo.7126263):**
- `code-and-data/` — Original CSV files and R script

**Generated figures:**
- `fig1_panels_AB.png` — Faculty vs group member productivity by prestige; decomposition by collab norms
- `fig1_panels_CD.png` — Funded labor per faculty by prestige decile
- `fig2A_coefficients.png` — Poisson regression coefficient plot
- `fig2B_matching.png` — Mid-career matching results (group size before/after move)
- `fig2C_cumprod.png` — Cumulative group size vs cumulative group productivity
- `ext1_temporal_proxy.png` — Cross-sectional proxy for temporal analysis
- `ext2_vpr_proxy.png` — Productivity variance by prestige (VPR proxy)
- `ext4_inefficiency.png` — Scatter identifying high-labor/low-productivity departments
- `figures/under_over_temple_labor_mix.png` — Temple's doctoral funding mix vs. same-Carnegie peers
- `figures/under_over_fellowship_residuals.png` — Named institution F31/F32 residual over/underperformers
- `figures/under_over_zhang_anonymous_residuals.png` — Anonymous Zhang productivity residuals

**Generated scorecards:**
- `outputs/under_overperformers/institution_training_scorecard.csv`
- `outputs/under_overperformers/temple_summary.csv`
- `outputs/under_overperformers/zhang_department_residuals_anonymized.csv`
- `outputs/under_overperformers/under_overperformer_summary.md`

### Notes
- The replication uses Python (statsmodels, scipy, sklearn) rather than R
- Cluster-robust SEs would need manual sandwich estimation; current implementation uses conventional SEs
- Full propensity score matching (R's MatchIt) is approximated with logistic regression propensity scores
- Individual-level analyses (Tables S4-S10) require AARC Data Use Agreement
