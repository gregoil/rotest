============
Rotest Usage
============

Rotest Shell
============

The `rotest shell` is an extension of an `IPython` environment meant to work with
resources and tests.

It creates a resources client, starts a log-to-screen pipe,
automatically imports resources, and provides basic functions to run tests.

Using the shell:

.. code-block:: console

    $ rotest shell
    Creating client
    Done! You can now lock resources and run tests, e.g.
        resource1 = ResourceClass.lock(skip_init=True, name='resource_name')
        resource2 = ResourceClass.lock(name='resource_name', config='config.json')
        shared_data['resource'] = resource1
        run_block(ResourceBlock, parameter=5)
        run_block(ResourceBlock.params(parameter=6), resource=resource2)

    Python 2.7.15 (default, Jun 27 2018, 13:05:28)
    Type "copyright", "credits" or "license" for more information.

    IPython 5.5.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]: calc = Calculator.lock()
    06:08:34 : Requesting resources from resource manager
    06:08:34 : Locked resources [Calculator(CalculatorData('calc'))]
    06:08:34 : Setting up the locked resources
    06:08:34 : Resource 'shell_resource' work dir was created under '~/.rotest'
    06:08:34 : Connecting resource 'calc'
    06:08:34 : Initializing resource 'calc'
    06:08:34 : Resource 'calc' validation failed
    06:08:34 : Initializing resource 'calc'
    06:08:34 : Resource 'calc' was initialized

    In [2]: print calc.calculate("1 + 1")
    2


All `BaseResources` have a `lock` method that can be used in the shell and in scripts,
which requests and initializes resources, returning a resource that's ready for work.

You can add more startup commands to the rotest shell via the entry-point `shell_startup_commands`.
For more information, see :ref:`configurations`.


Writing a Resource-Based Test
=============================

In this section, we are going to add our resource to our existing test.
The first thing we need to do, is setting up our resource named ``calc``. We
need to run the RPyC server of the calculator, using the following command:

.. code-block:: console

    $ rpyc_classic.py --port 1357
    INFO:SLAVE/1357:server started on [0.0.0.0]:1357

This way, we have a way to communicate to our resource, which is running on
our local computer (or may run on other computer, assuming you've set the
corresponding IP address in the Django admin).

Now, let's change the previously written module :file:`test_math.py` with the
following content:

.. code-block:: python

    from rotest.core import TestCase

    from resources.calculator import Calculator


    class AddTest(TestCase):
        calc = Calculator.request()

        def test_add(self):
            result = self.calc.calculate("1 + 1")
            self.assertEqual(result, 2)

We can request resources in the test's scope in two different ways.

* As shown in the example, write a request of the format:

  .. code-block:: python

    <request_name> = <resource_class>.request(<request_filters or service_parameters>)

  The optional ``request filters`` (in case of a resource that has data) are of the same
  syntax as the options passed to Django models ``<Model>.objects.filter()`` method,
  and can help you make the resource request of the test more specific, e.g.

  .. code-block:: python

    calc = Calculator.request(name='calc')

  If the resource doesn't point to ``DATA_CLASS`` (is None) then the resource is a service,
  and ``request_filters`` become initialization parameters.

* [Deprecated] Overriding the ``resources`` field and using ``rotest.core.request`` instances:

  .. code-block:: python

    resources = [<request1>, <request2>, ...]

  where each request is of the format

  request(<request_name>, <resource_class>, <request_filters or service_parameters>)

  where the parameters mean the same as in the previous requesting method.

* Dynamic requests (during the test-run)

  In the test method, you can call ``self.request_resources([<request1>, <request2>, ...])``

  The requests are instances of ``rotest.core.request``, as in the previous method.

.. warning::
   The method for declaring test resource and sub-resources has changed since
   version 6.0.0.

   The previous method didn't use the `request` classmethod, and instead
   used the constructor, e.g. calc = Calculator().

   That form is no longer supported!


Now, let's run the test:

.. code-block:: console

    $ rotest test_math.py
    AnonymousSuite
      AddTest.test_add ... OK

    Ran 1 test in 0.160s

    OK


Assert vs Expect
================

In the test method you can use the assert<X> methods to perform the testing,
but for cases where you don't want the action to stop the test, you can use ``expect``.

``expect`` only registers failures but stays in the same scope,
allowing for more testing actions in the same single test. E.g.

.. code-block:: python

    from rotest.core import TestCase

    from resources.calculator import Calculator


    class AddTest(TestCase):
        calc = Calculator()

        def test_add(self):
            self.expectEqual(self.calc.calculate("1 + 1"), 2)
            self.expectEqual(self.calc.calculate("1 + 2"), 2)
            self.expectEqual(self.calc.calculate("1 + 3"), 2)


In the above example the ``AddTest`` will have 2 failures to the same run (3!=2 and 4!=2).

It is recommended to use ``expect`` to test different side-effects of the same scenario,
like different side effects of the same action, but you can use it any way you please.

There is an ``expect`` method equivalent for every ``assert`` method, e.g. ``expectEqual`` and ``expectIsNone``.
