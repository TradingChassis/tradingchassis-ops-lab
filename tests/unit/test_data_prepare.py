"""Unit tests for local dataset preparation."""

from pathlib import Path

import pytest

from tradingchassis_ops_lab.data.prepare import UnsupportedDatasetError, prepare_dataset


def test_prepare_dataset_succeeds_for_supported_dataset(tmp_path: Path) -> None:
    """Preparing supported dataset creates expected runtime data files."""
    prepared = prepare_dataset("btcusdt-sample", data_root=tmp_path)
    assert prepared.dataset == "btcusdt-sample"
    assert (tmp_path / "datasets" / "btcusdt-sample" / "candles_1m.csv").is_file()
    assert len(prepared.files) == 1


def test_prepare_dataset_is_idempotent(tmp_path: Path) -> None:
    """Repeated prepare calls keep deterministic fixture content."""
    first = prepare_dataset("btcusdt-sample", data_root=tmp_path)
    second = prepare_dataset("btcusdt-sample", data_root=tmp_path)
    assert first.target_dir == second.target_dir
    assert first.files == second.files
    assert (second.target_dir / "candles_1m.csv").is_file()


def test_prepare_dataset_rejects_unknown_dataset(tmp_path: Path) -> None:
    """Unknown dataset names are rejected clearly."""
    with pytest.raises(UnsupportedDatasetError):
        prepare_dataset("ethusdt-sample", data_root=tmp_path)
