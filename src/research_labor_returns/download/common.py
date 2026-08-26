from __future__ import annotations

import csv
import hashlib
import os
import tarfile
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml

MANIFEST_COLUMNS = [
    "source",
    "source_organization",
    "source_url",
    "file_name",
    "release_year",
    "retrieved_at_utc",
    "file_size_bytes",
    "sha256",
    "upstream_checksum",
    "license_access_notes",
    "documentation_url",
]


@dataclass(frozen=True)
class ManifestRecord:
    source: str
    source_organization: str
    source_url: str
    file_name: str
    release_year: int | str | None
    retrieved_at_utc: str
    file_size_bytes: int
    sha256: str
    upstream_checksum: str
    license_access_notes: str
    documentation_url: str


def project_root() -> Path:
    override = os.getenv("RESEARCH_LABOR_ROOT")
    return Path(override).resolve() if override else Path(__file__).resolve().parents[3]


def load_sources() -> dict:
    with (project_root() / "config" / "sources.yml").open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def parse_years(value: str, allowed: Iterable[int]) -> list[int]:
    allowed_set = set(allowed)
    requested: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            start, end = (int(x) for x in part.split(":", 1))
            requested.update(range(start, end + 1))
        else:
            requested.add(int(part))
    invalid = sorted(requested - allowed_set)
    if invalid:
        raise ValueError(f"Years not listed as available: {invalid}")
    return sorted(requested)


def checksum(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_file(url: str, destination: Path, user_agent: str, retries: int = 4) -> Path:
    """Download once and never silently replace an existing immutable raw file."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError(f"Existing raw path is not a nonempty file: {destination}")
        return destination

    temporary = destination.with_suffix(destination.suffix + ".part")
    headers = {"User-Agent": user_agent}
    for attempt in range(retries):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(30, 180)) as response:
                response.raise_for_status()
                with temporary.open("wb") as stream:
                    for block in response.iter_content(chunk_size=1024 * 1024):
                        if block:
                            stream.write(block)
            temporary.replace(destination)
            return destination
        except requests.RequestException:
            temporary.unlink(missing_ok=True)
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def record_download(
    *,
    source: str,
    config: dict,
    url: str,
    path: Path,
    release_year: int | str | None,
    upstream_checksum: str = "",
) -> ManifestRecord:
    record = ManifestRecord(
        source=source,
        source_organization=config["organization"],
        source_url=url,
        file_name=path.name,
        release_year=release_year,
        retrieved_at_utc=datetime.now(UTC).replace(microsecond=0).isoformat(),
        file_size_bytes=path.stat().st_size,
        sha256=checksum(path),
        upstream_checksum=upstream_checksum,
        license_access_notes=config["license_notes"],
        documentation_url=config["documentation_url"],
    )
    manifest = project_root() / "data" / "metadata" / "download_manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    if manifest.exists():
        with manifest.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    key = (record.source, record.source_url, record.file_name)
    rows = [row for row in rows if (row["source"], row["source_url"], row["file_name"]) != key]
    rows.append(
        {name: str(value if value is not None else "") for name, value in asdict(record).items()}
    )
    rows.sort(key=lambda row: (row["source"], row["release_year"], row["file_name"]))
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return record


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise RuntimeError(f"Unsafe archive member: {member.name}")
        bundle.extractall(destination, filter="data")
