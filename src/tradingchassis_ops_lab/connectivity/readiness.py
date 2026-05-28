"""Local-only connectivity readiness evaluation and artifact helpers."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from tradingchassis_ops_lab.runs.spec import RunSpec

_READINESS_DISABLED = "disabled"
_READINESS_MISSING_CREDENTIALS = "missing_credentials"
_READINESS_CONFIGURED = "configured"
_READINESS_INVALID_CONFIG = "invalid_config"
_READINESS_UNKNOWN = "unknown"

_PROBE_DEFERRED_REASON = "local_only_no_network"

_REPORT_START = "<!-- connectivity_readiness:start -->"
_REPORT_END = "<!-- connectivity_readiness:end -->"


class ConnectivityReadinessArtifactsError(ValueError):
    """Raised when readiness artifact files cannot be read or written safely."""


def _utc_now_iso8601(now_utc: datetime | None = None) -> str:
    effective = now_utc if now_utc is not None else datetime.now(UTC)
    return effective.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _is_present_env(name: str, env: Mapping[str, str] | Mapping[str, object]) -> bool:
    value = env.get(name)
    if value is None:
        return False
    return str(value).strip() != ""


def evaluate_connectivity_readiness(
    spec: RunSpec,
    *,
    env: Mapping[str, str] | Mapping[str, object] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate connectivity readiness from spec placeholders and local env presence.

    This evaluator intentionally performs no network calls and never returns env values.
    """
    observed_env: Mapping[str, str] | Mapping[str, object] = env if env is not None else os.environ
    ts_utc = _utc_now_iso8601(now_utc)
    readiness = spec.connectivity_readiness

    payload: dict[str, Any] = {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "ts_utc": ts_utc,
        "enabled": False,
        "state": _READINESS_DISABLED,
        "target": None,
        "venue": spec.venue,
        "instrument": spec.instrument,
        "required_env": [],
        "optional_env": [],
        "present_env": [],
        "missing_env": [],
        "missing_required_count": 0,
        "probe_performed": False,
        "probe_deferred_reason": _PROBE_DEFERRED_REASON,
        "errors": [],
    }

    if readiness is None:
        return payload

    payload["enabled"] = readiness.enabled
    payload["target"] = readiness.target

    if not readiness.enabled:
        return payload

    try:
        required_env = sorted(readiness.credential_placeholders.required_env)
        optional_env = sorted(readiness.credential_placeholders.optional_env)
    except Exception as exc:
        payload["state"] = _READINESS_INVALID_CONFIG
        payload["errors"] = [str(exc)]
        return payload

    try:
        present_env = sorted(
            name for name in required_env + optional_env if _is_present_env(name, observed_env)
        )
        missing_env = sorted(
            name for name in required_env + optional_env if not _is_present_env(name, observed_env)
        )
        missing_required = [
            name for name in required_env if not _is_present_env(name, observed_env)
        ]
    except Exception as exc:
        payload["state"] = _READINESS_UNKNOWN
        payload["errors"] = [str(exc)]
        return payload

    payload["required_env"] = required_env
    payload["optional_env"] = optional_env
    payload["present_env"] = present_env
    payload["missing_env"] = missing_env
    payload["missing_required_count"] = len(missing_required)
    payload["state"] = (
        _READINESS_CONFIGURED if not missing_required else _READINESS_MISSING_CREDENTIALS
    )
    return payload


def write_connectivity_readiness_artifact(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic connectivity_readiness.json payload."""
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to write connectivity readiness artifact {path}: {exc}"
        ) from exc


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to read {label} file {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Malformed JSON in {label} file {path}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ConnectivityReadinessArtifactsError(
            f"Malformed {label} file {path}: expected a JSON object"
        )
    return payload


def update_connectivity_readiness_metadata_summary(
    path: Path,
    *,
    state: str,
    enabled: bool,
) -> None:
    """Patch metadata.json with minimal connectivity readiness summary."""
    metadata = _read_json_object(path, label="metadata")
    metadata["connectivity_readiness"] = {
        "state": state,
        "enabled": enabled,
        "probe_performed": False,
        "artifact": "connectivity_readiness.json",
    }
    try:
        path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to write metadata file {path}: {exc}"
        ) from exc


def write_connectivity_readiness_journal_event(path: Path, payload: dict[str, Any]) -> None:
    """Append compact readiness event to run journal JSONL."""
    event = {
        "ts_utc": payload["ts_utc"],
        "event": "connectivity_readiness_evaluated",
        "run_id": payload["run_id"],
        "state": payload["state"],
        "enabled": payload["enabled"],
        "required_env_count": len(payload["required_env"]),
        "missing_required_count": payload["missing_required_count"],
        "probe_performed": False,
    }
    try:
        with path.open("a", encoding="utf-8") as journal_file:
            journal_file.write(json.dumps(event, sort_keys=True))
            journal_file.write("\n")
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to append journal file {path}: {exc}"
        ) from exc


def patch_connectivity_readiness_section(path: Path, payload: dict[str, Any]) -> bool:
    """Update report.md with a concise connectivity readiness section when report exists.

    Returns True when report was updated, False when report file does not exist.
    """
    if not path.exists():
        return False
    if not path.is_file():
        raise ConnectivityReadinessArtifactsError(f"Expected report file at {path}")
    try:
        existing = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to read report file {path}: {exc}"
        ) from exc

    section = (
        f"{_REPORT_START}\n"
        "## Connectivity readiness\n\n"
        f"- state: {payload['state']}\n"
        f"- enabled: {payload['enabled']}\n"
        f"- missing_required_count: {payload['missing_required_count']}\n"
        "- probe_performed: False\n"
        "- No network calls were performed.\n"
        f"{_REPORT_END}"
    )

    if _REPORT_START in existing and _REPORT_END in existing:
        start = existing.index(_REPORT_START)
        end = existing.index(_REPORT_END) + len(_REPORT_END)
        updated = f"{existing[:start].rstrip()}\n\n{section}\n{existing[end:].lstrip()}"
    else:
        updated = f"{existing.rstrip()}\n\n{section}\n"

    try:
        path.write_text(updated, encoding="utf-8")
    except OSError as exc:
        raise ConnectivityReadinessArtifactsError(
            f"Failed to write report file {path}: {exc}"
        ) from exc
    return True
