"""Minimal NautilusTrader smoke backtest execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import nautilus_trader
import pandas as pd
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler

from tradingchassis_ops_lab.engines.nautilus.config import (
    resolve_smoke_bar_type,
    resolve_smoke_instrument,
)


class PreparedBacktestDatasetNotFoundError(FileNotFoundError):
    """Raised when the prepared local dataset required for backtest is missing."""


@dataclass(frozen=True)
class NautilusSmokeBacktestResult:
    """Execution facts from the minimal Nautilus smoke backtest."""

    dataset: str
    input_candles_count: int
    bars_processed: int
    engine_duration_ms: int
    nautilus_version: str


def _load_prepared_candles(*, dataset: str, data_root: Path = Path("data")) -> pd.DataFrame:
    csv_path = data_root / "datasets" / dataset / "candles_1m.csv"
    if not csv_path.is_file():
        raise PreparedBacktestDatasetNotFoundError(
            f"Prepared dataset file not found: {csv_path}. "
            "Run tc data prepare --dataset btcusdt-sample first."
        )

    frame = pd.read_csv(csv_path)
    frame["timestamp"] = pd.to_datetime(frame["ts_utc"], utc=True)
    return frame


def run_nautilus_backtest_smoke(
    *,
    dataset: str,
    venue: str,
    instrument: str,
    data_root: Path = Path("data"),
) -> NautilusSmokeBacktestResult:
    """Execute the smallest direct BacktestEngine smoke backtest."""
    candles = _load_prepared_candles(dataset=dataset, data_root=data_root)
    input_candles_count = len(candles.index)
    if input_candles_count == 0:
        raise ValueError("Prepared dataset candles CSV is empty.")

    nautilus_instrument = resolve_smoke_instrument(venue=venue, instrument=instrument)
    bar_type = resolve_smoke_bar_type(instrument_id=nautilus_instrument.id)

    ohlcv = candles.set_index("timestamp")[["open", "high", "low", "close", "volume"]]
    bars = BarDataWrangler(bar_type=bar_type, instrument=nautilus_instrument).process(ohlcv)

    engine = BacktestEngine(config=BacktestEngineConfig(run_analysis=False))
    started = perf_counter()
    try:
        engine.add_venue(
            venue=nautilus_instrument.id.venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            starting_balances=[Money(1_000_000, USDT)],
        )
        engine.add_instrument(nautilus_instrument)
        engine.add_data(bars)
        engine.run()
        result = engine.get_result()
    finally:
        engine.dispose()
    duration_ms = int((perf_counter() - started) * 1000)
    bars_processed = int(result.iterations) if result is not None else len(bars)

    return NautilusSmokeBacktestResult(
        dataset=dataset,
        input_candles_count=input_candles_count,
        bars_processed=bars_processed,
        engine_duration_ms=duration_ms,
        nautilus_version=nautilus_trader.__version__,
    )
