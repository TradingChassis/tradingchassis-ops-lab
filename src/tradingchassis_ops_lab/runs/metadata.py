"""Metadata creation and persistence helpers for run initialization."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.runs.spec import RunSpec


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_initial_metadata(
    spec: RunSpec,
    spec_path: Path,
    artifacts_dir: Path,
    config_sha256: str,
) -> dict[str, Any]:
    """Build metadata payload for a newly initialized run."""
    return {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "mode": spec.mode,
        "engine": spec.engine,
        "status": "initialized",
        "created_at_utc": _utc_now_iso8601(),
        "spec_path": str(spec_path.resolve()),
        "artifacts_dir": str(artifacts_dir.resolve()),
        "config_sha256": config_sha256,
        "venue": spec.venue,
        "instrument": spec.instrument,
        "strategy": spec.strategy.model_dump(mode="json"),
        "data": spec.data.model_dump(mode="json", exclude_none=False),
        "risk": spec.risk.model_dump(mode="json"),
        "observability": spec.observability.model_dump(mode="json"),
    }


def write_metadata(path: Path, metadata: dict[str, Any]) -> None:
    """Persist metadata payload as pretty, stable JSON."""
    path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
