"""Unit tests for deterministic dataset fingerprinting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingchassis_ops_lab.data.fingerprint import (
    PreparedDatasetNotFoundError,
    fingerprint_dataset,
    write_fingerprint,
)
from tradingchassis_ops_lab.data.prepare import UnsupportedDatasetError, prepare_dataset


def test_fingerprint_requires_prepared_dataset(tmp_path: Path) -> None:
    """Fingerprinting fails before a dataset is prepared."""
    with pytest.raises(PreparedDatasetNotFoundError):
        fingerprint_dataset("btcusdt-sample", data_root=tmp_path)


def test_fingerprint_dataset_has_required_fields_and_stable_hash(tmp_path: Path) -> None:
    """Fingerprint payload contains required fields and deterministic dataset hash."""
    prepare_dataset("btcusdt-sample", data_root=tmp_path)
    first = fingerprint_dataset("btcusdt-sample", data_root=tmp_path)
    second = fingerprint_dataset("btcusdt-sample", data_root=tmp_path)

    assert first.schema_version == "v1"
    assert first.dataset == "btcusdt-sample"
    assert first.algorithm == "sha256"
    assert first.files
    assert first.files[0].path == "candles_1m.csv"
    assert len(first.files[0].sha256) == 64
    assert first.dataset_sha256 == second.dataset_sha256


def test_file_and_dataset_hash_change_when_content_changes(tmp_path: Path) -> None:
    """Mutating prepared data changes file and dataset fingerprints."""
    prepared = prepare_dataset("btcusdt-sample", data_root=tmp_path)
    before = fingerprint_dataset("btcusdt-sample", data_root=tmp_path)

    candles_path = prepared.target_dir / "candles_1m.csv"
    candles_path.write_text(candles_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    after = fingerprint_dataset("btcusdt-sample", data_root=tmp_path)
    assert before.files[0].sha256 != after.files[0].sha256
    assert before.dataset_sha256 != after.dataset_sha256


def test_write_fingerprint_outputs_expected_json_shape(tmp_path: Path) -> None:
    """Persisted fingerprint JSON uses required keys and formatting-friendly structure."""
    prepare_dataset("btcusdt-sample", data_root=tmp_path)
    fingerprint = fingerprint_dataset("btcusdt-sample", data_root=tmp_path)
    output_path = write_fingerprint(fingerprint, data_root=tmp_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path == tmp_path / "fingerprints" / "btcusdt-sample.fingerprint.json"
    assert payload["schema_version"] == "v1"
    assert payload["dataset"] == "btcusdt-sample"
    assert payload["algorithm"] == "sha256"
    assert payload["root"] == str(tmp_path / "datasets" / "btcusdt-sample")
    assert isinstance(payload["files"], list)
    assert payload["files"][0]["path"] == "candles_1m.csv"
    assert "dataset_sha256" in payload


def test_fingerprint_rejects_unknown_dataset(tmp_path: Path) -> None:
    """Unknown datasets are rejected in fingerprint workflow too."""
    with pytest.raises(UnsupportedDatasetError):
        fingerprint_dataset("ethusdt-sample", data_root=tmp_path)
