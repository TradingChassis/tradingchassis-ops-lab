"""Artifact-driven Prometheus metrics rendering."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class RunObservabilityError(ValueError):
    """Base error for observability artifact loading/rendering failures."""


class RunArtifactsNotFoundError(RunObservabilityError):
    """Raised when the run artifacts directory does not exist."""


class RunArtifactsFileMissingError(RunObservabilityError):
    """Raised when required observability artifact files are missing."""


class RunArtifactsParseError(RunObservabilityError):
    """Raised when observability artifacts cannot be parsed."""


@dataclass(frozen=True)
class RunObservabilityArtifacts:
    """Normalized observability inputs loaded from one run directory."""

    run_id: str
    run_dir: Path
    metadata: dict[str, Any]
    metrics: dict[str, Any]
    journal_events: list[dict[str, Any]]
    reconciliation_result: dict[str, Any] | None
    include_journal: bool


def _load_json_required(path: Path, *, field_name: str) -> dict[str, Any]:
    if not path.is_file():
        raise RunArtifactsFileMissingError(f"Missing required {field_name}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunArtifactsParseError(f"Malformed JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RunArtifactsParseError(f"Expected JSON object in {path}")
    return payload


def _load_journal_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if not path.is_file():
        raise RunArtifactsParseError(f"Expected journal file at {path}")

    events: list[dict[str, Any]] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event_payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunArtifactsParseError(
                f"Malformed JSONL in {path} at line {index}: {exc}"
            ) from exc
        if not isinstance(event_payload, dict):
            payload_type = type(event_payload).__name__
            raise RunArtifactsParseError(
                f"Expected JSON object in {path} at line {index}; got {payload_type}"
            )
        events.append(event_payload)
    return events


def _load_json_optional(path: Path, *, field_name: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise RunArtifactsParseError(f"Expected {field_name} file at {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunArtifactsParseError(f"Malformed JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunArtifactsParseError(f"Expected JSON object in {path}")
    return payload


def load_run_observability_artifacts(
    run_id: str,
    artifacts_root: Path = Path("artifacts/runs"),
    include_journal: bool = True,
) -> RunObservabilityArtifacts:
    """Load observability artifacts for one run_id from local artifact storage."""
    run_dir = artifacts_root / run_id
    if not run_dir.is_dir():
        raise RunArtifactsNotFoundError(f"Run artifacts directory not found: {run_dir}")

    metadata = _load_json_required(run_dir / "metadata.json", field_name="metadata.json")
    metrics = _load_json_required(run_dir / "metrics.json", field_name="metrics.json")
    journal_events = _load_journal_events(run_dir / "journal.jsonl") if include_journal else []
    reconciliation_result = _load_json_optional(
        run_dir / "reconciliation_result.json",
        field_name="reconciliation_result.json",
    )

    return RunObservabilityArtifacts(
        run_id=run_id,
        run_dir=run_dir,
        metadata=metadata,
        metrics=metrics,
        journal_events=journal_events,
        reconciliation_result=reconciliation_result,
        include_journal=include_journal,
    )


def _escape_label_value(value: Any) -> str:
    rendered = str(value)
    rendered = rendered.replace("\\", "\\\\")
    rendered = rendered.replace("\n", "\\n")
    rendered = rendered.replace('"', '\\"')
    return rendered


def _format_labels(labels: list[tuple[str, Any]]) -> str:
    return ",".join(f'{key}="{_escape_label_value(value)}"' for key, value in labels)


def _parse_iso8601_to_seconds(raw_value: Any) -> float | None:
    if not isinstance(raw_value, str):
        return None
    cleaned = raw_value.strip()
    if not cleaned:
        return None
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp()


def _format_metric_value(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return format(value, "g")


def _bool_label(value: Any) -> str:
    return "true" if bool(value) else "false"


def _append_metric(
    lines: list[str],
    *,
    name: str,
    labels: list[tuple[str, Any]],
    value: float | int,
) -> None:
    lines.append(f"{name}{{{_format_labels(labels)}}} {_format_metric_value(value)}")


def render_prometheus_text(artifacts: RunObservabilityArtifacts) -> str:
    """Render deterministic Prometheus text exposition from run artifacts."""
    metadata = artifacts.metadata
    metrics = artifacts.metrics

    run_id = metadata.get("run_id", artifacts.run_id)
    mode = metadata.get("mode", metrics.get("mode", "unknown"))
    engine = metadata.get("engine", metrics.get("engine", "unknown"))
    venue = metadata.get("venue", "unknown")
    instrument = metadata.get("instrument", "unknown")
    dataset = metrics.get("dataset") or metadata.get("data", {}).get("dataset") or "unknown"
    status = metadata.get("status", metrics.get("status", "unknown"))
    is_placeholder = _bool_label(metrics.get("is_placeholder", False))
    engine_executed = _bool_label(metrics.get("engine_executed", False))

    core_labels = [
        ("run_id", run_id),
        ("mode", mode),
        ("engine", engine),
        ("venue", venue),
        ("instrument", instrument),
    ]
    run_info_labels = core_labels + [
        ("status", status),
        ("dataset", dataset),
        ("is_placeholder", is_placeholder),
        ("engine_executed", engine_executed),
    ]

    lines: list[str] = []
    _append_metric(lines, name="ops_lab_run_info", labels=run_info_labels, value=1)

    created_ts = _parse_iso8601_to_seconds(metadata.get("created_at_utc"))
    if created_ts is not None:
        _append_metric(
            lines,
            name="ops_lab_run_created_timestamp_seconds",
            labels=core_labels,
            value=created_ts,
        )

    started_ts = _parse_iso8601_to_seconds(metadata.get("started_at_utc"))
    if started_ts is not None:
        _append_metric(
            lines,
            name="ops_lab_run_started_timestamp_seconds",
            labels=core_labels,
            value=started_ts,
        )

    completed_ts = _parse_iso8601_to_seconds(metadata.get("completed_at_utc"))
    if completed_ts is not None:
        _append_metric(
            lines,
            name="ops_lab_run_completed_timestamp_seconds",
            labels=core_labels,
            value=completed_ts,
        )

    if started_ts is not None and completed_ts is not None:
        _append_metric(
            lines,
            name="ops_lab_run_duration_seconds",
            labels=core_labels,
            value=max(0.0, completed_ts - started_ts),
        )

    if isinstance(metrics.get("input_candles_count"), int):
        _append_metric(
            lines,
            name="ops_lab_backtest_input_candles_total",
            labels=core_labels,
            value=metrics["input_candles_count"],
        )
    if isinstance(metrics.get("bars_processed"), int):
        _append_metric(
            lines,
            name="ops_lab_backtest_bars_processed_total",
            labels=core_labels,
            value=metrics["bars_processed"],
        )
    if isinstance(metrics.get("engine_duration_ms"), (int, float)):
        _append_metric(
            lines,
            name="ops_lab_backtest_engine_duration_seconds",
            labels=core_labels,
            value=float(metrics["engine_duration_ms"]) / 1000.0,
        )

    if isinstance(metrics.get("heartbeat_count"), int):
        _append_metric(
            lines,
            name="ops_lab_paper_heartbeat_total",
            labels=core_labels,
            value=metrics["heartbeat_count"],
        )
    if isinstance(metrics.get("synthetic_duration_seconds"), (int, float)):
        _append_metric(
            lines,
            name="ops_lab_paper_synthetic_duration_seconds",
            labels=core_labels,
            value=float(metrics["synthetic_duration_seconds"]),
        )

    if artifacts.include_journal:
        _append_metric(
            lines,
            name="ops_lab_journal_events_total",
            labels=core_labels,
            value=len(artifacts.journal_events),
        )

        event_counts = Counter(
            event_name
            for event_name in (entry.get("event") for entry in artifacts.journal_events)
            if isinstance(event_name, str) and event_name.strip()
        )
        for event_name in sorted(event_counts):
            _append_metric(
                lines,
                name="ops_lab_journal_event_total",
                labels=core_labels + [("event", event_name)],
                value=event_counts[event_name],
            )

    if artifacts.reconciliation_result is not None:
        reconciliation = artifacts.reconciliation_result
        status = reconciliation.get("status")
        if status not in {"ok", "warning", "mismatch", "unknown"}:
            raise RunArtifactsParseError(
                "Malformed reconciliation_result.json: invalid status field."
            )
        _append_metric(
            lines,
            name="ops_lab_reconciliation_status",
            labels=core_labels + [("status", status)],
            value=1,
        )

        summary = reconciliation.get("summary")
        if not isinstance(summary, dict):
            raise RunArtifactsParseError(
                "Malformed reconciliation_result.json: summary must be an object."
            )
        for severity in ("ok", "warning", "mismatch", "unknown"):
            value = summary.get(severity)
            if not isinstance(value, int):
                raise RunArtifactsParseError(
                    f"Malformed reconciliation_result.json: summary.{severity} must be integer."
                )
            _append_metric(
                lines,
                name="ops_lab_reconciliation_checks_total",
                labels=core_labels + [("severity", severity)],
                value=value,
            )

        ts_seconds = _parse_iso8601_to_seconds(reconciliation.get("ts_utc"))
        if ts_seconds is None:
            raise RunArtifactsParseError(
                "Malformed reconciliation_result.json: ts_utc must be valid ISO-8601 timestamp."
            )
        _append_metric(
            lines,
            name="ops_lab_reconciliation_last_timestamp_seconds",
            labels=core_labels,
            value=ts_seconds,
        )

    return "\n".join(lines) + "\n"


def export_run_metrics(
    run_id: str,
    artifacts_root: Path = Path("artifacts/runs"),
    include_journal: bool = True,
) -> str:
    """Load one run's artifacts and return Prometheus exposition text."""
    artifacts = load_run_observability_artifacts(
        run_id=run_id,
        artifacts_root=artifacts_root,
        include_journal=include_journal,
    )
    return render_prometheus_text(artifacts)


def discover_run_ids(artifacts_root: Path = Path("artifacts/runs")) -> list[str]:
    """Discover run artifact directory names in deterministic order."""
    if not artifacts_root.is_dir():
        return []
    return sorted(path.name for path in artifacts_root.iterdir() if path.is_dir())


def _render_comment_only(message: str) -> str:
    return f"# {message}\n"


def render_metrics_text(
    *,
    artifacts_root: Path = Path("artifacts/runs"),
    run_id: str | None = None,
    include_journal: bool = True,
) -> str:
    """Render Prometheus text for one selected run or all discovered runs."""
    if run_id is not None:
        try:
            return export_run_metrics(
                run_id=run_id,
                artifacts_root=artifacts_root,
                include_journal=include_journal,
            )
        except RunObservabilityError:
            return _render_comment_only(
                f"ops_lab: run_id {run_id} not found or unreadable under {artifacts_root}"
            )

    discovered_run_ids = discover_run_ids(artifacts_root)
    if not discovered_run_ids:
        return _render_comment_only(f"ops_lab: no run artifacts found under {artifacts_root}")

    rendered_parts: list[str] = []
    for discovered_run_id in discovered_run_ids:
        try:
            rendered_parts.append(
                export_run_metrics(
                    run_id=discovered_run_id,
                    artifacts_root=artifacts_root,
                    include_journal=include_journal,
                )
            )
        except RunObservabilityError:
            rendered_parts.append(
                _render_comment_only(
                    (
                        "ops_lab: skipped run_id "
                        f"{discovered_run_id} due to missing or malformed artifacts"
                    )
                )
            )

    return "".join(rendered_parts)
