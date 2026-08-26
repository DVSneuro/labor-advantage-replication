from __future__ import annotations

import argparse

from .common import download_file, load_sources, parse_years, project_root, record_download


def main() -> None:
    sources = load_sources()
    config = sources["herd"]
    parser = argparse.ArgumentParser(description="Download immutable annual HERD public-use files")
    parser.add_argument("--years", default="2008:2024")
    args = parser.parse_args()
    years = parse_years(args.years, config["available_years"])
    raw_dir = project_root() / "data" / "raw" / "herd"
    user_agent = sources["project"]["retrieval_user_agent"]
    for year in years:
        url = config["file_url_template"].format(year=year)
        path = download_file(url, raw_dir / f"higher_education_r_and_d_{year}.zip", user_agent)
        record_download(source="herd", config=config, url=url, path=path, release_year=year)
        print(f"HERD {year}: {path.stat().st_size:,} bytes")
        if year >= config["short_file_start_year"]:
            short_url = config["short_file_url_template"].format(year=year)
            short_path = download_file(
                short_url,
                raw_dir / f"higher_education_r_and_d_{year}_short.zip",
                user_agent,
            )
            record_download(
                source="herd_short",
                config=config,
                url=short_url,
                path=short_path,
                release_year=year,
            )
            print(f"HERD {year} short: {short_path.stat().st_size:,} bytes")
    url = config["documentation_url"]
    path = download_file(url, raw_dir / "documentation" / "fy-2024-herd-user-guide.pdf", user_agent)
    record_download(
        source="herd_documentation", config=config, url=url, path=path, release_year=2024
    )


if __name__ == "__main__":
    main()
