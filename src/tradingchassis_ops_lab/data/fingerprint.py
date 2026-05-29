"""Deterministic local dataset fingerprinting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tradingchassis_ops_lab.data.prepare import SUPPORTED_DATASET, UnsupportedDatasetError


class PreparedDatasetNotFoundError(FileNotFoundError):
    """Raised when fingerprinting is requested before dataset preparation."""


@dataclass(frozen=True)
class FileFingerprint:
    """Per-file fingerprint details."""

    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class DatasetFingerprint:
    """Dataset-level deterministic fingerprint payload."""

    schema_version: str
    dataset: str
    algorithm: str
    root: str
    files: list[FileFingerprint]
    dataset_sha256: str


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _build_dataset_hash_payload(dataset: str, files: list[FileFingerprint]) -> str:
    payload = {
        "dataset": dataset,
        "algorithm": "sha256",
        "files": [asdict(file_fingerprint) for file_fingerprint in files],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _sha256_bytes(canonical.encode("utf-8"))


def fingerprint_dataset(dataset: str, data_root: Path = Path("data")) -> DatasetFingerprint:
    """Fingerprint a prepared dataset based on file contents."""
    if dataset != SUPPORTED_DATASET:
        raise UnsupportedDatasetError(f"Unsupported dataset: {dataset}")

    dataset_dir = data_root / "datasets" / dataset
    if not dataset_dir.is_dir():
        raise PreparedDatasetNotFoundError(
            "Prepared dataset not found. Run `tc data prepare --dataset btcusdt-sample` first."
        )

    candidate_files = sorted(path for path in dataset_dir.rglob("*") if path.is_file())
    if not candidate_files:
        raise PreparedDatasetNotFoundError(
            "Prepared dataset is empty. Run `tc data prepare --dataset btcusdt-sample` first."
        )

    files: list[FileFingerprint] = []
    for file_path in candidate_files:
        relative_path = file_path.relative_to(dataset_dir).as_posix()
        file_bytes = file_path.read_bytes()
        files.append(
            FileFingerprint(
                path=relative_path,
                sha256=_sha256_bytes(file_bytes),
                size_bytes=file_path.stat().st_size,
            )
        )

    dataset_sha256 = _build_dataset_hash_payload(dataset=dataset, files=files)
    return DatasetFingerprint(
        schema_version="v1",
        dataset=dataset,
        algorithm="sha256",
        root=str(dataset_dir),
        files=files,
        dataset_sha256=dataset_sha256,
    )


def write_fingerprint(fingerprint: DatasetFingerprint, data_root: Path = Path("data")) -> Path:
    """Write a dataset fingerprint JSON file and return the output path."""
    output_dir = data_root / "fingerprints"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{fingerprint.dataset}.fingerprint.json"

    payload = {
        "schema_version": fingerprint.schema_version,
        "dataset": fingerprint.dataset,
        "algorithm": fingerprint.algorithm,
        "root": fingerprint.root,
        "files": [asdict(file_fingerprint) for file_fingerprint in fingerprint.files],
        "dataset_sha256": fingerprint.dataset_sha256,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
