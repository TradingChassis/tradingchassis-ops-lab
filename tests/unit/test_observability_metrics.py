"""Unit tests for artifact-driven observability metrics rendering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingchassis_ops_lab.observability.metrics import (
    RunArtifactsFileMissingError,
    RunArtifactsNotFoundError,
    RunArtifactsParseError,
    discover_run_ids,
    export_run_metrics,
    render_metrics_text,
)


def _write_run_artifacts(
    *,
    artifacts_root: Path,
    run_id: str,
    metadata: dict,
    metrics: dict,
    journal_lines: list[dict] | None = None,
    connectivity_readiness: dict | None = None,
    connectivity_probe: dict | None = None,
) -> Path:
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if journal_lines is not None:
        (run_dir / "journal.jsonl").write_text(
            "".join(json.dumps(line, sort_keys=True) + "\n" for line in journal_lines),
            encoding="utf-8",
        )
    if connectivity_readiness is not None:
        (run_dir / "connectivity_readiness.json").write_text(
            json.dumps(connectivity_readiness, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if connectivity_probe is not None:
        (run_dir / "connectivity_probe.json").write_text(
            json.dumps(connectivity_probe, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return run_dir


def test_render_backtest_metrics_from_artifacts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-backtest"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "started_at_utc": "2026-05-20T19:00:01Z",
            "completed_at_utc": "2026-05-20T19:00:03Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={
            "dataset": "btcusdt-sample",
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
            "bars_processed": 20,
            "engine_duration_ms": 1500,
        },
        journal_lines=[
            {"event": "run_started"},
            {"event": "backtest_started"},
            {"event": "backtest_completed"},
            {"event": "run_completed"},
        ],
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_run_info{" in rendered
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in rendered
    assert "tradingchassis_ops_lab_backtest_bars_processed_total" in rendered
    assert "tradingchassis_ops_lab_backtest_engine_duration_seconds" in rendered


def test_render_scenario_metrics_from_artifacts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-backtest-scenario"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={
            "dataset": "btcusdt-sample",
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
            "bars_processed": 20,
            "engine_duration_ms": 1500,
            "scenario_name": "ops_smoke_demo",
            "scenario_version": "0.1.0",
            "strategy_registered": True,
            "bars_seen": 20,
            "orders_submitted": 0,
            "fills_count": 0,
            "deterministic_action_triggered": True,
        },
        journal_lines=[{"event": "run_started"}, {"event": "run_completed"}],
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)

    scenario_labels = (
        'run_id="metrics-backtest-scenario",scenario_name="ops_smoke_demo",scenario_version="0.1.0"'
    )
    assert (
        f"tradingchassis_ops_lab_backtest_scenario_strategy_registered{{{scenario_labels}}} 1"
        in rendered
    )
    assert (
        "tradingchassis_ops_lab_backtest_scenario_bars_seen_total"
        f"{{{scenario_labels}}} 20" in rendered
    )
    assert (
        "tradingchassis_ops_lab_backtest_scenario_orders_submitted_total"
        f"{{{scenario_labels}}} 0" in rendered
    )
    assert (
        f"tradingchassis_ops_lab_backtest_scenario_fills_total{{{scenario_labels}}} 0" in rendered
    )
    assert (
        "tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered"
        f"{{{scenario_labels}}} 1" in rendered
    )
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in rendered
    assert "tradingchassis_ops_lab_backtest_bars_processed_total" in rendered
    assert "tradingchassis_ops_lab_backtest_engine_duration_seconds" in rendered
    assert "tradingchassis_ops_lab_backtest_pnl" not in rendered
    assert "tradingchassis_ops_lab_backtest_returns" not in rendered
    assert "tradingchassis_ops_lab_backtest_sharpe" not in rendered
    assert "tradingchassis_ops_lab_backtest_alpha" not in rendered
    assert "tradingchassis_ops_lab_backtest_profitability" not in rendered


def test_render_scenario_metric_booleans_encode_as_zero_or_one(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-backtest-scenario-bools"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={
            "is_placeholder": False,
            "engine_executed": True,
            "scenario_name": "ops_smoke_demo",
            "strategy_registered": False,
            "deterministic_action_triggered": False,
            "bars_seen": 20,
            "orders_submitted": 0,
            "fills_count": 0,
        },
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert (
        'tradingchassis_ops_lab_backtest_scenario_strategy_registered{run_id="metrics-backtest-scenario-bools",'
        'scenario_name="ops_smoke_demo"} 0' in rendered
    )
    assert (
        "tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered"
        '{run_id="metrics-backtest-scenario-bools",scenario_name="ops_smoke_demo"} 0' in rendered
    )


def test_render_scenario_metrics_omitted_without_scenario_fields(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-backtest-no-scenario"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={
            "dataset": "btcusdt-sample",
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
            "bars_processed": 20,
            "engine_duration_ms": 1500,
        },
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_backtest_scenario_strategy_registered" not in rendered
    assert "tradingchassis_ops_lab_backtest_scenario_bars_seen_total" not in rendered
    assert "tradingchassis_ops_lab_backtest_scenario_orders_submitted_total" not in rendered
    assert "tradingchassis_ops_lab_backtest_scenario_fills_total" not in rendered
    assert "tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered" not in rendered
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in rendered


def test_render_paper_metrics_from_artifacts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-paper"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "started_at_utc": "2026-05-20T19:00:01Z",
            "completed_at_utc": "2026-05-20T19:00:04Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={
            "is_placeholder": True,
            "engine_executed": False,
            "heartbeat_count": 3,
            "synthetic_duration_seconds": 3,
        },
        journal_lines=[
            {"event": "run_started"},
            {"event": "paper_started"},
            {"event": "paper_heartbeat"},
            {"event": "paper_heartbeat"},
            {"event": "paper_completed"},
            {"event": "run_completed"},
        ],
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_run_info{" in rendered
    assert "tradingchassis_ops_lab_paper_heartbeat_total" in rendered
    assert "tradingchassis_ops_lab_paper_synthetic_duration_seconds" in rendered


def test_kill_switch_metric_emitted_when_safety_snapshot_exists(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-kill-switch-active"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "safety": {
                "kill_switch": {
                    "state": "active",
                    "checked_at_utc": "2026-05-22T12:00:00Z",
                    "last_reason": "manual stop",
                    "source": "runtime/kill_switch",
                }
            },
        },
        metrics={"is_placeholder": True, "engine_executed": False},
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_kill_switch_state{" in rendered
    assert 'run_id="metrics-kill-switch-active",state="active"} 2' in rendered


def test_kill_switch_metric_not_emitted_without_safety_snapshot(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-no-kill-switch-snapshot"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": False, "engine_executed": True},
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_kill_switch_state{" not in rendered


def test_connectivity_readiness_metrics_emitted_when_artifact_exists(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-readiness"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_readiness={
            "schema_version": "v1",
            "run_id": run_id,
            "state": "missing_credentials",
            "enabled": True,
            "missing_required_count": 2,
            "probe_performed": False,
            "required_env": ["TRADINGCHASSIS_PAPER_API_KEY", "TRADINGCHASSIS_PAPER_API_SECRET"],
            "present_env": [],
            "missing_env": ["TRADINGCHASSIS_PAPER_API_KEY", "TRADINGCHASSIS_PAPER_API_SECRET"],
        },
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    labels = (
        'run_id="metrics-connectivity-readiness",mode="paper",engine="nautilus",'
        'venue="binance",instrument="BTCUSDT",state="missing_credentials"'
    )
    assert f"tradingchassis_ops_lab_connectivity_readiness_state{{{labels}}} 2" in rendered
    assert f"tradingchassis_ops_lab_connectivity_readiness_enabled{{{labels}}} 1" in rendered
    assert (
        f"tradingchassis_ops_lab_connectivity_readiness_missing_required_env_total{{{labels}}} 2"
        in rendered
    )
    assert (
        f"tradingchassis_ops_lab_connectivity_readiness_probe_performed{{{labels}}} 0" in rendered
    )
    assert "tradingchassis_ops_lab_run_info{" in rendered


@pytest.mark.parametrize(
    ("state", "expected_value"),
    [
        ("disabled", 0),
        ("configured", 1),
        ("missing_credentials", 2),
        ("invalid_config", 3),
        ("unknown", -1),
        ("unexpected_state", -1),
    ],
)
def test_connectivity_readiness_state_metric_encoding(
    tmp_path: Path,
    state: str,
    expected_value: int,
) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = f"metrics-connectivity-state-{state}"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_readiness={
            "state": state,
            "enabled": False,
            "missing_required_count": 0,
            "probe_performed": True,
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert (
        "tradingchassis_ops_lab_connectivity_readiness_state"
        f'{{run_id="{run_id}",mode="paper",engine="nautilus",venue="binance",'
        f'instrument="BTCUSDT",state="{state}"}} {expected_value}'
    ) in rendered


def test_connectivity_readiness_metric_text_excludes_env_names_and_values(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-secrets"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_readiness={
            "state": "configured",
            "enabled": True,
            "missing_required_count": 0,
            "probe_performed": False,
            "required_env": ["TRADINGCHASSIS_PAPER_API_KEY"],
            "present_env": ["TRADINGCHASSIS_PAPER_API_KEY"],
            "errors": ["dummy-secret-value"],
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "TRADINGCHASSIS_PAPER_API_KEY" not in rendered
    assert "dummy-secret-value" not in rendered


def test_connectivity_readiness_metrics_omitted_when_artifact_is_absent(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-absent"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_connectivity_readiness_state" not in rendered
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in rendered


def test_malformed_connectivity_readiness_result_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-malformed"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_readiness={
            "state": "configured",
            "enabled": "yes",
            "missing_required_count": 0,
            "probe_performed": False,
        },
    )

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


def test_connectivity_probe_metrics_emitted_when_artifact_exists(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "schema_version": "v1",
            "run_id": run_id,
            "target": "local_fake_http",
            "network_scope": "loopback_only",
            "probe_performed": True,
            "state": "probe_ok",
            "http_status": 200,
            "latency_ms": 12.3,
            "error_class": None,
            "url": "http://127.0.0.1:18081/health",
            "response_body_stored": False,
            "errors": [],
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    labels = (
        'run_id="metrics-connectivity-probe",mode="paper",engine="nautilus",'
        'venue="binance_testnet",instrument="BTCUSDT",state="probe_ok",'
        'network_scope="loopback_only"'
    )
    assert f"tradingchassis_ops_lab_connectivity_probe_state{{{labels}}} 1" in rendered
    assert f"tradingchassis_ops_lab_connectivity_probe_performed{{{labels}}} 1" in rendered
    assert (
        f"tradingchassis_ops_lab_connectivity_probe_latency_seconds{{{labels}}} 0.0123" in rendered
    )
    assert f"tradingchassis_ops_lab_connectivity_probe_http_status{{{labels}}} 200" in rendered


@pytest.mark.parametrize(
    ("state", "expected_value"),
    [
        ("probe_ok", 1),
        ("probe_http_error", 2),
        ("probe_timeout", 3),
        ("probe_unreachable", 4),
        ("probe_unknown", -1),
        ("unexpected_state", -1),
    ],
)
def test_connectivity_probe_state_metric_encoding(
    tmp_path: Path,
    state: str,
    expected_value: int,
) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = f"metrics-connectivity-probe-state-{state}"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "state": state,
            "probe_performed": True,
            "network_scope": "loopback_only",
            "http_status": None,
            "latency_ms": None,
            "error_class": None,
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert (
        "tradingchassis_ops_lab_connectivity_probe_state"
        f'{{run_id="{run_id}",mode="paper",engine="nautilus",venue="binance_testnet",'
        f'instrument="BTCUSDT",state="{state}",network_scope="loopback_only"}} {expected_value}'
    ) in rendered


def test_connectivity_probe_metrics_omit_http_status_when_null(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe-timeout"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "state": "probe_timeout",
            "probe_performed": True,
            "network_scope": "loopback_only",
            "http_status": None,
            "latency_ms": 99.0,
            "error_class": "timeout",
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_connectivity_probe_http_status" not in rendered
    assert "tradingchassis_ops_lab_connectivity_probe_latency_seconds" in rendered
    assert 'error_class="timeout"' in rendered


def test_connectivity_probe_performed_boolean_encoding(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe-bool"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "state": "probe_unknown",
            "probe_performed": False,
            "network_scope": "loopback_only",
            "http_status": None,
            "latency_ms": None,
            "error_class": "unknown",
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_connectivity_probe_performed{" in rendered
    assert f'run_id="{run_id}"' in rendered
    assert 'state="probe_unknown"' in rendered
    assert 'network_scope="loopback_only"' in rendered
    assert 'error_class="unknown"' in rendered
    assert "} 0" in rendered


def test_connectivity_probe_metric_text_excludes_url_response_and_errors(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe-safety"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "state": "probe_http_error",
            "probe_performed": True,
            "network_scope": "loopback_only",
            "http_status": 500,
            "latency_ms": 10.0,
            "error_class": "http_error",
            "url": "http://127.0.0.1:18081/health",
            "response_body_stored": False,
            "errors": ["dummy-sensitive-error"],
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "127.0.0.1:18081" not in rendered
    assert "/health" not in rendered
    assert "response_body_stored" not in rendered
    assert "dummy-sensitive-error" not in rendered
    assert "TRADINGCHASSIS_" not in rendered


def test_connectivity_probe_metrics_omitted_when_artifact_is_absent(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe-absent"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
        },
    )
    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_connectivity_probe_state" not in rendered
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in rendered


def test_malformed_connectivity_probe_result_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-connectivity-probe-malformed"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "initialized",
            "created_at_utc": "2026-05-20T19:00:00Z",
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        connectivity_probe={
            "state": "probe_ok",
            "probe_performed": "yes",
            "network_scope": "loopback_only",
        },
    )

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


@pytest.mark.parametrize(
    ("state", "expected_value"),
    [
        ("absent", 0),
        ("cleared", 1),
        ("active", 2),
        ("manual_override", -1),
        ("unknown", -1),
    ],
)
def test_kill_switch_metric_state_encoding(tmp_path: Path, state: str, expected_value: int) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = f"metrics-kill-switch-{state}"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "safety": {
                "kill_switch": {
                    "state": state,
                    "checked_at_utc": "2026-05-22T12:00:00Z",
                    "last_reason": None,
                    "source": "runtime/kill_switch",
                }
            },
        },
        metrics={"is_placeholder": True, "engine_executed": False},
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert (
        f'tradingchassis_ops_lab_kill_switch_state{{run_id="{run_id}",state="{state}"}} '
        f"{expected_value}"
    ) in rendered


def test_journal_metrics_include_total_and_per_event_counts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-journal"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        journal_lines=[
            {"event": "z_event"},
            {"event": "a_event"},
            {"event": "a_event"},
        ],
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_journal_events_total" in rendered
    assert 'event="a_event"} 2' in rendered
    assert 'event="z_event"} 1' in rendered
    assert rendered.index('event="a_event"') < rendered.index('event="z_event"')


def test_no_include_journal_omits_journal_metrics(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-no-journal"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True},
        journal_lines=[{"event": "run_started"}],
    )

    rendered = export_run_metrics(
        run_id=run_id,
        artifacts_root=artifacts_root,
        include_journal=False,
    )
    assert "tradingchassis_ops_lab_journal_events_total" not in rendered
    assert "tradingchassis_ops_lab_journal_event_total" not in rendered


def test_render_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-deterministic"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "started_at_utc": "2026-05-20T19:00:01Z",
            "completed_at_utc": "2026-05-20T19:00:05Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={
            "dataset": "btcusdt-sample",
            "is_placeholder": False,
            "engine_executed": True,
            "input_candles_count": 20,
            "bars_processed": 20,
            "engine_duration_ms": 1234,
        },
        journal_lines=[
            {"event": "run_started"},
            {"event": "backtest_started"},
        ],
    )

    first = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    second = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert first == second


def test_missing_run_directory_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    with pytest.raises(RunArtifactsNotFoundError):
        export_run_metrics(run_id="missing-run", artifacts_root=artifacts_root)


def test_missing_required_artifact_files_fail_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-missing-files"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RunArtifactsFileMissingError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


def test_malformed_json_or_jsonl_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "metrics-malformed"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text("{bad-json", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


def test_reconciliation_metrics_emitted_when_result_exists(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "reconcile-reconciliation-metrics"
    run_dir = _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": True, "engine_executed": False},
        journal_lines=[{"event": "run_started"}],
    )
    (run_dir / "reconciliation_result.json").write_text(
        json.dumps(
            {
                "schema_version": "v1",
                "run_id": run_id,
                "ts_utc": "2026-05-21T00:01:00Z",
                "status": "warning",
                "summary": {"ok": 2, "warning": 1, "mismatch": 0, "unknown": 0},
            }
        ),
        encoding="utf-8",
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_reconciliation_status{" in rendered
    assert 'run_id="reconcile-reconciliation-metrics"' in rendered
    assert 'status="warning"} 1' in rendered
    assert "tradingchassis_ops_lab_reconciliation_checks_total{" in rendered
    assert 'severity="warning"} 1' in rendered
    assert "tradingchassis_ops_lab_reconciliation_last_timestamp_seconds{" in rendered


def test_reconciliation_metrics_omitted_when_result_missing(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "reconcile-no-reconciliation-metrics"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True},
    )

    rendered = export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
    assert "tradingchassis_ops_lab_reconciliation_status" not in rendered
    assert "tradingchassis_ops_lab_reconciliation_checks_total" not in rendered
    assert "tradingchassis_ops_lab_reconciliation_last_timestamp_seconds" not in rendered


def test_malformed_reconciliation_result_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "reconcile-malformed-reconciliation"
    run_dir = _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id=run_id,
        metadata={
            "run_id": run_id,
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True},
    )
    (run_dir / "reconciliation_result.json").write_text("{bad-json", encoding="utf-8")

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)

    (run_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "journal.jsonl").write_text('{"event":"ok"}\n{bad-json\n', encoding="utf-8")

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


def test_render_metrics_text_all_runs_discovers_multiple_runs_deterministically(
    tmp_path: Path,
) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id="z-run",
        metadata={
            "run_id": "z-run",
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True},
    )
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id="a-run",
        metadata={
            "run_id": "a-run",
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": True, "engine_executed": False},
    )

    assert discover_run_ids(artifacts_root) == ["a-run", "z-run"]
    rendered = render_metrics_text(artifacts_root=artifacts_root)
    assert 'run_id="a-run"' in rendered
    assert 'run_id="z-run"' in rendered
    assert rendered.index('run_id="a-run"') < rendered.index('run_id="z-run"')


def test_render_metrics_text_single_run_limits_output(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id="only-this",
        metadata={
            "run_id": "only-this",
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True},
    )
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id="not-selected",
        metadata={
            "run_id": "not-selected",
            "mode": "paper",
            "engine": "nautilus",
            "venue": "binance_testnet",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": True, "engine_executed": False},
    )

    rendered = render_metrics_text(artifacts_root=artifacts_root, run_id="only-this")
    assert 'run_id="only-this"' in rendered
    assert 'run_id="not-selected"' not in rendered


def test_render_metrics_text_missing_selected_run_returns_comment(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    rendered = render_metrics_text(artifacts_root=artifacts_root, run_id="missing-run")
    assert rendered.startswith("#")
    assert "missing-run" in rendered
