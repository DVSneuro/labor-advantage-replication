from __future__ import annotations

import argparse
import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from research_labor_returns.download.common import project_root

SOURCE_ROWS = {
    "total_rd_nominal_thousands": {"total"},
    "federal_rd_nominal_thousands": {"federal", "federal government"},
    "state_local_rd_nominal_thousands": {"state and local government"},
    "business_rd_nominal_thousands": {"business", "industry"},
    "nonprofit_rd_nominal_thousands": {"nonprofit organizations"},
    "institution_rd_nominal_thousands": {"institution funds", "institution funds, total"},
    "other_rd_nominal_thousands": {"all other sources"},
}


def _read_csv_from_zip(archive: Path) -> pd.DataFrame:
    with zipfile.ZipFile(archive) as bundle:
        names = [name for name in bundle.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise RuntimeError(f"Expected one CSV in {archive}, found {names}")
        with bundle.open(names[0]) as stream:
            # Older NCSES files contain Windows-1252 punctuation in institution names.
            return pd.read_csv(io.BytesIO(stream.read()), encoding="cp1252", low_memory=False)


def clean_year(archive: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = _read_csv_from_zip(archive)
    required = {"year", "inst_name_long", "question", "row", "data", "status"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f"HERD columns missing in {year}: {missing}")
    id_candidates = ["inst_id", "fice"]
    id_column = next((name for name in id_candidates if name in raw), None)
    if id_column is None:
        raise RuntimeError(f"No recognized HERD institution identifier in {year}")
    source = raw.loc[raw["question"].eq("Source")].copy()
    source["row_normalized"] = source["row"].astype(str).str.strip().str.casefold()
    keys = [id_column, "year", "inst_name_long"]
    optional_ids = [
        name for name in ["ncses_inst_id", "ipeds_unitid", "fice_combined"] if name in source
    ]
    result = source[keys + optional_ids].drop_duplicates(subset=[id_column, "year"]).copy()
    result = result.rename(
        columns={id_column: "herd_institution_id", "inst_name_long": "institution_name"}
    )
    for output_name, labels in SOURCE_ROWS.items():
        values = source.loc[
            source["row_normalized"].isin(labels), [id_column, "year", "data", "status"]
        ]
        duplicate = values.duplicated([id_column, "year"], keep=False)
        if duplicate.any():
            raise RuntimeError(f"Duplicate HERD Source row for {output_name} in {year}")
        values = values.rename(columns={"data": output_name, "status": f"{output_name}_status"})
        result = result.merge(
            values,
            how="left",
            left_on=["herd_institution_id", "year"],
            right_on=[id_column, "year"],
        )
        result = result.drop(columns=[id_column], errors="ignore")
    result["year"] = pd.to_numeric(result["year"], errors="raise").astype(int)
    result["source_values_in_thousands"] = True
    result["real_dollar_values_available"] = False
    availability = pd.DataFrame(
        {
            "source": "HERD",
            "year": year,
            "variable": list(SOURCE_ROWS),
            "source_rows": ["|".join(sorted(value)) for value in SOURCE_ROWS.values()],
            "structurally_available": [
                source["row_normalized"].isin(labels).any() for labels in SOURCE_ROWS.values()
            ],
            "institutions_nonmissing": [int(result[name].notna().sum()) for name in SOURCE_ROWS],
            "institutions_total": len(result),
        }
    )
    return result, availability


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonize annual HERD Source rows")
    parser.add_argument("--raw-dir", type=Path, default=project_root() / "data" / "raw" / "herd")
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root() / "data" / "processed" / "herd_institution_year.parquet",
    )
    args = parser.parse_args()
    archives = sorted(args.raw_dir.glob("higher_education_r_and_d_*.zip"))
    if not archives:
        raise FileNotFoundError(f"No annual HERD archives found under {args.raw_dir}")
    panels = []
    availability = []
    by_year: dict[int, list[Path]] = {}
    for archive in archives:
        match = re.search(r"_(\d{4})(?:_short)?$", archive.stem)
        if not match:
            raise RuntimeError(f"Could not parse HERD year from {archive.name}")
        by_year.setdefault(int(match.group(1)), []).append(archive)
    for year, year_archives in sorted(by_year.items()):
        parts = [clean_year(archive, year) for archive in year_archives]
        panel_year = pd.concat([part[0] for part in parts], ignore_index=True)
        duplicate = panel_year.duplicated(["herd_institution_id", "year"], keep=False)
        if duplicate.any():
            raise RuntimeError(f"HERD full/short files overlap in {year}")
        available_year = pd.concat([part[1] for part in parts], ignore_index=True)
        available_year = available_year.groupby(
            ["source", "year", "variable", "source_rows"], as_index=False
        ).agg(
            structurally_available=("structurally_available", "max"),
            institutions_nonmissing=("institutions_nonmissing", "sum"),
            institutions_total=("institutions_total", "sum"),
        )
        panels.append(panel_year)
        availability.append(available_year)
        print(f"HERD {year}: {len(panel_year):,} reporting institutions")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel = pd.concat(panels, ignore_index=True).sort_values(["herd_institution_id", "year"])
    deflator_path = project_root() / "data" / "processed" / "bea_gdp_deflator.parquet"
    if not deflator_path.exists():
        raise FileNotFoundError(
            f"Run research_labor_returns.clean.deflators before cleaning HERD: {deflator_path}"
        )
    deflator = pd.read_parquet(deflator_path)
    panel = panel.merge(deflator, on="year", how="left", validate="many_to_one")
    if panel["to_constant_2017_dollars"].isna().any():
        raise RuntimeError("HERD contains a year without a BEA GDP deflator")
    for nominal in SOURCE_ROWS:
        real = nominal.replace("_nominal_thousands", "_real_2017_thousands")
        panel[real] = panel[nominal] * panel["to_constant_2017_dollars"]
    panel["real_dollar_values_available"] = True
    panel["total_rd_real_2017_thousands_change"] = panel.groupby("herd_institution_id")[
        "total_rd_real_2017_thousands"
    ].diff()
    panel.to_parquet(args.output, index=False)
    availability_path = project_root() / "data" / "metadata" / "herd_variable_availability.csv"
    availability_path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(availability, ignore_index=True).to_csv(availability_path, index=False)


if __name__ == "__main__":
    main()
