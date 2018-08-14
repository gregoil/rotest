.. _configurations:

==============
Configurations
==============

Rotest behaviour can be configured in the following ways:

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

* Define ``host`` in the configuration file:

  .. code-block:: yaml

      rotest:
          host: rotestserver

* Use the default, which is ``localhost``.

Port
----

.. envvar:: ROTEST_SERVER_PORT

    Port on the server's side, to be used for communication with clients.

To define the relevant server's port the will be opened, and the port clients
will communicate with, use the following methods:

* Define :envvar:`ROTEST_SERVER_PORT` with the desired port.

* Define ``port`` in the configuration file:

  .. code-block:: yaml

      rotest:
          port: 8585

* Use the default, which is ``7777``.

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

* Define ``resource_request_timeout`` in the configuration file:

  .. code-block:: yaml

      rotest:
          resource_request_timeout: 60

* Use the default, which is ``0`` (not waiting at all).

Django Settings Module
----------------------

.. envvar:: DJANGO_SETTINGS_MODULE

    Django configuration path, in a module syntax.

Rotest is a Django library, and as such needs its configuration module, in
order to write and read data about the resources from the database. Define it
in the following ways:

* Define :envvar:`DJANGO_SETTINGS_MODULE`.

* Define ``django_settings`` in the configuration file:

  .. code-block:: yaml

      rotest:
          django_settings: package1.package2.settings

* There is no default value.

Artifacts Directory
-------------------

.. envvar:: ARTIFACTS_DIR

    Rotest artifact directory.

Rotest enables saving ZIP files containing the tests and resources data, using
an output handler named ``artifact`` (see :ref:`output_handlers`). Define it
in the following ways:

* Define :envvar:`ARTIFACTS_DIR`.

* Define ``artifact_dir`` in the configuration file:

  .. code-block:: yaml

      rotest:
          artifacts_dir: ~/rotest_artifacts

* Use the default, which is ``~/.rotest/artifacts``.

Shell Apps
-------------------

``rotest shell`` automatically attempts to load resources classes into
the environment to save the user the need to do so.
Define the default rotest applications to be loaded in the following ways:

* Define ``shell_apps`` in the configuration file:

  .. code-block:: yaml

      rotest:
          shell_apps: ["resources", "tools"]

* Use the default, which is ``[]``.

Shell Startup Commands
-------------------

``rotest shell`` enables defining startup commands, to save the user the need
to write them every time. The commands must be simple one-liners.
Define it in the following ways:

* Define ``shell_startup_commands`` in the configuration file:

  .. code-block:: yaml

      rotest:
          shell_startup_commands: ["from tests.blocks import *"]

* Use the default, which is ``[]``.

Discoverer Blacklist
-------------------

Rotest enables loading resources from an app, a thing that happens automatically
when running "rotest shell", but some files can/must be skipped when searching
for the resources. The methods (under ``rotest.management.utils.resources_discoverer``)
do get a `blacklist` argument, but the default value is extracted from the config.
Define it in the following ways:

* Define ``discoverer_blacklist`` in the configuration file:

  .. code-block:: yaml

      rotest:
          discoverer_blacklist: ["*/scripts/*", "*static.py"]

* Use the default, which is ``[]``.
