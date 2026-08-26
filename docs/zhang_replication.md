# Zhang et al. (2022) public replication audit

## Source and integrity

- Article: Zhang, Wapman, Larremore, and Clauset (2022), *Science Advances*,
  DOI [10.1126/sciadv.abq7056](https://doi.org/10.1126/sciadv.abq7056).
- Public archive: Zenodo DOI
  [10.5281/zenodo.7126263](https://doi.org/10.5281/zenodo.7126263), published
  2022-09-29 under CC BY 4.0.
- Archive file: `code-and-data.tar.gz`, 317,870 bytes.
- Upstream MD5: `1a41f29c40077646c9eece9c86bd3bb1`.
- Verified SHA256: `ed022bc83b6081549b186dcce6badd747d24b172484950d61666af9928400137`.

`research_labor_returns.download.zhang` queries the Zenodo record API, verifies that
the advertised checksum has not changed, streams the archive, verifies the downloaded
file, records retrieval metadata, and unpacks it into `data/raw/zhang2022/`.

## What the public archive contains

The archive has seven CSV files and one R script. It does **not** contain a separate
README, formal data dictionary, package lockfile, named institution crosswalk, or raw
annual observations.

| File | Rows | Unit / role |
|---|---:|---|
| `area-strict.csv` | 739 | One anonymized linked discipline-department row; 15 disciplines. |
| `area-non-strict.csv` | 1,800 | Broader anonymized discipline-department linkage; 17 disciplines. |
| `funding_by_segment_clean.csv` | 170 | Discipline by prestige-decile labor totals. |
| `prod_by_decile.csv` | 20 | Prestige decile by faculty/nonfaculty job group. |
| `decomp_by_decile.csv` | 40 | Prestige decile by collaboration-norm group and productivity component. |
| `gs_vs_cumprod.csv` | 42 | Cumulative group-size bin by high/low prestige half. |
| `moves.csv` | 684 | Anonymized before/after faculty-move record (`PersonId` is not an institution ID). |

The paper-level study covers 2008-2017, but the released department tables are
cross-sectional averages. They cannot support institution-year models.

### Identifiers and disciplines

The public CSVs do not contain institution names, IPEDS UNITIDs, ROR IDs, OpenAlex
IDs, or a stable anonymous institution ID. `Area` is a discipline label rather than an
institution identifier. `area-strict.csv` covers Agriculture, Anthropology, Biological
Sciences, Chemical Sciences, Computational Sciences, Economics, Engineering,
Geography, Health, Mathematical Sciences, Medical Sciences, Physical Sciences,
Political Science, Psychological Sciences, and Sociology. The non-strict file adds
Architecture/Design/Planning and Earth Sciences.

### Labor, prestige, and outcome variables

- Labor: graduate students per faculty; funded and unfunded labor per faculty; funded
  and unfunded headcounts in the aggregated decile file; windowed, annual, and
  cumulative group-size measures.
- Prestige: `uniform_percentile` / `uniform_percentile100`, prestige segments,
  deciles, and high/low or top-half flags. The public archive does not identify the
  institution attached to a score.
- Production/productivity: annual faculty publications, publications involving
  department collaborators, publications excluding them, first-/last-author outcomes,
  and group productivity. The archive calls the per-faculty publication measure
  productivity; the new project preserves the production/productivity distinction.
- Other covariates: tenure-track headcount, private-control flag, discipline, and
  collaboration-norm flag.

## Original-code compatibility audit

The upstream `labor.R` is retained byte-for-byte. It is not silently patched. A clean,
top-to-bottom run is blocked by:

1. references to undefined objects (`area_raw` and `area.nocollabnorm`);
2. no recorded R/package versions despite a large dependency set;
3. output paths that are not created by the script; and
4. a final macOS-only `quartz()` device call.

The reproducible benchmark therefore uses a small cross-platform Python script against
the unmodified public CSVs. This is a compatibility implementation, not a claim that
the full private-data paper has been reproduced.

## Reproduced public results

Run:

```bash
make download-zhang
make reproduce-zhang
```

This regenerates:

- `outputs/figures/zhang_funded_labor_by_prestige.png`: the concentration of funded
  graduate researchers and postdocs across prestige deciles, computed as the ratio of
  summed funded labor to summed tenure-track faculty within each decile and
  collaboration-norm stratum.
- `outputs/figures/zhang_group_size_productivity.png`: cumulative group productivity
  over cumulative group size for the lower- and higher-prestige halves.
- `outputs/tables/zhang_public_poisson_coefficients.csv`: the funded-labor and prestige
  coefficients from six Poisson specifications using discipline fixed effects and
  standard errors clustered by discipline.

These outputs reproduce the archive's central public-data relationships: funded labor
is concentrated toward higher prestige, and larger cumulative groups are associated
with greater cumulative group production. They do not reproduce the restricted AARC
individual-level tables or establish causal effects.
