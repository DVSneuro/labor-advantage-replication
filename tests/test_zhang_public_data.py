from pathlib import Path

import pandas as pd

from research_labor_returns.analysis.zhang_replication import labor_by_prestige

DATA = Path("legacy/initial_exploration/data/zhang2022")


def test_public_archive_shapes() -> None:
    assert pd.read_csv(DATA / "area-strict.csv").shape == (739, 51)
    assert pd.read_csv(DATA / "area-non-strict.csv").shape == (1800, 10)
    assert pd.read_csv(DATA / "moves.csv").shape == (684, 19)


def test_funded_labor_summary_has_complete_deciles() -> None:
    frame = pd.read_csv(DATA / "funding_by_segment_clean.csv")
    summary = labor_by_prestige(frame)
    assert len(summary) == 20
    assert set(summary["prestige_segment_equispaced"]) == set(range(1, 11))
    assert summary["funded_labor_per_faculty"].notna().all()
