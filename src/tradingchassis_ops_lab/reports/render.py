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
    """Render the backtest lifecycle skeleton report markdown."""
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
        "This report comes from the backtest lifecycle skeleton.\n"
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
    """Render the minimal NautilusTrader smoke backtest report markdown."""
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


def render_paper_skeleton_report(
    *,
    run_id: str,
    mode: str,
    engine: str,
    status: str,
    config_sha256: str,
    heartbeat_count: int,
    connectivity: str,
    kill_switch_state: str,
    lifecycle_outcome: str,
) -> str:
    """Render the paper lifecycle skeleton report markdown."""
    return (
        f"# Paper Skeleton Report: {run_id}\n\n"
        f"- mode: {mode}\n"
        f"- engine: {engine}\n"
        f"- status: {status}\n"
        f"- config_sha256: {config_sha256}\n"
        f"- heartbeat_count: {heartbeat_count}\n"
        f"- connectivity: {connectivity}\n\n"
        "## Safety status\n\n"
        f"- kill_switch_state: {kill_switch_state}\n"
        f"- lifecycle_outcome: {lifecycle_outcome}\n"
        "- control_signal: local file-based kill switch state\n"
        "- no order cancellation, no position flattening, no production safety guarantee\n\n"
        "## Skeleton Session Summary\n\n"
        "This run executes a bounded local paper lifecycle with deterministic behavior.\n"
        "No exchange or testnet integration is performed in this paper lifecycle skeleton.\n\n"
        "## Explicit Non-Features\n\n"
        "- no exchange/testnet connection\n"
        "- no API keys or secrets\n"
        "- no live market data\n"
        "- no orders\n"
        "- no fills\n"
        "- no strategy execution\n\n"
        "## Disclaimer\n\n"
        "This is not paper trading connectivity.\n"
        "This is only a lifecycle skeleton.\n"
    )
