from __future__ import annotations

from pathlib import Path

import pandas as pd

from research_labor_returns.download.common import project_root

SCHEMAS = {
    "gss_institution_year.parquet": (
        "institution_id",
        {
            "institution_id",
            "unitid",
            "year",
            "research_assistants",
            "teaching_assistants",
            "fellowship_trainee_students",
            "postdocs",
            "research_labor_core",
            "research_labor_broad",
        },
    ),
    "herd_institution_year.parquet": (
        "herd_institution_id",
        {
            "herd_institution_id",
            "year",
            "total_rd_nominal_thousands",
            "federal_rd_nominal_thousands",
            "institution_rd_nominal_thousands",
        },
    ),
    "ipeds_institution_year.parquet": (
        "unitid",
        {
            "unitid",
            "year",
            "graduate_enrollment",
            "full_time_instruction_research_staff",
            "total_revenue_nominal",
            "research_expense_nominal",
        },
    ),
    "labor_resources_institution_year.parquet": (
        "unitid",
        {
            "unitid",
            "year",
            "research_labor_core",
            "total_rd_nominal_thousands",
            "graduate_enrollment",
            "ipeds_matched",
        },
    ),
}


def validate_file(path: Path, identifier: str, required: set[str]) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_parquet(path)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise AssertionError(f"{path.name} is missing columns: {missing}")
    if frame.empty:
        raise AssertionError(f"{path.name} is empty")
    if frame.duplicated([identifier, "year"]).any():
        raise AssertionError(f"{path.name} has duplicate institution-years")


def main() -> None:
    root = project_root() / "data" / "processed"
    for name, (identifier, required) in SCHEMAS.items():
        validate_file(root / name, identifier, required)
    print("Processed schema validation passed")


if __name__ == "__main__":
    main()
