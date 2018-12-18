Debugging
=========

Rotest comes with easy ways to debug tests:

* Post run

  The builtin features in Rotest help you greatly when trying to figure out
  what went wrong in a test.

  * Logs of the tests can be found in the working directory.
  * ``excel`` output handler created a summary excel file in the working directory.
  * ``artifact`` output handler creates a zip of the working directory and sends it to the artifacts directory.
  * ``save-state`` command line option stores the state of resources into the working directory.
  * ``remote`` and ``db`` save the tests' metadata into the db, including traceback and timestamps,
    for future usage and research.

* Developing and real-time debugging

  * When running tests locally, using the `ipdbugger` (``--debug`` flag)
    can be a real life saver. It pops an ipdb interactive shell whenever an
    unexpected exception occurs (including failures) without exiting the scope
    of the test, giving the user full control over it.

    For example, if an AttributeError has occurred, you can add the missing
    attribute via the interactive shell, then use `jump` or `retry` to re-run
    code segments. If your tests are based on Blocks and Flows methodology
    (see :ref:`blocks`), you can use the `TestFlow` methods `list_blocks` and
    `jump_to` to control the flow of the test in the same way. E.g.

    .. code-block:: python

        self.parent.list_blocks()  # Prints the hierarchy down from the parent flow
        self.parent.jump_to(1)  # Jumps to the beginning of the block at index 1

  * It is also recommended to use ``rotest shell`` when debugging new code,
    especially when writing new `TestFlows` and `TestBlocks` (use the `shared_data`
    and `run_block` methods to simulate a containing TestFlow). Combining with
    IPython's ``autoreload`` ability, writing tests this way can be made easy and quick.
