"""Unit tests for backtest vs paper evidence comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingchassis_ops_lab.evidence.compare import (
    EvidenceArtifactsParseError,
    compare_backtest_paper,
)


def _write_run_dir(
    *,
    root: Path,
    run_id: str,
    metadata: dict,
    metrics: dict,
    journal: list[dict],
    write_report: bool = True,
    readiness: dict | None = None,
    probe: dict | None = None,
    reconciliation: dict | None = None,
) -> Path:
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "journal.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in journal),
        encoding="utf-8",
    )
    if write_report:
        (run_dir / "report.md").write_text("# report\n", encoding="utf-8")
    if readiness is not None:
        (run_dir / "connectivity_readiness.json").write_text(
            json.dumps(readiness, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if probe is not None:
        (run_dir / "connectivity_probe.json").write_text(
            json.dumps(probe, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if reconciliation is not None:
        (run_dir / "reconciliation_result.json").write_text(
            json.dumps(reconciliation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return run_dir


def _backtest_metadata(*, run_id: str, config_sha256: str = "backtest-hash") -> dict:
    return {
        "schema_version": "v1",
        "run_id": run_id,
        "mode": "backtest",
        "engine": "nautilus",
        "status": "completed",
        "config_sha256": config_sha256,
        "venue": "binance",
        "instrument": "BTCUSDT",
        "strategy": {"name": "ops_smoke_demo", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "lifecycle": "backtest_nautilus_smoke",
        "is_placeholder": False,
    }


def _backtest_metrics() -> dict:
    return {
        "schema_version": "v1",
        "run_id": "unused",
        "mode": "backtest",
        "engine": "nautilus",
        "status": "completed",
        "is_placeholder": False,
        "engine_executed": True,
        "dataset": "btcusdt-sample",
        "scenario_name": "ops_smoke_demo",
        "scenario_version": "0.1.0",
        "strategy_registered": True,
        "input_candles_count": 20,
        "bars_processed": 20,
        "engine_duration_ms": 1400,
        "bars_seen": 20,
        "orders_submitted": 0,
        "fills_count": 0,
        "deterministic_action_triggered": True,
        "metrics": {},
    }


def _backtest_journal() -> list[dict]:
    return [
        {"event": "run_started"},
        {"event": "backtest_started"},
        {"event": "backtest_completed"},
        {"event": "run_completed"},
    ]


def _paper_metadata(
    *,
    run_id: str,
    status: str = "completed",
    config_sha256: str = "paper-hash",
    kill_switch_state: str = "absent",
    lifecycle_outcome: str = "checked_continue",
) -> dict:
    return {
        "schema_version": "v1",
        "run_id": run_id,
        "mode": "paper",
        "engine": "nautilus",
        "status": status,
        "config_sha256": config_sha256,
        "venue": "binance_testnet",
        "instrument": "BTCUSDT",
        "strategy": {"name": "ops_smoke_demo", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "lifecycle": "paper_skeleton",
        "is_placeholder": True,
        "safety": {
            "kill_switch": {"state": kill_switch_state},
            "lifecycle_outcome": lifecycle_outcome,
        },
    }


def _paper_metrics(*, status: str = "completed", heartbeat_count: int = 3) -> dict:
    return {
        "schema_version": "v1",
        "run_id": "unused",
        "mode": "paper",
        "engine": "nautilus",
        "status": status,
        "is_placeholder": True,
        "engine_executed": False,
        "connectivity": "none",
        "paper_lifecycle": "synthetic_heartbeat"
        if status == "completed"
        else "blocked_kill_switch",
        "heartbeat_count": heartbeat_count,
        "synthetic_duration_seconds": 3 if status == "completed" else 0,
        "metrics": {},
    }


def _paper_journal(*, blocked: bool = False) -> list[dict]:
    if blocked:
        return [
            {"event": "run_started"},
            {"event": "paper_safety_checked"},
            {"event": "paper_safety_blocked"},
            {"event": "run_completed"},
        ]
    return [
        {"event": "run_started"},
        {"event": "paper_safety_checked"},
        {"event": "paper_started"},
        {"event": "paper_heartbeat"},
        {"event": "paper_heartbeat"},
        {"event": "paper_heartbeat"},
        {"event": "paper_completed"},
        {"event": "run_completed"},
    ]


def _pair_dirs(tmp_path: Path) -> tuple[Path, Path]:
    backtest_dir = _write_run_dir(
        root=tmp_path,
        run_id="bt-run",
        metadata=_backtest_metadata(run_id="bt-run"),
        metrics=_backtest_metrics(),
        journal=_backtest_journal(),
    )
    paper_dir = _write_run_dir(
        root=tmp_path,
        run_id="paper-run",
        metadata=_paper_metadata(run_id="paper-run"),
        metrics=_paper_metrics(),
        journal=_paper_journal(),
    )
    return backtest_dir, paper_dir


def test_compare_completed_runs_returns_schema_and_expected_status(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)

    evidence = compare_backtest_paper(
        backtest_dir,
        paper_dir,
        created_at_utc="2026-06-01T10:00:00Z",
    )

    assert evidence["schema_version"] == "v1"
    assert evidence["created_at_utc"] == "2026-06-01T10:00:00Z"
    assert evidence["backtest_run_id"] == "bt-run"
    assert evidence["paper_run_id"] == "paper-run"
    assert evidence["comparison_status"] == "differences_expected"


def test_compare_includes_expected_top_level_keys(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    evidence = compare_backtest_paper(backtest_dir, paper_dir)

    assert sorted(evidence.keys()) == [
        "artifact_presence",
        "backtest_run_id",
        "compared_fields",
        "comparison_status",
        "connectivity_summary",
        "created_at_utc",
        "journal_summary",
        "known_gaps",
        "mode_summary",
        "non_goals",
        "notes",
        "paper_run_id",
        "safety_summary",
        "schema_version",
    ]


def test_artifact_presence_detects_core_and_optional_artifacts(tmp_path: Path) -> None:
    backtest_dir = _write_run_dir(
        root=tmp_path,
        run_id="bt-run",
        metadata=_backtest_metadata(run_id="bt-run"),
        metrics=_backtest_metrics(),
        journal=_backtest_journal(),
    )
    paper_dir = _write_run_dir(
        root=tmp_path,
        run_id="paper-run",
        metadata=_paper_metadata(run_id="paper-run"),
        metrics=_paper_metrics(),
        journal=_paper_journal(),
        readiness={"state": "configured"},
        probe={"state": "probe_ok"},
        reconciliation={"status": "ok"},
    )

    evidence = compare_backtest_paper(backtest_dir, paper_dir)

    assert evidence["artifact_presence"]["backtest"]["metadata.json"] is True
    assert evidence["artifact_presence"]["paper"]["metrics.json"] is True
    assert evidence["artifact_presence"]["backtest"]["connectivity_probe.json"] is False
    assert evidence["artifact_presence"]["paper"]["connectivity_probe.json"] is True
    assert evidence["artifact_presence"]["paper"]["reconciliation_result.json"] is True


def test_journal_summary_and_shared_events_are_deterministic(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    evidence = compare_backtest_paper(backtest_dir, paper_dir)

    assert evidence["journal_summary"]["backtest"]["event_total"] == 4
    assert evidence["journal_summary"]["paper"]["event_total"] == 8
    assert evidence["journal_summary"]["shared_events"] == ["run_completed", "run_started"]


def test_mode_summary_includes_backtest_and_paper_operational_facts(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    evidence = compare_backtest_paper(backtest_dir, paper_dir)

    backtest_summary = evidence["mode_summary"]["backtest"]
    paper_summary = evidence["mode_summary"]["paper"]
    assert backtest_summary["scenario_name"] == "ops_smoke_demo"
    assert backtest_summary["bars_seen"] == 20
    assert backtest_summary["deterministic_action_triggered"] is True
    assert paper_summary["heartbeat_count"] == 3
    assert paper_summary["safety_lifecycle_outcome"] == "checked_continue"
    assert paper_summary["engine_executed"] is False


def test_venue_and_config_hash_mismatch_are_contextual_not_incompatible(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    evidence = compare_backtest_paper(backtest_dir, paper_dir)

    comparisons = {item["area"]: item for item in evidence["compared_fields"]}
    assert evidence["comparison_status"] == "differences_expected"
    assert comparisons["venue"]["comparable"] == "contextual"
    assert comparisons["venue"]["match"] is False
    assert comparisons["config_hash"]["comparable"] == "contextual"
    assert comparisons["config_hash"]["match"] is False
    assert comparisons["backtest_bars_vs_paper_heartbeat"]["comparable"] == "mode_specific"
    assert comparisons["safety_state"]["comparable"] == "gap"
    assert comparisons["readiness_state"]["comparable"] == "future_candidate"


def test_missing_required_artifact_returns_missing_artifacts_status(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    (paper_dir / "report.md").unlink()

    evidence = compare_backtest_paper(
        backtest_dir, paper_dir, created_at_utc="2026-06-01T10:00:00Z"
    )

    assert evidence["comparison_status"] == "missing_artifacts"
    assert "paper missing required artifacts" in " ".join(evidence["notes"])
    assert evidence["artifact_presence"]["paper"]["report.md"] is False


def test_wrong_modes_return_incompatible_runs(tmp_path: Path) -> None:
    backtest_dir = _write_run_dir(
        root=tmp_path,
        run_id="left-run",
        metadata=_backtest_metadata(run_id="left-run"),
        metrics=_backtest_metrics(),
        journal=_backtest_journal(),
    )
    paper_dir = _write_run_dir(
        root=tmp_path,
        run_id="right-run",
        metadata={**_paper_metadata(run_id="right-run"), "mode": "backtest"},
        metrics=_paper_metrics(),
        journal=_paper_journal(),
    )

    evidence = compare_backtest_paper(backtest_dir, paper_dir)
    assert evidence["comparison_status"] == "incompatible_runs"


def test_safety_blocked_paper_is_handled_as_valid_evidence(tmp_path: Path) -> None:
    backtest_dir = _write_run_dir(
        root=tmp_path,
        run_id="bt-run",
        metadata=_backtest_metadata(run_id="bt-run"),
        metrics=_backtest_metrics(),
        journal=_backtest_journal(),
    )
    paper_dir = _write_run_dir(
        root=tmp_path,
        run_id="paper-run",
        metadata=_paper_metadata(
            run_id="paper-run",
            status="safety_blocked",
            kill_switch_state="active",
            lifecycle_outcome="blocked_kill_switch",
        ),
        metrics=_paper_metrics(status="safety_blocked", heartbeat_count=0),
        journal=_paper_journal(blocked=True),
    )

    evidence = compare_backtest_paper(backtest_dir, paper_dir)
    assert evidence["comparison_status"] == "differences_expected"
    assert evidence["mode_summary"]["paper"]["status"] == "safety_blocked"
    assert evidence["mode_summary"]["paper"]["heartbeat_count"] == 0
    assert evidence["safety_summary"]["paper_kill_switch_state"] == "active"


def test_known_gaps_non_goals_and_scope_boundaries_are_stable(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    evidence = compare_backtest_paper(backtest_dir, paper_dir)
    evidence_text = json.dumps(evidence, sort_keys=True)

    assert evidence["known_gaps"] == [
        "backtest_no_safety_gate",
        "config_hash_mismatch_expected",
        "external_state_not_available",
        "fill_quality_not_available_no_fills",
        "orderbook_not_available_candle_only",
        "paper_no_engine_execution",
        "paper_no_market_data",
        "pnl_not_available",
        "readiness_probe_optional",
        "reconciliation_not_cross_run",
        "returns_sharpe_not_available",
        "slippage_not_available_no_orders",
        "strategy_plugin_not_available",
        "venue_label_mismatch_allowed",
    ]
    assert evidence["non_goals"] == [
        "alpha",
        "live_paper_trading",
        "order_execution",
        "pnl",
        "returns",
        "sharpe",
        "strategy_optimization",
    ]
    assert "backtest_pnl" not in evidence_text
    assert "profitability" not in evidence_text
    assert "performance" in evidence_text


def test_optional_readiness_probe_and_reconciliation_summary(tmp_path: Path) -> None:
    backtest_dir = _write_run_dir(
        root=tmp_path,
        run_id="bt-run",
        metadata=_backtest_metadata(run_id="bt-run"),
        metrics=_backtest_metrics(),
        journal=_backtest_journal(),
        readiness={"state": "disabled"},
        reconciliation={"status": "warning"},
    )
    paper_dir = _write_run_dir(
        root=tmp_path,
        run_id="paper-run",
        metadata=_paper_metadata(run_id="paper-run"),
        metrics=_paper_metrics(),
        journal=_paper_journal(),
        readiness={"state": "configured"},
        probe={"state": "probe_ok"},
    )

    evidence = compare_backtest_paper(backtest_dir, paper_dir)
    summary = evidence["connectivity_summary"]

    assert summary["backtest_readiness"] == "disabled"
    assert summary["paper_readiness"] == "configured"
    assert summary["paper_probe"] == "probe_ok"
    assert summary["backtest_probe"] is None
    assert summary["backtest_reconciliation"] == "warning"
    assert summary["paper_reconciliation"] is None


def test_compare_is_deterministic_when_created_at_is_injected(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    first = compare_backtest_paper(backtest_dir, paper_dir, created_at_utc="2026-06-01T10:00:00Z")
    second = compare_backtest_paper(backtest_dir, paper_dir, created_at_utc="2026-06-01T10:00:00Z")
    assert first == second


def test_malformed_required_json_raises_clear_error(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    (backtest_dir / "metadata.json").write_text("{broken-json", encoding="utf-8")

    with pytest.raises(EvidenceArtifactsParseError):
        compare_backtest_paper(backtest_dir, paper_dir)


def test_malformed_journal_jsonl_raises_clear_error(tmp_path: Path) -> None:
    backtest_dir, paper_dir = _pair_dirs(tmp_path)
    (paper_dir / "journal.jsonl").write_text(
        '{"event": "run_started"}\n{broken-json\n',
        encoding="utf-8",
    )

    with pytest.raises(EvidenceArtifactsParseError, match="journal.jsonl") as exc_info:
        compare_backtest_paper(backtest_dir, paper_dir)

    assert "line 2" in str(exc_info.value)
