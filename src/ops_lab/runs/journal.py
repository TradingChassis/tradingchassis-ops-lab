"""Run journal helpers for initialization events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ops_lab.runs.spec import RunSpec


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_run_initialized_event(
    spec: RunSpec,
    spec_path: Path,
    artifacts_dir: Path,
    config_sha256: str,
) -> dict[str, Any]:
    """Build the first lifecycle event for a run."""
    return {
        "ts_utc": _utc_now_iso8601(),
        "event": "run_initialized",
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": spec.engine,
        "status": "initialized",
        "config_sha256": config_sha256,
        "spec_path": str(spec_path.resolve()),
        "artifacts_dir": str(artifacts_dir.resolve()),
    }


def append_journal_event(path: Path, event: dict[str, Any]) -> None:
    """Append one compact JSON event line to the run journal."""
    with path.open("a", encoding="utf-8") as journal_file:
        journal_file.write(json.dumps(event, sort_keys=True))
        journal_file.write("\n")
