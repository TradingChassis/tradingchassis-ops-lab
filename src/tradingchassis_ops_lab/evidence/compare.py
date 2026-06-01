"""Backtest vs paper operational evidence comparison."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

ComparableKind = Literal["direct", "contextual", "mode_specific", "gap", "future_candidate"]

_SCHEMA_VERSION = "v1"
_CORE_ARTIFACT_NAMES = ("metadata.json", "metrics.json", "journal.jsonl", "report.md")
_OPTIONAL_ARTIFACT_NAMES = (
    "connectivity_readiness.json",
    "connectivity_probe.json",
    "reconciliation_result.json",
)
_KNOWN_GAPS = [
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
_NOTES = [
    "Operational evidence only; not strategy performance.",
    "Paper mode is a bounded synthetic lifecycle skeleton.",
]
_NON_GOALS = [
    "alpha",
    "live_paper_trading",
    "order_execution",
    "pnl",
    "returns",
    "sharpe",
    "strategy_optimization",
]


class EvidenceCompareError(ValueError):
    """Base error for evidence compare operations."""


class EvidenceArtifactsParseError(EvidenceCompareError):
    """Raised when required evidence artifacts are malformed."""


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_json_required(path: Path, *, field_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceArtifactsParseError(f"Malformed JSON in {field_name}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceArtifactsParseError(f"Expected JSON object in {field_name}: {path}")
    return payload


def _load_json_optional(path: Path, *, field_name: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceArtifactsParseError(f"Malformed JSON in {field_name}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceArtifactsParseError(f"Expected JSON object in {field_name}: {path}")
    return payload


def _load_journal_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvidenceArtifactsParseError(
                f"Malformed JSONL in journal.jsonl: {path} at line {index}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise EvidenceArtifactsParseError(
                f"Expected JSON object in journal.jsonl: {path} at line {index}"
            )
        events.append(payload)
    return events


def _read_optional_state(payload: dict[str, Any] | None, *, key: str = "state") -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _paper_safety_states(paper_metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return paper kill-switch state and lifecycle outcome when safety metadata is valid."""
    paper_safety = paper_metadata.get("safety")
    if not isinstance(paper_safety, dict):
        return None, None
    lifecycle_outcome = _read_optional_state(paper_safety, key="lifecycle_outcome")
    kill_switch_state: str | None = None
    kill_switch = paper_safety.get("kill_switch")
    if isinstance(kill_switch, dict):
        kill_switch_state = _read_optional_state(kill_switch, key="state")
    return kill_switch_state, lifecycle_outcome


def _build_artifact_presence(run_dir: Path) -> dict[str, bool]:
    names = sorted((*_CORE_ARTIFACT_NAMES, *_OPTIONAL_ARTIFACT_NAMES))
    return {name: (run_dir / name).is_file() for name in names}


def _build_missing_reason(
    *,
    side: Literal["backtest", "paper"],
    run_dir: Path,
    artifact_presence: dict[str, bool],
) -> list[str]:
    missing = [name for name in _CORE_ARTIFACT_NAMES if not artifact_presence.get(name, False)]
    if not missing:
        return []
    return [f"{side} missing required artifacts at {run_dir}: {', '.join(sorted(missing))}"]


def _journal_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    names = sorted(
        {
            event_name
            for event_name in (entry.get("event") for entry in events)
            if isinstance(event_name, str) and event_name.strip()
        }
    )
    return {"event_total": len(events), "events": names}


def _compare_field(
    *,
    area: str,
    backtest_value: Any,
    paper_value: Any,
    comparable: ComparableKind,
    note: str,
) -> dict[str, Any]:
    return {
        "area": area,
        "backtest": backtest_value,
        "paper": paper_value,
        "comparable": comparable,
        "match": backtest_value == paper_value,
        "note": note,
    }


def _build_compared_fields(
    *,
    backtest_metadata: dict[str, Any],
    paper_metadata: dict[str, Any],
    backtest_metrics: dict[str, Any],
    paper_metrics: dict[str, Any],
    artifact_presence: dict[str, dict[str, bool]],
    shared_events: list[str],
    readiness_state_backtest: str | None,
    readiness_state_paper: str | None,
    probe_state_backtest: str | None,
    probe_state_paper: str | None,
    paper_kill_switch_state: str | None,
) -> list[dict[str, Any]]:
    paper_strategy = paper_metadata.get("strategy")
    backtest_scenario = {
        "scenario_name": backtest_metrics.get("scenario_name"),
        "scenario_version": backtest_metrics.get("scenario_version"),
    }
    compared_fields = [
        _compare_field(
            area="engine",
            backtest_value=backtest_metadata.get("engine"),
            paper_value=paper_metadata.get("engine"),
            comparable="direct",
            note="Both run modes share the same engine label.",
        ),
        _compare_field(
            area="instrument",
            backtest_value=backtest_metadata.get("instrument"),
            paper_value=paper_metadata.get("instrument"),
            comparable="direct",
            note="Instrument label should align for operational context.",
        ),
        _compare_field(
            area="venue",
            backtest_value=backtest_metadata.get("venue"),
            paper_value=paper_metadata.get("venue"),
            comparable="contextual",
            note="Venue labels can differ across modes and remain valid.",
        ),
        _compare_field(
            area="strategy_scenario_identity",
            backtest_value=backtest_scenario,
            paper_value=paper_strategy,
            comparable="contextual",
            note="Backtest executes built-in scenario; paper records strategy metadata only.",
        ),
        _compare_field(
            area="config_hash",
            backtest_value=backtest_metadata.get("config_sha256"),
            paper_value=paper_metadata.get("config_sha256"),
            comparable="contextual",
            note="Hash mismatch is expected when specs differ by mode.",
        ),
        _compare_field(
            area="status",
            backtest_value=backtest_metadata.get("status"),
            paper_value=paper_metadata.get("status"),
            comparable="contextual",
            note="Paper may be completed or safety_blocked while still valid evidence.",
        ),
        _compare_field(
            area="engine_executed",
            backtest_value=backtest_metrics.get("engine_executed"),
            paper_value=paper_metrics.get("engine_executed"),
            comparable="mode_specific",
            note="Backtest executes engine; paper skeleton intentionally does not.",
        ),
        _compare_field(
            area="is_placeholder",
            backtest_value=backtest_metadata.get("is_placeholder"),
            paper_value=paper_metadata.get("is_placeholder"),
            comparable="mode_specific",
            note="Backtest is non-placeholder; paper is synthetic placeholder.",
        ),
        _compare_field(
            area="metrics_artifact_presence",
            backtest_value=artifact_presence["backtest"].get("metrics.json"),
            paper_value=artifact_presence["paper"].get("metrics.json"),
            comparable="direct",
            note="Both runs should provide metrics.json for comparison.",
        ),
        _compare_field(
            area="report_presence",
            backtest_value=artifact_presence["backtest"].get("report.md"),
            paper_value=artifact_presence["paper"].get("report.md"),
            comparable="direct",
            note="Both runs should provide report.md for operator review.",
        ),
        _compare_field(
            area="journal_shared_events",
            backtest_value=shared_events,
            paper_value=shared_events,
            comparable="direct",
            note="Shared lifecycle markers should be visible in both journals.",
        ),
        _compare_field(
            area="safety_state",
            backtest_value=None,
            paper_value=paper_kill_switch_state,
            comparable="gap",
            note="Safety gate applies to paper lifecycle only.",
        ),
        _compare_field(
            area="readiness_state",
            backtest_value=readiness_state_backtest,
            paper_value=readiness_state_paper,
            comparable="future_candidate",
            note="Readiness artifacts are optional and mode-dependent.",
        ),
        _compare_field(
            area="probe_state",
            backtest_value=probe_state_backtest,
            paper_value=probe_state_paper,
            comparable="future_candidate",
            note="Probe artifacts are optional and local-only.",
        ),
        _compare_field(
            area="backtest_bars_vs_paper_heartbeat",
            backtest_value={
                "bars_processed": backtest_metrics.get("bars_processed"),
                "bars_seen": backtest_metrics.get("bars_seen"),
            },
            paper_value={"heartbeat_count": paper_metrics.get("heartbeat_count")},
            comparable="mode_specific",
            note="Bars and heartbeats represent different lifecycle signals.",
        ),
    ]
    return compared_fields


def compare_backtest_paper(
    backtest_dir: Path,
    paper_dir: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Compare one backtest run directory with one paper run directory.

    This function is pure with respect to repository artifacts: it only reads
    artifact files and returns a deterministic evidence payload.
    """
    backtest_presence = _build_artifact_presence(backtest_dir)
    paper_presence = _build_artifact_presence(paper_dir)

    artifact_presence = {"backtest": backtest_presence, "paper": paper_presence}
    notes = list(_NOTES)
    missing_reasons = []
    missing_reasons.extend(
        _build_missing_reason(
            side="backtest",
            run_dir=backtest_dir,
            artifact_presence=backtest_presence,
        )
    )
    missing_reasons.extend(
        _build_missing_reason(
            side="paper",
            run_dir=paper_dir,
            artifact_presence=paper_presence,
        )
    )

    if missing_reasons:
        return {
            "schema_version": _SCHEMA_VERSION,
            "created_at_utc": created_at_utc or _utc_now_iso8601(),
            "backtest_run_id": backtest_dir.name,
            "paper_run_id": paper_dir.name,
            "comparison_status": "missing_artifacts",
            "compared_fields": [],
            "mode_summary": {
                "backtest": {"status": "unknown"},
                "paper": {"status": "unknown"},
            },
            "artifact_presence": artifact_presence,
            "journal_summary": {
                "backtest": {"event_total": 0, "events": []},
                "paper": {"event_total": 0, "events": []},
                "shared_events": [],
            },
            "safety_summary": {
                "paper_kill_switch_state": None,
                "paper_lifecycle_outcome": None,
                "backtest_safety_evaluated": False,
            },
            "connectivity_summary": {
                "backtest_readiness": None,
                "paper_readiness": None,
                "backtest_probe": None,
                "paper_probe": None,
                "backtest_reconciliation": None,
                "paper_reconciliation": None,
            },
            "known_gaps": list(_KNOWN_GAPS),
            "notes": notes + sorted(missing_reasons),
            "non_goals": list(_NON_GOALS),
        }

    backtest_metadata = _load_json_required(
        backtest_dir / "metadata.json", field_name="metadata.json"
    )
    backtest_metrics = _load_json_required(backtest_dir / "metrics.json", field_name="metrics.json")
    paper_metadata = _load_json_required(paper_dir / "metadata.json", field_name="metadata.json")
    paper_metrics = _load_json_required(paper_dir / "metrics.json", field_name="metrics.json")

    backtest_events = _load_journal_events(backtest_dir / "journal.jsonl")
    paper_events = _load_journal_events(paper_dir / "journal.jsonl")

    backtest_readiness = _load_json_optional(
        backtest_dir / "connectivity_readiness.json",
        field_name="connectivity_readiness.json",
    )
    paper_readiness = _load_json_optional(
        paper_dir / "connectivity_readiness.json",
        field_name="connectivity_readiness.json",
    )
    backtest_probe = _load_json_optional(
        backtest_dir / "connectivity_probe.json",
        field_name="connectivity_probe.json",
    )
    paper_probe = _load_json_optional(
        paper_dir / "connectivity_probe.json",
        field_name="connectivity_probe.json",
    )
    backtest_reconciliation = _load_json_optional(
        backtest_dir / "reconciliation_result.json",
        field_name="reconciliation_result.json",
    )
    paper_reconciliation = _load_json_optional(
        paper_dir / "reconciliation_result.json",
        field_name="reconciliation_result.json",
    )

    backtest_run_id = str(backtest_metadata.get("run_id", backtest_dir.name))
    paper_run_id = str(paper_metadata.get("run_id", paper_dir.name))
    comparison_status = "differences_expected"

    if backtest_metadata.get("mode") != "backtest" or paper_metadata.get("mode") != "paper":
        comparison_status = "incompatible_runs"

    backtest_journal = _journal_summary(backtest_events)
    paper_journal = _journal_summary(paper_events)
    shared_events = sorted(set(backtest_journal["events"]) & set(paper_journal["events"]))

    readiness_state_backtest = _read_optional_state(backtest_readiness)
    readiness_state_paper = _read_optional_state(paper_readiness)
    probe_state_backtest = _read_optional_state(backtest_probe)
    probe_state_paper = _read_optional_state(paper_probe)
    backtest_reconciliation_status = _read_optional_state(backtest_reconciliation, key="status")
    paper_reconciliation_status = _read_optional_state(paper_reconciliation, key="status")

    paper_kill_switch_state, paper_lifecycle_outcome = _paper_safety_states(paper_metadata)

    mode_summary = {
        "backtest": {
            "lifecycle": backtest_metadata.get("lifecycle"),
            "is_placeholder": backtest_metadata.get("is_placeholder"),
            "status": backtest_metadata.get("status"),
            "engine_executed": backtest_metrics.get("engine_executed"),
            "scenario_name": backtest_metrics.get("scenario_name"),
            "scenario_version": backtest_metrics.get("scenario_version"),
            "bars_seen": backtest_metrics.get("bars_seen"),
            "orders_submitted": backtest_metrics.get("orders_submitted"),
            "fills_count": backtest_metrics.get("fills_count"),
            "deterministic_action_triggered": backtest_metrics.get(
                "deterministic_action_triggered"
            ),
        },
        "paper": {
            "lifecycle": paper_metadata.get("lifecycle"),
            "is_placeholder": paper_metadata.get("is_placeholder"),
            "status": paper_metadata.get("status"),
            "engine_executed": paper_metrics.get("engine_executed"),
            "paper_lifecycle": paper_metrics.get("paper_lifecycle"),
            "heartbeat_count": paper_metrics.get("heartbeat_count"),
            "connectivity": paper_metrics.get("connectivity"),
            "safety_lifecycle_outcome": paper_lifecycle_outcome,
        },
    }

    compared_fields = _build_compared_fields(
        backtest_metadata=backtest_metadata,
        paper_metadata=paper_metadata,
        backtest_metrics=backtest_metrics,
        paper_metrics=paper_metrics,
        artifact_presence=artifact_presence,
        shared_events=shared_events,
        readiness_state_backtest=readiness_state_backtest,
        readiness_state_paper=readiness_state_paper,
        probe_state_backtest=probe_state_backtest,
        probe_state_paper=probe_state_paper,
        paper_kill_switch_state=paper_kill_switch_state,
    )

    return {
        "schema_version": _SCHEMA_VERSION,
        "created_at_utc": created_at_utc or _utc_now_iso8601(),
        "backtest_run_id": backtest_run_id,
        "paper_run_id": paper_run_id,
        "comparison_status": comparison_status,
        "compared_fields": compared_fields,
        "mode_summary": mode_summary,
        "artifact_presence": artifact_presence,
        "journal_summary": {
            "backtest": backtest_journal,
            "paper": paper_journal,
            "shared_events": shared_events,
        },
        "safety_summary": {
            "paper_kill_switch_state": paper_kill_switch_state,
            "paper_lifecycle_outcome": paper_lifecycle_outcome,
            "backtest_safety_evaluated": isinstance(backtest_metadata.get("safety"), dict),
        },
        "connectivity_summary": {
            "backtest_readiness": readiness_state_backtest,
            "paper_readiness": readiness_state_paper,
            "backtest_probe": probe_state_backtest,
            "paper_probe": probe_state_paper,
            "backtest_reconciliation": backtest_reconciliation_status,
            "paper_reconciliation": paper_reconciliation_status,
        },
        "known_gaps": list(_KNOWN_GAPS),
        "notes": notes,
        "non_goals": list(_NON_GOALS),
    }
