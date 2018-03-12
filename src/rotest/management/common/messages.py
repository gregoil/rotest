"""Holds the common resource management messages."""
from abc import ABCMeta

from basicstruct import BasicStruct


def slots_extender(new_slots):
    """Extender decorator to add new slots to the wrapped class.

    Arguments:
        new_slots (tuple): new slots names.

    Returns:
        func. a method that decorate a class.
    """
    def decorator(origin_class):
        """Decorate a class and add the given slots to it.

        Actually, it creates a new class that derives from the given class and
        add the new slots to it, also, it copies the documentation.

        Arguments:
            origin_class (class): the class to be wrapped.

        Returns:
            class. the new class.
        """
        new_class = type(origin_class.__name__, (origin_class,), {})
        new_class.__slots__ = origin_class.__slots__ + new_slots
        new_class.__doc__ = origin_class.__doc__
        return new_class

    return decorator


@slots_extender(('msg_id',))
class AbstractMessage(BasicStruct):
    """Basic message class.

    Holds the common data for resource management messages.

    Attributes:
        msg_id (number): sending side unique message identifier.
    """
    __metaclass__ = ABCMeta


@slots_extender(('reason',))
class ParsingFailure(AbstractMessage):
    """Reply message on a request that failed to parse."""
    pass


@slots_extender(('request_id',))
class AbstractReply(AbstractMessage):
    """Abstract reply message for parsed request.

    Attributes:
        request_id (number): msg_id of the requested operation.
    """
    __metaclass__ = ABCMeta


class SuccessReply(AbstractReply):
    """Success reply message, answer on successful request."""
    pass


@slots_extender(('should_skip',))
class ShouldSkipReply(AbstractReply):
    """Reply message to the 'should_skip' remote query."""
    pass


@slots_extender(('code', 'content'))
class ErrorReply(AbstractReply):
    """Error reply message, answer on unsuccessful request.

    Attributes:
        code (number): error code.
        content (str): content describing the failure.
    """
    pass


@slots_extender(('resources',))
class ResourcesReply(AbstractReply):
    """Resources reply message.

    Sent as an answer to a successful 'LockResources' request.

    Attributes:
        resources (list): list of
            :class:'rotest.common.models.base_resource.BaseResource'.
    """
    pass


@slots_extender(('descriptors',))
class QueryResources(AbstractMessage):
    """Query resources request message.

    Attributes:
        descriptors (dict): descriptors of to query in the format
            {'type': resource_type_name, 'properties': {'key': value}}
        timeout (number): seconds to wait for resources if they're unavailable.
    """
    pass


@slots_extender(('descriptors', 'timeout'))
class LockResources(AbstractMessage):
    """Lock resources request message.

    Attributes:
        descriptors (list): descriptors of resources. list of dictionaries of
            {'type': resource_type_name, 'properties': {'key': value}}
        timeout (number): seconds to wait for resources if they're unavailable.
    """
    pass


@slots_extender(('requests',))
class ReleaseResources(AbstractMessage):
    """Release resources request message.

    Attributes:
        requests (list): list of resources names.
    """
    pass


@slots_extender(('user_name',))
class CleanupUser(AbstractMessage):
    """Clean user's resources request message.

    Attributes:
        user_name (str): name of the user to be cleaned.
    """
    pass


@slots_extender(('tests', 'run_data'))
class StartTestRun(AbstractMessage):
    """Start the run of the test message.

    Attributes:
        tests (dict): structure and data of the tests to run.
        run_data (dict): additional data relevant to the run.
    """
    pass


class RunFinished(AbstractMessage):
    """Signals the end of the run.

    Note:
        This message is used in multiproccess runner to inform the manager of
        the end of a worker's run.
    """
    pass


@slots_extender(('run_data',))
class UpdateRunData(AbstractMessage):
    """Update the run data message.

    Attributes:
        run_data (dict): run data fields and values.
    """
    pass


@slots_extender(('model', 'filter', 'kwargs'))
class UpdateFields(AbstractMessage):
    """Request to update content in the server's DB.

    Attributes:
        model (type): Django model to apply changes on.
        filter (dict): arguments to filter by.
        kwargs (dict): changes to apply on the filtered instances.
    """
    pass


@slots_extender(('test_id',))
class AbstractTestEventMessage(AbstractMessage):
    """Abstract test event message.

    Attributes:
        test_id (number): identifier of the test.
    """
    pass


class StartTest(AbstractTestEventMessage):
    """Start the run of a test message."""
    pass


class SetupFinished(AbstractTestEventMessage):
    """Finished the setup of a test message."""
    pass


class StartTeardown(AbstractTestEventMessage):
    """Start the teardown of a test message."""
    pass


class ShouldSkip(AbstractTestEventMessage):
    """Check if the test should be skipped message."""
    pass


class StopTest(AbstractTestEventMessage):
    """End the run of a test message."""
    pass


@slots_extender(('resources',))
class UpdateResources(AbstractTestEventMessage):
    """Update the resources list of the test's locked resources.

    Attributes:
        resources (list): list of resource descriptor of the test.
    """
    pass


@slots_extender(('resources',))
class CloneResources(AbstractTestEventMessage):
    """Update the resources list of the test's locked resources.

    Attributes:
        resources (dict): dict of the locked resources of the test.

    Note:
        This message is used in multiproccess runner to inform the manager of
        the test's 'locked_resources' dict content.
    """
    pass


class StartComposite(AbstractTestEventMessage):
    """Start the run of a composite test message."""
    pass


class StopComposite(AbstractTestEventMessage):
    """End the run of a composite test message."""
    pass


@slots_extender(('code', 'info'))
class AddResult(AbstractTestEventMessage):
    """Update a test result message.

    Attributes:
        code (number): TestOutcome result code.
        info (str): additional data about the result (traceback, reason, etc.).
    """
    pass
