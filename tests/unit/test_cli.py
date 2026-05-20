"""CLI smoke tests for Slice 1 scaffolding."""

from typer.testing import CliRunner

from ops_lab.cli import app

runner = CliRunner()


def test_tc_help_exits_successfully() -> None:
    """Verify the CLI help output is available."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_tc_version_outputs_package_version() -> None:
    """Verify the CLI version command prints the current package version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
