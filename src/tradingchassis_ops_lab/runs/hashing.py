"""Config hashing utilities for run initialization."""

from __future__ import annotations

import hashlib
import json

from tradingchassis_ops_lab.runs.spec import RunSpec, run_spec_to_normalized_dict


def compute_config_sha256(spec: RunSpec) -> str:
    """Compute deterministic SHA-256 over canonicalized run config JSON."""
    normalized = run_spec_to_normalized_dict(spec)
    canonical = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
