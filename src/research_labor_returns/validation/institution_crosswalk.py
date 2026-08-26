from __future__ import annotations

from pathlib import Path

import pandas as pd

from research_labor_returns.download.common import project_root

EXPECTED_UNITIDS = {
    "Temple University": "216339",
    "Rutgers University-New Brunswick": "186380",
    "University of Illinois Chicago": "145600",
    "University of California Los Angeles": "110662",
    "University of Michigan-Ann Arbor": "170976",
    "University of Wisconsin-Madison": "240444",
    "The Ohio State University-Main Campus": "204796",
}


def validate(path: Path) -> None:
    crosswalk = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {
        "canonical_institution_name",
        "ipeds_unitid",
        "gss_identifier",
        "herd_identifier",
        "openalex_institution_id",
        "ror_id",
        "historical_institution_names",
        "system_campus_notes",
        "first_valid_year",
        "last_valid_year",
        "manually_reviewed_flag",
    }
    missing = sorted(required - set(crosswalk.columns))
    if missing:
        raise AssertionError(f"Crosswalk columns missing: {missing}")
    if crosswalk["canonical_institution_name"].duplicated().any():
        raise AssertionError("Duplicate canonical institution names")
    for column in ["ipeds_unitid", "gss_identifier", "herd_identifier", "ror_id"]:
        values = crosswalk.loc[crosswalk[column].ne(""), column]
        if values.duplicated().any():
            raise AssertionError(f"Duplicate nonempty identifier in {column}")
    indexed = crosswalk.set_index("canonical_institution_name")
    for name, unitid in EXPECTED_UNITIDS.items():
        if name not in indexed.index:
            raise AssertionError(f"Required identity test row is missing: {name}")
        if indexed.at[name, "ipeds_unitid"] != unitid:
            raise AssertionError(f"{name} resolved to the wrong IPEDS UNITID")
        if indexed.at[name, "manually_reviewed_flag"].casefold() != "true":
            raise AssertionError(f"{name} has not been manually reviewed")
        if not indexed.at[name, "system_campus_notes"]:
            raise AssertionError(f"{name} lacks a system/campus decision note")
    if indexed.at["Rutgers University-New Brunswick", "openalex_institution_id"]:
        raise AssertionError("Rutgers system-level OpenAlex ID must not be used for New Brunswick")


def main() -> None:
    path = project_root() / "data" / "crosswalks" / "institution_crosswalk.csv"
    validate(path)
    print(f"Institution crosswalk validation passed: {path}")


if __name__ == "__main__":
    main()
