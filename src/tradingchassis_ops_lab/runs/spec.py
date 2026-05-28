"""Run specification model and loader."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class RunSpecLoadError(ValueError):
    """Raised when a run spec cannot be loaded or validated."""


class StrictBaseModel(BaseModel):
    """Base model with strict unknown-field handling."""

    model_config = ConfigDict(extra="forbid")


class StrategySpec(StrictBaseModel):
    """Scenario identity metadata for the v1 run spec.

    Values are used for traceability in run metadata and config hashing.
    Backtest uses ``name`` to select from a tiny set of built-in scenarios.
    Dynamic custom strategy loading and plugin/module paths are intentionally
    out of scope.
    """

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
    """Dataset reference and optional fingerprint metadata.

    ``fingerprint`` is currently traceability metadata and is not enforced as
    a runtime gate by backtest/paper execution paths.
    """

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
    """Observability preference metadata for the v1 run spec.

    These fields are currently recorded in run metadata but do not disable
    artifact generation in the active lifecycle implementations.
    """

    journal: bool = True
    metrics: bool = False
    report: bool = False


_ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class CredentialPlaceholdersSpec(StrictBaseModel):
    """Environment variable name placeholders for readiness contract metadata."""

    required_env: list[str] = Field(default_factory=list)
    optional_env: list[str] = Field(default_factory=list)

    @field_validator("required_env", "optional_env", mode="before")
    @classmethod
    def _validate_env_name_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("must be a list of environment variable names")

        validated: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("environment variable names must be strings")
            cleaned = item.strip()
            if not cleaned:
                raise ValueError("environment variable names must be non-empty strings")
            if not _ENV_VAR_NAME_PATTERN.match(cleaned):
                raise ValueError("environment variable names must match ^[A-Z_][A-Z0-9_]*$")
            validated.append(cleaned)
        return validated

    @model_validator(mode="after")
    def _validate_duplicates_and_overlap(self) -> CredentialPlaceholdersSpec:
        if len(self.required_env) != len(set(self.required_env)):
            raise ValueError("required_env cannot contain duplicate names")
        if len(self.optional_env) != len(set(self.optional_env)):
            raise ValueError("optional_env cannot contain duplicate names")

        overlapping = sorted(set(self.required_env) & set(self.optional_env))
        if overlapping:
            raise ValueError(
                "required_env and optional_env cannot overlap: " + ", ".join(overlapping)
            )
        return self


class ConnectivityReadinessSpec(StrictBaseModel):
    """Reserved local-only connectivity readiness contract metadata.

    This block does not perform network checks or environment validation in the
    current implementation. It defines schema-only placeholders for later
    readiness evaluation work.
    """

    enabled: bool = False
    target: Literal["paper_testnet_probe"] | None = None
    venue: str | None = None
    credential_placeholders: CredentialPlaceholdersSpec = Field(
        default_factory=CredentialPlaceholdersSpec
    )
    notes: str | None = None

    @field_validator("venue", mode="before")
    @classmethod
    def _normalize_optional_venue(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string or null")
        cleaned = value.strip()
        return cleaned or None

    @field_validator("notes", mode="before")
    @classmethod
    def _normalize_optional_notes(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string or null")
        cleaned = value.strip()
        return cleaned or None


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
    connectivity_readiness: ConnectivityReadinessSpec | None = None

    @field_validator("run_id", "venue", "instrument", mode="before")
    @classmethod
    def _validate_non_empty_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must be a non-empty string")
        return cleaned

    @model_validator(mode="after")
    def _validate_connectivity_readiness_venue(self) -> RunSpec:
        if (
            self.connectivity_readiness is not None
            and self.connectivity_readiness.venue is not None
            and self.connectivity_readiness.venue != self.venue
        ):
            raise ValueError(
                "connectivity_readiness.venue must match top-level venue when provided"
            )
        return self


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
