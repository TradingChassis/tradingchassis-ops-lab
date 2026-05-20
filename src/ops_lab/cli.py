"""CLI entry point for ops_lab."""

from pathlib import Path

import typer

from ops_lab import __version__
from ops_lab.runs.artifacts import RunArtifactsAlreadyExistError, initialize_run_artifacts
from ops_lab.runs.hashing import compute_config_sha256
from ops_lab.runs.journal import append_journal_event, build_run_initialized_event
from ops_lab.runs.metadata import build_initial_metadata, write_metadata
from ops_lab.runs.spec import RunSpecLoadError, load_run_spec

app = typer.Typer(help="ops-lab command line interface.")
spec_app = typer.Typer(help="Run spec validation commands.")
run_app = typer.Typer(help="Run initialization commands.")
app.add_typer(spec_app, name="spec")
app.add_typer(run_app, name="run")


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
