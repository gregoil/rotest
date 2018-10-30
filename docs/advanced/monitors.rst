=============
Test Monitors
=============

Purpose
=======

Monitors are custom output handlers that are meant to give further validation
of tests in runtime, or save extra information about the tests.

The features of monitors:

* They can be applied or dropped as easily as adding a new output handler to the list.

* They save you writing validations that are needed in a group of similar tests.

* They can run in the background (in another thread).

A classic example is monitoring CPU usage during tests, or a resource's log file.

.. note::

    Monitors are associated with tests rather than the entire run,
    so when running in multiprocess, they run in the workers' processes,
    unlike normal output handlers which only run in the main process.


Writing A Monitor
=================

There are two monitor classes which you can inherit from:

.. autoclass:: rotest.core.result.monitor.monitor.AbstractMonitor
    :members: SINGLE_FAILURE, CYCLE, run_monitor, fail_test


.. autoclass:: rotest.core.result.monitor.monitor.AbstractResourceMonitor
    :members: RESOURCE_NAME


There are two types of monitors:

* Monitors that only react to test events, e.g. taking a screen-shot on error.

    Since monitors inherit from ``AbstractResultHandler``, you can react
    to any test event by overriding the appropriate method.

    See :ref:`custom_output_handlers` for a list of events.

    Each of those event methods get the test instance as the first parameter,
    through which you can access its fields (test.<resource>, test.config, test.work_dir, etc.)

* Monitors that run in the background and periodically save data or run a validation,
    like the above suggested CPU usage monitor.

    To create such a monitor, simply override the class field ``CYCLE`` and the
    method ``run_monitor``.

    Again, the ``run_monitor`` method (which is called periodically after `setUp`
    and until `tearDown`) gets the test instance as a parameter, through which
    you can get what you need.

    Note that the monitor thread is created only for upper tests, e.g. ``TestCases``
    or topmost ``TestFlows``.

    Remember that you might need to use some synchronization mechanism since
    you're running in a different thread yet using the test's own resources.


Use the method ``fail_test`` to add monitor failures to your tests in the background, e.g.

    .. code-block:: python

        self.fail_test(test, "Reached 100% CPU usage")


Note that when using ``TestBlocks`` and ``TestFlows``, you might want to limit
your monitor events to only be applied on main tests and not sub-components
(``run_monitor`` already behaves that way by default).

For your convenience, you can use the following decorators on the
overridden event methods to limit their activity:

.. autofunction:: rotest.core.result.monitor.monitor.skip_if_case

.. autofunction:: rotest.core.result.monitor.monitor.skip_if_flow

.. autofunction:: rotest.core.result.monitor.monitor.skip_if_block

.. autofunction:: rotest.core.result.monitor.monitor.skip_if_not_main

.. autofunction:: rotest.core.result.monitor.monitor.require_attr
