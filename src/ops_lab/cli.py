"""CLI entry point for ops_lab."""

import os
from pathlib import Path

import typer

from ops_lab import __version__
from ops_lab.data.fingerprint import (
    PreparedDatasetNotFoundError,
    fingerprint_dataset,
    write_fingerprint,
)
from ops_lab.data.prepare import UnsupportedDatasetError, prepare_dataset
from ops_lab.observability.metrics import (
    RunObservabilityError,
    export_run_metrics,
)
from ops_lab.runs.artifacts import RunArtifactsAlreadyExistError, initialize_run_artifacts
from ops_lab.runs.backtest import InvalidBacktestModeError, run_backtest_lifecycle
from ops_lab.runs.hashing import compute_config_sha256
from ops_lab.runs.journal import append_journal_event, build_run_initialized_event
from ops_lab.runs.metadata import build_initial_metadata, write_metadata
from ops_lab.runs.paper import InvalidPaperModeError, run_paper_lifecycle
from ops_lab.runs.spec import RunSpecLoadError, load_run_spec

app = typer.Typer(help="ops-lab command line interface.")
spec_app = typer.Typer(help="Run spec validation commands.")
run_app = typer.Typer(help="Run initialization commands.")
data_app = typer.Typer(help="Local dataset preparation and fingerprint commands.")
metrics_app = typer.Typer(help="Run artifact metrics export commands.")
app.add_typer(spec_app, name="spec")
app.add_typer(run_app, name="run")
app.add_typer(data_app, name="data")
app.add_typer(metrics_app, name="metrics")


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
    configured = os.environ.get("OPS_LAB_DATA_ROOT")
    if configured:
        return Path(configured)
    return Path("data")


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
