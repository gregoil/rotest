"""Resource manager server."""
# pylint: disable=no-self-use,protected-access,broad-except,too-many-locals
import time
from threading import Thread
from datetime import datetime
from Queue import Queue, Empty as EmptyQueueError

from django.db import transaction
from django.db.models.query_utils import Q
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist

from rotest.common.django_utils.common import get_sub_model
from rotest.management.models.resource_data import ResourceData
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.management.common.errors import (ServerError,
                                             UnknownUserError,
                                             ResourceReleaseError,
                                             ResourcePermissionError,
                                             ResourceUnavailableError,
                                             ResourceDoesNotExistError,
                                             ResourceAlreadyAvailableError)
from rotest.management.common.messages import (StopTest,
                                               StartTest,
                                               AddResult,
                                               ErrorReply,
                                               ShouldSkip,
                                               CleanupUser,
                                               SuccessReply,
                                               StartTestRun,
                                               UpdateFields,
                                               StopComposite,
                                               LockResources,
                                               UpdateRunData,
                                               ResourcesReply,
                                               QueryResources,
                                               StartComposite,
                                               UpdateResources,
                                               ShouldSkipReply,
                                               ReleaseResources)


class _WaitingForResourceException(Exception):
    """Raised when resources aren't available but timeout hasn't expired."""
    pass


class ManagerThread(Thread):
    """Resource manager main thread.

    Gets requests from the queue, add them to the requests list, process each
    request and sends a reply via the worker instance.

    Attributes:
        _requests (list): list of requests to handle.
        request_queue (Queue): queue of new requests, added by the workers.
        daemon (bool): A boolean value indicating whether this thread is a
            daemon thread (True) or not (False). Will be marked as True so
            once the server listener dies this thread will also die.
        REQUESTS_TIMEOUT (number): seconds to wait for new requests.
        REQUESTS_MAX_AMOUNT (number): maximum request amount.
    """
    daemon = True

    REQUESTS_TIMEOUT = 1
    REQUESTS_MAX_AMOUNT = 10

    def __init__(self, reactor, logger):
        """Construct the resource manager.

        Args:
            reactor (PollReactor): The reactor to work with.
            logger (logging.Logger): The logger of this resource manager.
        """
        super(ManagerThread, self).__init__()

        self.logger = logger

        self._requests = []
        self.request_queue = Queue()

        self._reactor = reactor
        self._stop_flag = False
        self._requests_handlers = {StopTest: self.stop_test,
                                   StartTest: self.start_test,
                                   ShouldSkip: self.should_skip,
                                   CleanupUser: self.cleanup_user,
                                   AddResult: self.add_test_result,
                                   UpdateFields: self.update_fields,
                                   StartTestRun: self.start_test_run,
                                   StopComposite: self.stop_composite,
                                   LockResources: self.lock_resources,
                                   UpdateRunData: self.update_run_data,
                                   QueryResources: self.query_resources,
                                   StartComposite: self.start_composite,
                                   UpdateResources: self.update_resources,
                                   ReleaseResources: self.release_resources}

    def run(self):
        """Handles the requests in the pool and waits for new requests."""
        self.logger.debug("Resource manager main thread started")

        while not self._stop_flag:
            try:
                self._handle_requests()
                self._accept_requests()

            except Exception as ex:
                self.logger.exception("Resource manager failed. "
                                      "Reason: %s", ex)

        self.logger.debug("Resource manager thread is down")

    def stop(self):
        """Turn on the 'stop' flag."""
        self._stop_flag = True

    def _accept_requests(self):
        """Add new requests.

        Pull new requests from the queue and add them to the requests list.

        Note:
            Pulling max requests amount according to REQUESTS_MAX_AMOUNT.
            Waiting max seconds for request according to REQUESTS_TIMEOUT.
        """
        try:
            request = self.request_queue.get(timeout=self.REQUESTS_TIMEOUT)
            self.logger.debug("Adding new requests")
            for _ in xrange(self.REQUESTS_MAX_AMOUNT):
                self._requests.append(request)
                request = self.request_queue.get_nowait()

        except EmptyQueueError:
            return

        self.logger.debug("Done adding new requests")

    def _get_request_handler(self, request):
        """Returns the suitable request handler.

        Args:
            request (Request): the request that should be handle.

        Returns:
            callable. the request handler.

        Raises:
            ServerError. no suitable handler found.
        """
        try:
            message_type = type(request.message)
            return self._requests_handlers[message_type]

        except KeyError:
            raise ServerError("Invalid message type %r" % message_type)

    def _handle_requests(self):
        """Iterate the requests pool and handle requests one by one."""
        for request in self._requests[:]:
            self.logger.debug("Handling request: %r", request)

            # an orphan request, client is not alive.
            if not request.server_request and not request.worker.is_alive:
                self.logger.warning("Client %r disconnected, request dropped",
                                    request.worker.name)
                self._requests.remove(request)
                continue

            try:
                request_handler = self._get_request_handler(request)
                reply = request_handler(request)

            except _WaitingForResourceException as ex:
                self.logger.exception(str(ex))
                continue

            except Exception as ex:
                if isinstance(ex, ServerError):
                    code = ex.ERROR_CODE
                    content = ex.get_error_content()

                else:
                    code = ServerError.ERROR_CODE
                    content = str(ex)

                self.logger.exception(str(ex))
                reply = ErrorReply(code=code, content=content)

            reply.request_id = request.message.msg_id
            self._reactor.callFromThread(request.respond, reply)

            self._requests.remove(request)

    def _lock_resource(self, resource, user_name):
        """Mark the resource as locked by the given user.

        For complex resource, marks also its sub-resources as locked by the
        given user.

        Note:
            The given resource *must* be available.

        Args:
            resource (ResourceData): resource to lock.
            user_name (str): name of the locking user.
        """
        for sub_resource in resource.get_sub_resources():
            self._lock_resource(sub_resource, user_name)

        resource.owner = user_name
        resource.owner_time = datetime.now()
        resource.save()

    def _release_resource(self, resource, user_name):
        """Mark the resource as free.

        For complex resource, marks also its sub-resources as free.

        Args:
            resource (ResourceData): resource to release.
            user_name (str): name of the releasing user.

        Raises:
            ResourceReleaseError: if resource is a complex resource and fails.
            ResourcePermissionError: if resource is locked by other user.
            ResourceAlreadyAvailableError: if resource was already available.
        """
        errors = {}

        for sub_resource in resource.get_sub_resources():
            try:
                self._release_resource(sub_resource, user_name)

            except ServerError as ex:
                errors[sub_resource.name] = (ex.ERROR_CODE, str(ex))
                self.logger.debug("Failed to release sub-resource %r, "
                                  "Reason: %s", sub_resource, ex)

        if resource.is_available(user_name):
            raise ResourceAlreadyAvailableError("Failed releasing resource "
                                                "%r, it was not locked"
                                                % resource.name)

        if resource.owner != user_name:
            raise ResourcePermissionError("Failed releasing resource %r, "
                                          "it is locked by %r"
                                          % (resource.name, resource.owner))

        resource.owner = ""
        resource.owner_time = None
        resource.save()

        if len(errors) != 0:
            raise ResourceReleaseError(errors)

    def cleanup_user(self, cleanup_request):
        """Cleaning up user's requests and locked resources.

        Args:
            cleanup_request (Request): CleanupUser request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        user_name = cleanup_request.message.user_name
        self.logger.debug("Clean up after user %r", user_name)

        self.logger.debug("Removing requests of user %r", user_name)
        for request in self._requests[:]:
            if request.worker.name == user_name and not request.server_request:
                self._requests.remove(request)

        self.logger.debug("Releasing locked resources of user %r", user_name)
        resources = ResourceData.objects.filter(owner=user_name)
        if resources.count() == 0:
            self.logger.debug("User %r didn't lock any resource", user_name)

        else:
            resources.update(owner="", owner_time=None)
            self.logger.debug("User %r was successfully cleaned", user_name)

        return SuccessReply()

    @transaction.atomic
    def query_resources(self, request):
        """Find and return the resources that answer the client's query.

        Args:
            request (Request): QueryResources request.

        Returns:
            ResourcesReply. a reply containing matching resources.
        """
        desc = ResourceDescriptor.decode(request.message.descriptors)
        self.logger.debug("Looking for resources with description %r", desc)

        # query for resources that are usable and match the descriptors
        query = (Q(is_usable=True, **desc.properties))
        matches = desc.type.objects.filter(query)

        if matches.count() == 0:
            raise ResourceDoesNotExistError("No existing resource meets "
                                            "the requirements: %r" % desc)

        query_result = [resource for resource in matches]

        return ResourcesReply(resources=query_result)

    @transaction.atomic
    def lock_resources(self, request):
        """Lock the given resources one by one.

        Note:
            If one of the resources fails to lock, all the resources that has
            been locked until that resource will be released.

        Args:
            request (Request): LockResources request.

        Returns:
            ResourcesReply. a reply containing requested resources.

        Raises:
            ResourceDoesNotExistError. at least one of the requested resources
                doesn't exist.
            ResourceUnavailableError. when the requested resources are not
                available.
            UnknownUserError. when unknown user has tried to lock a resource.
        """
        locked_resources = []

        client = request.worker.name
        user_name, _ = client.split(":")  # splitting <user_name>:<port>

        if not auth_models.User.objects.filter(username=user_name).exists():
            raise UnknownUserError(
                    "User %r has no matching object in the DB" % user_name)

        user = auth_models.User.objects.get(username=user_name)

        groups = list(user.groups.all())

        for descriptor_dict in request.message.descriptors:

            desc = ResourceDescriptor.decode(descriptor_dict)
            self.logger.debug("Locking %r resource", desc)

            # query for resources that are usable and match the user's
            # preference, which are either belong to a group he's in or
            # don't belong to any group.
            query = (Q(is_usable=True, **desc.properties) &
                     (Q(group__isnull=True) | Q(group__in=groups)))
            matches = desc.type.objects.filter(query).order_by('-reserved')

            if matches.count() == 0:
                raise ResourceDoesNotExistError("No existing resource meets "
                                                "the requirements: %r" % desc)

            availables = (resource for resource in matches
                          if resource.is_available(client))

            try:
                resource = availables.next()

                self._lock_resource(resource, client)
                locked_resources.append(resource)
                self.logger.debug("Resource %r locked successfully", desc)

            except StopIteration:
                timeout = request.message.timeout
                waiting_time = time.time() - request.creation_time
                if timeout is not None and waiting_time > timeout:
                    raise ResourceUnavailableError("No available resource "
                                                   "meets the requirements: "
                                                   "%r" % desc)

                raise _WaitingForResourceException("Resource %r is unavailable"
                                                   ", waiting for it to be "
                                                   "released", desc)

        return ResourcesReply(resources=locked_resources)

    def release_resources(self, request):
        """Release the given resources one by one.

        Args:
            request (Request): ReleaseResources request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.

        Raises:
            ResourceReleaseError: when error occurred while trying to release
                at least one of the given resources.
        """
        errors = {}
        for name in request.message.requests:
            try:
                resource_data = ResourceData.objects.get(name=name)

            except ObjectDoesNotExist:
                errors[name] = (ResourceDoesNotExistError.ERROR_CODE,
                                "Resource %r doesn't exist" % name)
                continue

            resource = get_sub_model(resource_data)

            self.logger.debug("Releasing %r resource", name)

            try:
                self._release_resource(resource, request.worker.name)
                self.logger.debug("Resource %r released successfully", name)

            except ServerError as ex:
                errors[name] = (ex.ERROR_CODE, ex.get_error_content())

        if len(errors) > 0:
            raise ResourceReleaseError(errors)

        return SuccessReply()

    def start_test_run(self, request):
        """Build the tests tree and the run data of the new run.

        Args:
            request (Request): StartTestRun request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.initialize_test_run(request.message.tests,
                                           request.message.run_data)

        return SuccessReply()

    def start_test(self, request):
        """Start a test run.

        Args:
            request (Request): StartTest request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.start_test(request.message.test_id)

        return SuccessReply()

    def should_skip(self, request):
        """Check if the test previously passed in the results DB.

        Args:
            request (Request): ShouldSkip request.

        Returns:
            ShouldSkipReply. a reply containing the query result.
        """
        query_result = request.worker.should_skip(request.message.test_id)

        return ShouldSkipReply(should_skip=query_result)

    def stop_test(self, request):
        """End a test run.

        Args:
            request (Request): StopTest request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.stop_test(request.message.test_id)

        return SuccessReply()

    def update_resources(self, request):
        """Update the resources list for a test data.

        Args:
            request (Request): UpdateResources request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.update_resources(request.message.test_id,
                                        request.message.resources)

        return SuccessReply()

    def update_fields(self, request):
        """Update content in the DB.

        Args:
            request (Request): UpdateFields request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        message = request.message
        objects = message.model.objects
        if message.filter is not None and len(message.filter) > 0:
            objects.filter(**message.filter).update(**message.kwargs)

        else:
            objects.all().update(**message.kwargs)

        return SuccessReply()

    def update_run_data(self, request):
        """Update the run data parameters for a run.

        Args:
            request (Request): UpdateRunData request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.update_run_data(request.message.run_data)

        return SuccessReply()

    def start_composite(self, request):
        """Start a composite test run.

        Args:
            request (Request): StartComposite request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.start_composite(request.message.test_id)

        return SuccessReply()

    def stop_composite(self, request):
        """End a composite test run.

        Args:
            request (Request): StopComposite request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.stop_composite(request.message.test_id)

        return SuccessReply()

    def add_test_result(self, request):
        """Add a result to a test.

        Args:
            request (Request): AddResult request.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        request.worker.add_test_result(request.message.test_id,
                                       request.message.code,
                                       request.message.info)

        return SuccessReply()
