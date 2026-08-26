from pathlib import Path

from research_labor_returns.validation.institution_crosswalk import validate


def test_required_campus_resolutions() -> None:
    validate(Path("data/crosswalks/institution_crosswalk.csv"))
