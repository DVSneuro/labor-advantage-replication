from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import pandas as pd

from research_labor_returns.download.common import project_root


def main() -> None:
    root = project_root()
    archive_path = root / "data" / "raw" / "bea" / "FlatFiles.ZIP"
    if not archive_path.exists():
        raise FileNotFoundError(archive_path)
    with ZipFile(archive_path) as archive:
        annual = pd.read_csv(BytesIO(archive.read("nipadataA.txt")))
    deflator = annual.loc[annual["%SeriesCode"].eq("A191RD"), ["Period", "Value"]].copy()
    deflator = deflator.rename(
        columns={"Period": "year", "Value": "gdp_implicit_price_deflator_2017_100"}
    )
    deflator["year"] = pd.to_numeric(deflator["year"], errors="raise").astype(int)
    deflator["gdp_implicit_price_deflator_2017_100"] = pd.to_numeric(
        deflator["gdp_implicit_price_deflator_2017_100"].astype(str).str.replace(",", ""),
        errors="raise",
    )
    deflator["to_constant_2017_dollars"] = 100 / deflator["gdp_implicit_price_deflator_2017_100"]
    required = set(range(2008, 2025))
    missing = sorted(required - set(deflator["year"]))
    if missing:
        raise RuntimeError(f"BEA GDP deflator is missing analysis years: {missing}")
    output = root / "data" / "processed" / "bea_gdp_deflator.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    deflator.sort_values("year").to_parquet(output, index=False)
    deflator.loc[deflator["year"].isin(required)].to_csv(
        root / "data" / "metadata" / "bea_gdp_deflator_2017_dollars.csv", index=False
    )
    print("Cleaned BEA GDP implicit price deflator (2017=100)")


if __name__ == "__main__":
    main()
