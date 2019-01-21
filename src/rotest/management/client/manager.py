"""Resource manager client implementation

Responsible for locking resources and preparing them for work,
also for the resources cleanup procedure and release.
"""
# pylint: disable=invalid-name,too-many-instance-attributes,too-many-branches
# pylint: disable=too-few-public-methods,too-many-arguments,too-many-locals
# pylint: disable=no-member,method-hidden,broad-except,too-many-public-methods
from __future__ import absolute_import

import time

import re
from attrdict import AttrDict
from future.utils import iteritems
from future.builtins import zip, str

from rotest.common import core_log
from rotest.management.client.client import AbstractClient
from rotest.api.common.responses import FailureResponseModel
from rotest.api.resource_control.lock_resources import USER_NOT_EXIST
from rotest.common.config import RESOURCE_MANAGER_HOST, ROTEST_WORK_DIR
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.management.common.errors import (ResourceReleaseError,
                                             ResourceUnavailableError,
                                             UnknownUserError)
from rotest.api.resource_control import (LockResources,
                                         QueryResources,
                                         ReleaseResources, CleanupUser)
from rotest.api.common.models import (ReleaseResourcesParamsModel,
                                      ResourceDescriptorModel,
                                      LockResourcesParamsModel, TokenModel)


class ClientResourceManager(AbstractClient):
    """Client side resource manager.

    Responsible for locking resources and preparing them for work,
    also for the resources cleanup procedure and release.

    Preparation includes validating, reseting and initializing resources.

    Attributes:
        locked_resources (list): resources locked and initialized by the client
            that are yet to be released.
        unused_resources (list): a sub-set of 'locked_resources' which
            are marked as not needed anymore - i.e. the test that requested
            them finished running.
        keep_resources (bool): whether to keep the resources locked until
            they are not needed.
    """
    DEFAULT_KEEP_RESOURCES = True

    def __init__(self, host=None, logger=core_log,
                 keep_resources=DEFAULT_KEEP_RESOURCES):
        """Initialize the resource client."""
        if host is None:
            host = RESOURCE_MANAGER_HOST

        self.locked_resources = []
        self.unused_resources = []
        self.keep_resources = keep_resources

        super(ClientResourceManager, self).__init__(logger=logger, host=host)

    def _release_locked_resources(self):
        """Release the locked resources of the client."""
        if len(self.locked_resources) > 0:
            self.logger.debug("Releasing locked resources %r",
                              self.locked_resources)

            self.release_resources({res.name: res for
                                    res in self.locked_resources},
                                   force_release=True)

    def disconnect(self):
        """Disconnect from manager server and release locked resources.

        Raises:
            RuntimeError: wasn't connected in the first place.
        """
        if self.is_connected():
            self._release_locked_resources()
            self.requester.request(CleanupUser, method="post",
                                   data=TokenModel({"token": self.token}))
            super(ClientResourceManager, self).disconnect()

    def _setup_resources(self, requests, resources, force_initialize,
                         enable_debug, skip_init):
        """Prepare the resources for work.

        Iterates over the resources and tries to prepare them for
        work by validating, resetting and initializing them.

        The locked and initialized resources are yielded instead of returned
        as a list so in case one got an exception in initialization, the
        user would know which resources were already initialized.

        Args:
            requests (tuple): list of the ResourceRequest.
            resources (list): list of the resources instances.
            force_initialize (bool): determines if the resources will be
                initialized even if their validation succeeds.
            enable_debug (bool): True to wrap the resource's method with debug.
            skip_init (bool): True to skip initialization and validation.

        Yields:
            tuple. pairs of locked and initialized resources (name, resource).

        Raises:
            ServerError. resource manager failed to lock resources.
        """
        self.logger.debug("Setting up the locked resources")

        for resource, request in zip(resources, requests):
            if enable_debug:
                resource.enable_debug()

            resource.setup_resource(skip_init=skip_init,
                                    force_initialize=force_initialize)

            yield (request.name, resource)

    def _cleanup_resources(self, resources):
        """Cleanup the resources and release them.

        Iterates over the resources dictionary and tries to cleanup each
        resource then releases them.

        Args:
            resources (AttrDict): dictionary of resources {name: BaseResource}.

        Raises:
            RuntimeError. releasing resources failed.
        """
        exceptions = []

        self.logger.debug("Cleaning up the locked resources")

        for name, resource in iteritems(resources):
            try:
                resource.logger.debug("Finalizing resource %r", name)
                resource.finalize()
                resource.logger.debug("Resource %r Finalized", name)

            except Exception as err:
                # A finalize failure should not stop other resources from
                # finalizing and from the release process to complete
                exceptions.append("%s: %s" % (str(err), name))
                self.logger.exception("Resource %r failed to finalize", name)

        if len(exceptions) > 0:
            raise RuntimeError("Releasing resources has failed. "
                               "Reasons: %s" % "\n".join(exceptions))

    def _wait_until_resources_are_locked(self, descriptors, timeout):
        """Wait until the given resources are locked.

        Args:
            descriptors (list): list of ResourceDescriptor objects,
                that represent the wanted resources.
            timeout (number): time to wait for the resources to be locked.

        Returns:
            InfluencedResourcesResponseModel. the response model received from
                the server.

        Raises:
            UnknownUserError. if the user requested the lock is unknown.
            ResourceUnavailableError. if timeout is reached and no resource
                could be locked.
        """
        encoded_requests = [descriptor.encode() for descriptor in
                            descriptors]

        request_data = LockResourcesParamsModel({
            "descriptors": encoded_requests,
            "token": self.token
        })

        start_time = time.time()
        while True:
            response = self.requester.request(LockResources,
                                              data=request_data,
                                              method="post")
            if isinstance(response, FailureResponseModel):
                match = re.match(USER_NOT_EXIST.format(".*"),
                                 response.details)
                if match:
                    raise UnknownUserError(response.details)

                if time.time() - start_time > timeout:
                    raise ResourceUnavailableError(response.details)

            else:
                break

        return response

    def _lock_resources(self, descriptors, config=None,
                        base_work_dir=ROTEST_WORK_DIR, timeout=None):
        """Send LockResources request to resource manager server.

        Note:
            The timeout can be configured by an environment variable.

        Args:
            descriptors (list): list of :class:`rotest.management.common.
                resource_descriptor.ResourceDescriptor`.
            timeout (number): seconds to wait for resources if they're
                unavailable. None - use the default timeout.

        Returns:
            list. list of locked resources.
        """
        if timeout is None:
            timeout = self.lock_timeout

        resources = []
        server_requests = [descriptor for descriptor in descriptors
                           if descriptor.type.DATA_CLASS is not None]

        if len(server_requests) > 0:
            if not self.is_connected():
                self.connect()

            response = \
                self._wait_until_resources_are_locked(server_requests, timeout)

            response_resources = \
                [self.parser.recursive_decode(resource)
                 for resource in response.resource_descriptors]

            resources.extend(descriptor.type(data=resource_data,
                                             config=config,
                                             base_work_dir=base_work_dir)
                             for (descriptor, resource_data) in
                             zip(server_requests, response_resources))

        for index, descriptor in enumerate(descriptors):
            if descriptor.type.DATA_CLASS is None:
                # it's a service
                resources.insert(index,
                                 descriptor.type(config=config,
                                                 base_work_dir=base_work_dir,
                                                 **descriptor.properties))

        return resources

    def _release_resources(self, resources):
        """Send ReleasesResources request to resource manager server.

        Args:
            resources (list): list of :class:`rotest.common.models.\
                BaseResource`s to be released.
        """
        self.logger.info("Releasing %r", resources)
        release_requests = [res.name
                            for res in resources if res.DATA_CLASS is not None]

        if len(release_requests) > 0:
            request_data = ReleaseResourcesParamsModel({
                "resources": release_requests,
                "token": self.token
            })
            response = self.requester.request(ReleaseResources,
                                              data=request_data,
                                              method="post")

            if isinstance(response, FailureResponseModel):
                raise ResourceReleaseError(response.errors)

        for resource in resources:
            if resource in self.locked_resources:
                self.locked_resources.remove(resource)

            if resource in self.unused_resources:
                self.unused_resources.remove(resource)

    def _find_matching_resources(self, descriptor, resources):
        """Get all similar resources that match the resource descriptor.

        Args:
            descriptor (ResourceDescriptor): resource descriptor to match.
            resources (list): list of available resources to filter from.

        Returns:
            list. resources matching the descriptor.
        """
        if descriptor.type.DATA_CLASS is None:
            # Dataless resource
            matching_resources = [resource for resource in resources
                                  if isinstance(resource, descriptor.type)]

            for field_name, value in list(descriptor.properties.items()):
                for resource in matching_resources[:]:
                    if getattr(resource, field_name, None) != value:
                        matching_resources.remove(resource)

        else:
            matching_query = self.query_resources(descriptor)
            matching_resources = [resource for resource in resources
                                  if resource.data in matching_query]

        return matching_resources

    def _retrieve_previous(self, requests, descriptors):
        """Search previously locked resources for matches to the request.

        If it finds a match, it removes the request and resource descriptor
        from the lists, so the resource won't be requested again.

        This method also releases previously locked resources that aren't
        needed anymore (doesn't answer any of the requests).

        Args:
            requests (tuple): List of the ResourceRequest.
            descriptors (list): list of :class:`rotest.management.common.
                resource_descriptor.ResourceDescriptor`.

        Returns:
            AttrDict. resources AttrDict {name: BaseResource}.
        """
        retrieved_resources = AttrDict()
        if len(self.unused_resources) == 0:
            return retrieved_resources

        for descriptor, request in zip(descriptors[:], requests[:]):
            # Check if the previously locked holds a similar resource
            if any(resource.DATA_CLASS == descriptor.type.DATA_CLASS
                   for resource in self.unused_resources):

                matching_resources = self._find_matching_resources(
                    descriptor,
                    self.unused_resources)

                if len(matching_resources) > 0:
                    previous_resource = matching_resources[0]
                    self.logger.info("Retrieved previously locked "
                                     "resource %r for %r",
                                     previous_resource,
                                     request.name)

                    retrieved_resources[request.name] = previous_resource

                    self.unused_resources.remove(previous_resource)
                    descriptors.remove(descriptor)
                    requests.remove(request)

        if len(self.unused_resources) > 0:
            self.logger.debug("Releasing unused locked resources %r",
                              self.unused_resources)

            self.release_resources({res.name: res for
                                    res in self.unused_resources},
                                   force_release=True)

        return retrieved_resources

    def request_resources(self, requests,
                          config=None,
                          skip_init=False,
                          use_previous=True,
                          enable_debug=False,
                          force_initialize=False,
                          base_work_dir=ROTEST_WORK_DIR):
        """Lock the required resources and prepare them for work.

        * Requests the resources from the manager server.
        * Iterates over the locked resources to try to prepare them for work.
        * The locked and initialized resources then returned as an AttrDict.

        Args:
            requests (tuple): List of the ResourceRequest.
            config (dict): run configuration dictionary.
            skip_init (bool): True to skip resources initialize and validation.
            use_previous (bool): whether to use previously locked resources and
                release the unused ones.
            enable_debug (bool): True to wrap the resource's method with debug.
            force_initialize (bool): determines if the resources will be
                initialized even if their validation succeeds.
            base_work_dir (str): base work directory path.

        Returns:
            AttrDict. resources AttrDict {name: BaseResource}.

        Raises:
            ServerError. resource manager failed to lock resources.
        """
        requests = list(requests)
        descriptors = [ResourceDescriptor(request.type, **request.kwargs)
                       for request in requests]

        initialized_resources = AttrDict()

        if use_previous:
            # Find matches in previously locked resources
            initialized_resources = self._retrieve_previous(requests,
                                                            descriptors)

        self.logger.debug("Requesting resources from resource manager")
        locked_resources = self._lock_resources(descriptors, config,
                                                base_work_dir)

        self.logger.info("Locked resources %s", locked_resources)

        try:
            self.logger.debug("Setting up the locked resources")

            for name, resource in self._setup_resources(requests,
                                                        locked_resources,
                                                        force_initialize,
                                                        enable_debug,
                                                        skip_init):

                initialized_resources[name] = resource

                if self.keep_resources:
                    self.locked_resources.append(resource)

            return initialized_resources

        except Exception:
            self._cleanup_resources(initialized_resources)
            self._release_resources(locked_resources)
            raise

    def release_resources(self, resources, dirty=False, force_release=False):
        """Cleanup the resources and release them.

        Iterates over the resources dictionary and tries to cleanup each
        resource then releases them.

        Args:
            resources (AttrDict): resources AttrDict {name: BaseResource}.
            dirty (bool): the resources requested dirty state.
            force_release (bool): release even if the client is supposed
                to keep the resources.

        Raises:
            RuntimeError. releasing resources failed.
        """
        if self.keep_resources and not force_release and not dirty:
            self.logger.debug("Refraining from releasing the resources yet")
            self.unused_resources.extend(list(resources.values()))
            return

        try:
            self._cleanup_resources(resources)

        finally:
            self._release_resources(resources=list(resources.values()))

    def query_resources(self, descriptor):
        """Query the content of the server's DB.

        Args:
            descriptor (ResourceDescriptor): descriptor of the query
                (containing model class and query filter kwargs).
        """
        request_data = ResourceDescriptorModel(descriptor.encode())
        response = self.requester.request(QueryResources,
                                          data=request_data,
                                          method="post")
        if isinstance(response, FailureResponseModel):
            raise Exception(response.details)

        return [self.parser.recursive_decode(resource)
                for resource in response.resource_descriptors]
