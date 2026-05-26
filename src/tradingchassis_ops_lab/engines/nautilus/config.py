"""Narrow config helpers for minimal NautilusTrader smoke backtest."""

from __future__ import annotations

from collections.abc import Callable

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

from tradingchassis_ops_lab.engines.nautilus.strategies import create_ops_smoke_demo_strategy

OPS_SMOKE_DEMO_SCENARIO_NAME = "ops_smoke_demo"


class UnknownBacktestScenarioError(ValueError):
    """Raised when a run spec references an unsupported built-in scenario."""


def resolve_smoke_instrument(*, venue: str, instrument: str):
    """Resolve the single supported instrument for the smoke backtest."""
    normalized_venue = venue.strip().lower()
    normalized_instrument = instrument.strip().upper()
    if normalized_venue != "binance" or normalized_instrument != "BTCUSDT":
        raise ValueError(
            "Minimal NautilusTrader smoke backtest supports only venue=binance instrument=BTCUSDT."
        )
    return TestInstrumentProvider.btcusdt_binance()


def resolve_smoke_bar_type(*, instrument_id: InstrumentId) -> BarType:
    """Build the bar type expected by the fixture candle dataset."""
    return BarType.from_str(f"{instrument_id}-1-MINUTE-LAST-EXTERNAL")


def build_smoke_scenario_strategy(
    *,
    scenario_name: str,
    scenario_version: str,
    instrument_id: InstrumentId,
    bar_type: BarType,
) -> Strategy:
    """Resolve and build the single supported built-in smoke scenario strategy."""
    normalized_name = scenario_name.strip().lower()
    factories: dict[str, Callable[[], Strategy]] = {
        OPS_SMOKE_DEMO_SCENARIO_NAME: lambda: create_ops_smoke_demo_strategy(
            instrument_id=instrument_id,
            bar_type=bar_type,
            scenario_version=scenario_version,
        ),
    }
    factory = factories.get(normalized_name)
    if factory is None:
        allowed = ", ".join(sorted(factories))
        raise UnknownBacktestScenarioError(
            f"Unsupported backtest scenario strategy.name={scenario_name!r}. "
            f"Allowed built-in scenarios: {allowed}."
        )
    return factory()
