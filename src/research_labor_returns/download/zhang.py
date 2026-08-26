from __future__ import annotations

import hashlib

import requests

from .common import (
    download_file,
    load_sources,
    project_root,
    record_download,
    safe_extract_tar,
)


def main() -> None:
    sources = load_sources()
    config = sources["zhang2022"]
    user_agent = sources["project"]["retrieval_user_agent"]
    response = requests.get(config["record_url"], headers={"User-Agent": user_agent}, timeout=60)
    response.raise_for_status()
    record = response.json()
    candidates = [item for item in record["files"] if item["key"] == config["file_name"]]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected exactly one Zenodo file named {config['file_name']}")
    remote = candidates[0]
    remote_md5 = remote["checksum"].removeprefix("md5:")
    if remote_md5 != config["expected_md5"]:
        raise RuntimeError(f"Zenodo metadata checksum changed: {remote_md5}")

    raw_dir = project_root() / "data" / "raw" / "zhang2022"
    archive = download_file(remote["links"]["self"], raw_dir / config["file_name"], user_agent)
    actual_md5 = hashlib.md5(archive.read_bytes()).hexdigest()  # noqa: S324 - upstream MD5
    if actual_md5 != remote_md5:
        raise RuntimeError(f"Downloaded Zhang archive failed MD5 verification: {actual_md5}")
    record_download(
        source="zhang2022",
        config=config,
        url=remote["links"]["self"],
        path=archive,
        release_year=config["release_year"],
        upstream_checksum=f"md5:{remote_md5}",
    )
    extracted = raw_dir / "code-and-data"
    if not extracted.exists():
        safe_extract_tar(archive, raw_dir)
    print(f"Verified and unpacked {archive} into {extracted}")


if __name__ == "__main__":
    main()
