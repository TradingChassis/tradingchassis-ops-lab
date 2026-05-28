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
        "strategy": {"name": "ops_smoke_demo", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }


def _valid_connectivity_readiness_dict() -> dict:
    return {
        "enabled": True,
        "target": "paper_testnet_probe",
        "venue": "binance",
        "credential_placeholders": {
            "required_env": [
                "TRADINGCHASSIS_PAPER_API_KEY",
                "TRADINGCHASSIS_PAPER_API_SECRET",
            ],
            "optional_env": ["TRADINGCHASSIS_PAPER_PASSPHRASE"],
        },
        "notes": "Local readiness contract only; no network calls.",
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
    assert loaded.connectivity_readiness is None


def test_load_run_spec_parses_with_disabled_connectivity_readiness_block(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["connectivity_readiness"] = {
        "enabled": False,
        "notes": "Local readiness contract only; no network calls.",
    }
    spec_path = tmp_path / "connectivity_disabled.yaml"
    _write_yaml(spec_path, spec)

    loaded = load_run_spec(spec_path)
    assert loaded.connectivity_readiness is not None
    assert loaded.connectivity_readiness.enabled is False
    assert loaded.connectivity_readiness.target is None
    assert loaded.connectivity_readiness.credential_placeholders.required_env == []
    assert loaded.connectivity_readiness.credential_placeholders.optional_env == []


def test_load_run_spec_parses_with_enabled_connectivity_readiness_block(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    spec["connectivity_readiness"] = _valid_connectivity_readiness_dict()
    spec_path = tmp_path / "connectivity_enabled.yaml"
    _write_yaml(spec_path, spec)

    loaded = load_run_spec(spec_path)
    assert loaded.connectivity_readiness is not None
    assert loaded.connectivity_readiness.enabled is True
    assert loaded.connectivity_readiness.target == "paper_testnet_probe"
    assert loaded.connectivity_readiness.venue == "binance"
    assert loaded.connectivity_readiness.credential_placeholders.required_env == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
    ]
    assert loaded.connectivity_readiness.credential_placeholders.optional_env == [
        "TRADINGCHASSIS_PAPER_PASSPHRASE"
    ]


def test_load_run_spec_rejects_invalid_connectivity_env_var_name(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["credential_placeholders"]["required_env"] = ["INVALID-ENV-NAME"]
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_invalid_env_name.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_empty_connectivity_env_var_name(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["credential_placeholders"]["required_env"] = ["  "]
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_empty_env_name.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_duplicate_required_connectivity_env_var_names(
    tmp_path: Path,
) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["credential_placeholders"]["required_env"] = [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_KEY",
    ]
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_duplicate_required_env.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_overlap_between_required_and_optional_env(
    tmp_path: Path,
) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["credential_placeholders"]["optional_env"] = ["TRADINGCHASSIS_PAPER_API_KEY"]
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_overlap_env.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_connectivity_venue_mismatch(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["venue"] = "binance_testnet"
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_venue_mismatch.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


def test_load_run_spec_rejects_unknown_field_in_connectivity_readiness(tmp_path: Path) -> None:
    spec = _valid_spec_dict()
    readiness = _valid_connectivity_readiness_dict()
    readiness["adapter"] = "unsupported"
    spec["connectivity_readiness"] = readiness
    spec_path = tmp_path / "connectivity_unknown_field.yaml"
    _write_yaml(spec_path, spec)

    with pytest.raises(RunSpecLoadError):
        load_run_spec(spec_path)


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
