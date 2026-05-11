# Zhang et al. (2022) Replication & Extensions

## Replication of "Labor advantages drive the greater productivity of faculty at elite universities"

### Files

**Notebooks (executed, with embedded outputs):**
- `01_replication.ipynb` — Core replication: Figures 1A-D, 2A-C, Poisson regressions, matching, key stats
- `02_critical_review_extensions.ipynb` — Critical review + blueprints for 4 extensions

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

### Notes
- The replication uses Python (statsmodels, scipy, sklearn) rather than R
- Cluster-robust SEs would need manual sandwich estimation; current implementation uses conventional SEs
- Full propensity score matching (R's MatchIt) is approximated with logistic regression propensity scores
- Individual-level analyses (Tables S4-S10) require AARC Data Use Agreement
