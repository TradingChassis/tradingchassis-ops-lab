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
