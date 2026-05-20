"""CLI entry point for ops_lab.

This module only exposes basic CLI plumbing in Slice 1.
Run commands and business workflows are intentionally deferred.
"""

import typer

from ops_lab import __version__

app = typer.Typer(help="ops-lab command line interface.")


@app.callback()
def main() -> None:
    """Base command group for future subcommands."""


@app.command("version")
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)
