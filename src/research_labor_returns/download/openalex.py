from __future__ import annotations

import argparse
import gzip
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

from .common import load_sources, project_root, record_download

SELECT = ",".join(
    [
        "id",
        "doi",
        "publication_year",
        "type",
        "authorships",
        "cited_by_count",
        "citation_normalized_percentile",
        "fwci",
        "open_access",
        "countries_distinct_count",
        "institutions_distinct_count",
    ]
)


def _institution_ids(crosswalk: Path) -> list[str]:
    frame = pd.read_csv(crosswalk, dtype=str)
    values = frame.loc[frame["openalex_institution_id"].notna(), "openalex_institution_id"]
    return sorted({value.rsplit("/", 1)[-1] for value in values if value.strip()})


def main() -> None:
    sources = load_sources()
    config = sources["openalex"]
    parser = argparse.ArgumentParser(
        description="Cache raw OpenAlex works for reviewed institutions"
    )
    parser.add_argument("--start-year", type=int, default=2008)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument(
        "--crosswalk",
        type=Path,
        default=project_root() / "data" / "crosswalks" / "institution_crosswalk.csv",
    )
    args = parser.parse_args()
    api_key = os.getenv("OPENALEX_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set OPENALEX_API_KEY; systematic API acquisition should not rely on the small "
            "anonymous request budget"
        )
    email = os.getenv("OPENALEX_EMAIL", "")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"
    session.headers["User-Agent"] = (
        f"research-labor-returns/0.1 (mailto:{email})" if email else "research-labor-returns/0.1"
    )
    output_dir = project_root() / "data" / "raw" / "openalex" / "works"
    output_dir.mkdir(parents=True, exist_ok=True)
    for institution_id in _institution_ids(args.crosswalk):
        destination = output_dir / f"{institution_id}_{args.start_year}_{args.end_year}.jsonl.gz"
        if destination.exists():
            print(f"OpenAlex {institution_id}: already present")
            continue
        temporary = destination.with_suffix(destination.suffix + ".part")
        cursor = "*"
        count = 0
        with gzip.open(temporary, "wt", encoding="utf-8") as stream:
            while cursor:
                params = {
                    "filter": (
                        f"institutions.id:{institution_id},"
                        f"from_publication_date:{args.start_year}-01-01,"
                        f"to_publication_date:{args.end_year}-12-31"
                    ),
                    "select": SELECT,
                    "per_page": 100,
                    "cursor": cursor,
                }
                response = session.get(f"{config['api_url']}/works", params=params, timeout=90)
                if response.status_code == 429:
                    time.sleep(int(response.headers.get("Retry-After", "5")))
                    continue
                response.raise_for_status()
                payload = response.json()
                for work in payload["results"]:
                    stream.write(json.dumps(work, separators=(",", ":")) + "\n")
                    count += 1
                cursor = payload["meta"].get("next_cursor")
                if not payload["results"]:
                    break
                time.sleep(0.1)
        temporary.replace(destination)
        record_download(
            source="openalex_works_api",
            config=config,
            url=(
                f"{config['api_url']}/works?filter=institutions.id:{institution_id},"
                f"from_publication_date:{args.start_year}-01-01,"
                f"to_publication_date:{args.end_year}-12-31"
            ),
            path=destination,
            release_year=config["release_year"],
        )
        print(f"OpenAlex {institution_id}: {count:,} works")


if __name__ == "__main__":
    main()
