"""Minimal local HTTP serving for artifact-backed Prometheus metrics."""

from __future__ import annotations

from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ops_lab.observability.metrics import render_metrics_text

PROMETHEUS_TEXT_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def build_metrics_renderer(
    *,
    artifacts_root: Path,
    run_id: str | None,
    include_journal: bool = True,
) -> Callable[[], str]:
    """Build a no-argument renderer used by the HTTP request handler."""

    def _render() -> str:
        return render_metrics_text(
            artifacts_root=artifacts_root,
            run_id=run_id,
            include_journal=include_journal,
        )

    return _render


def make_metrics_handler(render_metrics: Callable[[], str]) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to one renderer callback."""

    class MetricsRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/metrics":
                body = b"Not Found\n"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            rendered = render_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", PROMETHEUS_TEXT_CONTENT_TYPE)
            self.send_header("Content-Length", str(len(rendered)))
            self.end_headers()
            self.wfile.write(rendered)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            del format, args

    return MetricsRequestHandler


def serve_metrics(
    *,
    artifacts_root: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    run_id: str | None = None,
    include_journal: bool = True,
) -> None:
    """Serve local artifact-derived Prometheus metrics over HTTP."""
    renderer = build_metrics_renderer(
        artifacts_root=artifacts_root,
        run_id=run_id,
        include_journal=include_journal,
    )
    handler_class = make_metrics_handler(renderer)
    with ThreadingHTTPServer((host, port), handler_class) as server:
        server.serve_forever()
