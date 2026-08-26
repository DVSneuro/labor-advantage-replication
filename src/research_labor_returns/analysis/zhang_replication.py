from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from research_labor_returns.download.common import project_root

COLLAB_LABELS = {True: "Disciplines with collaboration norms", False: "Other disciplines"}
COLORS = {True: "#fc8d62", False: "#66c2a5"}


def zhang_data_dir() -> Path:
    path = project_root() / "data" / "raw" / "zhang2022" / "code-and-data"
    if not path.exists():
        raise FileNotFoundError("Run `make download-zhang` before reproducing Zhang et al.")
    return path


def labor_by_prestige(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["AreaHasCollabNorm", "prestige_segment_equispaced"], as_index=False)
        .agg(ft_funded=("ft_funded", "sum"), tt_headcount=("tt_headcount", "sum"))
        .assign(funded_labor_per_faculty=lambda data: data.ft_funded / data.tt_headcount)
    )


def plot_labor_by_prestige(frame: pd.DataFrame, destination: Path) -> None:
    summary = labor_by_prestige(frame)
    fig, axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    for group, values in summary.groupby("AreaHasCollabNorm"):
        axis.plot(
            values["prestige_segment_equispaced"],
            values["funded_labor_per_faculty"],
            marker="o",
            linewidth=2.2,
            color=COLORS[bool(group)],
            label=COLLAB_LABELS[bool(group)],
        )
    axis.set(
        xlabel="Prestige decile (higher is more prestigious)",
        ylabel="Funded researchers per faculty",
    )
    axis.set_xticks(range(1, 11))
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=300)
    plt.close(fig)


def plot_group_size_productivity(frame: pd.DataFrame, destination: Path) -> None:
    fig, axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    labels = {0: "Lower-prestige half", 1: "Higher-prestige half"}
    colors = {0: "#333333", 1: "#fc8d62"}
    for group, values in frame.groupby("prestige_top_half"):
        values = values.sort_values("CumulativeGroupSize")
        x = values["CumulativeGroupSize"].to_numpy(dtype=float)
        mean = values["mean"].to_numpy(dtype=float)
        sem = values["sem"].to_numpy(dtype=float)
        axis.plot(x, mean, linewidth=2.2, color=colors[int(group)], label=labels[int(group)])
        axis.fill_between(
            x, mean - 1.96 * sem, mean + 1.96 * sem, color=colors[int(group)], alpha=0.2
        )
    axis.set(xlabel="Cumulative group size", ylabel="Cumulative group productivity")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=300)
    plt.close(fig)


def fit_public_poisson_models(frame: pd.DataFrame) -> pd.DataFrame:
    formula_template = (
        "{outcome} ~ scale_log_funded_per_faculty_p1 + scale_uniform_percentile100 + "
        "scale_log_unfunded_per_faculty_p1 + scale_tt_headcount + CONTROL + C(Area)"
    )
    rows = []
    for collaboration_norm in [True, False]:
        subset = frame.loc[frame["AreaHasCollabNorm"].eq(collaboration_norm)].copy()
        for outcome in ["Productivity", "ProductivityWithDeptCollabs", "WindowedGroupSize"]:
            model = smf.glm(
                formula=formula_template.format(outcome=outcome),
                data=subset,
                family=sm.families.Poisson(),
            ).fit(cov_type="cluster", cov_kwds={"groups": subset["Area"]})
            for term in ["scale_log_funded_per_faculty_p1", "scale_uniform_percentile100"]:
                rows.append(
                    {
                        "collaboration_norm": collaboration_norm,
                        "outcome": outcome,
                        "term": term,
                        "estimate": model.params[term],
                        "std_error_clustered_by_discipline": model.bse[term],
                        "p_value": model.pvalues[term],
                        "n": int(model.nobs),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    data_dir = zhang_data_dir()
    figures = project_root() / "outputs" / "figures"
    tables = project_root() / "outputs" / "tables"
    funding = pd.read_csv(data_dir / "funding_by_segment_clean.csv")
    group_productivity = pd.read_csv(data_dir / "gs_vs_cumprod.csv")
    strict = pd.read_csv(data_dir / "area-strict.csv")
    plot_labor_by_prestige(funding, figures / "zhang_funded_labor_by_prestige.png")
    plot_group_size_productivity(group_productivity, figures / "zhang_group_size_productivity.png")
    coefficients = fit_public_poisson_models(strict)
    tables.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(tables / "zhang_public_poisson_coefficients.csv", index=False)
    print("Reproduced two central public figures and six public-data Poisson specifications")


if __name__ == "__main__":
    main()
