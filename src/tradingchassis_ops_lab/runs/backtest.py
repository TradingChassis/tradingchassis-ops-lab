"""Backtest lifecycle orchestration for minimal NautilusTrader smoke runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.engines.nautilus.backtest import run_nautilus_backtest_smoke
from tradingchassis_ops_lab.reports.render import render_backtest_nautilus_smoke_report
from tradingchassis_ops_lab.runs.artifacts import initialize_run_artifacts
from tradingchassis_ops_lab.runs.hashing import compute_config_sha256
from tradingchassis_ops_lab.runs.journal import append_journal_event
from tradingchassis_ops_lab.runs.metadata import build_initial_metadata, write_metadata
from tradingchassis_ops_lab.runs.spec import RunSpec, load_run_spec


class InvalidBacktestModeError(ValueError):
    """Raised when a non-backtest spec is used with backtest command."""


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _build_lifecycle_event(
    *,
    event: str,
    status: str,
    spec: RunSpec,
    config_sha256: str,
    artifacts_dir: Path,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ts_utc": _utc_now_iso8601(),
        "event": event,
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": spec.engine,
        "status": status,
        "config_sha256": config_sha256,
        "artifacts_dir": str(artifacts_dir.resolve()),
    }
    if extra_fields:
        payload.update(extra_fields)
    return payload


def _write_smoke_metrics(
    path: Path,
    *,
    spec: RunSpec,
    input_candles_count: int,
    bars_processed: int,
    engine_duration_ms: int,
    scenario_name: str,
    scenario_version: str,
    strategy_registered: bool,
    bars_seen: int,
    orders_submitted: int,
    fills_count: int,
    deterministic_action_triggered: bool,
) -> None:
    payload = {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": "nautilus",
        "status": "completed",
        "is_placeholder": False,
        "engine_executed": True,
        "dataset": spec.data.dataset,
        "scenario_name": scenario_name,
        "scenario_version": scenario_version,
        "strategy_registered": strategy_registered,
        "input_candles_count": input_candles_count,
        "bars_processed": bars_processed,
        "engine_duration_ms": engine_duration_ms,
        "bars_seen": bars_seen,
        "orders_submitted": orders_submitted,
        "fills_count": fills_count,
        "deterministic_action_triggered": deterministic_action_triggered,
        "metrics": {},
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_backtest_lifecycle(spec_path: Path) -> tuple[Path, str]:
    """Run minimal NautilusTrader smoke backtest lifecycle and persist artifacts.

    Current behavior executes one built-in Nautilus smoke demo scenario based
    on RunSpec strategy identity fields. Custom strategy loading is deferred.
    """
    spec = load_run_spec(spec_path)
    if spec.mode != "backtest":
        raise InvalidBacktestModeError(
            f"Spec mode must be backtest for `tc run backtest`; got mode={spec.mode}"
        )

    config_sha256 = compute_config_sha256(spec)
    artifacts_dir = initialize_run_artifacts(
        spec_path=spec_path,
        spec=spec,
        config_sha256=config_sha256,
    )

    metadata = build_initial_metadata(
        spec=spec,
        spec_path=spec_path,
        artifacts_dir=artifacts_dir,
        config_sha256=config_sha256,
    )
    metadata["status"] = "running"
    metadata["started_at_utc"] = _utc_now_iso8601()
    metadata["lifecycle"] = "backtest_nautilus_smoke"
    metadata["is_placeholder"] = False
    engine_started_at = _utc_now_iso8601()
    metadata["engine_execution"] = {
        "status": "running",
        "engine": "nautilus",
        "scenario_name": spec.strategy.name,
        "scenario_version": spec.strategy.version,
        "strategy_registered": False,
        "bars_seen": 0,
        "orders_submitted": 0,
        "fills_count": 0,
        "deterministic_action_triggered": False,
        "nautilus_version": None,
        "started_at_utc": engine_started_at,
        "completed_at_utc": None,
        "error": None,
    }
    write_metadata(artifacts_dir / "metadata.json", metadata)

    journal_path = artifacts_dir / "journal.jsonl"
    append_journal_event(
        journal_path,
        _build_lifecycle_event(
            event="run_started",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
        ),
    )
    append_journal_event(
        journal_path,
        _build_lifecycle_event(
            event="backtest_started",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
            extra_fields={"note": "nautilus engine smoke run started"},
        ),
    )

    try:
        smoke_result = run_nautilus_backtest_smoke(
            dataset=spec.data.dataset,
            venue=spec.venue,
            instrument=spec.instrument,
            scenario_name=spec.strategy.name,
            scenario_version=spec.strategy.version,
        )
    except Exception as exc:
        failed_at = _utc_now_iso8601()
        metadata["status"] = "failed"
        metadata["completed_at_utc"] = failed_at
        metadata["engine_execution"] = {
            "status": "failed",
            "engine": "nautilus",
            "scenario_name": spec.strategy.name,
            "scenario_version": spec.strategy.version,
            "strategy_registered": False,
            "bars_seen": 0,
            "orders_submitted": 0,
            "fills_count": 0,
            "deterministic_action_triggered": False,
            "nautilus_version": None,
            "started_at_utc": engine_started_at,
            "completed_at_utc": failed_at,
            "error": str(exc),
        }
        write_metadata(artifacts_dir / "metadata.json", metadata)
        append_journal_event(
            journal_path,
            _build_lifecycle_event(
                event="run_failed",
                status="failed",
                spec=spec,
                config_sha256=config_sha256,
                artifacts_dir=artifacts_dir,
                extra_fields={"error": str(exc)},
            ),
        )
        raise

    append_journal_event(
        journal_path,
        _build_lifecycle_event(
            event="backtest_completed",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
            extra_fields={
                "result": "engine_smoke_completed",
                "input_candles_count": smoke_result.input_candles_count,
                "bars_processed": smoke_result.bars_processed,
                "scenario_name": smoke_result.scenario_name,
                "scenario_version": smoke_result.scenario_version,
                "strategy_registered": smoke_result.strategy_registered,
                "bars_seen": smoke_result.bars_seen,
                "orders_submitted": smoke_result.orders_submitted,
                "fills_count": smoke_result.fills_count,
                "deterministic_action_triggered": smoke_result.deterministic_action_triggered,
            },
        ),
    )

    _write_smoke_metrics(
        artifacts_dir / "metrics.json",
        spec=spec,
        input_candles_count=smoke_result.input_candles_count,
        bars_processed=smoke_result.bars_processed,
        engine_duration_ms=smoke_result.engine_duration_ms,
        scenario_name=smoke_result.scenario_name,
        scenario_version=smoke_result.scenario_version,
        strategy_registered=smoke_result.strategy_registered,
        bars_seen=smoke_result.bars_seen,
        orders_submitted=smoke_result.orders_submitted,
        fills_count=smoke_result.fills_count,
        deterministic_action_triggered=smoke_result.deterministic_action_triggered,
    )
    (artifacts_dir / "report.md").write_text(
        render_backtest_nautilus_smoke_report(
            run_id=spec.run_id,
            dataset=spec.data.dataset,
            status="completed",
            input_candles_count=smoke_result.input_candles_count,
            bars_processed=smoke_result.bars_processed,
            engine_duration_ms=smoke_result.engine_duration_ms,
            scenario_name=smoke_result.scenario_name,
            scenario_version=smoke_result.scenario_version,
            strategy_registered=smoke_result.strategy_registered,
            bars_seen=smoke_result.bars_seen,
            orders_submitted=smoke_result.orders_submitted,
            fills_count=smoke_result.fills_count,
            deterministic_action_triggered=smoke_result.deterministic_action_triggered,
        ),
        encoding="utf-8",
    )

    completed_at = _utc_now_iso8601()
    metadata["status"] = "completed"
    metadata["completed_at_utc"] = completed_at
    metadata["engine_execution"] = {
        "status": "completed",
        "engine": "nautilus",
        "scenario_name": smoke_result.scenario_name,
        "scenario_version": smoke_result.scenario_version,
        "strategy_registered": smoke_result.strategy_registered,
        "bars_seen": smoke_result.bars_seen,
        "orders_submitted": smoke_result.orders_submitted,
        "fills_count": smoke_result.fills_count,
        "deterministic_action_triggered": smoke_result.deterministic_action_triggered,
        "nautilus_version": smoke_result.nautilus_version,
        "started_at_utc": engine_started_at,
        "completed_at_utc": completed_at,
        "error": None,
    }
    write_metadata(artifacts_dir / "metadata.json", metadata)

    append_journal_event(
        journal_path,
        _build_lifecycle_event(
            event="run_completed",
            status="completed",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
        ),
    )

    return artifacts_dir, config_sha256
