from __future__ import annotations

import pandas as pd

from research_labor_returns.download.common import project_root

IDENTIFIERS = {
    "GSS": {
        "institution_id",
        "unitid",
        "year",
        "institution_name",
        "state",
        "heading_institution_code",
        "control_code",
        "reported_units",
        "doctoral_counts_available",
    },
    "HERD": {
        "herd_institution_id",
        "year",
        "institution_name",
        "ncses_inst_id",
        "ipeds_unitid",
        "fice_combined",
        "source_values_in_thousands",
        "real_dollar_values_available",
    },
    "IPEDS": {
        "unitid",
        "year",
        "institution_name_ipeds",
        "directory_final_revised_file",
        "enrollment_final_revised_file",
        "employees_schema",
        "employees_final_revised_file",
        "finance_form",
        "finance_final_revised_file",
    },
}


def _summarize(source: str, frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    variables = [
        name
        for name in frame.columns
        if name not in IDENTIFIERS[source] and not name.endswith("_status")
    ]
    for year, year_frame in frame.groupby("year"):
        for variable in variables:
            missing = int(year_frame[variable].isna().sum())
            structural_reason = ""
            if (
                source == "GSS"
                and variable
                in {
                    "doctoral_students",
                    "full_time_doctoral_students",
                    "doctoral_research_assistants",
                }
                and year < 2017
            ):
                structural_reason = "Not collected separately from master's students before 2017"
            if source == "HERD" and variable == "nonprofit_rd_nominal_thousands" and year < 2010:
                structural_reason = "Not collected as a separate source before the HERD redesign"
            rows.append(
                {
                    "source": source,
                    "year": int(year),
                    "variable": variable,
                    "institutions_total": len(year_frame),
                    "institutions_nonmissing": len(year_frame) - missing,
                    "institutions_missing": missing,
                    "proportion_missing": missing / len(year_frame),
                    "structural_missingness_reason": structural_reason,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    root = project_root()
    processed = root / "data" / "processed"
    tables = root / "outputs" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    gss = pd.read_parquet(processed / "gss_institution_year.parquet")
    herd = pd.read_parquet(processed / "herd_institution_year.parquet")
    ipeds = pd.read_parquet(processed / "ipeds_institution_year.parquet")
    report = pd.concat(
        [_summarize("GSS", gss), _summarize("HERD", herd), _summarize("IPEDS", ipeds)],
        ignore_index=True,
    )
    report.to_csv(tables / "missingness_by_source_year.csv", index=False)
    print(f"Wrote {len(report):,} source-year-variable missingness rows")


if __name__ == "__main__":
    main()
