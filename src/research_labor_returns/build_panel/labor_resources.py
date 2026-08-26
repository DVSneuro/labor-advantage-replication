from __future__ import annotations

import numpy as np
import pandas as pd

from research_labor_returns.download.common import project_root


def _identifier(values: pd.Series) -> pd.Series:
    result = pd.to_numeric(values, errors="coerce").astype("Int64").astype("string")
    return result.mask(result.eq("999999"))


def _apply_reviewed_overrides(
    frame: pd.DataFrame, source_id: str, unitid: str, crosswalk_id: str, crosswalk: pd.DataFrame
) -> pd.DataFrame:
    reviewed = crosswalk.loc[
        crosswalk["manually_reviewed_flag"].str.casefold().eq("true")
        & crosswalk[crosswalk_id].ne("")
        & crosswalk["ipeds_unitid"].ne(""),
        [crosswalk_id, "ipeds_unitid"],
    ]
    mapping = reviewed.set_index(crosswalk_id)["ipeds_unitid"]
    missing = frame[unitid].isna()
    frame.loc[missing, unitid] = frame.loc[missing, source_id].astype("string").map(mapping)
    return frame


def main() -> None:
    root = project_root()
    processed = root / "data" / "processed"
    crosswalk = pd.read_csv(
        root / "data" / "crosswalks" / "institution_crosswalk.csv",
        dtype=str,
        keep_default_na=False,
    )
    gss = pd.read_parquet(processed / "gss_institution_year.parquet")
    herd = pd.read_parquet(processed / "herd_institution_year.parquet")
    ipeds = pd.read_parquet(processed / "ipeds_institution_year.parquet")
    gss["unitid"] = _identifier(gss["unitid"])
    herd["unitid"] = _identifier(herd["ipeds_unitid"])
    ipeds["unitid"] = _identifier(ipeds["unitid"])
    gss = _apply_reviewed_overrides(gss, "institution_id", "unitid", "gss_identifier", crosswalk)
    herd["herd_institution_id"] = herd["herd_institution_id"].astype("string")
    herd = _apply_reviewed_overrides(
        herd, "herd_institution_id", "unitid", "herd_identifier", crosswalk
    )
    for name, frame in [("GSS", gss), ("HERD", herd)]:
        usable = frame.loc[frame["unitid"].notna()]
        duplicate = usable.duplicated(["unitid", "year"], keep=False)
        if duplicate.any():
            examples = usable.loc[duplicate, ["unitid", "year"]].drop_duplicates().head()
            raise RuntimeError(f"{name} has duplicate UNITID-years:\n{examples}")

    gss_usable = gss.loc[gss["unitid"].notna()].copy()
    herd_usable = herd.loc[herd["unitid"].notna()].copy()
    source_counts = (
        gss.groupby("year")
        .size()
        .rename("gss_total")
        .to_frame()
        .join(herd.groupby("year").size().rename("herd_total"), how="outer")
        .join(gss_usable.groupby("year").size().rename("gss_identified"), how="outer")
        .join(herd_usable.groupby("year").size().rename("herd_identified"), how="outer")
        .reset_index()
    )
    merged = gss_usable.merge(
        herd_usable,
        on=["unitid", "year"],
        how="outer",
        suffixes=("_gss", "_herd"),
        indicator=True,
        validate="one_to_one",
    )
    match_rates = (
        merged.groupby(["year", "_merge"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"both": "matched", "left_only": "gss_only", "right_only": "herd_only"})
    )
    match_rates = source_counts.merge(match_rates, on="year", how="left", validate="one_to_one")
    for column in ["matched", "gss_only", "herd_only"]:
        if column not in match_rates:
            match_rates[column] = 0
    match_rates["gss_identifier_coverage"] = (
        match_rates["gss_identified"] / match_rates["gss_total"]
    )
    match_rates["herd_identifier_coverage"] = (
        match_rates["herd_identified"] / match_rates["herd_total"]
    )
    match_rates["gss_match_rate"] = match_rates["matched"] / match_rates["gss_total"]
    match_rates["herd_match_rate"] = match_rates["matched"] / match_rates["herd_total"]
    match_rates["gss_identified_match_rate"] = (
        match_rates["matched"] / match_rates["gss_identified"]
    )
    match_rates["herd_identified_match_rate"] = (
        match_rates["matched"] / match_rates["herd_identified"]
    )
    # Before 2010, the public HERD files lack UNITIDs and only a handful of
    # institutions can be linked using reviewed overrides. Treat 2010 as the
    # start of the deterministic panel rather than presenting those sparse
    # overrides as representative coverage.
    panel = (
        merged.loc[merged["_merge"].eq("both") & merged["year"].ge(2010)]
        .drop(columns="_merge")
        .copy()
    )
    panel = panel.merge(ipeds, on=["unitid", "year"], how="left", validate="one_to_one")
    panel["ipeds_matched"] = panel["institution_name_ipeds"].notna()
    rd_millions = panel["total_rd_nominal_thousands"] / 1_000
    panel["research_labor_per_million_nominal_rd"] = panel["research_labor_core"] / rd_millions
    panel["nominal_rd_per_research_trainee"] = (
        panel["total_rd_nominal_thousands"] * 1_000 / panel["research_labor_core"]
    )
    real_rd_millions = panel["total_rd_real_2017_thousands"] / 1_000
    panel["research_labor_per_million_real_2017_rd"] = (
        panel["research_labor_core"] / real_rd_millions
    )
    panel["real_2017_rd_per_research_trainee"] = (
        panel["total_rd_real_2017_thousands"] * 1_000 / panel["research_labor_core"]
    )
    for column in [
        "research_labor_per_million_nominal_rd",
        "nominal_rd_per_research_trainee",
        "research_labor_per_million_real_2017_rd",
        "real_2017_rd_per_research_trainee",
    ]:
        panel.loc[~np.isfinite(panel[column]), column] = np.nan
    panel.sort_values(["unitid", "year"]).to_parquet(
        processed / "labor_resources_institution_year.parquet", index=False
    )
    tables = root / "outputs" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    match_rates.to_csv(tables / "gss_herd_match_rates_by_year.csv", index=False)
    print(
        f"Built labor/resource foundation with {panel['unitid'].nunique():,} institutions "
        f"and {len(panel):,} institution-years"
    )


if __name__ == "__main__":
    main()
