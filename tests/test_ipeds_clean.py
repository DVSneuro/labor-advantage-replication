import pandas as pd

from research_labor_returns.clean.ipeds import _employees_legacy, _employees_modern


def test_legacy_employee_categories_are_not_double_counted() -> None:
    frame = pd.DataFrame(
        {
            "UNITID": [1, 1, 1, 1, 1],
            "FTPT": [2, 2, 2, 2, 3],
            "FUNCTCD": [11, 12, 13, 13, 13],
            "FSTAT": [0, 0, 0, 2, 0],
            "EAPTOT": [10, 20, 5, 3, 100],
        }
    )
    result = _employees_legacy(frame).set_index("unitid").loc[1]
    assert result["full_time_instruction_research_staff"] == 35
    assert result["full_time_primarily_research_staff"] == 5
    assert result["full_time_tenured_or_tenure_track_ir_staff"] == 3


def test_modern_employee_categories_use_published_aggregates() -> None:
    frame = pd.DataFrame(
        {
            "UNITID": [1, 1, 1, 1, 1, 1],
            "EAPCAT": [20000, 20010, 20020, 20030, 22000, 42000],
            "EAPFT": [40, 35, 12, 8, 7, 0],
            "EAPTOT": [50, 45, 12, 8, 9, 15],
        }
    )
    result = _employees_modern(frame).set_index("unitid").loc[1]
    assert result["full_time_instruction_research_staff"] == 40
    assert result["full_time_primarily_research_staff"] == 7
    assert result["full_time_tenured_or_tenure_track_ir_staff"] == 20
    assert result["graduate_assistants_research"] == 15
