"""Unit tests for local-only connectivity probe helpers."""

from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

from tradingchassis_ops_lab.connectivity.probe import (
    evaluate_connectivity_probe,
    patch_connectivity_probe_section,
    update_connectivity_probe_metadata_summary,
    validate_loopback_probe_url,
    write_connectivity_probe_artifact,
    write_connectivity_probe_journal_event,
)
from tradingchassis_ops_lab.runs.spec import load_run_spec


def _write_spec(path: Path) -> None:
    spec = {
        "spec_version": "v1",
        "run_id": "connectivity-probe-unit",
        "mode": "paper",
        "engine": "nautilus",
        "venue": "binance_testnet",
        "instrument": "BTCUSDT",
        "strategy": {"name": "ops_smoke_demo", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")


def _get_unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_server(
    *, status_code: int, delay_seconds: float = 0.0
) -> tuple[ThreadingHTTPServer, str]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            self.send_response(status_code)
            self.end_headers()
            self.wfile.write(b"local-fake-body")

        def log_message(self, _format: str, *args: object) -> None:
            del args

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_address[1])
    return server, f"http://127.0.0.1:{port}/health"


def test_validate_loopback_probe_url_accepts_localhost_and_ipv4_loopback() -> None:
    assert (
        validate_loopback_probe_url("http://127.0.0.1:18080/health")
        == "http://127.0.0.1:18080/health"
    )
    assert (
        validate_loopback_probe_url("http://localhost:18081/health")
        == "http://localhost:18081/health"
    )


def test_validate_loopback_probe_url_accepts_ipv6_loopback() -> None:
    assert validate_loopback_probe_url("http://[::1]:12345/health") == "http://[::1]:12345/health"


def test_validate_loopback_probe_url_rejects_non_local_targets() -> None:
    rejected = [
        "https://127.0.0.1:18080/health",
        "http://testnet.binance.vision/api/v3/time",
        "http://user:pass@127.0.0.1:18080/health",
        "http://127.0.0.1:18080/health?api_key=secret",
        "http://127.0.0.1:12345/health#fragment",
    ]
    for url in rejected:
        try:
            validate_loopback_probe_url(url)
        except ValueError:
            continue
        raise AssertionError(f"Expected URL validation failure for {url}")


def test_evaluate_connectivity_probe_probe_ok(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path)
    spec = load_run_spec(spec_path)

    server, url = _start_server(status_code=200)
    try:
        payload = evaluate_connectivity_probe(spec, url=url, timeout_ms=1000)
    finally:
        server.shutdown()
        server.server_close()

    assert payload["state"] == "probe_ok"
    assert payload["http_status"] == 200
    assert payload["probe_performed"] is True
    assert payload["network_scope"] == "loopback_only"
    assert payload["response_body_stored"] is False
    rendered = json.dumps(payload, sort_keys=True)
    assert "local-fake-body" not in rendered


def test_evaluate_connectivity_probe_http_error(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path)
    spec = load_run_spec(spec_path)

    server, url = _start_server(status_code=500)
    try:
        payload = evaluate_connectivity_probe(spec, url=url, timeout_ms=1000)
    finally:
        server.shutdown()
        server.server_close()

    assert payload["state"] == "probe_http_error"
    assert payload["http_status"] == 500
    assert payload["error_class"] == "http_error"
    assert payload["response_body_stored"] is False


def test_evaluate_connectivity_probe_unreachable(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path)
    spec = load_run_spec(spec_path)

    unused_port = _get_unused_port()
    payload = evaluate_connectivity_probe(
        spec,
        url=f"http://127.0.0.1:{unused_port}/health",
        timeout_ms=200,
    )
    assert payload["state"] == "probe_unreachable"
    assert payload["error_class"] == "connection_error"
    assert payload["response_body_stored"] is False


def test_evaluate_connectivity_probe_timeout(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    _write_spec(spec_path)
    spec = load_run_spec(spec_path)

    server, url = _start_server(status_code=200, delay_seconds=0.3)
    try:
        payload = evaluate_connectivity_probe(spec, url=url, timeout_ms=50)
    finally:
        server.shutdown()
        server.server_close()

    assert payload["state"] == "probe_timeout"
    assert payload["error_class"] == "timeout"
    assert payload["response_body_stored"] is False


def test_probe_artifact_metadata_journal_and_report_updates(tmp_path: Path) -> None:
    run_dir = tmp_path / "artifacts" / "runs" / "connectivity-probe-unit"
    run_dir.mkdir(parents=True)
    metadata_path = run_dir / "metadata.json"
    journal_path = run_dir / "journal.jsonl"
    report_path = run_dir / "report.md"
    metadata_path.write_text(
        json.dumps({"run_id": "connectivity-probe-unit"}) + "\n", encoding="utf-8"
    )
    journal_path.write_text('{"event":"run_initialized"}\n', encoding="utf-8")
    report_path.write_text("# Existing report\n", encoding="utf-8")

    payload = {
        "schema_version": "v1",
        "run_id": "connectivity-probe-unit",
        "ts_utc": "2026-05-20T00:00:00Z",
        "target": "local_fake_http",
        "venue": "binance_testnet",
        "instrument": "BTCUSDT",
        "url": "http://127.0.0.1:8080/health",
        "method": "GET",
        "network_scope": "loopback_only",
        "probe_performed": True,
        "state": "probe_ok",
        "http_status": 200,
        "latency_ms": 1.234,
        "error_class": None,
        "response_body_stored": False,
        "errors": [],
    }

    artifact_path = run_dir / "connectivity_probe.json"
    write_connectivity_probe_artifact(artifact_path, payload)
    update_connectivity_probe_metadata_summary(metadata_path, state="probe_ok")
    write_connectivity_probe_journal_event(journal_path, payload)
    patched = patch_connectivity_probe_section(report_path, payload)

    assert patched is True
    assert artifact_path.is_file()
    artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact_payload["state"] == "probe_ok"
    assert artifact_payload["response_body_stored"] is False

    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["connectivity_probe"]["state"] == "probe_ok"
    assert metadata_payload["connectivity_probe"]["network_scope"] == "loopback_only"
    assert metadata_payload["connectivity_probe"]["artifact"] == "connectivity_probe.json"

    journal_lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(journal_lines) == 2
    journal_payload = json.loads(journal_lines[-1])
    assert journal_payload["event"] == "connectivity_probe_evaluated"
    assert journal_payload["state"] == "probe_ok"
    assert journal_payload["http_status"] == 200

    report = report_path.read_text(encoding="utf-8")
    assert "## Connectivity probe" in report
    assert "state: probe_ok" in report
    assert "response_body_stored: False" in report
    assert "external connectivity: not used" in report


def test_patch_connectivity_probe_section_no_report_returns_false(tmp_path: Path) -> None:
    payload = {
        "state": "probe_ok",
        "network_scope": "loopback_only",
        "probe_performed": True,
        "http_status": 200,
        "latency_ms": 1.0,
        "response_body_stored": False,
    }
    missing_report_path = tmp_path / "missing-report.md"
    assert patch_connectivity_probe_section(missing_report_path, payload) is False
