import os
import sys

import mock
import pytest

from rotest.cli.main import main


@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_default_port(resource_manager, capsys):
    sys.argv = ["rotest", "server"]
    main()

    resource_manager.assert_called_once_with(port=7777)
    out, _ = capsys.readouterr()
    assert "Running in attached mode" in out


@mock.patch("rotest.cli.server.ResourceManagerServer",
            mock.MagicMock())
@mock.patch("subprocess.Popen")
def test_running_django_server(popen, capsys):
    sys.argv = ["rotest", "server"]
    main()

    popen.assert_called_once_with(
        ["python",
         os.path.join(os.path.abspath(os.path.curdir), "manage.py"),
         "runserver",
         "0.0.0.0:8000"])

    out, _ = capsys.readouterr()
    assert "Running the Django server as well" in out


@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_custom_port(resource_manager, capsys):
    sys.argv = ["rotest", "server", "--port", "8888"]
    main()

    resource_manager.assert_called_once_with(port=8888)

    out, _ = capsys.readouterr()
    assert "Running in attached mode" in out


@mock.patch("rotest.cli.server.ResourceManagerServer",
            mock.MagicMock())
@mock.patch("subprocess.Popen")
def test_not_running_django_server(popen, capsys):
    sys.argv = ["rotest", "server", "--no-django"]
    main()

    popen.assert_not_called()

    out, _ = capsys.readouterr()
    assert "Running the Django server as well" not in out


@pytest.mark.skipif(sys.platform == "win32",
                    reason="Daemon mode isn't implemented in Windows")
@mock.patch("daemon.DaemonContext")
@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_using_daemon_mode(resource_manager, daemon_context, capsys):
    sys.argv = ["rotest", "server", "--daemon"]
    main()

    resource_manager.assert_called_once_with(port=7777)
    daemon_context.assert_called_once()

    out, _ = capsys.readouterr()
    assert "Running in detached mode (as daemon)" in out


@pytest.mark.skipif(sys.platform != "win32",
                    reason="Windows only behaviour")
@mock.patch("rotest.cli.server.ResourceManagerServer")
def test_raising_on_windows_when_user_tries_daemon_mode(resource_manager):
    sys.argv = ["rotest", "server", "--daemon"]
    with pytest.raises(RuntimeError,
                       match="Cannot run as daemon on Windows"):
        main()

    resource_manager.assert_not_called()
