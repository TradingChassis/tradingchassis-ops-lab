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
    connectivity_readiness: dict[str, Any] | None
    connectivity_probe: dict[str, Any] | None
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
    connectivity_readiness = _load_json_optional(
        run_dir / "connectivity_readiness.json",
        field_name="connectivity_readiness.json",
    )
    connectivity_probe = _load_json_optional(
        run_dir / "connectivity_probe.json",
        field_name="connectivity_probe.json",
    )

    return RunObservabilityArtifacts(
        run_id=run_id,
        run_dir=run_dir,
        metadata=metadata,
        metrics=metrics,
        journal_events=journal_events,
        reconciliation_result=reconciliation_result,
        connectivity_readiness=connectivity_readiness,
        connectivity_probe=connectivity_probe,
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


def _bool_metric_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return 1 if value else 0
    return None


def _kill_switch_state_from_metadata(metadata: dict[str, Any]) -> str | None:
    safety = metadata.get("safety")
    if not isinstance(safety, dict):
        return None
    kill_switch = safety.get("kill_switch")
    if not isinstance(kill_switch, dict):
        return None
    state = kill_switch.get("state")
    if isinstance(state, str) and state.strip():
        return state.strip()
    return "unknown"


def _kill_switch_state_value(state: str) -> int:
    if state == "absent":
        return 0
    if state == "cleared":
        return 1
    if state == "active":
        return 2
    return -1


def _connectivity_readiness_state_value(state: str) -> int:
    if state == "disabled":
        return 0
    if state == "configured":
        return 1
    if state == "missing_credentials":
        return 2
    if state == "invalid_config":
        return 3
    if state == "unknown":
        return -1
    return -1


def _connectivity_probe_state_value(state: str) -> int:
    if state == "probe_ok":
        return 1
    if state == "probe_http_error":
        return 2
    if state == "probe_timeout":
        return 3
    if state == "probe_unreachable":
        return 4
    if state == "probe_unknown":
        return -1
    return -1


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
    _append_metric(lines, name="tradingchassis_ops_lab_run_info", labels=run_info_labels, value=1)

    if artifacts.connectivity_readiness is not None:
        readiness = artifacts.connectivity_readiness
        state = readiness.get("state")
        if not isinstance(state, str) or not state.strip():
            raise RunArtifactsParseError(
                "Malformed connectivity_readiness.json: state must be a non-empty string."
            )
        enabled = readiness.get("enabled")
        if not isinstance(enabled, bool):
            raise RunArtifactsParseError(
                "Malformed connectivity_readiness.json: enabled must be boolean."
            )
        missing_required_count = readiness.get("missing_required_count")
        if not isinstance(missing_required_count, int):
            raise RunArtifactsParseError(
                "Malformed connectivity_readiness.json: missing_required_count must be integer."
            )
        probe_performed = readiness.get("probe_performed")
        if not isinstance(probe_performed, bool):
            raise RunArtifactsParseError(
                "Malformed connectivity_readiness.json: probe_performed must be boolean."
            )
        readiness_labels = core_labels + [("state", state)]
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_readiness_state",
            labels=readiness_labels,
            value=_connectivity_readiness_state_value(state),
        )
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_readiness_enabled",
            labels=readiness_labels,
            value=1 if enabled else 0,
        )
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_readiness_missing_required_env_total",
            labels=readiness_labels,
            value=missing_required_count,
        )
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_readiness_probe_performed",
            labels=readiness_labels,
            value=1 if probe_performed else 0,
        )

    if artifacts.connectivity_probe is not None:
        connectivity_probe = artifacts.connectivity_probe
        state = connectivity_probe.get("state")
        if not isinstance(state, str) or not state.strip():
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: state must be a non-empty string."
            )
        probe_performed = connectivity_probe.get("probe_performed")
        if not isinstance(probe_performed, bool):
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: probe_performed must be boolean."
            )
        network_scope = connectivity_probe.get("network_scope")
        if not isinstance(network_scope, str) or not network_scope.strip():
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: network_scope must be a non-empty string."
            )
        error_class = connectivity_probe.get("error_class")
        if error_class is not None and (
            not isinstance(error_class, str) or not error_class.strip()
        ):
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: error_class must be null or non-empty string."
            )
        http_status = connectivity_probe.get("http_status")
        if http_status is not None and not isinstance(http_status, int):
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: http_status must be integer or null."
            )
        latency_ms = connectivity_probe.get("latency_ms")
        if latency_ms is not None and not isinstance(latency_ms, (int, float)):
            raise RunArtifactsParseError(
                "Malformed connectivity_probe.json: latency_ms must be numeric or null."
            )

        probe_labels = core_labels + [("state", state), ("network_scope", network_scope)]
        if isinstance(error_class, str):
            probe_labels.append(("error_class", error_class))

        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_probe_state",
            labels=probe_labels,
            value=_connectivity_probe_state_value(state),
        )
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_connectivity_probe_performed",
            labels=probe_labels,
            value=1 if probe_performed else 0,
        )
        if latency_ms is not None:
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_connectivity_probe_latency_seconds",
                labels=probe_labels,
                value=float(latency_ms) / 1000.0,
            )
        if http_status is not None:
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_connectivity_probe_http_status",
                labels=probe_labels,
                value=http_status,
            )

    kill_switch_state = _kill_switch_state_from_metadata(metadata)
    if kill_switch_state is not None:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_kill_switch_state",
            labels=[("run_id", run_id), ("state", kill_switch_state)],
            value=_kill_switch_state_value(kill_switch_state),
        )

    created_ts = _parse_iso8601_to_seconds(metadata.get("created_at_utc"))
    if created_ts is not None:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_run_created_timestamp_seconds",
            labels=core_labels,
            value=created_ts,
        )

    started_ts = _parse_iso8601_to_seconds(metadata.get("started_at_utc"))
    if started_ts is not None:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_run_started_timestamp_seconds",
            labels=core_labels,
            value=started_ts,
        )

    completed_ts = _parse_iso8601_to_seconds(metadata.get("completed_at_utc"))
    if completed_ts is not None:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_run_completed_timestamp_seconds",
            labels=core_labels,
            value=completed_ts,
        )

    if started_ts is not None and completed_ts is not None:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_run_duration_seconds",
            labels=core_labels,
            value=max(0.0, completed_ts - started_ts),
        )

    if isinstance(metrics.get("input_candles_count"), int):
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_backtest_input_candles_total",
            labels=core_labels,
            value=metrics["input_candles_count"],
        )
    if isinstance(metrics.get("bars_processed"), int):
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_backtest_bars_processed_total",
            labels=core_labels,
            value=metrics["bars_processed"],
        )
    if isinstance(metrics.get("engine_duration_ms"), (int, float)):
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_backtest_engine_duration_seconds",
            labels=core_labels,
            value=float(metrics["engine_duration_ms"]) / 1000.0,
        )

    scenario_name = metrics.get("scenario_name")
    if isinstance(scenario_name, str) and scenario_name.strip():
        scenario_labels: list[tuple[str, Any]] = [
            ("run_id", run_id),
            ("scenario_name", scenario_name),
        ]
        scenario_version = metrics.get("scenario_version")
        if isinstance(scenario_version, str) and scenario_version.strip():
            scenario_labels.append(("scenario_version", scenario_version))

        strategy_registered = _bool_metric_value(metrics.get("strategy_registered"))
        if strategy_registered is not None:
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_backtest_scenario_strategy_registered",
                labels=scenario_labels,
                value=strategy_registered,
            )

        deterministic_action_triggered = _bool_metric_value(
            metrics.get("deterministic_action_triggered")
        )
        if deterministic_action_triggered is not None:
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered",
                labels=scenario_labels,
                value=deterministic_action_triggered,
            )

        bars_seen = metrics.get("bars_seen")
        if isinstance(bars_seen, int):
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_backtest_scenario_bars_seen_total",
                labels=scenario_labels,
                value=bars_seen,
            )

        orders_submitted = metrics.get("orders_submitted")
        if isinstance(orders_submitted, int):
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_backtest_scenario_orders_submitted_total",
                labels=scenario_labels,
                value=orders_submitted,
            )

        fills_count = metrics.get("fills_count")
        if isinstance(fills_count, int):
            _append_metric(
                lines,
                name="tradingchassis_ops_lab_backtest_scenario_fills_total",
                labels=scenario_labels,
                value=fills_count,
            )

    if isinstance(metrics.get("heartbeat_count"), int):
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_paper_heartbeat_total",
            labels=core_labels,
            value=metrics["heartbeat_count"],
        )
    if isinstance(metrics.get("synthetic_duration_seconds"), (int, float)):
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_paper_synthetic_duration_seconds",
            labels=core_labels,
            value=float(metrics["synthetic_duration_seconds"]),
        )

    if artifacts.include_journal:
        _append_metric(
            lines,
            name="tradingchassis_ops_lab_journal_events_total",
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
                name="tradingchassis_ops_lab_journal_event_total",
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
            name="tradingchassis_ops_lab_reconciliation_status",
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
                name="tradingchassis_ops_lab_reconciliation_checks_total",
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
            name="tradingchassis_ops_lab_reconciliation_last_timestamp_seconds",
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
                "tradingchassis_ops_lab: run_id "
                f"{run_id} not found or unreadable under {artifacts_root}"
            )

    discovered_run_ids = discover_run_ids(artifacts_root)
    if not discovered_run_ids:
        return _render_comment_only(
            f"tradingchassis_ops_lab: no run artifacts found under {artifacts_root}"
        )

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
                        "tradingchassis_ops_lab: skipped run_id "
                        f"{discovered_run_id} due to missing or malformed artifacts"
                    )
                )
            )

    return "".join(rendered_parts)
