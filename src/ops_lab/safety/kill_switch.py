"""File-based kill switch state and audit helpers."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

SCHEMA_VERSION = "v1"
EVENT_ACTIVATED = "kill_activated"
EVENT_CLEARED = "kill_cleared"
STATE_ACTIVE = "active"
STATE_CLEARED = "cleared"
STATE_ABSENT = "absent"


class KillSwitchError(ValueError):
    """Base error for kill switch operations."""


class KillSwitchValidationError(KillSwitchError):
    """Raised when caller inputs or payload schema are invalid."""


class KillSwitchReadError(KillSwitchError):
    """Raised when kill switch files are malformed or unreadable."""


@dataclass(frozen=True)
class KillSwitchState:
    """Canonical persisted kill switch state payload."""

    schema_version: str
    run_id: str
    state: str
    updated_at_utc: str
    last_event_id: str
    last_reason: str
    last_actor: str
    active_since_utc: str | None
    cleared_at_utc: str | None


@dataclass(frozen=True)
class KillSwitchEvent:
    """Append-only kill switch event payload written to JSONL."""

    schema_version: str
    event_id: str
    ts_utc: str
    run_id: str
    event: str
    reason: str
    actor: str
    source: str
    previous_state: str
    new_state: str


@dataclass(frozen=True)
class KillSwitchStatus:
    """Status response for callers and CLI output."""

    schema_version: str
    run_id: str
    state: str
    updated_at_utc: str | None = None
    last_event_id: str | None = None
    last_reason: str | None = None
    last_actor: str | None = None
    active_since_utc: str | None = None
    cleared_at_utc: str | None = None


def _utc_now_iso8601() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _validate_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise KillSwitchValidationError("run_id must be a non-empty string.")
    return normalized


def _validate_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise KillSwitchValidationError("reason must be non-empty after trimming whitespace.")
    return normalized


def _resolve_actor(actor: str | None) -> str:
    if actor is not None and actor.strip():
        return actor.strip()
    user = os.environ.get("USER", "").strip()
    return user or "unknown"


def _state_path(runtime_root: Path, run_id: str) -> Path:
    return runtime_root / f"{run_id}.state.json"


def _events_path(runtime_root: Path, run_id: str) -> Path:
    return runtime_root / f"{run_id}.events.jsonl"


def _artifact_journal_path(artifacts_root: Path, run_id: str) -> Path:
    return artifacts_root / run_id / "journal.jsonl"


def _write_state(path: Path, state: KillSwitchState) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(state), indent=2, sort_keys=True) + "\n"
        path.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise KillSwitchReadError(f"Failed to write kill switch state file {path}: {exc}") from exc


def _append_event(path: Path, event: KillSwitchEvent) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as event_file:
            event_file.write(json.dumps(asdict(event), sort_keys=True))
            event_file.write("\n")
    except OSError as exc:
        raise KillSwitchReadError(
            f"Failed to append kill switch events file {path}: {exc}"
        ) from exc


def _append_optional_artifact_journal_event(path: Path, event: KillSwitchEvent) -> None:
    if not path.exists():
        return
    if not path.is_file():
        raise KillSwitchReadError(f"Expected artifact journal file at {path}")
    try:
        with path.open("a", encoding="utf-8") as journal_file:
            journal_file.write(json.dumps(asdict(event), sort_keys=True))
            journal_file.write("\n")
    except OSError as exc:
        raise KillSwitchReadError(f"Failed to append artifact journal file {path}: {exc}") from exc


def _parse_state_payload(payload: dict[str, object], state_file: Path) -> KillSwitchState:
    required = {
        "schema_version",
        "run_id",
        "state",
        "updated_at_utc",
        "last_event_id",
        "last_reason",
        "last_actor",
        "active_since_utc",
        "cleared_at_utc",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise KillSwitchReadError(
            f"Malformed kill switch state file {state_file}: missing keys {missing}"
        )

    state_value = payload["state"]
    if state_value not in {STATE_ACTIVE, STATE_CLEARED}:
        raise KillSwitchReadError(
            f"Malformed kill switch state file {state_file}: unsupported state {state_value!r}"
        )

    if payload["schema_version"] != SCHEMA_VERSION:
        raise KillSwitchReadError(
            f"Malformed kill switch state file {state_file}: "
            f"unsupported schema_version {payload['schema_version']!r}"
        )

    for key in (
        "run_id",
        "updated_at_utc",
        "last_event_id",
        "last_reason",
        "last_actor",
    ):
        if not isinstance(payload[key], str) or not payload[key]:
            raise KillSwitchReadError(
                f"Malformed kill switch state file {state_file}: "
                f"key {key!r} must be non-empty string"
            )

    for key in ("active_since_utc", "cleared_at_utc"):
        if payload[key] is not None and not isinstance(payload[key], str):
            raise KillSwitchReadError(
                f"Malformed kill switch state file {state_file}: key {key!r} must be string or null"
            )

    return KillSwitchState(
        schema_version=SCHEMA_VERSION,
        run_id=str(payload["run_id"]),
        state=str(state_value),
        updated_at_utc=str(payload["updated_at_utc"]),
        last_event_id=str(payload["last_event_id"]),
        last_reason=str(payload["last_reason"]),
        last_actor=str(payload["last_actor"]),
        active_since_utc=payload["active_since_utc"],
        cleared_at_utc=payload["cleared_at_utc"],
    )


def _read_state(state_file: Path) -> KillSwitchState:
    try:
        raw_payload = json.loads(state_file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise KillSwitchReadError(
            f"Failed to read kill switch state file {state_file}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise KillSwitchReadError(
            f"Malformed JSON in kill switch state file {state_file}: {exc}"
        ) from exc

    if not isinstance(raw_payload, dict):
        raise KillSwitchReadError(
            f"Malformed kill switch state file {state_file}: expected a JSON object"
        )
    return _parse_state_payload(raw_payload, state_file)


def get_kill_switch_status(
    run_id: str,
    runtime_root: Path = Path("runtime/kill_switch"),
) -> KillSwitchStatus:
    """Return current kill switch status; absent when no state file exists."""
    normalized_run_id = _validate_run_id(run_id)
    state_file = _state_path(runtime_root, normalized_run_id)
    if not state_file.exists():
        return KillSwitchStatus(
            schema_version=SCHEMA_VERSION,
            run_id=normalized_run_id,
            state=STATE_ABSENT,
        )
    state = _read_state(state_file)
    return KillSwitchStatus(**asdict(state))


def activate_kill_switch(
    run_id: str,
    reason: str,
    actor: str | None = None,
    runtime_root: Path = Path("runtime/kill_switch"),
    artifacts_root: Path = Path("artifacts/runs"),
) -> KillSwitchState:
    """Append kill_activated event and persist active state."""
    normalized_run_id = _validate_run_id(run_id)
    normalized_reason = _validate_reason(reason)
    resolved_actor = _resolve_actor(actor)
    status = get_kill_switch_status(normalized_run_id, runtime_root=runtime_root)
    previous_state = status.state
    ts_utc = _utc_now_iso8601()
    event = KillSwitchEvent(
        schema_version=SCHEMA_VERSION,
        event_id=str(uuid4()),
        ts_utc=ts_utc,
        run_id=normalized_run_id,
        event=EVENT_ACTIVATED,
        reason=normalized_reason,
        actor=resolved_actor,
        source="tc",
        previous_state=previous_state,
        new_state=STATE_ACTIVE,
    )
    _append_event(_events_path(runtime_root, normalized_run_id), event)
    _append_optional_artifact_journal_event(
        _artifact_journal_path(artifacts_root, normalized_run_id),
        event,
    )

    state = KillSwitchState(
        schema_version=SCHEMA_VERSION,
        run_id=normalized_run_id,
        state=STATE_ACTIVE,
        updated_at_utc=ts_utc,
        last_event_id=event.event_id,
        last_reason=normalized_reason,
        last_actor=resolved_actor,
        active_since_utc=ts_utc,
        cleared_at_utc=None,
    )
    _write_state(_state_path(runtime_root, normalized_run_id), state)
    return state


def clear_kill_switch(
    run_id: str,
    reason: str,
    actor: str | None = None,
    runtime_root: Path = Path("runtime/kill_switch"),
    artifacts_root: Path = Path("artifacts/runs"),
) -> KillSwitchState:
    """Append kill_cleared event and persist cleared state.

    We intentionally preserve `active_since_utc` when available for a clearer
    audit trail of when the most recent active period started.
    """
    normalized_run_id = _validate_run_id(run_id)
    normalized_reason = _validate_reason(reason)
    resolved_actor = _resolve_actor(actor)
    status = get_kill_switch_status(normalized_run_id, runtime_root=runtime_root)
    previous_state = status.state
    ts_utc = _utc_now_iso8601()
    event = KillSwitchEvent(
        schema_version=SCHEMA_VERSION,
        event_id=str(uuid4()),
        ts_utc=ts_utc,
        run_id=normalized_run_id,
        event=EVENT_CLEARED,
        reason=normalized_reason,
        actor=resolved_actor,
        source="tc",
        previous_state=previous_state,
        new_state=STATE_CLEARED,
    )
    _append_event(_events_path(runtime_root, normalized_run_id), event)
    _append_optional_artifact_journal_event(
        _artifact_journal_path(artifacts_root, normalized_run_id),
        event,
    )

    state = KillSwitchState(
        schema_version=SCHEMA_VERSION,
        run_id=normalized_run_id,
        state=STATE_CLEARED,
        updated_at_utc=ts_utc,
        last_event_id=event.event_id,
        last_reason=normalized_reason,
        last_actor=resolved_actor,
        active_since_utc=status.active_since_utc,
        cleared_at_utc=ts_utc,
    )
    _write_state(_state_path(runtime_root, normalized_run_id), state)
    return state
