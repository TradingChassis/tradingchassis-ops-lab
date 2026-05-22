"""Unit tests for local observability HTTP metrics serving."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from tradingchassis_ops_lab.observability.serve import (
    PROMETHEUS_TEXT_CONTENT_TYPE,
    build_metrics_renderer,
    make_metrics_handler,
)


def _write_run_artifacts(
    *,
    artifacts_root: Path,
    run_id: str,
    metadata: dict,
    metrics: dict,
) -> None:
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")


def _start_server(handler_class: type) -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_metrics_handler_returns_prometheus_text_for_metrics_endpoint(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts" / "runs"
    _write_run_artifacts(
        artifacts_root=artifacts_root,
        run_id="serve-metrics",
        metadata={
            "run_id": "serve-metrics",
            "mode": "backtest",
            "engine": "nautilus",
            "venue": "binance",
            "instrument": "BTCUSDT",
            "status": "completed",
            "created_at_utc": "2026-05-20T19:00:00Z",
            "data": {"dataset": "btcusdt-sample"},
        },
        metrics={"is_placeholder": False, "engine_executed": True, "input_candles_count": 20},
    )
    renderer = build_metrics_renderer(artifacts_root=artifacts_root, run_id=None)
    handler_class = make_metrics_handler(renderer)
    server, thread = _start_server(handler_class)

    try:
        url = f"http://127.0.0.1:{server.server_port}/metrics"
        with urllib.request.urlopen(url, timeout=2) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Content-Type"] == PROMETHEUS_TEXT_CONTENT_TYPE
            assert "tradingchassis_ops_lab_run_info{" in body
            assert 'run_id="serve-metrics"' in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_metrics_handler_returns_404_for_unknown_path() -> None:
    handler_class = make_metrics_handler(lambda: "tradingchassis_ops_lab_run_info{} 1\n")
    server, thread = _start_server(handler_class)

    try:
        url = f"http://127.0.0.1:{server.server_port}/unknown"
        with urllib.request.urlopen(url, timeout=2):
            raise AssertionError("Expected HTTP 404 for unknown path")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
