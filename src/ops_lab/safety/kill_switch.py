"""Placeholder kill switch interfaces for future slices.

Slice 1 intentionally avoids implementing safety kill switch behavior.
"""


def trigger_kill_switch_placeholder() -> None:
    """Reserve kill switch behavior for a future slice."""
    raise NotImplementedError("Kill switch behavior will be implemented in a future slice.")
