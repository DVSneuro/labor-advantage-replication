from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import yaml

from research_labor_returns.download.common import project_root

IDENTITY_COLUMNS = [
    "institution_id",
    "UNITID",
    "year",
    "Institution_Name",
    "institution_state",
    "hdg_inst",
    "toc_code",
]


def _era(year: int, crosswalk: dict) -> dict:
    matches = [item for item in crosswalk["eras"] if item["start"] <= year <= item["end"]]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one GSS crosswalk era for {year}, found {len(matches)}")
    return matches[0]["variables"]


def _read_sas_from_zip(archive: Path) -> pd.DataFrame:
    with zipfile.ZipFile(archive) as bundle:
        names = [name for name in bundle.namelist() if name.lower().endswith("_code.sas7bdat")]
        if len(names) != 1:
            raise RuntimeError(f"Expected one *_code.sas7bdat in {archive}, found {names}")
        with tempfile.TemporaryDirectory(prefix="gss-") as temporary:
            target = Path(temporary) / Path(names[0]).name
            with bundle.open(names[0]) as source, target.open("wb") as destination:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    destination.write(block)
            return pd.read_sas(target, format="sas7bdat", encoding="latin1")


def _sum_components(frame: pd.DataFrame, columns: list[str] | None) -> pd.Series:
    if columns is None:
        return pd.Series(pd.NA, index=frame.index, dtype="Float64")
    missing = [name for name in columns if name not in frame.columns]
    if missing:
        raise RuntimeError(f"GSS source columns missing: {missing}")
    values = frame[columns].apply(pd.to_numeric, errors="coerce")
    return values.sum(axis=1, min_count=len(columns)).astype("Float64")


def _valid_unitids(values: pd.Series) -> list[str]:
    identifiers = values.dropna().astype("Int64").astype("string")
    return sorted(set(identifiers.loc[identifiers.ne("999999")]))


def clean_year(archive: Path, year: int, variables: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = _read_sas_from_zip(archive)
    missing_identity = [name for name in IDENTITY_COLUMNS if name not in raw.columns]
    if missing_identity:
        raise RuntimeError(f"GSS identity columns missing in {year}: {missing_identity}")
    unit = raw[IDENTITY_COLUMNS].copy()
    unit["institution_id"] = pd.to_numeric(unit["institution_id"], errors="raise").astype("Int64")
    unit["UNITID"] = pd.to_numeric(unit["UNITID"], errors="coerce").astype("Int64")
    unit["year"] = pd.to_numeric(unit["year"], errors="raise").astype(int)
    if not unit["year"].eq(year).all():
        raise RuntimeError(f"GSS archive year and internal year disagree for {year}")
    for output_name, source_columns in variables.items():
        unit[output_name] = _sum_components(raw, source_columns)

    numeric = list(variables)
    keys = ["institution_id", "year"]
    names = unit.groupby(keys, dropna=False)["Institution_Name"].nunique(dropna=True)
    if (names > 1).any():
        raise RuntimeError(f"Multiple GSS institution names within a reporting ID/year in {year}")
    result = unit.groupby(keys, as_index=False, dropna=False).agg(
        unitids=("UNITID", lambda values: "|".join(_valid_unitids(values))),
        unitid_count=("UNITID", lambda values: len(_valid_unitids(values))),
        institution_name=("Institution_Name", "first"),
        state=("institution_state", "first"),
        heading_institution_code=("hdg_inst", "first"),
        control_code=("toc_code", "first"),
        reported_units=("Institution_Name", "size"),
        **{name: (name, lambda values: values.sum(min_count=1)) for name in numeric},
    )
    result["institution_id"] = result["institution_id"].astype("string")
    result["unitid"] = result["unitids"].where(result["unitid_count"].eq(1), pd.NA).astype("string")
    result["fellowship_trainee_students"] = result["fellowship_students"].add(
        result["traineeship_students"], fill_value=None
    )
    result["research_labor_core"] = result["research_assistants"].add(
        result["postdocs"], fill_value=None
    )
    result["research_labor_broad"] = (
        result["research_assistants"] + result["fellowship_trainee_students"] + result["postdocs"]
    )
    result["doctoral_counts_available"] = variables["doctoral_students"] is not None

    availability = pd.DataFrame(
        {
            "source": "GSS",
            "year": year,
            "variable": list(variables),
            "source_columns": [
                "|".join(columns) if columns is not None else "" for columns in variables.values()
            ],
            "structurally_available": [columns is not None for columns in variables.values()],
            "institutions_nonmissing": [int(result[name].notna().sum()) for name in variables],
            "institutions_total": len(result),
        }
    )
    return result, availability


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonize annual GSS files to institution-year")
    parser.add_argument("--raw-dir", type=Path, default=project_root() / "data" / "raw" / "gss")
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root() / "data" / "processed" / "gss_institution_year.parquet",
    )
    args = parser.parse_args()
    with (project_root() / "config" / "gss_variable_crosswalk.yml").open(
        encoding="utf-8"
    ) as stream:
        crosswalk = yaml.safe_load(stream)
    archives = sorted(args.raw_dir.glob("graduate_students_postdocs_*.zip"))
    if not archives:
        raise FileNotFoundError(f"No annual GSS archives found under {args.raw_dir}")
    panels = []
    availability = []
    for archive in archives:
        year = int(archive.stem.rsplit("_", 1)[-1])
        panel_year, available_year = clean_year(archive, year, _era(year, crosswalk))
        panels.append(panel_year)
        availability.append(available_year)
        print(f"GSS {year}: {len(panel_year):,} reporting institutions")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(panels, ignore_index=True).sort_values(["institution_id", "year"]).to_parquet(
        args.output, index=False
    )
    availability_path = project_root() / "data" / "metadata" / "gss_variable_availability.csv"
    availability_path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(availability, ignore_index=True).to_csv(availability_path, index=False)


if __name__ == "__main__":
    main()
