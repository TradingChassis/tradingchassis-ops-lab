"""Placeholder metadata interfaces for future slices.

Slice 1 intentionally avoids persisting operational metadata.
"""


def write_run_metadata_placeholder() -> None:
    """Reserve metadata writing for a future slice."""
    raise NotImplementedError("Run metadata writing will be implemented in a future slice.")
