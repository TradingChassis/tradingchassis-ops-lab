"""Run specification model and loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class RunSpecLoadError(ValueError):
    """Raised when a run spec cannot be loaded or validated."""


class StrictBaseModel(BaseModel):
    """Base model with strict unknown-field handling."""

    model_config = ConfigDict(extra="forbid")


class StrategySpec(StrictBaseModel):
    """Strategy metadata for the v1 run spec."""

    name: str
    version: str

    @field_validator("name", "version", mode="before")
    @classmethod
    def _validate_non_empty_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned


class DataSpec(StrictBaseModel):
    """Dataset reference and placeholder fingerprint."""

    dataset: str
    fingerprint: str | None = None

    @field_validator("dataset", mode="before")
    @classmethod
    def _validate_dataset(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned

    @field_validator("fingerprint", mode="before")
    @classmethod
    def _normalize_fingerprint(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string or null")
        cleaned = value.strip()
        return cleaned or None


class RiskSpec(StrictBaseModel):
    """Risk profile placeholder for the v1 run spec."""

    profile: str

    @field_validator("profile", mode="before")
    @classmethod
    def _validate_profile(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned


class ObservabilitySpec(StrictBaseModel):
    """Simple observability toggles for the v1 run spec."""

    journal: bool = True
    metrics: bool = False
    report: bool = False


class RunSpec(StrictBaseModel):
    """Validated run specification for initialization workflows."""

    spec_version: Literal["v1"]
    run_id: str
    mode: Literal["backtest", "paper"]
    engine: Literal["nautilus"]
    venue: str
    instrument: str
    strategy: StrategySpec
    data: DataSpec
    risk: RiskSpec
    observability: ObservabilitySpec

    @field_validator("run_id", "venue", "instrument", mode="before")
    @classmethod
    def _validate_non_empty_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned


def load_run_spec(path: Path) -> RunSpec:
    """Load and validate a run spec from a YAML file."""
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RunSpecLoadError(f"Spec file not found: {path}") from exc
    except OSError as exc:
        raise RunSpecLoadError(f"Failed to read spec file {path}: {exc}") from exc

    try:
        raw_spec = yaml.safe_load(contents)
    except yaml.YAMLError as exc:
        raise RunSpecLoadError(f"Invalid YAML in spec file {path}: {exc}") from exc

    if raw_spec is None:
        raise RunSpecLoadError(f"Spec file is empty: {path}")
    if not isinstance(raw_spec, dict):
        raise RunSpecLoadError(f"Spec file must contain a YAML mapping at top level: {path}")

    try:
        return RunSpec.model_validate(raw_spec)
    except ValidationError as exc:
        raise RunSpecLoadError(f"Spec validation failed for {path}: {exc}") from exc


def run_spec_to_normalized_dict(spec: RunSpec) -> dict[str, Any]:
    """Convert a validated run spec into a normalization-friendly dictionary."""
    return spec.model_dump(mode="json", exclude_none=False)
