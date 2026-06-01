"""Markdown rendering for backtest-vs-paper evidence artifacts."""

from __future__ import annotations

from typing import Any


def _render_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(_render_value(item) for item in value) if value else "-"
    if isinstance(value, dict):
        parts = [f"{key}={_render_value(value[key])}" for key in sorted(value)]
        return ", ".join(parts) if parts else "{}"
    return str(value)


def _escape_table_cell(value: Any) -> str:
    return _render_value(value).replace("|", "\\|").replace("\n", " ")


def render_backtest_vs_paper_evidence_report(evidence: dict[str, Any]) -> str:
    """Render a concise operational evidence markdown report."""
    backtest = evidence.get("mode_summary", {}).get("backtest", {})
    paper = evidence.get("mode_summary", {}).get("paper", {})
    artifact_presence = evidence.get("artifact_presence", {})
    compared_fields = evidence.get("compared_fields", [])
    journal_summary = evidence.get("journal_summary", {})
    safety_summary = evidence.get("safety_summary", {})
    connectivity_summary = evidence.get("connectivity_summary", {})
    known_gaps = evidence.get("known_gaps", [])
    non_goals = evidence.get("non_goals", [])
    notes = evidence.get("notes", [])

    compared_lines = [
        "| Area | Backtest | Paper | Classification | Match | Note |",
        "|---|---|---|---|---|---|",
    ]
    for field in compared_fields:
        compared_lines.append(
            "| "
            + " | ".join(
                [
                    _escape_table_cell(field.get("area")),
                    _escape_table_cell(field.get("backtest")),
                    _escape_table_cell(field.get("paper")),
                    _escape_table_cell(field.get("comparable")),
                    _escape_table_cell(field.get("match")),
                    _escape_table_cell(field.get("note")),
                ]
            )
            + " |"
        )
    if len(compared_lines) == 2:
        compared_lines.append("| - | - | - | - | - | - |")

    artifact_lines = [
        "| Artifact | Backtest | Paper |",
        "|---|---|---|",
    ]
    artifact_names = sorted(
        set(artifact_presence.get("backtest", {}).keys())
        | set(artifact_presence.get("paper", {}).keys())
    )
    for name in artifact_names:
        artifact_lines.append(
            "| "
            + " | ".join(
                [
                    name,
                    _escape_table_cell(artifact_presence.get("backtest", {}).get(name)),
                    _escape_table_cell(artifact_presence.get("paper", {}).get(name)),
                ]
            )
            + " |"
        )
    if len(artifact_lines) == 2:
        artifact_lines.append("| - | - | - |")

    shared_events = journal_summary.get("shared_events", [])
    rendered_shared_events = ", ".join(_render_value(item) for item in shared_events) or "-"

    notes_lines = "\n".join(f"- {_render_value(note)}" for note in notes) if notes else "- none"
    gaps_lines = (
        "\n".join(f"- `{_render_value(item)}`" for item in known_gaps) if known_gaps else "- none"
    )
    non_goals_lines = (
        "\n".join(f"- `{_render_value(item)}`" for item in non_goals) if non_goals else "- none"
    )
    backtest_event_total = _render_value(journal_summary.get("backtest", {}).get("event_total"))
    paper_event_total = _render_value(journal_summary.get("paper", {}).get("event_total"))
    paper_kill_switch_state = _render_value(safety_summary.get("paper_kill_switch_state"))
    paper_lifecycle_outcome = _render_value(safety_summary.get("paper_lifecycle_outcome"))
    backtest_safety_evaluated = _render_value(safety_summary.get("backtest_safety_evaluated"))
    backtest_readiness = _render_value(connectivity_summary.get("backtest_readiness"))
    paper_readiness = _render_value(connectivity_summary.get("paper_readiness"))
    backtest_probe = _render_value(connectivity_summary.get("backtest_probe"))
    paper_probe = _render_value(connectivity_summary.get("paper_probe"))
    backtest_reconciliation = _render_value(connectivity_summary.get("backtest_reconciliation"))
    paper_reconciliation = _render_value(connectivity_summary.get("paper_reconciliation"))
    backtest_mode_line = (
        "- backtest:"
        f" status={_render_value(backtest.get('status'))},"
        f" lifecycle={_render_value(backtest.get('lifecycle'))},"
        f" is_placeholder={_render_value(backtest.get('is_placeholder'))},"
        f" engine_executed={_render_value(backtest.get('engine_executed'))},"
        f" scenario_name={_render_value(backtest.get('scenario_name'))},"
        f" scenario_version={_render_value(backtest.get('scenario_version'))},"
        f" bars_seen={_render_value(backtest.get('bars_seen'))},"
        f" orders_submitted={_render_value(backtest.get('orders_submitted'))},"
        f" fills_count={_render_value(backtest.get('fills_count'))},"
        " deterministic_action_triggered="
        f"{_render_value(backtest.get('deterministic_action_triggered'))}\n"
    )
    paper_mode_line = (
        "- paper:"
        f" status={_render_value(paper.get('status'))},"
        f" lifecycle={_render_value(paper.get('lifecycle'))},"
        f" is_placeholder={_render_value(paper.get('is_placeholder'))},"
        f" engine_executed={_render_value(paper.get('engine_executed'))},"
        f" paper_lifecycle={_render_value(paper.get('paper_lifecycle'))},"
        f" heartbeat_count={_render_value(paper.get('heartbeat_count'))},"
        f" connectivity={_render_value(paper.get('connectivity'))},"
        f" safety_lifecycle_outcome={_render_value(paper.get('safety_lifecycle_outcome'))}\n\n"
    )

    return (
        "# Backtest vs Paper Operational Evidence\n\n"
        f"- comparison_status: `{_render_value(evidence.get('comparison_status'))}`\n"
        f"- backtest_run_id: `{_render_value(evidence.get('backtest_run_id'))}`\n"
        f"- paper_run_id: `{_render_value(evidence.get('paper_run_id'))}`\n\n"
        "## Summary\n\n"
        "This is operational evidence, not strategy performance.\n\n"
        "## Mode summary\n\n"
        f"{backtest_mode_line}"
        f"{paper_mode_line}"
        "## Compared fields\n\n"
        + "\n".join(compared_lines)
        + "\n\n## Artifact presence\n\n"
        + "\n".join(artifact_lines)
        + "\n\n## Journal summary\n\n"
        f"- backtest event_total: {backtest_event_total}\n"
        f"- paper event_total: {paper_event_total}\n"
        f"- shared_events: {rendered_shared_events}\n\n"
        "## Safety and connectivity\n\n"
        f"- paper kill switch state: {paper_kill_switch_state}\n"
        f"- paper lifecycle outcome: {paper_lifecycle_outcome}\n"
        f"- backtest safety evaluated: {backtest_safety_evaluated}\n"
        f"- backtest readiness state: {backtest_readiness}\n"
        f"- paper readiness state: {paper_readiness}\n"
        f"- backtest probe state: {backtest_probe}\n"
        f"- paper probe state: {paper_probe}\n"
        f"- backtest reconciliation status: {backtest_reconciliation}\n"
        f"- paper reconciliation status: {paper_reconciliation}\n\n"
        "## Known gaps\n\n"
        f"{gaps_lines}\n\n"
        "## Non-goals\n\n"
        f"{non_goals_lines}\n\n"
        "## Notes\n\n"
        f"{notes_lines}\n\n"
        "## Disclaimer\n\n"
        "- no PnL reporting\n"
        "- no Sharpe/returns reporting\n"
        "- no live/testnet/exchange evidence\n"
        "- paper mode is a bounded synthetic lifecycle skeleton\n"
        "- no real orders, fills, balances, positions, or account state\n"
    )
