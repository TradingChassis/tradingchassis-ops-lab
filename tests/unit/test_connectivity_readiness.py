"""Unit tests for local-only connectivity readiness evaluator helpers."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from tradingchassis_ops_lab.connectivity.readiness import (
    evaluate_connectivity_readiness,
    write_connectivity_readiness_artifact,
)
from tradingchassis_ops_lab.runs.spec import load_run_spec


def _write_spec(path: Path, *, enabled: bool = True, include_readiness: bool = True) -> None:
    spec: dict[str, object] = {
        "spec_version": "v1",
        "run_id": "connectivity-readiness-unit",
        "mode": "paper",
        "engine": "nautilus",
        "venue": "binance",
        "instrument": "BTCUSDT",
        "strategy": {"name": "ops_smoke_demo", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }
    if include_readiness:
        spec["connectivity_readiness"] = {
            "enabled": enabled,
            "target": "paper_testnet_probe",
            "venue": "binance",
            "credential_placeholders": {
                "required_env": [
                    "TRADINGCHASSIS_PAPER_API_SECRET",
                    "TRADINGCHASSIS_PAPER_API_KEY",
                ],
                "optional_env": ["TRADINGCHASSIS_PAPER_PASSPHRASE"],
            },
        }
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")


def test_evaluate_disabled_when_connectivity_block_missing(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, include_readiness=False)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(spec, env={})
    assert payload["state"] == "disabled"
    assert payload["enabled"] is False
    assert payload["target"] is None


def test_evaluate_disabled_when_connectivity_enabled_false(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=False)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(spec, env={})
    assert payload["state"] == "disabled"
    assert payload["enabled"] is False
    assert payload["target"] == "paper_testnet_probe"


def test_evaluate_missing_credentials_when_required_env_absent(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(spec, env={})
    assert payload["state"] == "missing_credentials"
    assert payload["missing_required_count"] == 2
    assert payload["required_env"] == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
    ]
    assert payload["missing_env"] == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
        "TRADINGCHASSIS_PAPER_PASSPHRASE",
    ]


def test_evaluate_configured_when_required_env_present(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(
        spec,
        env={
            "TRADINGCHASSIS_PAPER_API_KEY": "dummy-key",
            "TRADINGCHASSIS_PAPER_API_SECRET": "dummy-secret",
        },
    )
    assert payload["state"] == "configured"
    assert payload["missing_required_count"] == 0
    assert payload["present_env"] == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
    ]
    assert payload["missing_env"] == ["TRADINGCHASSIS_PAPER_PASSPHRASE"]


def test_optional_env_does_not_change_configured_state(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(
        spec,
        env={
            "TRADINGCHASSIS_PAPER_API_KEY": "dummy-key",
            "TRADINGCHASSIS_PAPER_API_SECRET": "dummy-secret",
            "TRADINGCHASSIS_PAPER_PASSPHRASE": "",
        },
    )
    assert payload["state"] == "configured"
    assert payload["missing_required_count"] == 0
    assert payload["missing_env"] == ["TRADINGCHASSIS_PAPER_PASSPHRASE"]


def test_required_env_present_but_empty_counts_as_missing(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(
        spec,
        env={
            "TRADINGCHASSIS_PAPER_API_KEY": "   ",
            "TRADINGCHASSIS_PAPER_API_SECRET": "dummy-secret",
        },
    )
    assert payload["state"] == "missing_credentials"
    assert payload["missing_required_count"] == 1
    assert "TRADINGCHASSIS_PAPER_API_KEY" in payload["missing_env"]
    assert "TRADINGCHASSIS_PAPER_API_KEY" not in payload["present_env"]
    rendered = json.dumps(payload, sort_keys=True)
    assert "dummy-secret" not in rendered


def test_evaluator_never_includes_env_values_in_payload(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(
        spec,
        env={
            "TRADINGCHASSIS_PAPER_API_KEY": "super-secret-key",
            "TRADINGCHASSIS_PAPER_API_SECRET": "super-secret-secret",
            "TRADINGCHASSIS_PAPER_PASSPHRASE": "top-secret-passphrase",
        },
    )
    rendered = json.dumps(payload, sort_keys=True)
    assert "super-secret-key" not in rendered
    assert "super-secret-secret" not in rendered
    assert "top-secret-passphrase" not in rendered


def test_write_connectivity_artifact_uses_deterministic_sorted_lists(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path, enabled=True)
    spec = load_run_spec(spec_path)

    payload = evaluate_connectivity_readiness(
        spec,
        env={
            "TRADINGCHASSIS_PAPER_API_SECRET": "secret",
            "TRADINGCHASSIS_PAPER_API_KEY": "key",
            "TRADINGCHASSIS_PAPER_PASSPHRASE": "pass",
        },
    )
    artifact_path = tmp_path / "connectivity_readiness.json"
    write_connectivity_readiness_artifact(artifact_path, payload)
    parsed = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert parsed["required_env"] == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
    ]
    assert parsed["optional_env"] == ["TRADINGCHASSIS_PAPER_PASSPHRASE"]
    assert parsed["present_env"] == [
        "TRADINGCHASSIS_PAPER_API_KEY",
        "TRADINGCHASSIS_PAPER_API_SECRET",
        "TRADINGCHASSIS_PAPER_PASSPHRASE",
    ]
    assert parsed["missing_env"] == []
