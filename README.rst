Rotest
------

.. image:: https://img.shields.io/pypi/v/rotest.svg
    :alt: PyPI
    :target: https://pypi.org/project/rotest/

.. image:: https://img.shields.io/pypi/pyversions/rotest.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/rotest/

.. image:: https://travis-ci.org/gregoil/rotest.svg?branch=master
    :target: https://travis-ci.org/gregoil/rotest

.. image:: https://ci.appveyor.com/api/projects/status/uy9grwc52wkpaaq9/branch/master?svg=true
    :target: https://ci.appveyor.com/project/gregoil/rotest

.. image:: https://coveralls.io/repos/github/gregoil/rotest/badge.svg?branch=master
    :target: https://coveralls.io/github/gregoil/rotest

.. image:: https://img.shields.io/readthedocs/rotest/stable.svg
    :alt: Read the Docs (version)
    :target: http://rotest.readthedocs.io/en/stable/

Rotest is a resource oriented testing framework, for writing system or
integration tests.

Rotest is based on Python's `unittest` module and on the Django framework.
It enables defining simple abstracted components in the system, called
resources. The resources may be DUT (devices under test) or they may help
the test process. The tests look very much like tests written using the
builtin module `unittest`.

Why Use Rotest?
===============
- Allowing teams to share resources without interfering with one another.
- Easily abstracting automated components in the system.
- Lots of useful features: multiprocess, filtering tests, variety of output
  handlers (and the ability to create custom ones), and much more.

Examples
========
For a complete step-by-step explanation about the framework, you can read
our documentation at `Read The Docs <http://rotest.rtfd.io>`_. If you just want
to see how it looks, read further.

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
    from rotest.core.case import TestCase


    class SimpleCalculationTest(TestCase):
        calculator = Calculator()

        def test_simple_calculation(self):
            self.assertEqual(self.calculator.calculate("1+2"), 3)


    if __name__ == "__main__":
        main(SimpleCalculationTest)

The test can include the `setUp` and `tearDown` methods of `unittest` as
well, and it differs only in the request for resources.

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
                            Enable run of unsuccessful tests only, enter the
                            number of times the failed tests should run
      -p PROCESSES, --processes=PROCESSES
                            Use multiprocess test runner
      -o OUTPUTS, --outputs=OUTPUTS
                            Output handlers separated by comma. Options: dots,
                            xml, full, remote, tree, excel, db, artifact,
                            signature, loginfo, logdebug, pretty
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
