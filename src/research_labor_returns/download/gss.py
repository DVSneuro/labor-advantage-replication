from __future__ import annotations

import argparse

from .common import download_file, load_sources, parse_years, project_root, record_download


def main() -> None:
    sources = load_sources()
    config = sources["gss"]
    parser = argparse.ArgumentParser(description="Download immutable annual GSS public-use files")
    parser.add_argument("--years", default="2008:2024")
    args = parser.parse_args()
    years = parse_years(args.years, config["available_years"])
    raw_dir = project_root() / "data" / "raw" / "gss"
    user_agent = sources["project"]["retrieval_user_agent"]
    for year in years:
        url = config["file_url_template"].format(year=year)
        path = download_file(url, raw_dir / f"graduate_students_postdocs_{year}.zip", user_agent)
        record_download(source="gss", config=config, url=url, path=path, release_year=year)
        print(f"GSS {year}: {path.stat().st_size:,} bytes")
    for key, name in [
        ("documentation_url", "gss-2024-puf-user-guide.pdf"),
        ("availability_url", "gss-2024-puf-user-guide-appendix-a.pdf"),
        ("dictionary_url", "gss-2024-puf-user-guide-appendix-b.xlsx"),
    ]:
        url = config[key]
        path = download_file(url, raw_dir / "documentation" / name, user_agent)
        record_download(
            source="gss_documentation", config=config, url=url, path=path, release_year=2024
        )


if __name__ == "__main__":
    main()
