"""Artifact layout management for run initialization."""

from __future__ import annotations

import shutil
from pathlib import Path

from tradingchassis_ops_lab.runs.spec import RunSpec


class RunArtifactsAlreadyExistError(FileExistsError):
    """Raised when attempting to initialize an already-existing run artifacts directory."""


def get_run_artifacts_dir(run_id: str, artifacts_root: Path = Path("artifacts/runs")) -> Path:
    """Return the run-specific artifact directory path."""
    return artifacts_root / run_id


def initialize_run_artifacts(
    spec_path: Path,
    spec: RunSpec,
    config_sha256: str,
    artifacts_root: Path = Path("artifacts/runs"),
) -> Path:
    """Create run artifacts directory and copy validated spec."""
    del config_sha256  # Reserved for future use in artifact manifests.
    run_dir = get_run_artifacts_dir(run_id=spec.run_id, artifacts_root=artifacts_root)
    if run_dir.exists():
        raise RunArtifactsAlreadyExistError(f"Run artifacts already exist at {run_dir}")

    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()
    shutil.copy2(spec_path, run_dir / "run_spec.yaml")
    return run_dir
