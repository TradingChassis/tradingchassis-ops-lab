"""Narrow config helpers for Slice 5 Nautilus smoke backtest."""

from __future__ import annotations

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.test_kit.providers import TestInstrumentProvider


def resolve_smoke_instrument(*, venue: str, instrument: str):
    """Resolve the single supported instrument for the smoke backtest."""
    normalized_venue = venue.strip().lower()
    normalized_instrument = instrument.strip().upper()
    if normalized_venue != "binance" or normalized_instrument != "BTCUSDT":
        raise ValueError("Slice 5 smoke backtest supports only venue=binance instrument=BTCUSDT.")
    return TestInstrumentProvider.btcusdt_binance()


def resolve_smoke_bar_type(*, instrument_id: InstrumentId) -> BarType:
    """Build the bar type expected by the fixture candle dataset."""
    return BarType.from_str(f"{instrument_id}-1-MINUTE-LAST-EXTERNAL")
