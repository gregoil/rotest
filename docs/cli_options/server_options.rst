==============
Server Options
==============

.. program:: rotest server

You can run the server using command :command:`rotest server`.

Getting Help
============

.. option:: -h, --help

    Show a help message and exit.

The :option:`--help` option is here to help:

.. code-block:: console

    $ rotest server --help
    Usage: rotest server [OPTIONS]

      Run resource management server.

    Options:
      --port INTEGER  Port for communicating with the client  [default: 7777]
      -D, --daemon    Run as a daemon  [default: False]
      -h, --help      Show this message and exit.

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
    <2018-01-24 18:49:19,654>[DEBUG][main@98]: Starting resource manager, port:8888
    <2018-01-24 18:49:19,655>[DEBUG][manager@101]: Resource manager main thread started

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
