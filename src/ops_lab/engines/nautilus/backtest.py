"""Placeholder backtest mode adapter for future slices.

Slice 1 intentionally avoids implementing run execution behavior.
"""


def run_backtest_placeholder() -> None:
    """Reserve backtest execution for a future slice."""
    raise NotImplementedError("Backtest execution will be implemented in a future slice.")
