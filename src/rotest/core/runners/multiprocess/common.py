"""Utilities for multiprocess tests running."""
# pylint: disable=invalid-name
import os
import psutil

from rotest.common import core_log


PROCESS_TERMINATION_TIMEOUT = 10


class WrappedException(object):
    """Used to wrapping exceptions so they could be passed via queues.

    Queue pickles every object it is requires to pass, and since Traceback
    objects cannot be pickled and therfore cannot be transfered using queue,
    there is a need to pass the traceback in another way.
    This class is designed to wrap traceback strings in order to pass them
    between workers and the manager processes using Queue.
    """
    def __init__(self, exception_string):
        self.message = exception_string

    def __str__(self):
        return self.message


def get_item_by_id(test_item, item_id):
    """Return the requested test item by its identifier.

    Goes over the test item's sub tests recursively and returns
    the one that matches the requested identifier.
    The search algorithm assumes that the identifiers assignment was the
    default one (use of default indexer), which identifies the tests in a DFS
    recursion.
    The algorithm continues the search in the sub-branch which root has the
    highest identifier that is still smaller or equal to the searched
    identifier.

    Args:
        test_item (object): test instance object.
        item_id (number): requested test identifier.

    Returns:
        TestCase / TestSuite. test item object.
    """
    if test_item.identifier == item_id:
        return test_item

    if test_item.IS_COMPLEX:
        sub_test = max([sub_test for sub_test in test_item
                        if sub_test.identifier <= item_id],
                       key=lambda test: test.identifier)

        return get_item_by_id(sub_test, item_id)


def kill_process(process):
    """Kill a single process.

    Args:
        process (psutil.Process): process to kill.
    """
    if not process.is_running():
        return

    process.kill()

    try:
        process.wait(PROCESS_TERMINATION_TIMEOUT)

    except psutil.TimeoutExpired:
        core_log.warning("Process %d failed to terminate", process.pid)


def kill_process_tree(process):
    """Kill a process and all its subprocesses.

    Note:
        Kill the process and all its sub processes recursively.
        If the given process is the current process - Kills the sub process
        before the given process. Otherwise - Kills the given process before
        its sub processes

    Args:
        process (psutil.Process): process to kill.
    """
    sub_processes = process.children(recursive=True)

    if process.pid == os.getpid():
        for sub_process in sub_processes:
            kill_process(sub_process)

        kill_process(process)

    else:
        kill_process(process)

        for sub_process in sub_processes:
            kill_process(sub_process)
