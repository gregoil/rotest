.. _configurations:

==============
Configurations
==============

Rotest behaviour can be configured in the following ways:

* Defining variables in the Django settings module.

* A configuration file called :file:`rotest.yml` in YAML format.

* Environment variables.

* Command line arguments.

Each way has its own advantages, and should be used in different occasions:
configuration file fits where some configuration should be used by any user of
the code, environment variables should be specific per user or maybe more
session-based, and command line arguments are relevant for a specific run.

.. note::

    In general:

    * Command line arguments take precedence over environment variables.

    * Environment variables take precedence over the configuration file.

    * Configuration file take precedence over the Django settings module.

    * Some configuration attributes have default values, in case there's no
      answer.

General
-------

To use a configuration file, put any of the following path names in the
project's root directory: :file:`rotest.yml`, :file:`rotest.yaml`,
:file:`.rotest.yml`, :file:`.rotest.yaml`.

The configuration file is of the form:

.. code-block:: yaml

    rotest:
        attribute1: value1
        attribute2: value2

You can configure environment variables this way in Linux / Mac / any Unix
machine:

.. code-block:: console

    $ export ENVIRONMENT_VARIABLE=value

and this way in Windows:

.. code-block:: console

    $ set ENVIRONMENT_VARIABLE=value
    $ setx ENVIRONMENT_VARIABLE=value  # Set it permanently (reopen the shell)

Working Directory
-----------------

.. envvar:: ROTEST_WORK_DIR

    Working directory to save artifacts to.

Rotest uses the computer's storage in order to save several artifacts. You can
use the following methods:

* Define :envvar:`ROTEST_WORK_DIR` to point to the path.

* Define variable `ROTEST_WORK_DIR` in the Django settings module.

* Define ``workdir`` in the configuration file:

  .. code-block:: yaml

      rotest:
          workdir: /home/user/workdir

* Use the default, which is :file:`~/.rotest` or :file:`%HOME%\\.rotest` in
  Windows.

Host
----

.. envvar:: ROTEST_HOST

    DNS or IP address to the Rotest's server.

Rotest is built on a client-server architecture. To define the relevant server
that the client should contact with, use the following methods:

* Define :envvar:`ROTEST_HOST` to point to the server DNS or IP address.

* Define variable `ROTEST_HOST` in the Django settings module.

* Define ``host`` in the configuration file:

  .. code-block:: yaml

      rotest:
          host: rotestserver

* Use the default, which is ``localhost``.

Port
----

.. envvar:: ROTEST_SERVER_PORT

    Port for the Django server, to be used for communication with clients.

To define the relevant server's port that will be opened, and the port clients
will communicate with, use the following methods:

* Define :envvar:`ROTEST_SERVER_PORT` with the desired port.

* Define variable `ROTEST_SERVER_PORT` in the Django settings module.

* Define ``port`` in the configuration file:

  .. code-block:: yaml

      rotest:
          port: 8585

* Use the default, which is ``8000``.

Resource Request Timeout
------------------------

.. envvar:: ROTEST_RESOURCE_REQUEST_TIMEOUT

    Amount of time to wait before deciding that no resource is available.

Rotest's server distributes resources to multiple clients. Sometimes, a client
cannot get some of the resources at the moment, so the server returns an
answer that there's no resource available. This amount of time is configurable
via the following methods:

* Define :envvar:`ROTEST_RESOURCE_REQUEST_TIMEOUT` with the number of seconds
  to wait before giving up on waiting for resources.

* Define variable `ROTEST_RESOURCE_REQUEST_TIMEOUT` in the Django settings module.

* Define ``resource_request_timeout`` in the configuration file:

  .. code-block:: yaml

      rotest:
          resource_request_timeout: 60

* Use the default, which is ``0`` (not waiting at all).

Smart client
------------

.. envvar:: ROTEST_SMART_CLIENT

    Enable or disable the smart client, which keeps resources from one test to the next.

To define smart client behavior, use the following methods:

* Define :envvar:`ROTEST_SMART_CLIENT` with to be 'True' or 'False'.

* Define variable `ROTEST_SMART_CLIENT` in the Django settings module.

* Define ``smart_client`` in the configuration file:

  .. code-block:: yaml

      rotest:
          smart_client: false

* Use the default, which is ``True``.

Artifacts Directory
-------------------

.. envvar:: ARTIFACTS_DIR

    Rotest artifact directory.

Rotest enables saving ZIP files containing the tests and resources data, using
an output handler named ``artifact`` (see :ref:`output_handlers`). Define it
in the following ways:

* Define :envvar:`ARTIFACTS_DIR`.

* Define variable `ARTIFACTS_DIR` in the Django settings module.

* Define ``artifact_dir`` in the configuration file:

  .. code-block:: yaml

      rotest:
          artifacts_dir: ~/rotest_artifacts

* Use the default, which is ``~/.rotest/artifacts``.

Shell Startup Commands
----------------------

``rotest shell`` enables defining startup commands, to save the user the need
to write them every time. The commands must be simple one-liners.
Define it in the following ways:

* Define variable `SHELL_STARTUP_COMMANDS` in the Django settings module
  that points to a list of strings to execute as commands.

* Define ``shell_startup_commands`` in the configuration file:

  .. code-block:: yaml

      rotest:
          shell_startup_commands: ["from tests.blocks import *"]

* Use the default, which is ``[]``.

Shell Output Handlers
----------------------

``rotest shell`` enables defining output handlers for components run in it,
(see :ref:`output_handlers`).

* Define variable `SHELL_OUTPUT_HANDLERS` in the Django settings module
  that points to a list of output handler names.

* Define ``shell_output_handlers`` in the configuration file:

  .. code-block:: yaml

      rotest:
          shell_output_handlers: ["loginfo"]

* Use the default, which is ``["logdebug"]``.

Discoverer Blacklist
--------------------

Rotest enables discovering tests by running ``rotest <path to search>``,
but sometimes some files can / must be skipped when searching for tests.
The patterns are in fnmatch syntax.

Define it in the following ways:

* Define variable `DISCOVERER_BLACKLIST` in the Django settings module.

* Define ``discoverer_blacklist`` in the configuration file:

  .. code-block:: yaml

      rotest:
          discoverer_blacklist: ["*/scripts/*", "*static.py"]

* Use the default, which is ``[".tox", ".git", ".idea", "setup.py"]``.
