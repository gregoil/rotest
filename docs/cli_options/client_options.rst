==============
Client Options
==============

.. program:: rotest

Getting Help
============

.. option:: -h, --help

    Show a help message and exit.

First, and most important, using the help options :option:`-h` or
:option:`--help`:

.. code-block:: console

    $ python some_test_file.py -h
    Usage: some_test_file.py [options]

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

Listing and Filtering
=====================

.. option:: -l, --list

    Print the tests hierarchy and quit.

.. option:: -f FILTER, --filter FILTER

    Run only tests that match the filter expression, e.g. "Tag1* and not Tag13".

Next, you can print a list of all the tests that will be run, using
:option:`-l` or :option:`--list` options:

.. code-block:: console

    $ python some_test_file.py -l
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

        $ python some_test_file.py -f FLOW -l
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

        $ python some_test_file.py -f "basic and not skipped*" -l
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

Stopping at first failure
=========================

.. option:: -F, --failfast

    Stop the run on first failure.

The :option:`-F` or :option:`--failfast` options can stop execution after
first failure:

.. code-block:: console

    $ python some_test_file.py --failfast
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

    Enter ipdb debug mode upon any test exception.

The :option:`-D` or :option:`--debug` options can enter debug mode when
exceptions are raised at the top level of the code:

.. code-block:: console

    $ python some_test_file.py --debug
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

Retrying Tests
==============

.. option:: -d DELTA_ITERATIONS,
            --delta DELTA_ITERATIONS
            --delta-iterations DELTA_ITERATIONS

    Rerun test a specified amount of times until it passes.

In case you have flaky tests, you can automatically rerun a test until getting
a success result. Use options :option:`--delta-iterations` or :option:`-d`:

.. code-block:: console

    $ python some_test_file.py --delta-iterations 2
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

.. option:: -p PROCESSES, --processes PROCESSES

    Spawn specified amount of processes to execute tests.

To optimize the running time of tests, you can use options :option:`-p` or
:option:`--processes` to run several work processes that can run tests
separately.

Any test have a ``TIMEOUT`` attribute (defaults to 30 minutes), and it will be
enforced only when spawning at least one worker process:

.. code-block:: python

    class SomeTest(TestCase):
        # Test will stop if it exceeds execution time of an hour,
        # only when the number of processes spawned is greater or equal to 1
        TIMEOUT = 60 * 60

        def test(self):
            pass

Specifying Resources to Use
============================

.. option:: -r <query>, --resources <query>

    Choose resources based on the given query.

You can run tests with specific resources, using options :option:`--resources`
or :option:`-r`.

The request is of the form:

.. code-block:: console

    $ python some_test_file.py --resources <query-for-resource-1>,<query-for-resource-2>,...

As an example, let's suppose we have the following test:

.. code-block:: python

    class SomeTest(TestCase):
        resources = [request("res1", Resource1),
                     request("res2", Resource2)]

        def test(self):
            ...

You can request resources by their names:

.. code-block:: console

    $ python some_test_file.py --resources res1=name1,res2=name2

Alternatively, you can make more complex queries:

.. code-block:: console

    $ python some_test_file.py --resources res1.group.name=QA,res2.comment=nightly

Activating Output Handlers
==========================

.. option:: -o OUTPUTS, --outputs OUTPUTS

To activate an output handler, use options :option:`-o` or :option:`--outputs`,
with the output handlers separated using commas:

.. code-block:: console

    $ python some_test_file.py --outputs excel,logdebug

For more about output handlers, read on :ref:`output_handlers`.
