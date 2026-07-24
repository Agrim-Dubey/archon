"""CLI integration tests."""
from typer.testing import CliRunner
from app.cli.main import app
runner = CliRunner()
def test_cli_help():
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
