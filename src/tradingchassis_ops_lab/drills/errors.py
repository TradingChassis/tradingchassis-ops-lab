"""Errors for deterministic local failure drills."""

from __future__ import annotations


class DrillError(ValueError):
    """Base error for failure drill operations."""


class DrillValidationError(DrillError):
    """Raised when drill inputs fail validation."""


class DrillArtifactsError(DrillError):
    """Raised when run artifact directories or files are invalid."""
