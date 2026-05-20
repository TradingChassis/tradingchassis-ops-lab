"""Report rendering helpers."""

from __future__ import annotations


def render_backtest_skeleton_report(
    *,
    run_id: str,
    mode: str,
    engine: str,
    status: str,
    config_sha256: str,
) -> str:
    """Render the Slice 4 skeleton backtest report markdown."""
    return (
        f"# Backtest Skeleton Report: {run_id}\n\n"
        f"- mode: {mode}\n"
        f"- engine: {engine}\n"
        f"- status: {status}\n"
        f"- config_sha256: {config_sha256}\n\n"
        "## Artifacts\n\n"
        "- run_spec.yaml\n"
        "- metadata.json\n"
        "- journal.jsonl\n"
        "- metrics.json\n"
        "- report.md\n\n"
        "## Disclaimer\n\n"
        "This report comes from the Slice 4 backtest lifecycle skeleton.\n"
        "No NautilusTrader backtest was executed.\n"
        "No orders, fills, strategy PnL, or trading performance metrics were produced.\n"
    )
