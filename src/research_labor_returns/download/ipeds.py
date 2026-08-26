from __future__ import annotations

import argparse

from .common import download_file, load_sources, parse_years, project_root, record_download


def main() -> None:
    sources = load_sources()
    config = sources["ipeds"]
    parser = argparse.ArgumentParser(description="Download selected annual IPEDS complete files")
    parser.add_argument("--years", default="2008:2023")
    parser.add_argument(
        "--components", default=",".join(config["components"]), help="Comma-separated config keys"
    )
    args = parser.parse_args()
    years = parse_years(args.years, config["available_years"])
    component_keys = [item.strip() for item in args.components.split(",") if item.strip()]
    unknown = sorted(set(component_keys) - set(config["components"]))
    if unknown:
        raise ValueError(f"Unknown IPEDS components: {unknown}")
    raw_dir = project_root() / "data" / "raw" / "ipeds"
    user_agent = sources["project"]["retrieval_user_agent"]
    for year in years:
        for component_key in component_keys:
            stem = config["components"][component_key].format(
                year=year,
                start2=f"{(year - 1) % 100:02d}",
                end2=f"{year % 100:02d}",
            )
            url = f"{config['base_url']}/{stem}.zip"
            path = download_file(url, raw_dir / str(year) / f"{stem}.zip", user_agent)
            record_download(
                source=f"ipeds_{component_key}",
                config=config,
                url=url,
                path=path,
                release_year=year,
            )
            print(f"IPEDS {year} {component_key}: {path.stat().st_size:,} bytes")
            dictionary_stem = f"{stem}_Dict"
            dictionary_url = f"{config['base_url']}/{dictionary_stem}.zip"
            dictionary_path = download_file(
                dictionary_url,
                raw_dir / str(year) / "dictionaries" / f"{dictionary_stem}.zip",
                user_agent,
            )
            record_download(
                source=f"ipeds_{component_key}_dictionary",
                config=config,
                url=dictionary_url,
                path=dictionary_path,
                release_year=year,
            )


if __name__ == "__main__":
    main()
