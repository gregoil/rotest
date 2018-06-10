==============
Server Options
==============

.. program:: rotest server

You can run the server using command :command:`rotest server`.
The command by default runs Django's server as well, though it can be disabled.

Getting Help
============

.. option:: -h, --help

    Show a help message and exit.

The :option:`--help` option is here to help:

.. code-block:: console

    $ rotest server --help
    Run resource management server.

    Usage:
        rotest server [options]

    Options:
        -h,  --help                 Show help message and exit.
        -p <port>, --port <port>    Port for communicating with the client.
        --no-django                 Skip running the Django web server.
        --django-port <port>        Django's web server port [default: 8000].
        -D, --daemon                Run as a background process.

Selecting Server's Port
=======================

.. option:: --port <port>

    Select the port for communicating with the client.

By default, the server uses the specified configuration for the port (see
:envvar:`ROTEST_SERVER_PORT`), or defaults to ``7777``. If this port is already
in use and you'd like to change it, use option :option:`--port`:

.. code-block:: console

    $ rotest server --port 8888
    Running in attached mode
    Running the Django server as well
    <2018-05-23 19:54:54,550>[DEBUG][main@91]: Starting resource manager, port:8888
    <2018-05-23 19:54:54,551>[DEBUG][manager@101]: Resource manager main thread started
    Performing system checks...

    System check identified no issues (0 silenced).
    May 23, 2018 - 19:54:56
    Django version 1.7.11, using settings 'rotest_demo.settings'
    Starting development server at http://0.0.0.0:8000/
    Quit the server with CONTROL-C.

Skip running Django server
==========================

.. option:: --no-django

    Skip running the Django web server.

You can disable running Django server, using option :option:`--no-django`:

.. code-block:: console

    $ rotest server --no-django
    Running in attached mode
    <2018-05-23 19:54:54,550>[DEBUG][main@91]: Starting resource manager, port:7777
    <2018-05-23 19:54:54,551>[DEBUG][manager@101]: Resource manager main thread started

Selecting Django's Port
=======================

.. option:: --django-port <port>

    Select Django's web server port.

By default, the server uses port 8000 for running Django's server. If you'd
like to change it, use option :option:`--django-port`:

.. code-block:: console

    $ rotest server --django-port 9000
    Running in attached mode
    Running the Django server as well
    <2018-05-23 19:54:54,550>[DEBUG][main@91]: Starting resource manager, port:7777
    <2018-05-23 19:54:54,551>[DEBUG][manager@101]: Resource manager main thread started
    Performing system checks...

    System check identified no issues (0 silenced).
    May 23, 2018 - 19:54:56
    Django version 1.7.11, using settings 'rotest_demo.settings'
    Starting development server at http://0.0.0.0:9000/
    Quit the server with CONTROL-C.

Daemon Mode
===========

.. option:: -D, --daemon

    Run as a daemon process.

.. warning::

    Not implemented in Windows.

A common case is to run the server in the background. Use options
:option:`--daemon` or :option:`-D` to run the server as a daemon process:

.. code-block:: console

    $ rotest server --daemon
    Running in detached mode (as daemon)
