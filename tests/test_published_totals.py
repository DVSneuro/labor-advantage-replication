from research_labor_returns.validation.published_totals import GSS_2024_TOTALS


def test_published_gss_totals_are_pinned() -> None:
    assert GSS_2024_TOTALS == {
        "graduate_students": 818_078,
        "doctoral_students": 312_148,
        "postdocs": 69_877,
    }
