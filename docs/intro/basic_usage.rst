===========
Basic Usage
===========

In this tutorial you'll learn:

* What are the building blocks of Rotest.
* How to create a Rotest project.
* How to run tests.

The Building Blocks of Rotest
=============================

Rotest is separated into several component types, each performs its specific
tasks. Here is a brief explanation of the components:

* :class:`rotest.core.TestCase`: The most basic runnable unit. Just like
  :class:`unittest.TestCase`, it defines the actions and assertions that should
  be performed to do the test. For example:

  .. code-block:: python

      from rotest.core import TestCase


      class MyCase(TestCase):
          def test_something(self):
              result = some_function()
              self.assertEqual(result, some_value)

* :class:`rotest.core.TestSuite`: Again, a known concept from the
  :mod:`unittest` module. It aggregates tests, to make a semantic separation
  between them. This way, you can hold a bunch of tests and run them as a set.
  A :class:`rotest.core.TestSuite` can hold each of the following:

  - :class:`rotest.core.TestCase` classes.
  - :class:`rotest.core.TestSuite` classes.
  - The more complex concept of :class:`rotest.core.TestFlow` classes.

  .. code-block:: python

      from rotest.core import TestSuite


      class MySuite(TestSuite):
          components = [TestCase1,
                        TestCase2,
                        OtherTestSuite]

Creating a Rotest Project
=========================

Rotest has a built in a client-server infrastructure, for a good reason. There
must be someone who can distribute resources between tests, that are being run
by several developers or testers. Thus, there must be a server that have a
database of all the instances. Rotest uses the infrastructure of Django, to
define this database, and to make use of the Django's admin frontend to enable
changing it.

First, create a Django project, using:

.. code-block:: console

    $ django-admin startproject rotest_demo
    $ cd rotest_demo

You'll end up with the following tree:

.. code-block:: console

    .
    ├── manage.py
    └── rotest_demo
        ├── __init__.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py

Inside it, create a file in the root directory of the project called
:file:`rotest.yml`, that includes all configuration of Rotest:

.. code-block:: yaml

    rotest:
        host: localhost
        django_settings: rotest_demo.settings

Pay attention to the following:

* The `rotest` keyword defines its section as the place for Rotest's
  configuration.
* The `host` key is how the client should contact the server. It's an IP
  address, or a DNS of the server. For now, both the client and server are
  running on the same machine., but it doesn't have to be that way.
* The `django_settings` key is directing to the settings of the Django app,
  that defines all relevant Django configuration (DB configuration, installed
  Django applications, and so on).

Adding Tests
============

Let's create a test that doesn't require any resource. Create a file named
:file:`test_math.py` with the following content:

.. code-block:: python

    from rotest import main
    from rotest.core import TestCase


    class AddTest(TestCase):
        def test_add(self):
            self.assertEqual(1 + 1, 2)


    if __name__ == "__main__":
        main()

That's a very simple test, that asserts integers addition operation in Python.
To run it, just do the following:

.. code-block:: console

    $ python test_math.py
        21:46:20 : Test run has started
    Tests Run Started
        21:46:20 : Test AnonymousSuite_None has started running
    Test AnonymousSuite Started
        21:46:20 : Running AnonymousSuite_None test-suite
        21:46:20 : Test AddTest.test_add_None has started running
    Test AddTest.test_add Started
        21:46:20 : Finished setUp - Skipping test is now available
        21:46:20 : Starting tearDown - Skipping test is unavailable
        21:46:20 : Test AddTest.test_add_None ended successfully
    Success: test_add (__main__.AddTest)
        21:46:20 : Test AddTest.test_add_None has stopped running
    Test AddTest.test_add Finished
        21:46:20 : Test AnonymousSuite_None has stopped running
    Test AnonymousSuite Finished
        21:46:20 : Test run has finished
    Tests Run Finished

    Ran 1 test in 0.012s

    OK
      21:46:20 : Finalizing 'AnonymousSuite' test runner
      21:46:20 : Finalizing test 'AnonymousSuite'

Alternatively, you can skip importing and using :func:`rotest.main`,
and use the built-in tests discoverer:

.. code-block:: console

    $ rotest test_math.py
    or
    $ rotest <dir to search tests in>
