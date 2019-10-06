==============
Client Options
==============

.. program:: rotest

Running tests
=============

Running tests can be done in the following ways:

* Using the `rotest` command:

  .. code-block:: console

      $ rotest [PATHS]... [OPTIONS]

  The command can get every path - either files or directories. Every directory
  will be recursively visited for finding more files. If no path was given, the
  current working directory will be selected by default.

* Calling the :func:`rotest.main` function:

  .. code-block:: python

      from rotest import main
      from rotest.core import TestCase


      class Case(TestCase):
          def test(self):
              pass


      if __name__ == "__main__":
          main()

  Then, this same file can be ran:

  .. code-block:: console

      $ python test_file.py [OPTIONS]

Getting Help
============

.. option:: -h, --help

    Show a help message and exit.

If you're not sure what you can do, the help options :option:`-h` and
:option:`--help` are here to help:

.. code-block:: console

    $ rotest -h
    Run tests in a module or directory.

    Usage:
        rotest [<path>...] [options]

    Options:
        -h,  --help
                Show help message and exit.
        --version
                Print version information and exit.
        -c <path>, --config <path>
                Test configuration file path.
        -s, --save-state
                Enable saving state of resources.
        -d <delta-iterations>, --delta <delta-iterations>
                Enable run of failed tests only - enter the number of times the
                failed tests should be run.
        -p <processes>, --processes <processes>
                Use multiprocess test runner - specify number of worker
                processes to be created.
        -o <outputs>, --outputs <outputs>
                Output handlers separated by comma.
        -f <query>, --filter <query>
                Run only tests that match the filter expression,
                e.g. 'Tag1* and not Tag13'.
        -n <name>, --name <name>
                Assign a name for current launch.
        -l, --list
                Print the tests hierarchy and quit.
        -F, --failfast
                Stop the run on first failure.
        -D, --debug
                Enter ipdb debug mode upon any test exception, and enable
                entering debug mode on Ctrl-Pause (Windows) or Ctrl-Quit (Linux).
        -S, --skip-init
                Skip initialization and validation of resources.
        -r <query>, --resources <query>
                Specify resources to request by attributes,
                e.g. '-r res1.group=QA,res2.comment=CI'.

Listing, Filtering and Ordering
===============================

.. option:: -l, --list

    Print the tests hierarchy and quit.

.. option:: -f <query>, --filter <query>

    Run only tests that match the filter expression, e.g. "Tag1* and not Tag13".

Next, you can print a list of all the tests that will be run, using
:option:`-l` or :option:`--list` options:

.. code-block:: console

    $ rotest some_test_file.py -l
    CalculatorSuite []
    |   CasesSuite []
    |   |   PassingCase.test_passing ['BASIC']
    |   |   FailingCase.test_failing ['BASIC']
    |   |   ErrorCase.test_error ['BASIC']
    |   |   SkippedCase.test_skip ['BASIC']
    |   |   SkippedByFilterCase.test_skipped_by_filter ['BASIC']
    |   |   ExpectedFailureCase.test_expected_failure ['BASIC']
    |   |   UnexpectedSuccessCase.test_unexpected_success ['BASIC']
    |   PassingSuite []
    |   |   PassingCase.test_passing ['BASIC']
    |   |   SuccessFlow ['FLOW']
    |   |   |   PassingBlock.test_method
    |   |   |   PassingBlock.test_method
    |   FlowsSuite []
    |   |   FailsAtSetupFlow ['FLOW']
    |   |   |   PassingBlock.test_method
    |   |   |   FailingBlock.test_method
    |   |   |   ErrorBlock.test_method
    |   |   FailsAtTearDownFlow ['FLOW']
    |   |   |   PassingBlock.test_method
    |   |   |   TooManyLogLinesBlock.test_method
    |   |   |   FailingBlock.test_method
    |   |   |   ErrorBlock.test_method
    |   |   SuccessFlow ['FLOW']
    |   |   |   PassingBlock.test_method
    |   |   |   PassingBlock.test_method

You can see the tests hierarchy, as well as the tags each test has. Speaking
about tags, you can apply filters on the tests to be run, or on the shown list
of tests using the :option:`-f` or :option:`--filter` options:

.. code-block:: console
    :emphasize-lines: 13,17,21,26

        $ rotest some_test_file.py -f FLOW -l
        CalculatorSuite []
        |   CasesSuite []
        |   |   PassingCase.test_passing ['BASIC']
        |   |   FailingCase.test_failing ['BASIC']
        |   |   ErrorCase.test_error ['BASIC']
        |   |   SkippedCase.test_skip ['BASIC']
        |   |   SkippedByFilterCase.test_skipped_by_filter ['BASIC']
        |   |   ExpectedFailureCase.test_expected_failure ['BASIC']
        |   |   UnexpectedSuccessCase.test_unexpected_success ['BASIC']
        |   PassingSuite []
        |   |   PassingCase.test_passing ['BASIC']
        |   |   SuccessFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   PassingBlock.test_method
        |   FlowsSuite []
        |   |   FailsAtSetupFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   FailingBlock.test_method
        |   |   |   ErrorBlock.test_method
        |   |   FailsAtTearDownFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   TooManyLogLinesBlock.test_method
        |   |   |   FailingBlock.test_method
        |   |   |   ErrorBlock.test_method
        |   |   SuccessFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   PassingBlock.test_method

    The output will be colored in a similar way as above.

You can include boolean literals like ``not``, ``or`` and ``and`` in your
filter, as well as using test names and wildcards (all non-literals are case
insensitive):

.. code-block:: console
    :emphasize-lines: 4-6,9-10,12

        $ rotest some_test_file.py -f "basic and not skipped*" -l
        CalculatorSuite []
        |   CasesSuite []
        |   |   PassingCase.test_passing ['BASIC']
        |   |   FailingCase.test_failing ['BASIC']
        |   |   ErrorCase.test_error ['BASIC']
        |   |   SkippedCase.test_skip ['BASIC']
        |   |   SkippedByFilterCase.test_skipped_by_filter ['BASIC']
        |   |   ExpectedFailureCase.test_expected_failure ['BASIC']
        |   |   UnexpectedSuccessCase.test_unexpected_success ['BASIC']
        |   PassingSuite []
        |   |   PassingCase.test_passing ['BASIC']
        |   |   SuccessFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   PassingBlock.test_method
        |   FlowsSuite []
        |   |   FailsAtSetupFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   FailingBlock.test_method
        |   |   |   ErrorBlock.test_method
        |   |   FailsAtTearDownFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   TooManyLogLinesBlock.test_method
        |   |   |   FailingBlock.test_method
        |   |   |   ErrorBlock.test_method
        |   |   SuccessFlow ['FLOW']
        |   |   |   PassingBlock.test_method
        |   |   |   PassingBlock.test_method

.. option:: -O <tags>, --order <tags>

    Order discovered tests according to this list of tags,
    where tests answering the first tag (which syntax is similar
    to a filter expression) will get higher priority,
    tests answering the second tag will have a secondry priority, etc.

Stopping at first failure
=========================

.. option:: -F, --failfast

    Stop the run on first failure.

The :option:`-F` or :option:`--failfast` options can stop execution after
first failure:

.. code-block:: console

    $ rotest some_test_file.py --failfast
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


    ======================================================================
    FAIL: FailingCase.test_failing
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/odp/code/rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
        test_method(*args, **kwargs)
      File "tests/calculator_tests.py", line 34, in test_failing
        self.assertEqual(1, 2)
    AssertionError: 1 != 2

    Ran 2 tests in 0.205s

    FAILED (failures=1)

Debug Mode
==========

.. option:: -D, --debug

    Enter ipdb debug mode upon any test exception, and enable entering
    debug mode on Ctrl-Pause (Windows) or Ctrl-Quit (Linux).

The :option:`-D` or :option:`--debug` options can enter debug mode when
exceptions are raised at the top level of the test code:

.. code-block:: console

    $ rotest some_test_file.py --debug
    AnonymousSuite
      FailingCase.test ...
    Traceback (most recent call last):
       File "tests/some_test_file.py", line 11, in test
        self.assertEqual(self.calculator.calculate("1+1"), 3)
       File "/usr/lib64/python2.7/unittest/case.py", line 513, in assertEqual
        assertion_func(first, second, msg=msg)
       File "/usr/lib64/python2.7/unittest/case.py", line 506, in _baseAssertEqual
        raise self.failureException(msg)
     AssertionError: 2.0 != 3
    > tests/some_test_file.py(12)test()
         10     def test(self):
         11         self.assertEqual(self.calculator.calculate("1+1"), 3)
    ---> 12
         13
         14 if __name__ == "__main__":

    ipdb> help

    Documented commands (type help <topic>):
    ========================================
    EOF    c          d        help    longlist  pinfo    raise    tbreak   whatis
    a      cl         debug    ignore  n         pinfo2   restart  u        where
    alias  clear      disable  j       next      pp       retry    unalias
    args   commands   down     jump    p         psource  return   unt
    b      condition  enable   l       pdef      q        run      until
    break  cont       exit     list    pdoc      quit     s        up
    bt     continue   h        ll      pfile     r        step     w

Once in the debugging session, you can do any of the following:

* Inspect the situation, by evaluating expressions or using commands that
  are supported by ``ipdb``. For example: continuing the flow, jumping into a
  specific line, etc.
* ``retry`` the action, if it's a known flaky action and someone's going to
  take care of it soon.
* ``raise`` the exception, and failing the test.

Furthermore, running tests with ``--debug`` also overrides the break\\quit signals
to enable you enter debug mode whenever you like. Just press `Ctrl-\\` on Linux machines or
`Ctrl-Pause` on Windows (f*** you, Mac users) during a test to emulate an exception.

Retrying Tests
==============

.. option:: -d <delta-iterations>, --delta <delta-iterations>

    Rerun test a specified amount of times until it passes.

In case you have flaky tests, you can automatically rerun a test until getting
a success result. Use options :option:`--delta` or :option:`-d`:

.. code-block:: console

    $ rotest some_test_file.py --delta 2
    AnonymousSuite
      FailingCase.test ... FAIL
      Traceback (most recent call last):
        File "rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
          test_method(*args, **kwargs)
        File "some_test_file.py", line 11, in test
          self.assertEqual(self.calculator.calculate("1+1"), 3)
      AssertionError: 2.0 != 3


    ======================================================================
    FAIL: FailingCase.test
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "rotest/src/rotest/core/case.py", line 310, in test_method_wrapper
        test_method(*args, **kwargs)
      File "some_test_file.py", line 11, in test
        self.assertEqual(self.calculator.calculate("1+1"), 3)
    AssertionError: 2.0 != 3

    Ran 1 test in 0.122s

    FAILED (failures=1)
    AnonymousSuite
      FailingCase.test ... OK

    Ran 1 test in 0.082s

    OK

Running Tests in Parallel
=========================

.. option:: -p <processes>, --processes <processes>

    Spawn specified amount of processes to execute tests.

To optimize the running time of tests, you can use options :option:`-p` or
:option:`--processes` to run several work processes that can run tests
separately.

Any test have a ``TIMEOUT`` attribute (defaults to 60 minutes), and it will be
enforced only when spawning at least one worker process:

.. code-block:: python

    class SomeTest(TestCase):
        # Test will stop if it exceeds execution time of an hour,
        # only when the number of processes spawned is greater or equal to 1
        TIMEOUT = 60 * 60

        def test(self):
            pass

.. warning::

    When running with multiprocess you can't use IPDBugger (--debug).

.. warning::

    It is **not** recommended using this option when you have a SQLite database,
    since it doesn't allow parallel access (all the workers request resources in the same time).


Specifying Resources to Use
============================

.. option:: -r <query>, --resources <query>

    Choose resources based on the given query.

You can run tests with specific resources, using options :option:`--resources`
or :option:`-r`.

The request is of the form:

.. code-block:: console

    $ rotest some_test_file.py --resources <query-for-resource-1>,<query-for-resource-2>,...

As an example, let's suppose we have the following test:

.. code-block:: python

    class SomeTest(TestCase):
        res1 = Resource1()
        res2 = Resource2()

        def test(self):
            ...

You can request resources by their names:

.. code-block:: console

    $ rotest some_test_file.py --resources res1=name1,res2=name2

Alternatively, you can make more complex queries:

.. code-block:: console

    $ rotest some_test_file.py --resources res1.group.name=QA,res2.comment=nightly

Activating Output Handlers
==========================

.. option:: -o <outputs>, --outputs <outputs>

To activate an output handler, use options :option:`-o` or :option:`--outputs`,
with the output handlers separated using commas:

.. code-block:: console

    $ rotest some_test_file.py --outputs excel,logdebug

For more about output handlers, read on :ref:`output_handlers`.

.. _custom_entry_points:

Adding New Options
==================

You can create new CLI options and behavior using the two entrypoints:
``cli_client_parsers`` and ``cli_client_actions``.

For example:

.. code-block:: python

    # utils/baz.py

    def add_baz_option(parser):
        """Add the 'baz' flag to the CLI options."""
        parser.add_argument("--baz", "-B", action="store_true",
                            help="The amazing Baz flag")


    def use_baz_option(tests, config):
        """Print the list of tests if 'baz' is on."""
        if config.baz is True:
            print tests


And in your ``setup.py`` file inside ``setup()``:

    .. code-block:: python

        entry_points={
            "rotest.cli_client_parsers":
                ["baz_parser = utils.baz:add_baz_option"],
            "rotest.cli_client_actions":
                ["baz_func = utils.baz:use_baz_option"]
        },


* Make sure it's being installed in the environment by calling

    .. code-block:: console

        python setup.py develop
