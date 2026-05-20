"""Backtest lifecycle skeleton orchestration for Slice 4."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ops_lab.reports.render import render_backtest_skeleton_report
from ops_lab.runs.artifacts import initialize_run_artifacts
from ops_lab.runs.hashing import compute_config_sha256
from ops_lab.runs.journal import append_journal_event
from ops_lab.runs.metadata import build_initial_metadata, write_metadata
from ops_lab.runs.spec import RunSpec, load_run_spec


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


def _write_metrics_placeholder(path: Path, *, spec: RunSpec) -> None:
    payload = {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": spec.engine,
        "status": "completed",
        "is_placeholder": True,
        "message": "Slice 4 skeleton metrics; no strategy/backtest execution performed.",
        "metrics": {},
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_backtest_skeleton(spec_path: Path) -> tuple[Path, str]:
    """Run Slice 4 backtest lifecycle skeleton and persist artifacts."""
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
    metadata["lifecycle"] = "backtest_skeleton"
    metadata["is_placeholder"] = True
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
            extra_fields={"note": "skeleton lifecycle only; no engine execution"},
        ),
    )
    append_journal_event(
        journal_path,
        _build_lifecycle_event(
            event="backtest_completed",
            status="running",
            spec=spec,
            config_sha256=config_sha256,
            artifacts_dir=artifacts_dir,
            extra_fields={"result": "placeholder"},
        ),
    )

    _write_metrics_placeholder(artifacts_dir / "metrics.json", spec=spec)
    (artifacts_dir / "report.md").write_text(
        render_backtest_skeleton_report(
            run_id=spec.run_id,
            mode=spec.mode,
            engine=spec.engine,
            status="completed",
            config_sha256=config_sha256,
        ),
        encoding="utf-8",
    )

    metadata["status"] = "completed"
    metadata["completed_at_utc"] = _utc_now_iso8601()
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
