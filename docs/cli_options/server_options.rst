==============
Server Options
==============

.. program:: rotest

You can run the server using command :command:`rotest server`.

Getting Help
============

.. option:: -h, --help

    Show a help message and exit.

The :option:`--help` option is here to help:

.. code-block:: console

    $ rotest server --help
    Run resource manager server.

    Usage:
        rotest server [--server-port <port>] [--run-django-server]
                      [--django-port <port>] [-D | --daemon]

    Options:
        -h --help
            show this help message and exit

        --server-port <port>
            port for communicating with the client

        --run-django-server
            run the Django frontend as well

        --django-port <port>
            set Django's port [default: 8000]

        -D --daemon
            run as a daemon

Selecting Server's Port
=======================

.. option:: --server-port <port>

    Select the port for communicating with the client.

By default, the server uses the specified configuration for the port (see
:envvar:`ROTEST_SERVER_PORT`), or defaults to ``7777``. If this port is already
in use and you'd like to change it, use option :option:`--server-port`:

.. code-block:: console

    $ rotest server --server-port 8888
    Running in attached mode
    <2018-01-24 18:49:19,654>[DEBUG][main@98]: Starting resource manager, port:8888
    <2018-01-24 18:49:19,655>[DEBUG][manager@101]: Resource manager main thread started

Running Django's Frontend
=========================

.. option:: --run-django-server

    Run the Django frontend as well.

.. option:: --django-port <port>

    Set Django's port (defaults to 8000).

As well as the server, one may want to run the Django's server, which enables
editing and viewing the database that contains the resources. Use option
:option:`--run-django-server` to run the Django's server, and optionally
option :option:`--django-port` to choose the used port. It defaults to port
8000:

.. code-block:: console

    $ rotest server --run-django-server --django-port 9999
    Running in attached mode
    Running the Django server as well
    <2018-01-24 18:54:46,590>[DEBUG][main@98]: Starting resource manager, port:7778
    <2018-01-24 18:54:46,591>[DEBUG][manager@101]: Resource manager main thread started
    Performing system checks...

    System check identified no issues (0 silenced).
    January 24, 2018 - 18:54:47
    Django version 1.7.11, using settings 'rotest_template.settings'
    Starting development server at http://0.0.0.0:9999/
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

You can combine it with the other options, like :option:`--run-django-server`.
