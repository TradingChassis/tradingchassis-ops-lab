"""CLI entry point for tradingchassis_ops_lab."""

import json
import os
from pathlib import Path

import typer

from tradingchassis_ops_lab import __version__
from tradingchassis_ops_lab.data.fingerprint import (
    PreparedDatasetNotFoundError,
    fingerprint_dataset,
    write_fingerprint,
)
from tradingchassis_ops_lab.data.prepare import UnsupportedDatasetError, prepare_dataset
from tradingchassis_ops_lab.drills import (
    DrillArtifactsError,
    DrillValidationError,
    execute_reconciliation_mismatch_drill,
    execute_restart_recovery_drill,
    execute_stale_market_data_drill,
)
from tradingchassis_ops_lab.observability.metrics import (
    RunObservabilityError,
    export_run_metrics,
)
from tradingchassis_ops_lab.observability.serve import serve_metrics
from tradingchassis_ops_lab.reconciliation.checks import (
    ReconciliationError,
    run_reconciliation_check,
)
from tradingchassis_ops_lab.runs.artifacts import (
    RunArtifactsAlreadyExistError,
    initialize_run_artifacts,
)
from tradingchassis_ops_lab.runs.backtest import InvalidBacktestModeError, run_backtest_lifecycle
from tradingchassis_ops_lab.runs.hashing import compute_config_sha256
from tradingchassis_ops_lab.runs.journal import append_journal_event, build_run_initialized_event
from tradingchassis_ops_lab.runs.metadata import build_initial_metadata, write_metadata
from tradingchassis_ops_lab.runs.paper import InvalidPaperModeError, run_paper_lifecycle
from tradingchassis_ops_lab.runs.spec import RunSpecLoadError, load_run_spec
from tradingchassis_ops_lab.safety.kill_switch import (
    KillSwitchError,
    activate_kill_switch,
    clear_kill_switch,
    get_kill_switch_status,
)

app = typer.Typer(help="TradingChassis Ops Lab CLI.")
spec_app = typer.Typer(help="Run spec validation commands.")
run_app = typer.Typer(help="Run initialization commands.")
data_app = typer.Typer(help="Local dataset preparation and fingerprint commands.")
metrics_app = typer.Typer(
    help="Local artifact-derived metrics commands (export one run or serve /metrics over HTTP)."
)
kill_app = typer.Typer(help="File-based kill switch safety commands.")
reconcile_app = typer.Typer(help="File-based reconciliation commands.")
drill_app = typer.Typer(help="Deterministic local failure drills.")
app.add_typer(spec_app, name="spec")
app.add_typer(run_app, name="run")
app.add_typer(data_app, name="data")
app.add_typer(metrics_app, name="metrics")
app.add_typer(kill_app, name="kill")
app.add_typer(reconcile_app, name="reconcile")
app.add_typer(drill_app, name="drill")


@app.callback()
def main() -> None:
    """Base command group for future subcommands."""


@app.command("version")
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@spec_app.command("validate")
def spec_validate(spec: Path = typer.Option(..., "--spec", help="Path to run spec YAML.")) -> None:
    """Validate a run spec YAML file."""
    try:
        parsed = load_run_spec(spec)
    except RunSpecLoadError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Spec is valid: run_id={parsed.run_id} mode={parsed.mode} engine={parsed.engine}")


@run_app.command("init")
def run_init(spec: Path = typer.Option(..., "--spec", help="Path to run spec YAML.")) -> None:
    """Initialize run artifacts for a validated run spec."""
    try:
        parsed = load_run_spec(spec)
        config_sha256 = compute_config_sha256(parsed)
        artifacts_dir = initialize_run_artifacts(
            spec_path=spec,
            spec=parsed,
            config_sha256=config_sha256,
        )
    except RunSpecLoadError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except RunArtifactsAlreadyExistError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    metadata = build_initial_metadata(
        spec=parsed,
        spec_path=spec,
        artifacts_dir=artifacts_dir,
        config_sha256=config_sha256,
    )
    write_metadata(artifacts_dir / "metadata.json", metadata)

    event = build_run_initialized_event(
        spec=parsed,
        spec_path=spec,
        artifacts_dir=artifacts_dir,
        config_sha256=config_sha256,
    )
    append_journal_event(artifacts_dir / "journal.jsonl", event)

    typer.echo(f"Initialized run artifacts at {artifacts_dir.resolve()}")
    typer.echo(f"config_sha256={config_sha256}")


@run_app.command("backtest")
def run_backtest(spec: Path = typer.Option(..., "--spec", help="Path to run spec YAML.")) -> None:
    """Run a minimal Nautilus smoke backtest and persist lifecycle artifacts."""
    try:
        artifacts_dir, config_sha256 = run_backtest_lifecycle(spec)
    except (RunSpecLoadError, InvalidBacktestModeError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except RunArtifactsAlreadyExistError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Backtest lifecycle artifacts at {artifacts_dir.resolve()}")
    typer.echo(f"config_sha256={config_sha256}")
    typer.echo("status=completed")


@run_app.command("paper")
def run_paper(spec: Path = typer.Option(..., "--spec", help="Path to run spec YAML.")) -> None:
    """Run a bounded deterministic paper lifecycle skeleton and persist artifacts."""
    try:
        artifacts_dir, config_sha256 = run_paper_lifecycle(spec)
    except (RunSpecLoadError, InvalidPaperModeError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except RunArtifactsAlreadyExistError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Paper lifecycle artifacts at {artifacts_dir.resolve()}")
    typer.echo(f"config_sha256={config_sha256}")
    typer.echo("status=completed")


def _resolve_data_root() -> Path:
    configured = os.environ.get("TRADINGCHASSIS_OPS_LAB_DATA_ROOT")
    if configured:
        return Path(configured)
    return Path("data")


def _resolve_runtime_root() -> Path:
    configured = os.environ.get("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT")
    if configured:
        return Path(configured)
    return Path("runtime/kill_switch")


def _resolve_artifacts_root() -> Path:
    configured = os.environ.get("TRADINGCHASSIS_OPS_LAB_ARTIFACTS_ROOT")
    if configured:
        return Path(configured)
    return Path("artifacts/runs")


@data_app.command("prepare")
def data_prepare(
    dataset: str = typer.Option(..., "--dataset", help="Dataset name to prepare."),
) -> None:
    """Prepare a supported local dataset from committed fixtures."""
    data_root = _resolve_data_root()
    try:
        prepared = prepare_dataset(dataset=dataset, data_root=data_root)
    except (UnsupportedDatasetError, FileNotFoundError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Prepared dataset={prepared.dataset}")
    typer.echo(f"target_dir={prepared.target_dir.resolve()}")
    typer.echo(f"files={len(prepared.files)}")


@data_app.command("fingerprint")
def data_fingerprint(
    dataset: str = typer.Option(..., "--dataset", help="Dataset name to fingerprint."),
) -> None:
    """Fingerprint a prepared local dataset and persist fingerprint JSON."""
    data_root = _resolve_data_root()
    try:
        fingerprint = fingerprint_dataset(dataset=dataset, data_root=data_root)
        output_path = write_fingerprint(fingerprint=fingerprint, data_root=data_root)
    except (UnsupportedDatasetError, PreparedDatasetNotFoundError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"dataset_sha256={fingerprint.dataset_sha256}")
    typer.echo(f"fingerprint_file={output_path.resolve()}")


@metrics_app.command("export")
def metrics_export(
    run_id: str = typer.Option(..., "--run-id", help="Run ID to export metrics for."),
    artifacts_root: Path = typer.Option(
        Path("artifacts/runs"),
        "--artifacts-root",
        help="Root directory containing run artifact subdirectories.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional output file path for Prometheus text exposition.",
    ),
    include_journal: bool = typer.Option(
        True,
        "--include-journal/--no-include-journal",
        help="Include journal-derived metrics.",
    ),
) -> None:
    """Export run artifact metrics as Prometheus text exposition."""
    try:
        rendered = export_run_metrics(
            run_id=run_id,
            artifacts_root=artifacts_root,
            include_journal=include_journal,
        )
    except RunObservabilityError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if output is None:
        typer.echo(rendered, nl=False)
        return

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    except OSError as exc:
        typer.secho(
            f"Failed to write metrics output file {output}: {exc}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1) from exc

    typer.echo(f"Exported metrics to {output.resolve()}")


@metrics_app.command("serve")
def metrics_serve(
    artifacts_root: Path = typer.Option(
        Path("artifacts/runs"),
        "--artifacts-root",
        help="Root directory containing local run artifact subdirectories.",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host interface for the local metrics server.",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        min=1,
        max=65535,
        help="Port for the local metrics server.",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Optional run ID filter. If omitted, serves all discovered runs.",
    ),
) -> None:
    """Serve local artifact-derived metrics at /metrics for local scraping."""
    target = f"http://{host}:{port}/metrics"
    if run_id:
        typer.echo(f"Serving local artifact-derived metrics for run_id={run_id} at {target}")
    else:
        typer.echo(f"Serving local artifact-derived metrics for all runs at {target}")

    try:
        serve_metrics(
            artifacts_root=artifacts_root,
            host=host,
            port=port,
            run_id=run_id,
        )
    except OSError as exc:
        typer.secho(
            f"Failed to start metrics server on {host}:{port}: {exc}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(1) from exc


@kill_app.command("activate")
def kill_activate(
    run_id: str = typer.Option(..., "--run-id", help="Run ID to activate kill switch for."),
    reason: str = typer.Option(..., "--reason", help="Operator reason for activation."),
    actor: str | None = typer.Option(None, "--actor", help="Optional operator identity."),
) -> None:
    """Activate file-based kill switch state for a run."""
    runtime_root = _resolve_runtime_root()
    artifacts_root = _resolve_artifacts_root()
    try:
        state = activate_kill_switch(
            run_id=run_id,
            reason=reason,
            actor=actor,
            runtime_root=runtime_root,
            artifacts_root=artifacts_root,
        )
    except KillSwitchError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"run_id={state.run_id}")
    typer.echo("state=active")
    typer.echo("event=kill_activated")
    typer.echo(f"reason={state.last_reason}")
    typer.echo(f"actor={state.last_actor}")
    typer.echo(f"state_path={(runtime_root / f'{state.run_id}.state.json').resolve()}")


@kill_app.command("status")
def kill_status(
    run_id: str = typer.Option(..., "--run-id", help="Run ID to inspect kill switch status for."),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Print kill switch status as JSON.",
    ),
) -> None:
    """Show kill switch status for one run."""
    runtime_root = _resolve_runtime_root()
    try:
        status = get_kill_switch_status(run_id=run_id, runtime_root=runtime_root)
    except KillSwitchError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    if as_json:
        payload: dict[str, str | None]
        if status.state == "absent":
            payload = {
                "schema_version": "v1",
                "run_id": status.run_id,
                "state": "absent",
            }
        else:
            payload = {
                "schema_version": status.schema_version,
                "run_id": status.run_id,
                "state": status.state,
                "updated_at_utc": status.updated_at_utc,
                "last_event_id": status.last_event_id,
                "last_reason": status.last_reason,
                "last_actor": status.last_actor,
                "active_since_utc": status.active_since_utc,
                "cleared_at_utc": status.cleared_at_utc,
            }
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    typer.echo(f"run_id={status.run_id}")
    typer.echo(f"state={status.state}")
    if status.state != "absent":
        typer.echo(f"updated_at_utc={status.updated_at_utc}")
        typer.echo(f"last_reason={status.last_reason}")
        typer.echo(f"last_actor={status.last_actor}")


@kill_app.command("clear")
def kill_clear(
    run_id: str = typer.Option(..., "--run-id", help="Run ID to clear kill switch for."),
    reason: str = typer.Option(..., "--reason", help="Operator reason for clear."),
    actor: str | None = typer.Option(None, "--actor", help="Optional operator identity."),
) -> None:
    """Clear file-based kill switch state for a run."""
    runtime_root = _resolve_runtime_root()
    artifacts_root = _resolve_artifacts_root()
    try:
        state = clear_kill_switch(
            run_id=run_id,
            reason=reason,
            actor=actor,
            runtime_root=runtime_root,
            artifacts_root=artifacts_root,
        )
    except KillSwitchError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"run_id={state.run_id}")
    typer.echo("state=cleared")
    typer.echo("event=kill_cleared")
    typer.echo(f"reason={state.last_reason}")
    typer.echo(f"actor={state.last_actor}")
    typer.echo(f"state_path={(runtime_root / f'{state.run_id}.state.json').resolve()}")


@reconcile_app.command("check")
def reconcile_check(
    run_id: str = typer.Option(..., "--run-id", help="Run ID for reconciliation artifact output."),
    expected: Path = typer.Option(..., "--expected", help="Expected state JSON fixture path."),
    observed: Path = typer.Option(..., "--observed", help="Observed state JSON fixture path."),
) -> None:
    """Run deterministic file-based reconciliation from local JSON fixtures."""
    try:
        result = run_reconciliation_check(
            run_id=run_id,
            expected_path=expected,
            observed_path=observed,
        )
    except ReconciliationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"run_id={result['run_id']}")
    typer.echo(f"status={result['status']}")
    typer.echo(f"pass={str(result['pass']).lower()}")
    summary = result["summary"]
    typer.echo(f"summary_ok={summary['ok']}")
    typer.echo(f"summary_warning={summary['warning']}")
    typer.echo(f"summary_mismatch={summary['mismatch']}")
    typer.echo(f"summary_unknown={summary['unknown']}")
    result_path = Path("artifacts/runs") / result["run_id"] / "reconciliation_result.json"
    typer.echo(f"result_path={result_path}")
    for check in result["checks"]:
        matched = str(check["matched"]).lower()
        typer.echo(
            f"check_{check['name']}={check['severity']} "
            f"matched={matched} details={check['details']}"
        )

    if result["status"] in {"mismatch", "unknown"}:
        raise typer.Exit(1)


@drill_app.command("stale-market-data")
def drill_stale_market_data(
    run_id: str = typer.Option(..., "--run-id", help="Run ID for drill output."),
    artifacts_root: Path = typer.Option(
        Path("artifacts/runs"),
        "--artifacts-root",
        help="Root directory containing run artifact subdirectories.",
    ),
) -> None:
    """Run deterministic stale market data warning drill."""
    try:
        result = execute_stale_market_data_drill(run_id=run_id, artifacts_root=artifacts_root)
    except (DrillValidationError, DrillArtifactsError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    report = result["report"]
    report_path = Path(result["report_path"])
    typer.echo(f"run_id={report['run_id']}")
    typer.echo(f"drill_name={report['drill_name']}")
    typer.echo(f"outcome={report['outcome']}")
    typer.echo("status=completed")
    typer.echo(f"report_path={report_path.resolve()}")


@drill_app.command("reconciliation-mismatch")
def drill_reconciliation_mismatch(
    run_id: str = typer.Option(..., "--run-id", help="Run ID for drill output."),
    artifacts_root: Path = typer.Option(
        Path("artifacts/runs"),
        "--artifacts-root",
        help="Root directory containing run artifact subdirectories.",
    ),
) -> None:
    """Run deterministic reconciliation mismatch drill."""
    try:
        result = execute_reconciliation_mismatch_drill(run_id=run_id, artifacts_root=artifacts_root)
    except (DrillValidationError, DrillArtifactsError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    report = result["report"]
    report_path = Path(result["report_path"])
    typer.echo(f"run_id={report['run_id']}")
    typer.echo(f"drill_name={report['drill_name']}")
    typer.echo(f"outcome={report['outcome']}")
    typer.echo("status=completed")
    typer.echo(f"report_path={report_path.resolve()}")
    typer.secho(
        (
            "Expected non-zero exit: reconciliation mismatch drill intentionally "
            "demonstrates mismatch."
        ),
        fg=typer.colors.YELLOW,
        err=True,
    )
    raise typer.Exit(1)


@drill_app.command("restart-recovery")
def drill_restart_recovery(
    run_id: str = typer.Option(..., "--run-id", help="Run ID for drill output."),
    artifacts_root: Path = typer.Option(
        Path("artifacts/runs"),
        "--artifacts-root",
        help="Root directory containing run artifact subdirectories.",
    ),
) -> None:
    """Run deterministic artifact-based restart recovery rehearsal."""
    try:
        result = execute_restart_recovery_drill(run_id=run_id, artifacts_root=artifacts_root)
    except (DrillValidationError, DrillArtifactsError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    report = result["report"]
    report_path = Path(result["report_path"])
    typer.echo(f"run_id={report['run_id']}")
    typer.echo(f"drill_name={report['drill_name']}")
    typer.echo(f"outcome={report['outcome']}")
    typer.echo("status=completed")
    typer.echo(f"report_path={report_path.resolve()}")
