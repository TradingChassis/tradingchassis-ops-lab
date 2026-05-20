"""Unit tests for Slice 7 artifact-driven observability metrics rendering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ops_lab.observability.metrics import (
    RunArtifactsFileMissingError,
    RunArtifactsNotFoundError,
    RunArtifactsParseError,
    export_run_metrics,
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
    run_id = "slice7-backtest"
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
    assert "ops_lab_run_info{" in rendered
    assert "ops_lab_backtest_input_candles_total" in rendered
    assert "ops_lab_backtest_bars_processed_total" in rendered
    assert "ops_lab_backtest_engine_duration_seconds" in rendered


def test_render_paper_metrics_from_artifacts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "slice7-paper"
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
    assert "ops_lab_run_info{" in rendered
    assert "ops_lab_paper_heartbeat_total" in rendered
    assert "ops_lab_paper_synthetic_duration_seconds" in rendered


def test_journal_metrics_include_total_and_per_event_counts(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "slice7-journal"
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
    assert "ops_lab_journal_events_total" in rendered
    assert 'event="a_event"} 2' in rendered
    assert 'event="z_event"} 1' in rendered
    assert rendered.index('event="a_event"') < rendered.index('event="z_event"')


def test_no_include_journal_omits_journal_metrics(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "slice7-no-journal"
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
    assert "ops_lab_journal_events_total" not in rendered
    assert "ops_lab_journal_event_total" not in rendered


def test_render_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "slice7-deterministic"
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
    run_id = "slice7-missing-files"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RunArtifactsFileMissingError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)


def test_malformed_json_or_jsonl_fails_clearly(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "slice7-malformed"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text("{bad-json", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)

    (run_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "journal.jsonl").write_text('{"event":"ok"}\n{bad-json\n', encoding="utf-8")

    with pytest.raises(RunArtifactsParseError):
        export_run_metrics(run_id=run_id, artifacts_root=artifacts_root)
