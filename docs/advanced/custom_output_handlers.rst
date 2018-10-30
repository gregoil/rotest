=============================
Adding Custom Output Handlers
=============================

Third Party Output Handlers
===========================

* `rotest_reportportal <https://github.com/gregoil/rotest_reportportal>`_

  - Plugin to the amazing `Report Portal <http://reportportal.io/>`_ system,
    that enables viewing test results and investigating them.

How to Make Your Own Output Handler
===================================

You can make your own Output Handler, following the next two steps:

* Inheriting from
  :class:`rotest.core.result.handlers.abstract_handler.AbstractResultHandler`,
  and overriding the relevant methods.

* Register the above inheriting class as an entrypoint in your setup.py file inside ``setup()``:

    .. code-block:: python

        entry_points={
            "rotest.result_handlers":
                ["<handler tag, e.g. my_handler> = <import path to the monitor's module>:<monitor class name>"]
        },

* Make sure it's being installed in the environment by calling

    .. code-block:: console

        python setup.py develop


For an example, you can refer to
`rotest_reportportal <https://github.com/gregoil/rotest_reportportal>`_ plugin.

.. _available_events:

Available Events
================

The available methods of an output handler:

.. autoclass:: rotest.core.result.handlers.abstract_handler.AbstractResultHandler
    :members:
