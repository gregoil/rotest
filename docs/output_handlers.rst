.. _output_handlers:

===============
Output Handlers
===============

Output Handlers are a great concept in Rotest. They let you take actions
when certain events occurs, as a logic separated from the test's logic.

Rotest has several builtin output handlers, as well as enable making custom
output handlers.

Dots
====

The most compact way to display results - using one character per test:

.. code-block:: console

    $ python some_test_file.py -o dots
    .FEssxu.....FsF..FEE...

    ...

Based on the following legend:

+---+--------------------+
| . | Success            |
+---+--------------------+
| F | Failure            |
+---+--------------------+
| E | Error              |
+---+--------------------+
| s | Skip               |
+---+--------------------+
| x | Expected Failure   |
+---+--------------------+
| u | Unexpected Success |
+---+--------------------+

Full
====

If you want to just be aware of every event, use the ``full`` output handler:

.. code-block:: console

    $ python some_test_file.py -o full
    Tests Run Started
    Test CalculatorSuite Started
    Test CasesSuite Started
    Test PassingCase.test_passing Started
    Success: test_passing (__main__.PassingCase)
    Test PassingCase.test_passing Finished
    Test FailingCase.test_failing Started
    Failure: test_failing (__main__.FailingCase)
    Traceback (most recent call last):
      File "rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
        test_method(*args, **kwargs)
      File "tests/calculator_tests.py", line 34, in test_failing
        self.assertEqual(1, 2)
    AssertionError: 1 != 2

    Test FailingCase.test_failing Finished
    Test ErrorCase.test_error Started
    Error: test_error (__main__.ErrorCase)
    Traceback (most recent call last):
      File "rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
        test_method(*args, **kwargs)
      File "tests/calculator_tests.py", line 44, in test_error
        1 / 0
    ZeroDivisionError: integer division or modulo by zero

    ...

Tree
====

For a tree view, use:

.. code-block:: console

    $ python some_test_file.py -o tree
    CalculatorSuite
      CasesSuite
        PassingCase.test_passing ... OK
        FailingCase.test_failing ... FAIL
        Traceback (most recent call last):
          File "/home/odp/code/rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
            test_method(*args, **kwargs)
          File "tests/calculator_tests.py", line 34, in test_failing
            self.assertEqual(1, 2)
        AssertionError: 1 != 2

        ErrorCase.test_error ... ERROR
        Traceback (most recent call last):
          File "/home/odp/code/rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
            test_method(*args, **kwargs)
          File "tests/calculator_tests.py", line 44, in test_error
            1 / 0
        ZeroDivisionError: integer division or modulo by zero

    ...

Logs
====

To see the logs while running the tests, use ``logdebug`` or ``loginfo``.
Additionally, you can use ``pretty`` for an easier to read logging system.
As expected, ``logdebug`` will print every log record with level which is
higher or equal to ``DEBUG`` (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``,
``CRITICAL``), whereas ``loginfo`` will print every log record with level which
is higher or equal to ``INFO`` (``INFO``, ``WARNING``, ``ERROR``,
``CRITICAL``).

Excel
===========

Sometimes, you want to have a better visualization of the results. Rotest can
output the results into a human-readable :file:`results.xls` file, which can be
sent via email for instance. The relevant option is ``-o excel``.

This artifact is saved in the working directory of Rotest. For more about
this location, see :ref:`configurations`.

Remote
======

.. program:: rotest

When adding ``remote`` to the list of output handlers, all test events and
results are saved in the remote (server's) database, which enables keeping
tests run history. Furthermore, tests skip delta filtering (:option:`--delta`
run option) queries the remote database to see which tests already passed.

DB
==

The ``db`` handler behaves the same as ``remote`` handler, only uses a local
DB (which should be defined in your project's ``settings.py`` file)

Artifact
========

This handler saves the working directory of the tests into a ZIP file, which
might be useful for keeping important runs' logs and other files for future
debugging or evaluation.

Those artifacts are saved in the artifacts directory of Rotest. It is
recommended to make this folder a shared folder between all your users.
For more about this location, see :ref:`configurations`.
