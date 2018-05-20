import mock
from click.testing import CliRunner

from rotest.cli.main import main


def test_getting_help():
    runner = CliRunner()
    result = runner.invoke(main, ["-h"])

    assert "run" in result.output
    assert "server" in result.output
    assert "--version" in result.output
    assert "--help" in result.output


@mock.patch("django.setup")
def test_django_setup(django_setup):
    runner = CliRunner()
    runner.invoke(main, ["run", "-h"])

    django_setup.assert_called_once()
