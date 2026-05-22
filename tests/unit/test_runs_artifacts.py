"""Unit tests for run artifact directory initialization."""

from pathlib import Path

import pytest
import yaml

from tradingchassis_ops_lab.runs.artifacts import (
    RunArtifactsAlreadyExistError,
    initialize_run_artifacts,
)
from tradingchassis_ops_lab.runs.spec import load_run_spec


def _write_valid_spec(path: Path, run_id: str) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "spec_version": "v1",
                "run_id": run_id,
                "mode": "backtest",
                "engine": "nautilus",
                "venue": "binance",
                "instrument": "BTCUSDT",
                "strategy": {"name": "toy_mean_reversion", "version": "0.1.0"},
                "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
                "risk": {"profile": "tiny"},
                "observability": {"journal": True, "metrics": False, "report": False},
            }
        ),
        encoding="utf-8",
    )


def test_initialize_run_artifacts_creates_dir_and_spec_copy(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_valid_spec(spec_path, run_id="run-spec-artifacts-run")
    spec = load_run_spec(spec_path)

    run_dir = initialize_run_artifacts(
        spec_path=spec_path,
        spec=spec,
        config_sha256="abc123",
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    assert run_dir == tmp_path / "artifacts" / "runs" / "run-spec-artifacts-run"
    assert run_dir.is_dir()
    assert (run_dir / "run_spec.yaml").is_file()


def test_initialize_run_artifacts_fails_for_duplicate_run(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_valid_spec(spec_path, run_id="run-spec-artifacts-duplicate")
    spec = load_run_spec(spec_path)
    artifacts_root = tmp_path / "artifacts" / "runs"

    initialize_run_artifacts(
        spec_path=spec_path,
        spec=spec,
        config_sha256="abc123",
        artifacts_root=artifacts_root,
    )

    with pytest.raises(RunArtifactsAlreadyExistError):
        initialize_run_artifacts(
            spec_path=spec_path,
            spec=spec,
            config_sha256="abc123",
            artifacts_root=artifacts_root,
        )
