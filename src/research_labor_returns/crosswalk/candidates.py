from __future__ import annotations

import pandas as pd

from research_labor_returns.download.common import project_root

COLUMNS = [
    "source",
    "source_year",
    "source_identifier",
    "source_name",
    "candidate_canonical_name",
    "candidate_identifier",
    "match_basis",
    "similarity_score",
    "reason_for_review",
    "status",
    "reviewer",
    "review_date",
]


def main() -> None:
    root = project_root()
    gss = pd.read_parquet(root / "data" / "processed" / "gss_institution_year.parquet")
    ambiguous = gss.loc[gss["unitid_count"].ne(1)].copy()
    rows = []
    for (source_id, name, unitids), group in ambiguous.groupby(
        ["institution_id", "institution_name", "unitids"], dropna=False
    ):
        years = f"{int(group.year.min())}-{int(group.year.max())}"
        candidates = unitids.split("|") if unitids else [""]
        for candidate in candidates:
            rows.append(
                {
                    "source": "GSS",
                    "source_year": years,
                    "source_identifier": source_id,
                    "source_name": name,
                    "candidate_canonical_name": "",
                    "candidate_identifier": candidate,
                    "match_basis": "GSS-provided school-level IPEDS UNITID",
                    "similarity_score": "",
                    "reason_for_review": (
                        "Reporting institution maps to multiple school UNITIDs"
                        if candidate
                        else "GSS supplies no usable IPEDS UNITID"
                    ),
                    "status": "pending",
                    "reviewer": "",
                    "review_date": "",
                }
            )
    destination = root / "data" / "crosswalks" / "institution_matches_to_review.csv"
    existing = pd.read_csv(destination, dtype=str, keep_default_na=False)
    generated = pd.DataFrame(rows, columns=COLUMNS)
    preserved = existing.loc[existing["status"].ne("pending")]
    result = pd.concat([preserved, generated], ignore_index=True).drop_duplicates(
        ["source", "source_identifier", "candidate_identifier"], keep="first"
    )
    result.sort_values(["source", "source_name", "candidate_identifier"]).to_csv(
        destination, index=False
    )
    print(f"Wrote {len(result):,} distinct unresolved deterministic GSS identity candidates")


if __name__ == "__main__":
    main()
