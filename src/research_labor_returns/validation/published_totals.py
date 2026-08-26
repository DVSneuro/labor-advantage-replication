from __future__ import annotations

import math

import pandas as pd

from research_labor_returns.download.common import project_root

# NCSES GSS 2024 table 2-1, NSF 26-307.
GSS_2024_TOTALS = {
    "graduate_students": 818_078,
    "doctoral_students": 312_148,
    "postdocs": 69_877,
}

# Summed from the HERD 2024 public standard and short forms. The published headline
# rounds total R&D to $117.7 billion, so the exact public-file sum is the test target.
HERD_2024_TOTAL_RD_THOUSANDS = 117_718_608


def main() -> None:
    processed = project_root() / "data" / "processed"
    gss = pd.read_parquet(processed / "gss_institution_year.parquet")
    gss_2024 = gss.loc[gss["year"].eq(2024)]
    if len(gss_2024) != 635:
        raise AssertionError(
            f"Expected 635 GSS reporting institutions in 2024, got {len(gss_2024)}"
        )
    for variable, expected in GSS_2024_TOTALS.items():
        actual = int(gss_2024[variable].sum())
        if actual != expected:
            raise AssertionError(f"GSS 2024 {variable}: expected {expected:,}, got {actual:,}")

    herd = pd.read_parquet(processed / "herd_institution_year.parquet")
    herd_2024 = herd.loc[herd["year"].eq(2024)]
    if len(herd_2024) != 925:
        raise AssertionError(
            f"Expected 925 HERD standard+short reporting institutions in 2024, got {len(herd_2024)}"
        )
    actual_rd = herd_2024["total_rd_nominal_thousands"].sum()
    if not math.isclose(actual_rd, HERD_2024_TOTAL_RD_THOUSANDS, abs_tol=0.5):
        raise AssertionError(
            f"HERD 2024 total R&D: expected {HERD_2024_TOTAL_RD_THOUSANDS:,}, got {actual_rd:,}"
        )
    print("Published-total validation passed for GSS and HERD 2024")


if __name__ == "__main__":
    main()
