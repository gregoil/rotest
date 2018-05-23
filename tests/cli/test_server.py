import sys

import mock
import pytest
from click.testing import CliRunner

from rotest.cli.server import server


@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_default_port(resource_manager):
    runner = CliRunner()
    result = runner.invoke(server)

    resource_manager.assert_called_once_with(port=7777)
    assert result.exit_code == 0
    assert "Running in attached mode" in result.output


@mock.patch("rotest.cli.server.ResourceManagerServer",
            mock.MagicMock())
@mock.patch("subprocess.Popen")
def test_running_django_server(popen):
    runner = CliRunner()
    result = runner.invoke(server)

    popen.assert_called_once_with(["django-admin",
                                   "runserver",
                                   "0.0.0.0:8000"])
    assert result.exit_code == 0
    assert "Running the Django server as well" in result.output


@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_custom_port(resource_manager):
    runner = CliRunner()
    result = runner.invoke(server, ["--port", "8888"])

    resource_manager.assert_called_once_with(port=8888)
    assert result.exit_code == 0
    assert "Running in attached mode" in result.output


@mock.patch("rotest.cli.server.ResourceManagerServer",
            mock.MagicMock())
@mock.patch("subprocess.Popen")
def test_not_running_django_server(popen):
    runner = CliRunner()
    result = runner.invoke(server, ["--no-django"])

    popen.assert_not_called()
    assert result.exit_code == 0
    assert "Running the Django server as well" not in result.output


@pytest.mark.skipif(sys.platform == "win32",
                    reason="Daemon mode isn't implemented in Windows")
@mock.patch("daemon.DaemonContext")
@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_daemon_mode(resource_manager, daemon_context):
    runner = CliRunner()
    result = runner.invoke(server, ["--daemon"])

    assert result.exit_code == 0
    resource_manager.assert_called_once_with(port=7777)
    daemon_context.assert_called_once()
    assert "Running in detached mode (as daemon)" in result.output


@pytest.mark.skipif(sys.platform != "win32",
                    reason="Windows only behaviour")
@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_raising_on_windows_when_user_tries_daemon_mode(resource_manager):
    runner = CliRunner()
    result = runner.invoke(server, ["--daemon"])

    assert result.exit_code != 0
    resource_manager.assert_not_called()
    assert "Cannot run as daemon on Windows" in result.exception.message
