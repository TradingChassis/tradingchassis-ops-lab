"""Local dataset preparation helpers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_DATASET = "btcusdt-sample"
DATASET_FILES = ("candles_1m.csv",)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES_ROOT = _REPO_ROOT / "fixtures" / "datasets"


class UnsupportedDatasetError(ValueError):
    """Raised when a dataset is not supported."""


@dataclass(frozen=True)
class PreparedDataset:
    """Result of preparing a local dataset."""

    dataset: str
    source_dir: Path
    target_dir: Path
    files: list[Path]


def _resolve_fixture_dir(dataset: str) -> Path:
    if dataset != SUPPORTED_DATASET:
        raise UnsupportedDatasetError(f"Unsupported dataset: {dataset}")
    return _FIXTURES_ROOT / dataset


def prepare_dataset(dataset: str, data_root: Path = Path("data")) -> PreparedDataset:
    """Prepare a local fixture dataset under the runtime data directory."""
    source_dir = _resolve_fixture_dir(dataset)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Fixture dataset directory not found: {source_dir}")

    target_dir = data_root / "datasets" / dataset
    target_dir.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []
    for file_name in DATASET_FILES:
        source_file = source_dir / file_name
        if not source_file.is_file():
            raise FileNotFoundError(f"Fixture dataset file not found: {source_file}")
        target_file = target_dir / file_name
        shutil.copy2(source_file, target_file)
        copied_files.append(target_file)

    return PreparedDataset(
        dataset=dataset,
        source_dir=source_dir,
        target_dir=target_dir,
        files=sorted(copied_files),
    )
