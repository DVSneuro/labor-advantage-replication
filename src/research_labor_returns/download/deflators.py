from __future__ import annotations

from .common import download_file, load_sources, project_root, record_download


def main() -> None:
    sources = load_sources()
    config = sources["bea_gdp_deflator"]
    path = download_file(
        config["file_url"],
        project_root() / "data" / "raw" / "bea" / "FlatFiles.ZIP",
        sources["project"]["retrieval_user_agent"],
    )
    record_download(
        source="bea_gdp_deflator",
        config=config,
        url=config["file_url"],
        path=path,
        release_year=config["release_year"],
    )
    print(f"BEA NIPA flat files: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
