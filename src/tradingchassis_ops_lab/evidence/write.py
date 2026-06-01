"""Evidence artifact pathing and file-writing helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tradingchassis_ops_lab.evidence.render import render_backtest_vs_paper_evidence_report

_EVIDENCE_JSON_NAME = "backtest_vs_paper_evidence.json"
_EVIDENCE_REPORT_NAME = "backtest_vs_paper_evidence.md"
_VALIDATE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class EvidenceWriteError(ValueError):
    """Raised when evidence artifacts cannot be written safely."""


@dataclass(frozen=True)
class BacktestPaperEvidencePaths:
    """Canonical paths for one backtest-vs-paper evidence artifact set."""

    evidence_dir: Path
    json_path: Path
    report_path: Path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_artifact_id(value: str, *, field_name: str = "run_id") -> str:
    """Validate one artifact identifier used for filesystem path joins."""
    cleaned = value.strip()
    if not cleaned:
        raise EvidenceWriteError(f"{field_name} must be a non-empty string.")
    if cleaned in {".", ".."} or ".." in cleaned:
        raise EvidenceWriteError(f"{field_name} must not contain '..'.")
    if "/" in cleaned or "\\" in cleaned:
        raise EvidenceWriteError(f"{field_name} must not contain path separators.")
    if Path(cleaned).is_absolute():
        raise EvidenceWriteError(f"{field_name} must not be an absolute path.")
    if not _VALIDATE_RUN_ID_RE.fullmatch(cleaned):
        raise EvidenceWriteError(
            f"{field_name} contains invalid characters; allowed: letters, digits, '.', '_', '-'."
        )
    return cleaned


def build_backtest_paper_pair_id(*, backtest_run_id: str, paper_run_id: str) -> str:
    """Build deterministic evidence pair id."""
    left = validate_artifact_id(backtest_run_id, field_name="backtest_run_id")
    right = validate_artifact_id(paper_run_id, field_name="paper_run_id")
    return f"{left}__{right}"


def build_backtest_paper_evidence_paths(
    *,
    backtest_run_id: str,
    paper_run_id: str,
    evidence_root: Path = Path("artifacts/evidence"),
) -> BacktestPaperEvidencePaths:
    """Resolve canonical output paths for one evidence pair."""
    evidence_root_resolved = evidence_root.resolve()
    pair_id = build_backtest_paper_pair_id(
        backtest_run_id=backtest_run_id,
        paper_run_id=paper_run_id,
    )
    evidence_dir = (evidence_root_resolved / pair_id).resolve()
    if not _is_relative_to(evidence_dir, evidence_root_resolved):
        raise EvidenceWriteError(
            "Resolved evidence directory escapes evidence root: "
            f"{evidence_dir} not under {evidence_root_resolved}."
        )
    return BacktestPaperEvidencePaths(
        evidence_dir=evidence_dir,
        json_path=evidence_dir / _EVIDENCE_JSON_NAME,
        report_path=evidence_dir / _EVIDENCE_REPORT_NAME,
    )


def write_backtest_paper_evidence_artifacts(
    *,
    evidence: dict[str, Any],
    evidence_root: Path = Path("artifacts/evidence"),
) -> BacktestPaperEvidencePaths:
    """Write evidence JSON and markdown report artifacts."""
    backtest_run_id = evidence.get("backtest_run_id")
    paper_run_id = evidence.get("paper_run_id")
    if not isinstance(backtest_run_id, str):
        raise EvidenceWriteError("Evidence payload missing non-empty backtest_run_id.")
    if not isinstance(paper_run_id, str):
        raise EvidenceWriteError("Evidence payload missing non-empty paper_run_id.")
    backtest_run_id_validated = validate_artifact_id(backtest_run_id, field_name="backtest_run_id")
    paper_run_id_validated = validate_artifact_id(paper_run_id, field_name="paper_run_id")

    paths = build_backtest_paper_evidence_paths(
        backtest_run_id=backtest_run_id_validated,
        paper_run_id=paper_run_id_validated,
        evidence_root=evidence_root,
    )
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)

    paths.json_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths.report_path.write_text(
        render_backtest_vs_paper_evidence_report(evidence),
        encoding="utf-8",
    )
    return paths
