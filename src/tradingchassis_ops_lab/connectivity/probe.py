"""Local-only connectivity probe helpers for loopback fake endpoints."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.runs.spec import RunSpec

_TARGET = "local_fake_http"
_METHOD = "GET"
_NETWORK_SCOPE = "loopback_only"

_STATE_OK = "probe_ok"
_STATE_HTTP_ERROR = "probe_http_error"
_STATE_TIMEOUT = "probe_timeout"
_STATE_UNREACHABLE = "probe_unreachable"
_STATE_UNKNOWN = "probe_unknown"

_ERROR_TIMEOUT = "timeout"
_ERROR_CONNECTION = "connection_error"
_ERROR_HTTP = "http_error"
_ERROR_UNKNOWN = "unknown"

_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}

_REPORT_START = "<!-- connectivity_probe:start -->"
_REPORT_END = "<!-- connectivity_probe:end -->"


class ConnectivityProbeArtifactsError(ValueError):
    """Raised when probe artifact files cannot be read or written safely."""


class ConnectivityProbeInvalidTargetError(ValueError):
    """Raised when probe URL target violates local-only loopback rules."""


def _utc_now_iso8601(now_utc: datetime | None = None) -> str:
    effective = now_utc if now_utc is not None else datetime.now(UTC)
    return effective.astimezone(UTC).isoformat().replace("+00:00", "Z")


def validate_loopback_probe_url(url: str) -> str:
    """Validate and normalize a local-only loopback probe URL."""
    parsed = urllib.parse.urlsplit(url)

    if parsed.scheme.lower() != "http":
        raise ConnectivityProbeInvalidTargetError(
            "Probe URL must use http:// for Unit 1 local fake probe."
        )
    if parsed.username is not None or parsed.password is not None:
        raise ConnectivityProbeInvalidTargetError("Probe URL must not include userinfo.")
    if parsed.query:
        raise ConnectivityProbeInvalidTargetError("Probe URL must not include query parameters.")
    if parsed.fragment:
        raise ConnectivityProbeInvalidTargetError("Probe URL must not include URL fragments.")
    if not parsed.hostname:
        raise ConnectivityProbeInvalidTargetError("Probe URL must include a host.")

    host = parsed.hostname.lower()
    if host not in _ALLOWED_HOSTS:
        raise ConnectivityProbeInvalidTargetError(
            "Probe URL host must be loopback-only (localhost, 127.0.0.1, or [::1])."
        )

    normalized_host = f"[{host}]" if ":" in host else host
    normalized_netloc = (
        f"{normalized_host}:{parsed.port}" if parsed.port is not None else normalized_host
    )
    normalized_path = parsed.path or "/"
    return urllib.parse.urlunsplit(("http", normalized_netloc, normalized_path, "", ""))


def evaluate_connectivity_probe(
    spec: RunSpec,
    *,
    url: str,
    timeout_ms: int,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Execute read-only HTTP GET probe against validated loopback endpoint."""
    validated_url = validate_loopback_probe_url(url)
    ts_utc = _utc_now_iso8601(now_utc)
    timeout_seconds = timeout_ms / 1000.0
    started = time.perf_counter()

    payload: dict[str, Any] = {
        "schema_version": "v1",
        "run_id": spec.run_id,
        "ts_utc": ts_utc,
        "target": _TARGET,
        "venue": spec.venue,
        "instrument": spec.instrument,
        "url": validated_url,
        "method": _METHOD,
        "network_scope": _NETWORK_SCOPE,
        "probe_performed": True,
        "state": _STATE_UNKNOWN,
        "http_status": None,
        "latency_ms": None,
        "error_class": None,
        "response_body_stored": False,
        "errors": [],
    }

    request = urllib.request.Request(validated_url, method=_METHOD)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
            payload["state"] = _STATE_OK
            payload["http_status"] = int(response.status)
            payload["latency_ms"] = latency_ms
            return payload
    except urllib.error.HTTPError as exc:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        payload["state"] = _STATE_HTTP_ERROR
        payload["http_status"] = int(exc.code)
        payload["latency_ms"] = latency_ms
        payload["error_class"] = _ERROR_HTTP
        payload["errors"] = [_ERROR_HTTP]
        exc.close()
        return payload
    except urllib.error.URLError as exc:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            payload["state"] = _STATE_TIMEOUT
            payload["error_class"] = _ERROR_TIMEOUT
            payload["errors"] = [_ERROR_TIMEOUT]
        elif isinstance(reason, TimeoutError):
            payload["state"] = _STATE_TIMEOUT
            payload["error_class"] = _ERROR_TIMEOUT
            payload["errors"] = [_ERROR_TIMEOUT]
        else:
            payload["state"] = _STATE_UNREACHABLE
            payload["error_class"] = _ERROR_CONNECTION
            payload["errors"] = [_ERROR_CONNECTION]
        payload["latency_ms"] = latency_ms
        return payload
    except socket.timeout:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        payload["state"] = _STATE_TIMEOUT
        payload["latency_ms"] = latency_ms
        payload["error_class"] = _ERROR_TIMEOUT
        payload["errors"] = [_ERROR_TIMEOUT]
        return payload
    except Exception:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        payload["state"] = _STATE_UNKNOWN
        payload["latency_ms"] = latency_ms
        payload["error_class"] = _ERROR_UNKNOWN
        payload["errors"] = [_ERROR_UNKNOWN]
        return payload


def write_connectivity_probe_artifact(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic connectivity_probe.json payload."""
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConnectivityProbeArtifactsError(
            f"Failed to write connectivity probe artifact {path}: {exc}"
        ) from exc


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConnectivityProbeArtifactsError(f"Failed to read {label} file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConnectivityProbeArtifactsError(
            f"Malformed JSON in {label} file {path}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ConnectivityProbeArtifactsError(
            f"Malformed {label} file {path}: expected a JSON object"
        )
    return payload


def update_connectivity_probe_metadata_summary(path: Path, *, state: str) -> None:
    """Patch metadata.json with minimal connectivity probe summary."""
    metadata = _read_json_object(path, label="metadata")
    metadata["connectivity_probe"] = {
        "state": state,
        "probe_performed": True,
        "network_scope": _NETWORK_SCOPE,
        "artifact": "connectivity_probe.json",
    }
    try:
        path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConnectivityProbeArtifactsError(
            f"Failed to write metadata file {path}: {exc}"
        ) from exc


def write_connectivity_probe_journal_event(path: Path, payload: dict[str, Any]) -> None:
    """Append compact connectivity probe event to run journal JSONL."""
    event = {
        "ts_utc": payload["ts_utc"],
        "event": "connectivity_probe_evaluated",
        "run_id": payload["run_id"],
        "state": payload["state"],
        "probe_performed": payload["probe_performed"],
        "network_scope": payload["network_scope"],
        "http_status": payload["http_status"],
        "latency_ms": payload["latency_ms"],
        "error_class": payload["error_class"],
    }
    try:
        with path.open("a", encoding="utf-8") as journal_file:
            journal_file.write(json.dumps(event, sort_keys=True))
            journal_file.write("\n")
    except OSError as exc:
        raise ConnectivityProbeArtifactsError(
            f"Failed to append journal file {path}: {exc}"
        ) from exc


def patch_connectivity_probe_section(path: Path, payload: dict[str, Any]) -> bool:
    """Update report.md with concise connectivity probe section when report exists."""
    if not path.exists():
        return False
    if not path.is_file():
        raise ConnectivityProbeArtifactsError(f"Expected report file at {path}")

    try:
        existing = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConnectivityProbeArtifactsError(f"Failed to read report file {path}: {exc}") from exc

    section = (
        f"{_REPORT_START}\n"
        "## Connectivity probe\n\n"
        f"- state: {payload['state']}\n"
        f"- network_scope: {payload['network_scope']}\n"
        f"- probe_performed: {payload['probe_performed']}\n"
        f"- http_status: {payload['http_status']}\n"
        f"- latency_ms: {payload['latency_ms']}\n"
        f"- response_body_stored: {payload['response_body_stored']}\n"
        "- external connectivity: not used\n"
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
        raise ConnectivityProbeArtifactsError(f"Failed to write report file {path}: {exc}") from exc
    return True
