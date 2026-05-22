"""Unit tests for deterministic local failure drills."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingchassis_ops_lab.drills.errors import DrillArtifactsError
from tradingchassis_ops_lab.drills.executor import (
    execute_reconciliation_mismatch_drill,
    execute_restart_recovery_drill,
    execute_stale_market_data_drill,
)
from tradingchassis_ops_lab.observability.metrics import export_run_metrics


def _prepare_run_dir(tmp_path: Path, run_id: str, *, with_journal: bool = False) -> Path:
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_spec.yaml").write_text("spec_version: v1\n", encoding="utf-8")
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "paper",
                "engine": "nautilus",
                "venue": "binance_testnet",
                "instrument": "BTCUSDT",
                "status": "completed",
                "created_at_utc": "2026-05-20T19:00:00Z",
                "data": {"dataset": "btcusdt-sample"},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {"is_placeholder": True, "engine_executed": False},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if with_journal:
        (run_dir / "journal.jsonl").write_text('{"event":"run_started"}\n', encoding="utf-8")
    return run_dir


def test_stale_market_data_writes_expected_warning_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-stale"
    run_dir = _prepare_run_dir(tmp_path, run_id, with_journal=True)

    result = execute_stale_market_data_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    report = result["report"]
    report_path = Path(result["report_path"])
    assert report["drill_name"] == "stale_market_data"
    assert report["outcome"] == "expected_warning"
    assert report["reconciliation_status"] == "warning"
    assert report["summary"]["warning"] >= 1
    assert report["status"] == "completed"
    assert report["pass"] is True
    assert report_path == run_dir / "drills" / "stale_market_data.json"
    assert report_path.is_file()


def test_reconciliation_mismatch_writes_expected_mismatch_report(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-mismatch"
    run_dir = _prepare_run_dir(tmp_path, run_id, with_journal=True)

    result = execute_reconciliation_mismatch_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    report = result["report"]
    report_path = Path(result["report_path"])
    assert report["drill_name"] == "reconciliation_mismatch"
    assert report["outcome"] == "expected_mismatch"
    assert report["reconciliation_status"] == "mismatch"
    assert report["summary"]["mismatch"] >= 1
    assert report["status"] == "completed"
    assert report["pass"] is True
    assert report_path == run_dir / "drills" / "reconciliation_mismatch.json"
    assert report_path.is_file()


def test_restart_recovery_writes_checklist_and_statement(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-restart"
    run_dir = _prepare_run_dir(tmp_path, run_id, with_journal=True)

    result = execute_restart_recovery_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    report = result["report"]
    report_path = Path(result["report_path"])
    assert report["drill_name"] == "restart_recovery"
    assert report["outcome"] == "simulated_recovery_ok"
    assert report["summary"]["run_dir_exists"] is True
    assert report["summary"]["metadata_present"] is True
    assert report["summary"]["run_spec_present"] is True
    assert report["summary"]["journal_present"] is True
    assert report["summary"]["metrics_present"] is True
    assert (
        report["statement"]
        == "no process restart performed; this is artifact-based recovery rehearsal"
    )
    assert report_path == run_dir / "drills" / "restart_recovery.json"
    assert report_path.is_file()


def test_missing_run_directory_fails_clearly(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DrillArtifactsError):
        execute_stale_market_data_drill(
            run_id="drill-missing",
            artifacts_root=tmp_path / "artifacts" / "runs",
        )


def test_journal_append_when_present_and_absent_behavior(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with_journal = "drill-journal-present"
    without_journal = "drill-journal-absent"

    run_dir_with_journal = _prepare_run_dir(tmp_path, with_journal, with_journal=True)
    run_dir_without_journal = _prepare_run_dir(tmp_path, without_journal, with_journal=False)

    execute_stale_market_data_drill(
        run_id=with_journal,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )
    execute_stale_market_data_drill(
        run_id=without_journal,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    with_lines = (run_dir_with_journal / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(with_lines) == 3
    with_event = json.loads(with_lines[-1])
    assert with_event["event"] == "failure_drill_executed"
    assert with_event["drill_name"] == "stale_market_data"

    assert not (run_dir_without_journal / "journal.jsonl").exists()
    assert (run_dir_without_journal / "drills" / "stale_market_data.json").is_file()


def test_deterministic_shape_and_stable_keys(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-stable-shape"
    run_dir = _prepare_run_dir(tmp_path, run_id, with_journal=False)
    report_path = run_dir / "drills" / "restart_recovery.json"

    first = execute_restart_recovery_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )
    second = execute_restart_recovery_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )

    assert list(first["report"].keys()) == list(second["report"].keys())
    written_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert sorted(first["report"].keys()) == sorted(written_payload.keys())


def test_metrics_include_failure_drill_journal_event_when_present(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-metrics-journal"
    _prepare_run_dir(tmp_path, run_id, with_journal=True)

    execute_restart_recovery_drill(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
    )
    rendered = export_run_metrics(
        run_id=run_id,
        artifacts_root=tmp_path / "artifacts" / "runs",
        include_journal=True,
    )

    assert "tradingchassis_ops_lab_journal_event_total{" in rendered
    assert 'event="failure_drill_executed"} 1' in rendered
