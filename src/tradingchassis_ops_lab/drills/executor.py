"""Deterministic local failure drill execution."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.drills.errors import DrillArtifactsError, DrillValidationError
from tradingchassis_ops_lab.reconciliation.checks import (
    ReconciliationError,
    run_reconciliation_check,
)
from tradingchassis_ops_lab.runs.journal import append_journal_event

_SCHEMA_VERSION = "v1"
_LIMITATIONS = [
    "local file-based demonstration only",
    "no exchange connectivity",
    "no order cancel/flatten/restart orchestration",
]
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_FIXTURE = _REPO_ROOT / "examples/reconciliation/expected_match.json"
_STALE_OBSERVED_FIXTURE = _REPO_ROOT / "examples/reconciliation/observed_stale_warning.json"
_MISMATCH_OBSERVED_FIXTURE = _REPO_ROOT / "examples/reconciliation/observed_position_mismatch.json"


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _validate_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise DrillValidationError("run_id must be a non-empty string.")
    return normalized


def _ensure_run_dir(run_id: str, artifacts_root: Path) -> Path:
    run_dir = artifacts_root / run_id
    if not run_dir.is_dir():
        raise DrillArtifactsError(f"Run artifacts directory not found: {run_dir}")
    return run_dir


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise DrillArtifactsError(f"Fixture file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DrillArtifactsError(f"Malformed JSON fixture {path}: {exc}") from exc
    except OSError as exc:
        raise DrillArtifactsError(f"Failed to read fixture file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise DrillArtifactsError(f"Fixture payload must be JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise DrillArtifactsError(f"Failed to write drill artifact {path}: {exc}") from exc


def _rewrite_fixture_run_id(payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    copied = dict(payload)
    copied["run_id"] = run_id
    return copied


def _run_fixture_reconciliation(
    *,
    run_id: str,
    expected_fixture_path: Path,
    observed_fixture_path: Path,
    artifacts_root: Path,
) -> dict[str, Any]:
    expected_payload = _rewrite_fixture_run_id(_load_json_object(expected_fixture_path), run_id)
    observed_payload = _rewrite_fixture_run_id(_load_json_object(observed_fixture_path), run_id)

    with tempfile.TemporaryDirectory(prefix="tradingchassis-ops-lab-drill-") as temp_dir:
        temp_path = Path(temp_dir)
        expected_path = temp_path / "expected.json"
        observed_path = temp_path / "observed.json"
        _write_json(expected_path, expected_payload)
        _write_json(observed_path, observed_payload)
        try:
            return run_reconciliation_check(
                run_id=run_id,
                expected_path=expected_path,
                observed_path=observed_path,
                artifacts_root=artifacts_root,
            )
        except ReconciliationError as exc:
            raise DrillArtifactsError(str(exc)) from exc


def _drill_report_path(run_dir: Path, drill_name: str) -> Path:
    return run_dir / "drills" / f"{drill_name}.json"


def _append_optional_journal_event(
    *,
    run_dir: Path,
    run_id: str,
    drill_name: str,
    outcome: str,
    report_path: Path,
    extras: dict[str, Any] | None = None,
) -> None:
    journal_path = run_dir / "journal.jsonl"
    if not journal_path.is_file():
        return

    event: dict[str, Any] = {
        "ts_utc": _utc_now_iso8601(),
        "event": "failure_drill_executed",
        "run_id": run_id,
        "drill_name": drill_name,
        "outcome": outcome,
        "status": "completed",
        "report_path": str(report_path.resolve()),
    }
    if extras:
        event.update(extras)
    append_journal_event(journal_path, event)


def execute_stale_market_data_drill(
    *,
    run_id: str,
    artifacts_root: Path = Path("artifacts/runs"),
) -> dict[str, Any]:
    """Run deterministic stale market data warning drill."""
    normalized_run_id = _validate_run_id(run_id)
    run_dir = _ensure_run_dir(normalized_run_id, artifacts_root=artifacts_root)

    reconciliation = _run_fixture_reconciliation(
        run_id=normalized_run_id,
        expected_fixture_path=_EXPECTED_FIXTURE,
        observed_fixture_path=_STALE_OBSERVED_FIXTURE,
        artifacts_root=artifacts_root,
    )
    report = {
        "schema_version": _SCHEMA_VERSION,
        "run_id": normalized_run_id,
        "drill_name": "stale_market_data",
        "ts_utc": _utc_now_iso8601(),
        "status": "completed",
        "outcome": "expected_warning",
        "pass": reconciliation["status"] == "warning",
        "inputs": {
            "expected_fixture": str(_EXPECTED_FIXTURE.resolve()),
            "observed_fixture": str(_STALE_OBSERVED_FIXTURE.resolve()),
        },
        "checks": reconciliation["checks"],
        "summary": reconciliation["summary"],
        "limitations": _LIMITATIONS,
        "reconciliation_status": reconciliation["status"],
        "reconciliation_result_path": str(
            (artifacts_root / normalized_run_id / "reconciliation_result.json").resolve()
        ),
    }
    report_path = _drill_report_path(run_dir, "stale_market_data")
    _write_json(report_path, report)
    _append_optional_journal_event(
        run_dir=run_dir,
        run_id=normalized_run_id,
        drill_name="stale_market_data",
        outcome="expected_warning",
        report_path=report_path,
        extras={"reconciliation_status": reconciliation["status"]},
    )
    return {"report": report, "report_path": report_path}


def execute_reconciliation_mismatch_drill(
    *,
    run_id: str,
    artifacts_root: Path = Path("artifacts/runs"),
) -> dict[str, Any]:
    """Run deterministic reconciliation mismatch drill."""
    normalized_run_id = _validate_run_id(run_id)
    run_dir = _ensure_run_dir(normalized_run_id, artifacts_root=artifacts_root)

    reconciliation = _run_fixture_reconciliation(
        run_id=normalized_run_id,
        expected_fixture_path=_EXPECTED_FIXTURE,
        observed_fixture_path=_MISMATCH_OBSERVED_FIXTURE,
        artifacts_root=artifacts_root,
    )
    report = {
        "schema_version": _SCHEMA_VERSION,
        "run_id": normalized_run_id,
        "drill_name": "reconciliation_mismatch",
        "ts_utc": _utc_now_iso8601(),
        "status": "completed",
        "outcome": "expected_mismatch",
        "pass": reconciliation["status"] == "mismatch",
        "inputs": {
            "expected_fixture": str(_EXPECTED_FIXTURE.resolve()),
            "observed_fixture": str(_MISMATCH_OBSERVED_FIXTURE.resolve()),
        },
        "checks": reconciliation["checks"],
        "summary": reconciliation["summary"],
        "limitations": _LIMITATIONS,
        "reconciliation_status": reconciliation["status"],
        "reconciliation_result_path": str(
            (artifacts_root / normalized_run_id / "reconciliation_result.json").resolve()
        ),
    }
    report_path = _drill_report_path(run_dir, "reconciliation_mismatch")
    _write_json(report_path, report)
    _append_optional_journal_event(
        run_dir=run_dir,
        run_id=normalized_run_id,
        drill_name="reconciliation_mismatch",
        outcome="expected_mismatch",
        report_path=report_path,
        extras={"reconciliation_status": reconciliation["status"]},
    )
    return {"report": report, "report_path": report_path}


def execute_restart_recovery_drill(
    *,
    run_id: str,
    artifacts_root: Path = Path("artifacts/runs"),
) -> dict[str, Any]:
    """Run deterministic artifact-based restart/recovery rehearsal."""
    normalized_run_id = _validate_run_id(run_id)
    run_dir = _ensure_run_dir(normalized_run_id, artifacts_root=artifacts_root)

    metadata_path = run_dir / "metadata.json"
    run_spec_path = run_dir / "run_spec.yaml"
    journal_path = run_dir / "journal.jsonl"
    metrics_path = run_dir / "metrics.json"
    summary = {
        "run_dir_exists": run_dir.is_dir(),
        "metadata_present": metadata_path.is_file(),
        "run_spec_present": run_spec_path.is_file(),
        "journal_present": journal_path.is_file(),
        "metrics_present": metrics_path.is_file(),
    }
    checks = [
        {
            "name": "required_artifacts",
            "severity": (
                "ok" if summary["metadata_present"] and summary["run_spec_present"] else "mismatch"
            ),
            "matched": summary["metadata_present"] and summary["run_spec_present"],
            "details": (
                f"metadata_present={summary['metadata_present']} "
                f"run_spec_present={summary['run_spec_present']}"
            ),
        },
        {
            "name": "simulation_scope",
            "severity": "ok",
            "matched": True,
            "details": "no process restart performed; this is artifact-based recovery rehearsal",
        },
    ]

    report = {
        "schema_version": _SCHEMA_VERSION,
        "run_id": normalized_run_id,
        "drill_name": "restart_recovery",
        "ts_utc": _utc_now_iso8601(),
        "status": "completed",
        "outcome": "simulated_recovery_ok",
        "pass": True,
        "inputs": {
            "run_dir": str(run_dir.resolve()),
        },
        "checks": checks,
        "summary": summary,
        "limitations": _LIMITATIONS,
        "statement": "no process restart performed; this is artifact-based recovery rehearsal",
    }
    report_path = _drill_report_path(run_dir, "restart_recovery")
    _write_json(report_path, report)
    _append_optional_journal_event(
        run_dir=run_dir,
        run_id=normalized_run_id,
        drill_name="restart_recovery",
        outcome="simulated_recovery_ok",
        report_path=report_path,
        extras={"simulated": True},
    )
    return {"report": report, "report_path": report_path}
