"""Unit tests for file-based kill switch behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingchassis_ops_lab.safety.kill_switch import (
    KillSwitchValidationError,
    activate_kill_switch,
    clear_kill_switch,
    get_kill_switch_status,
)


def _state_path(runtime_root: Path, run_id: str) -> Path:
    return runtime_root / f"{run_id}.state.json"


def _events_path(runtime_root: Path, run_id: str) -> Path:
    return runtime_root / f"{run_id}.events.jsonl"


def test_activate_creates_state_and_events_files(tmp_path: Path, monkeypatch) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-activate"
    monkeypatch.setenv("USER", "ops-user")

    state = activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    state_file = _state_path(runtime_root, run_id)
    events_file = _events_path(runtime_root, run_id)
    assert state_file.is_file()
    assert events_file.is_file()
    assert state.state == "active"

    state_payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_payload["schema_version"] == "v1"
    assert state_payload["run_id"] == run_id
    assert state_payload["state"] == "active"
    assert state_payload["last_reason"] == "manual stop"
    assert state_payload["last_actor"] == "ops-user"
    assert state_payload["active_since_utc"] is not None
    assert state_payload["cleared_at_utc"] is None

    event_payload = json.loads(events_file.read_text(encoding="utf-8").splitlines()[0])
    assert event_payload["event"] == "kill_activated"
    assert event_payload["previous_state"] == "absent"
    assert event_payload["new_state"] == "active"
    assert event_payload["reason"] == "manual stop"
    assert event_payload["actor"] == "ops-user"
    assert event_payload["source"] == "tc"


def test_repeated_activate_appends_event_and_stays_active(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-repeat-activate"

    first = activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )
    second = activate_kill_switch(
        run_id=run_id,
        reason="manual stop again",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    events_lines = _events_path(runtime_root, run_id).read_text(encoding="utf-8").splitlines()
    assert len(events_lines) == 2
    first_event = json.loads(events_lines[0])
    second_event = json.loads(events_lines[1])
    assert first_event["previous_state"] == "absent"
    assert second_event["previous_state"] == "active"
    assert second.state == "active"
    assert second.last_reason == "manual stop again"
    assert first.last_event_id != second.last_event_id


def test_get_status_returns_absent_when_state_file_missing(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    status = get_kill_switch_status("kill-switch-missing", runtime_root=runtime_root)
    assert status.schema_version == "v1"
    assert status.run_id == "kill-switch-missing"
    assert status.state == "absent"


def test_clear_writes_cleared_state_and_event(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-clear"
    activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    cleared = clear_kill_switch(
        run_id=run_id,
        reason="manual reset",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    assert cleared.state == "cleared"
    assert cleared.cleared_at_utc is not None
    assert cleared.active_since_utc is not None

    state_payload = json.loads(_state_path(runtime_root, run_id).read_text(encoding="utf-8"))
    assert state_payload["state"] == "cleared"
    assert state_payload["last_reason"] == "manual reset"
    assert state_payload["cleared_at_utc"] is not None

    events_lines = _events_path(runtime_root, run_id).read_text(encoding="utf-8").splitlines()
    assert len(events_lines) == 2
    clear_event = json.loads(events_lines[1])
    assert clear_event["event"] == "kill_cleared"
    assert clear_event["new_state"] == "cleared"


def test_status_returns_cleared_after_clear(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-status-cleared"
    activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )
    clear_kill_switch(
        run_id=run_id,
        reason="manual reset",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    status = get_kill_switch_status(run_id=run_id, runtime_root=runtime_root)
    assert status.state == "cleared"


def test_empty_reason_fails_validation(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    with pytest.raises(KillSwitchValidationError):
        activate_kill_switch(
            run_id="kill-switch-empty-reason",
            reason="   ",
            runtime_root=runtime_root,
        )

    with pytest.raises(KillSwitchValidationError):
        clear_kill_switch(
            run_id="kill-switch-empty-reason",
            reason="\t",
            runtime_root=runtime_root,
        )


def test_actor_fallback_prefers_user_then_unknown(tmp_path: Path, monkeypatch) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"

    monkeypatch.setenv("USER", "alice")
    with_user = activate_kill_switch(
        run_id="kill-switch-actor-user",
        reason="reason",
        runtime_root=runtime_root,
    )
    assert with_user.last_actor == "alice"

    monkeypatch.delenv("USER", raising=False)
    unknown = activate_kill_switch(
        run_id="kill-switch-actor-unknown",
        reason="reason",
        runtime_root=runtime_root,
    )
    assert unknown.last_actor == "unknown"


def test_activation_mirrors_to_artifacts_journal_when_present(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-mirror"
    journal_path = artifacts_root / run_id / "journal.jsonl"
    journal_path.parent.mkdir(parents=True)
    journal_path.write_text('{"event":"run_started"}\n', encoding="utf-8")

    activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    journal_lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(journal_lines) == 2
    mirrored_event = json.loads(journal_lines[1])
    assert mirrored_event["event"] == "kill_activated"
    assert mirrored_event["run_id"] == run_id


def test_activation_succeeds_when_artifacts_journal_absent(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "kill_switch"
    artifacts_root = tmp_path / "artifacts" / "runs"
    run_id = "kill-switch-no-mirror"

    state = activate_kill_switch(
        run_id=run_id,
        reason="manual stop",
        runtime_root=runtime_root,
        artifacts_root=artifacts_root,
    )

    assert state.state == "active"
    assert _state_path(runtime_root, run_id).is_file()
