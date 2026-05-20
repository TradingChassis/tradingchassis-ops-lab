"""Placeholder run spec models for future slices.

Slice 1 intentionally avoids implementing finalized run spec schemas.
"""

from pydantic import BaseModel


class RunSpecPlaceholder(BaseModel):
    """Temporary marker model for future run spec work."""


def load_run_spec_placeholder() -> None:
    """Reserve a run spec loader interface for a future slice."""
    raise NotImplementedError("Run spec loading will be implemented in a future slice.")
