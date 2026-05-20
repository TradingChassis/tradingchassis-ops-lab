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


def render_backtest_nautilus_smoke_report(
    *,
    run_id: str,
    dataset: str,
    status: str,
    input_candles_count: int,
    bars_processed: int,
    engine_duration_ms: int,
) -> str:
    """Render the Slice 5 Nautilus smoke backtest report markdown."""
    return (
        f"# Nautilus Smoke Backtest Report: {run_id}\n\n"
        f"- status: {status}\n"
        f"- engine: nautilus\n"
        f"- dataset: {dataset}\n"
        f"- input_candles_count: {input_candles_count}\n"
        f"- bars_processed: {bars_processed}\n"
        f"- engine_duration_ms: {engine_duration_ms}\n\n"
        "## Smoke Backtest Summary\n\n"
        "This run executed a minimal NautilusTrader engine smoke backtest.\n"
        "The fixture dataset candles were loaded from prepared local data and converted to "
        "Nautilus bars before engine execution.\n"
        "The engine completed successfully for smoke validation.\n\n"
        "## Disclaimer\n\n"
        "This is not a validated strategy performance report.\n"
        "No profitability claims are made.\n"
        "No orders, fills, or PnL metrics are produced by this artifact contract.\n"
    )
