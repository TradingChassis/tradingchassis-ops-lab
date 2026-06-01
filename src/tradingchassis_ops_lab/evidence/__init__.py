"""Evidence comparison helpers."""

from tradingchassis_ops_lab.evidence.compare import (
    EvidenceArtifactsParseError,
    EvidenceCompareError,
    compare_backtest_paper,
)
from tradingchassis_ops_lab.evidence.render import render_backtest_vs_paper_evidence_report
from tradingchassis_ops_lab.evidence.write import (
    BacktestPaperEvidencePaths,
    EvidenceWriteError,
    build_backtest_paper_evidence_paths,
    build_backtest_paper_pair_id,
    validate_artifact_id,
    write_backtest_paper_evidence_artifacts,
)

__all__ = [
    "BacktestPaperEvidencePaths",
    "EvidenceArtifactsParseError",
    "EvidenceCompareError",
    "EvidenceWriteError",
    "build_backtest_paper_evidence_paths",
    "build_backtest_paper_pair_id",
    "compare_backtest_paper",
    "render_backtest_vs_paper_evidence_report",
    "validate_artifact_id",
    "write_backtest_paper_evidence_artifacts",
]
