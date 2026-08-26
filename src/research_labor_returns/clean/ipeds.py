from __future__ import annotations

from io import BytesIO, TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from research_labor_returns.download.common import project_root

YEARS = range(2008, 2024)


def _stem(year: int, component: str) -> str:
    if component in {"HD", "EF", "EAP"}:
        suffix = "A" if component == "EF" else ""
        return f"{component}{year}{suffix}"
    return f"F{(year - 1) % 100:02d}{year % 100:02d}_{component}"


def _read_complete_file(path: Path) -> tuple[pd.DataFrame, bool]:
    """Read NCES' final/revised member when a historical archive contains both releases."""
    with ZipFile(path) as archive:
        csv_members = [name for name in archive.namelist() if name.casefold().endswith(".csv")]
        if not csv_members:
            raise RuntimeError(f"No CSV found in {path}")
        revised = [name for name in csv_members if "_rv." in name.casefold()]
        member = revised[0] if revised else csv_members[0]
        payload = archive.read(member)
        try:
            frame = pd.read_csv(
                TextIOWrapper(BytesIO(payload), encoding="utf-8-sig"), low_memory=False
            )
        except UnicodeDecodeError:
            frame = pd.read_csv(
                TextIOWrapper(BytesIO(payload), encoding="cp1252"), low_memory=False
            )
    frame.columns = (
        frame.columns.str.strip()
        .str.replace("\ufeff", "", regex=False)
        .str.replace("ï»¿", "", regex=False)
        .str.upper()
    )
    return frame, bool(revised)


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(pd.NA, index=frame.index, dtype="Float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _directory(raw: Path, year: int) -> pd.DataFrame:
    frame, revised = _read_complete_file(raw / str(year) / f"{_stem(year, 'HD')}.zip")
    columns = [
        "UNITID",
        "INSTNM",
        "CONTROL",
        "DEGGRANT",
        "GROFFER",
        "HLOFFER",
        "HOSPITAL",
        "MEDICAL",
        "CCBASIC",
        "CARNEGIE",
    ]
    selected = frame[[column for column in columns if column in frame]].copy()
    selected = selected.rename(
        columns={
            "UNITID": "unitid",
            "INSTNM": "institution_name_ipeds",
            "CONTROL": "control",
            "DEGGRANT": "degree_granting",
            "GROFFER": "graduate_offering",
            "HLOFFER": "highest_degree_offered",
            "HOSPITAL": "has_hospital",
            "MEDICAL": "grants_medical_degree",
            "CCBASIC": "carnegie_basic_2005_or_2021",
            "CARNEGIE": "carnegie_2000",
        }
    )
    selected["unitid"] = pd.to_numeric(selected["unitid"], errors="raise").astype("Int64")
    selected["year"] = year
    selected["directory_final_revised_file"] = revised
    return selected


def _enrollment(raw: Path, year: int) -> pd.DataFrame:
    frame, revised = _read_complete_file(raw / str(year) / f"{_stem(year, 'EF')}.zip")
    frame["EFALEVEL"] = pd.to_numeric(frame["EFALEVEL"], errors="coerce")
    frame["EFTOTLT"] = _numeric(frame, "EFTOTLT")
    subset = frame.loc[frame["EFALEVEL"].isin([1, 12]), ["UNITID", "EFALEVEL", "EFTOTLT"]]
    if subset.duplicated(["UNITID", "EFALEVEL"]).any():
        raise RuntimeError(f"IPEDS {year} enrollment has duplicate aggregate rows")
    wide = subset.pivot(index="UNITID", columns="EFALEVEL", values="EFTOTLT").rename(
        columns={1: "total_enrollment", 12: "graduate_enrollment"}
    )
    wide = wide.reset_index().rename(columns={"UNITID": "unitid"})
    wide["unitid"] = pd.to_numeric(wide["unitid"], errors="raise").astype("Int64")
    wide["enrollment_final_revised_file"] = revised
    return wide


def _employees_legacy(frame: pd.DataFrame) -> pd.DataFrame:
    for column in ["UNITID", "FTPT", "FUNCTCD", "FSTAT", "EAPTOT"]:
        frame[column] = _numeric(frame, column)
    full_time = frame.loc[frame["FTPT"].eq(2)]

    def aggregate(functions: list[int], statuses: list[int]) -> pd.Series:
        rows = full_time.loc[
            full_time["FUNCTCD"].isin(functions) & full_time["FSTAT"].isin(statuses)
        ]
        return rows.groupby("UNITID")["EAPTOT"].sum(min_count=1)

    result = pd.DataFrame(index=pd.Index(frame["UNITID"].dropna().unique(), name="unitid"))
    result["full_time_instruction_research_staff"] = aggregate([11, 12, 13], [0])
    result["full_time_instruction_research_faculty"] = aggregate([11, 12, 13], [1])
    result["full_time_tenured_or_tenure_track_ir_staff"] = aggregate([11, 12, 13], [2, 3])
    result["full_time_primarily_research_staff"] = aggregate([13], [0])
    return result.reset_index()


def _employees_modern(frame: pd.DataFrame) -> pd.DataFrame:
    for column in ["UNITID", "EAPCAT", "EAPFT", "EAPTOT"]:
        frame[column] = _numeric(frame, column)
    wanted = frame.loc[
        frame["EAPCAT"].isin([20000, 20010, 20020, 20030, 22000, 40000, 41000, 42000]),
        ["UNITID", "EAPCAT", "EAPFT", "EAPTOT"],
    ]
    if wanted.duplicated(["UNITID", "EAPCAT"]).any():
        raise RuntimeError("Modern IPEDS EAP file has duplicate aggregate categories")
    full_time = wanted.pivot(index="UNITID", columns="EAPCAT", values="EAPFT")
    total = wanted.pivot(index="UNITID", columns="EAPCAT", values="EAPTOT")
    result = pd.DataFrame(index=full_time.index.union(total.index))
    result["full_time_instruction_research_staff"] = full_time.get(20000)
    result["full_time_instruction_research_faculty"] = full_time.get(20010)
    result["full_time_tenured_or_tenure_track_ir_staff"] = full_time.get(20020, 0) + full_time.get(
        20030, 0
    )
    result["full_time_primarily_research_staff"] = full_time.get(22000)
    result["graduate_assistants_total"] = total.get(40000)
    result["graduate_assistants_teaching"] = total.get(41000)
    result["graduate_assistants_research"] = total.get(42000)
    return result.rename_axis("unitid").reset_index()


def _employees(raw: Path, year: int) -> pd.DataFrame:
    frame, revised = _read_complete_file(raw / str(year) / f"{_stem(year, 'EAP')}.zip")
    result = _employees_legacy(frame) if year <= 2011 else _employees_modern(frame)
    result["unitid"] = pd.to_numeric(result["unitid"], errors="raise").astype("Int64")
    result["employees_schema"] = "legacy_2008_2011" if year <= 2011 else "soc_2012_plus"
    result["employees_final_revised_file"] = revised
    return result


FINANCE_MAP = {
    "F1A": {
        "F1D01": "total_revenue_nominal",
        "F1B01": "tuition_revenue_nominal",
        "F1B10": "federal_appropriations_nominal",
        "F1B11": "state_appropriations_nominal",
        "F1B12": "local_appropriations_nominal",
        "F1C021": "research_expense_nominal",
        "F1H02": "endowment_assets_end_nominal",
    },
    "F2": {
        "F2D16": "total_revenue_nominal",
        "F2D01": "tuition_revenue_nominal",
        "F2D02": "federal_appropriations_nominal",
        "F2D03": "state_appropriations_nominal",
        "F2D04": "local_appropriations_nominal",
        "F2E021": "research_expense_nominal",
        "F2H02": "endowment_assets_end_nominal",
    },
}


def _finance(raw: Path, year: int) -> pd.DataFrame:
    parts = []
    for form, mapping in FINANCE_MAP.items():
        frame, revised = _read_complete_file(raw / str(year) / f"{_stem(year, form)}.zip")
        missing = sorted(set(mapping) - set(frame.columns))
        if missing:
            raise RuntimeError(f"IPEDS {year} {form} is missing expected variables: {missing}")
        selected = frame[["UNITID", *mapping]].rename(columns={"UNITID": "unitid", **mapping})
        for column in mapping.values():
            selected[column] = _numeric(selected, column)
        selected["finance_form"] = form
        selected["finance_final_revised_file"] = revised
        parts.append(selected)
    result = pd.concat(parts, ignore_index=True)
    result["unitid"] = pd.to_numeric(result["unitid"], errors="raise").astype("Int64")
    if result.duplicated("unitid").any():
        raise RuntimeError(f"IPEDS {year} institution appears in both F1A and F2 finance files")
    return result


def main() -> None:
    root = project_root()
    raw = root / "data" / "raw" / "ipeds"
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    annual = []
    availability = []
    for year in YEARS:
        directory = _directory(raw, year)
        enrollment = _enrollment(raw, year)
        employees = _employees(raw, year)
        finance = _finance(raw, year)
        merged = directory.merge(enrollment, on="unitid", how="left", validate="one_to_one")
        merged = merged.merge(employees, on="unitid", how="left", validate="one_to_one")
        merged = merged.merge(finance, on="unitid", how="left", validate="one_to_one")
        annual.append(merged)
        for column in merged.columns:
            availability.append(
                {
                    "source": "IPEDS",
                    "year": year,
                    "variable": column,
                    "nonmissing_count": int(merged[column].notna().sum()),
                    "institution_count": len(merged),
                }
            )
    panel = pd.concat(annual, ignore_index=True).sort_values(["unitid", "year"])
    if panel.duplicated(["unitid", "year"]).any():
        raise RuntimeError("IPEDS panel contains duplicate UNITID-years")
    panel.to_parquet(processed / "ipeds_institution_year.parquet", index=False)
    pd.DataFrame(availability).to_csv(
        root / "data" / "metadata" / "ipeds_variable_availability.csv", index=False
    )
    print(f"Cleaned IPEDS: {panel['unitid'].nunique():,} institutions, {len(panel):,} rows")


if __name__ == "__main__":
    main()
