"""Unit tests for run spec loading and validation."""

from pathlib import Path

import pytest
import yaml

from tradingchassis_ops_lab.runs.spec import RunSpec, RunSpecLoadError, load_run_spec


def _valid_spec_dict() -> dict:
    return {
        "spec_version": "v1",
        "run_id": "run-spec-spec-run",
        "mode": "backtest",
        "engine": "nautilus",
        "venue": "binance",
        "instrument": "BTCUSDT",
        "strategy": {"name": "toy_mean_reversion", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_load_run_spec_parses_valid_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "valid.yaml"
    _write_yaml(spec_path, _valid_spec_dict())

    loaded = load_run_spec(spec_path)
    assert isinstance(loaded, RunSpec)
    assert loaded.run_id == "run-spec-spec-run"
    assert loaded.mode == "backtest"
    assert loaded.engine == "nautilus"


def test_load_run_spec_rejects_invalid_mode(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["mode"] = "sim"
    spec_path = tmp_path / "invalid_mode.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_invalid_engine(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["engine"] = "custom"
    spec_path = tmp_path / "invalid_engine.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_missing_required_field(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    del spec["strategy"]
    spec_path = tmp_path / "missing_field.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_empty_required_string(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["run_id"] = "   "
    spec_path = tmp_path / "empty_run_id.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_extra_field(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["unexpected"] = "not allowed"
    spec_path = tmp_path / "extra_field.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)
