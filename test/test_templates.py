import os
from click.testing import CliRunner

from faculty_cli.cli import cli


def test_init():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["template", "init"])
        assert result.exit_code == 0
        assert os.path.isfile("parameters.yaml")
        assert os.path.isdir("faculty-resources")
        assert os.path.isdir("workspace")
