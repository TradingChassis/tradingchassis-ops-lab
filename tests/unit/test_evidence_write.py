"""Unit tests for evidence write/path safety helpers."""

from __future__ import annotations

import pytest

from tradingchassis_ops_lab.evidence.write import (
    EvidenceWriteError,
    build_backtest_paper_evidence_paths,
    build_backtest_paper_pair_id,
    validate_artifact_id,
)


@pytest.mark.parametrize(
    "run_id",
    [
        "2026-05-20-btcusdt-backtest-001",
        "run_1",
        "run.1",
        "RUN-OK",
    ],
)
def test_validate_artifact_id_accepts_expected_values(run_id: str) -> None:
    assert validate_artifact_id(run_id) == run_id


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "   ",
        "../evil",
        "foo/bar",
        r"foo\bar",
        "/abs/path",
        "..",
        "run id with spaces",
        "run:id",
    ],
)
def test_validate_artifact_id_rejects_unsafe_values(run_id: str) -> None:
    with pytest.raises(EvidenceWriteError):
        validate_artifact_id(run_id)


def test_build_pair_id_rejects_path_traversal_values() -> None:
    with pytest.raises(EvidenceWriteError):
        build_backtest_paper_pair_id(backtest_run_id="../evil", paper_run_id="paper-ok")


def test_build_evidence_paths_stay_under_evidence_root(tmp_path) -> None:
    root = tmp_path / "evidence-root"
    paths = build_backtest_paper_evidence_paths(
        backtest_run_id="run.1",
        paper_run_id="run_2",
        evidence_root=root,
    )
    resolved_root = root.resolve()
    resolved_evidence_dir = paths.evidence_dir.resolve()
    assert resolved_evidence_dir.is_relative_to(resolved_root)
    assert paths.json_path.name == "backtest_vs_paper_evidence.json"
    assert paths.report_path.name == "backtest_vs_paper_evidence.md"
