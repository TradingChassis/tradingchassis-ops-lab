"""Built-in Nautilus strategy for the ops smoke demo scenario."""

from __future__ import annotations

from dataclasses import dataclass

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


@dataclass(frozen=True)
class OpsSmokeDemoCounters:
    """Operational counters collected by the built-in demo strategy."""

    bars_seen: int
    orders_submitted: int
    fills_count: int
    deterministic_action_triggered: bool


class OpsSmokeDemoStrategyConfig(StrategyConfig, frozen=True):
    """Configuration for the built-in ops smoke demo strategy."""

    instrument_id: InstrumentId
    bar_type: BarType
    scenario_version: str
    action_bar_index: int = 5


class OpsSmokeDemoStrategy(Strategy):
    """Minimal deterministic strategy used for local operational smoke runs."""

    def __init__(self, config: OpsSmokeDemoStrategyConfig) -> None:
        super().__init__(config)
        self.bars_seen = 0
        self.orders_submitted = 0
        self.fills_count = 0
        self.deterministic_action_triggered = False

    def on_start(self) -> None:
        """Subscribe to prepared 1-minute bars for deterministic counting."""
        self.subscribe_bars(bar_type=self.config.bar_type)

    def on_stop(self) -> None:
        """Cleanly unsubscribe from bars for stable shutdown logs."""
        self.unsubscribe_bars(bar_type=self.config.bar_type)

    def on_bar(self, bar) -> None:  # noqa: ANN001
        """Track bar flow and trigger one deterministic non-trading action."""
        del bar
        self.bars_seen += 1
        if self.bars_seen == self.config.action_bar_index:
            self.deterministic_action_triggered = True

    def on_order_submitted(self, event) -> None:  # noqa: ANN001
        """Track order submissions when/if future behavior adds them."""
        del event
        self.orders_submitted += 1

    def on_order_filled(self, event) -> None:  # noqa: ANN001
        """Track fills when/if future behavior adds them."""
        del event
        self.fills_count += 1

    def counters(self) -> OpsSmokeDemoCounters:
        """Return stable operational counters for artifact reporting."""
        return OpsSmokeDemoCounters(
            bars_seen=self.bars_seen,
            orders_submitted=self.orders_submitted,
            fills_count=self.fills_count,
            deterministic_action_triggered=self.deterministic_action_triggered,
        )


def create_ops_smoke_demo_strategy(
    *,
    instrument_id: InstrumentId,
    bar_type: BarType,
    scenario_version: str,
) -> OpsSmokeDemoStrategy:
    """Build the single built-in smoke demo strategy instance."""
    config = OpsSmokeDemoStrategyConfig(
        instrument_id=instrument_id,
        bar_type=bar_type,
        scenario_version=scenario_version,
    )
    return OpsSmokeDemoStrategy(config=config)
