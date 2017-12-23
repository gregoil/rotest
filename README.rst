Rotest
------
.. image:: https://travis-ci.org/gregoil/rotest.svg?branch=travis_ci
    :target: https://travis-ci.org/gregoil/rotest

.. image:: https://ci.appveyor.com/api/projects/status/uy9grwc52wkpaaq9?svg=true
    :target: https://ci.appveyor.com/project/gregoil/rotest

Rotest is a resource oriented testing framework, for writing system or
integration tests.

Rotest is based on Python's `unittest` module and on the Django framework.
It enables defining simple abstracted components in the system, called
resources. The resources may be DUT (devices under test) or they may help
the test process. The tests look very much like tests written using the
builtin module `unittest`.

Why Use Rotest?
===============
- Enabling a great team use resources without interfering each other.
- Easily abstracting automated components in the system.
- Lots of useful features: multiprocess, filtering tests, variety of result
  handlers (and the ability to define custom ones), and much more.

The Playground
=================
We appreciate support with the development of **rotest**.

To help you get started we created a *playground* for you to experiment with
rotest and test your own features. In order to get started you'll have to
follow some simple steps.

First clone this repository anywhere on your file-system.

.. code-block:: bash

    git clone https://github.com/gregoil/rotest.git


*cd* into the rotest root directory.

.. code-block:: bash

    cd rotest

Install our dependencies, We recommend using a `virtualenv`.

.. code-block:: bash

    python -m pip install -r requirements.txt


Set rotest on **develop** mode.

(This basically means that instead of installing rotest as a 3rd-party package,
whenever you import rotest it will reference your local directory where you
did the clone, from there you can make changes to the package.)

.. code-block:: bash

    python setup.py develop


A feature of rotest is it's easy-to-configure django resource database, So:

Install any DB technology you want, I'd use sqlite for simplicity's sake.

.. code-block:: bash

    sudo apt-get install sqlite3


Export the DJANGO_SETTINGS_MODULE environment variable.

.. code-block:: bash

    export DJANGO_SETTINGS_MODULE=rotest.common.django_utils.all_settings

Set up our resource database:

.. code-block:: bash

    python src/rotest/common/django_utils/manage.py migrate


Create an admin account in our rotest-app,
This command will prompt you for the user's name, password, email, etc...
Just fill it.

.. code-block:: bash

    python src/rotest/common/django_utils/manage.py createsuperuser



We can create the books table by migrating

(Note: if the playground/migrations directory isn't empty these commands will
output that there is nothing to migrate.)

.. code-block:: bash

    python src/rotest/common/django_utils/manage.py makemigrations
    python src/rotest/common/django_utils/manage.py migrate

----------------------------------------------------------------------------

----
Note
----
We can simply run `makemigrations` because playground directory was
created with the command:

.. code-block:: bash

    django-admin startapp playground

And then it was referenced to in

.. code-block:: console

    src/rotest/common/django_utils/all_settings.py

And all of it's models (`ResourceData`s) are referenced to at it's `models.py`
file,

And we also added these lines to `admin.py`:

.. code-block:: python

    from django.contrib import admin
    from . import models
    admin.site.register(models.BookData)

----------------------------------------------------------------------------

Run the server in another terminal/console/shell

(Make sure you have the environment variables listed in this article.)

.. code-block:: bash

    python src/rotest/common/django_utils/manage.py runserver 0.0.0.0:8000

Launch the rotest resource manager to run on a machine and then configure
your development station to that machine.

For simplicity sake, we'll do all of this on one machine, so we will use
**localhost**. (Note: although rotest defaults to localhost if no
`RESOURCE_MANAGER_HOST` is defined, explicit is better than implicit)

In another terminal/console/shell run the server:

(Make sure you have the environment variables listed in this article.)

.. code-block:: bash

    python src/rotest/management/server/main.py


In your development terminal/console/shell configure the resource manager:

(This is how we will access/lock/release resources, that's basically our
proxy to the database and what guarantees the successful teamwork.)

.. code-block:: bash

    export RESOURCE_MANAGER_HOST=localhost

That's it for the boilerplate, now we can actually start messing around with
the infrastructure.

Add a book resource using the rotest GUI with the following values:

name: gotbook
title: Game of Thrones
author: George R. R. Martin

.. code-block:: console

    http://localhost:8000/admin/playground/bookdata/add/


Let's try and run the most basic test in the playground, *test_book*.
run the following command

.. code-block:: bash

    python playground/book/test_book.py

.. code-block:: console

    $ python playground/book/test_book.py
    AnonymousSuite
      BookCase.test_clockwork_orange ... OK
      BookCase.test_display_for_library ... OK
      BookCase.test_the_bible ... SKIP
      Game of Thrones is not a holy book.

    ======================================================================
    SKIPPED: BookCase.test_the_bible
    ----------------------------------------------------------------------
    A Book is not a holy book.
    Ran 3 tests in 0.189s

    OK (skipped=1)

You can even try a more verbose version of the same test, for easier debugging.

.. code-block:: bash

    python playground/book/test_book.py -o logdebug


Examples
========
For a complete step-by-step explanation about the framework, you can read
our documentation in the tutorial. If you just want to see how it looks,
read further.

For our example, let's look at an example for a `Calculator` resource:

.. code-block:: python

    import os
    import rpyc
    from django.db import models
    from rotest.management import base_resource
    from rotest.management.models import resource_data


    class CalculatorData(resource_data.ResourceData):
        class Meta:
            app_label = "resources"

        ip_address = models.IPAddressField()


    class Calculator(base_resource.BaseResource):
        DATA_CLASS = CalculatorData

        PORT = 1357
        EXECUTABLE_PATH = os.path.join(os.path.expanduser("~"),
                                       "calc.py")

        def connect(self):
            self._rpyc = rpyc.classic.connect(self.data.ip_address,
                                              self.PORT)

        def calculate(self, expression):
            result = self._rpyc.modules.subprocess.check_output(
                ["python", self.EXECUTABLE_PATH, expression])
            return int(result.strip())

        def finalize(self):
            if self._rpyc is not None:
                self._rpyc.close()
                self._rpyc = None

The `CalculatorData` class is a standard Django model that exposes IP
address of the calculator machine through the data attribute.
Also, we're using `rpyc` for automating the access to those machines. Except
from that, it's easy to notice how the `connect` method is making the
connection to the machine, and how the `finalize` method is cleaning
afterwards.

Now, an example for a test:

.. code-block:: python

    from rotest.core.runner import main
    from rotest.core.case import TestCase, request


    class SimpleCalculationTest(TestCase):
        resources = [request("calculator", Calculator)]

        def test_simple_calculation(self):
            self.assertEqual(self.calculator.calculate("1+2"), 3)


    if __name__ == "__main__":
        main(SimpleCalculationTest)

The test can include the `setUp` and `tearDown` methods of `unittest` as
well, and it differs only in the request for resources. The request includes
the target member name, the requested class and might include more
parameters for finding the suitable resource.

Following, those are the options exposed when running the test:

.. code-block:: console

    $ python test.py --help
    Usage: test.py [options]

    Options:
      -h, --help            show this help message and exit
      -c CONFIG_PATH, --config-path=CONFIG_PATH
                            Tests' configuration file path
      -s, --save-state      Enable save state
      -d DELTA_ITERATIONS, --delta-iterations=DELTA_ITERATIONS
                            Enable run of failed tests only, enter the number of
                            times the failed tests should run
      -p PROCESSES, --processes=PROCESSES
                            Use multiprocess test runner
      -o OUTPUTS, --outputs=OUTPUTS
                            Output handlers separated by comma, options "['dots',
                            'xml', 'full', 'remote', 'db', 'excel', 'tree',
                            'artifact', 'signature', 'loginfo', 'logdebug']"
      -f FILTER, --filter=FILTER
                            Run only tests that match the filter expression, e.g
                            "Tag1* and not Tag13"
      -n RUN_NAME, --name=RUN_NAME
                            Assign run name
      -l, --list            Print the tests hierarchy and quit
      -F, --failfast        Stop the run on first failure
      -D, --debug           Enter ipdb debug mode upon any test exception
      -S, --skip-init       Skip initialization and validation of resources
      -r RESOURCES, --resources=RESOURCES
                            Specific resources to request by name
