"""Placeholder metrics interfaces for future slices.

Slice 1 intentionally avoids implementing runtime metrics behavior.
"""


def emit_metrics_placeholder() -> None:
    """Reserve metrics emission for a future slice."""
    raise NotImplementedError("Metrics emission will be implemented in a future slice.")
