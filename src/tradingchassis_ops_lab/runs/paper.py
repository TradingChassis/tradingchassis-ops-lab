"""Paper lifecycle orchestration for bounded skeleton runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.reports.render import render_paper_skeleton_report
from tradingchassis_ops_lab.runs.artifacts import initialize_run_artifacts
from tradingchassis_ops_lab.runs.hashing import compute_config_sha256
from tradingchassis_ops_lab.runs.journal import append_journal_event
from tradingchassis_ops_lab.runs.metadata import build_initial_metadata, write_metadata
from tradingchassis_ops_lab.runs.spec import RunSpec, load_run_spec

_HEARTBEAT_COUNT = 3
_SYNTHETIC_DURATION_SECONDS = 3


class InvalidPaperModeError(ValueError):
    """Raised when a non-paper spec is used with paper command."""


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


def _append_synthetic_heartbeat_events(
    *,
    journal_path: Path,
    spec: RunSpec,
    config_sha256: str,
    artifacts_dir: Path,
) -> None:
    for heartbeat_index in range(1, _HEARTBEAT_COUNT + 1):
        append_journal_event(
            journal_path,
            _build_lifecycle_event(
                event="paper_heartbeat",
                status="running",
                spec=spec,
                config_sha256=config_sha256,
                artifacts_dir=artifacts_dir,
                extra_fields={
                    "heartbeat_index": heartbeat_index,
                    "heartbeat_total": _HEARTBEAT_COUNT,
                    "synthetic": True,
                },
            ),
        )


def _write_placeholder_metrics(path: Path, *, spec: RunSpec) -> None:
    payload = {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": "nautilus",
        "status": "completed",
        "is_placeholder": True,
        "engine_executed": False,
        "connectivity": "none",
        "paper_lifecycle": "synthetic_heartbeat",
        "heartbeat_count": _HEARTBEAT_COUNT,
        "synthetic_duration_seconds": _SYNTHETIC_DURATION_SECONDS,
        "metrics": {},
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_paper_lifecycle(spec_path: Path) -> tuple[Path, str]:
    """Run deterministic paper lifecycle skeleton and persist artifacts."""
    spec = load_run_spec(spec_path)
    if spec.mode != "paper":
        raise InvalidPaperModeError(
            f"Spec mode must be paper for `tc run paper`; got mode={spec.mode}"
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
    metadata["lifecycle"] = "paper_skeleton"
    metadata["is_placeholder"] = True
    paper_started_at = _utc_now_iso8601()
    metadata["paper_execution"] = {
        "status": "running",
        "engine": "nautilus",
        "connectivity": "none",
        "session_type": "synthetic_heartbeat",
        "started_at_utc": paper_started_at,
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
            event="paper_started",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
            extra_fields={
                "note": "paper skeleton lifecycle started; no exchange/testnet connectivity",
            },
        ),
    )

    try:
        _append_synthetic_heartbeat_events(
            journal_path=journal_path,
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
        )
    except Exception as exc:
        failed_at = _utc_now_iso8601()
        metadata["status"] = "failed"
        metadata["completed_at_utc"] = failed_at
        metadata["paper_execution"] = {
            "status": "failed",
            "engine": "nautilus",
            "connectivity": "none",
            "session_type": "synthetic_heartbeat",
            "started_at_utc": paper_started_at,
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
            event="paper_completed",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
            extra_fields={
                "result": "paper_skeleton_completed",
                "heartbeat_count": _HEARTBEAT_COUNT,
            },
        ),
    )

    _write_placeholder_metrics(artifacts_dir / "metrics.json", spec=spec)
    (artifacts_dir / "report.md").write_text(
        render_paper_skeleton_report(
            run_id=spec.run_id,
            mode=spec.mode,
            engine=spec.engine,
            status="completed",
            config_sha256=config_sha256,
            heartbeat_count=_HEARTBEAT_COUNT,
            connectivity="none",
        ),
        encoding="utf-8",
    )

    completed_at = _utc_now_iso8601()
    metadata["status"] = "completed"
    metadata["completed_at_utc"] = completed_at
    metadata["paper_execution"] = {
        "status": "completed",
        "engine": "nautilus",
        "connectivity": "none",
        "session_type": "synthetic_heartbeat",
        "started_at_utc": paper_started_at,
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
