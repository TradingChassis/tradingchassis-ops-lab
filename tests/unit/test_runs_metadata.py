"""Unit tests for run metadata helpers."""

import json
from pathlib import Path

import yaml

from ops_lab.runs.metadata import build_initial_metadata, write_metadata
from ops_lab.runs.spec import load_run_spec


def _write_valid_spec(path: Path, run_id: str = "slice2-metadata-run") -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "spec_version": "v1",
                "run_id": run_id,
                "mode": "paper",
                "engine": "nautilus",
                "venue": "binance_testnet",
                "instrument": "BTCUSDT",
                "strategy": {"name": "toy_mean_reversion", "version": "0.1.0"},
                "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
                "risk": {"profile": "tiny"},
                "observability": {"journal": True, "metrics": False, "report": False},
            }
        ),
        encoding="utf-8",
    )


def test_write_metadata_contains_required_fields(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    artifacts_dir = tmp_path / "artifacts" / "runs" / "slice2-metadata-run"
    artifacts_dir.mkdir(parents=True)
    _write_valid_spec(spec_path)
    spec = load_run_spec(spec_path)

    metadata = build_initial_metadata(
        spec=spec,
        spec_path=spec_path,
        artifacts_dir=artifacts_dir,
        config_sha256="cafebabe",
    )
    metadata_path = artifacts_dir / "metadata.json"
    write_metadata(metadata_path, metadata)

    parsed = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == "v1"
    assert parsed["run_id"] == "slice2-metadata-run"
    assert parsed["mode"] == "paper"
    assert parsed["engine"] == "nautilus"
    assert parsed["status"] == "initialized"
    assert parsed["config_sha256"] == "cafebabe"
    assert parsed["strategy"]["name"] == "toy_mean_reversion"
    assert parsed["data"]["fingerprint"] == "placeholder"
    assert parsed["risk"]["profile"] == "tiny"
    assert parsed["observability"]["journal"] is True
