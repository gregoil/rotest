"""Resource manager client implementation

Responsible for locking resources and preparing them for work,
also for the resources cleanup procedure and release.
"""
# pylint: disable=invalid-name,too-many-instance-attributes
# pylint: disable=too-few-public-methods,too-many-arguments
# pylint: disable=no-member,method-hidden,broad-except,too-many-public-methods
from itertools import izip

from attrdict import AttrDict

from rotest.common import core_log
from rotest.management.common import messages
from rotest.management.client.client import AbstractClient
from rotest.management.common.errors import ResourceDoesNotExistError
from rotest.common.config import ROTEST_WORK_DIR, RESOURCE_MANAGER_HOST
from rotest.management.common.resource_descriptor import ResourceDescriptor


class ResourceRequest(object):
    """Holds the data for a resource request.

    Attributes:
        resource_name (str): attribute name to be assigned.
        resource_class (type): resource type.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        save_state (bool): flag to determine if the resource saves its state.
            Notice that if the case's save_state flag set to False it will
            override the expected behavior.
        kwargs (dict): requested resource arguments.
    """
    def __init__(self, resource_name, resource_class,
                 force_initialize=False, save_state=True, **kwargs):
        """Initialize the required parameters of resource request."""
        self.name = resource_name
        self.type = resource_class
        self.save_state = save_state
        self.force_initialize = force_initialize

        self.kwargs = kwargs

    def __eq__(self, oth):
        """Compare with another request."""
        return oth.name == self.name

    def __repr__(self):
        """Return a string representing the request."""
        return "Request %r of type %r (kwargs=%r)" % (self.name, self.type,
                                                      self.kwargs)

    def clone(self):
        """Create a copy of the request."""
        return ResourceRequest(self.name, self.type, self.force_initialize,
                               self.save_state, **self.kwargs)


class ClientResourceManager(AbstractClient):
    """Client side resource manager.

    Responsible for locking resources and preparing them for work,
    also for the resources cleanup procedure and release.

    Preparation includes validating, reseting and initializing resources.
    Cleanup includes storing state, and finalizing resources.

    Attributes:
        locked_resources (list): resources locked and initialized by the client
            that are yet to be released.
        keep_resources (bool): whether to keep the resources locked until
            they are not needed.
    """
    DEFAULT_STATE_DIR = "state"
    DEFAULT_KEEP_RESOURCES = True

    def __init__(self, host=None, logger=core_log,
                 keep_resources=DEFAULT_KEEP_RESOURCES):
        """Initialize the resource client."""
        if host is None:
            host = RESOURCE_MANAGER_HOST

        self.locked_resources = []
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
        self._release_locked_resources()
        if self.is_connected():
            super(ClientResourceManager, self).disconnect()

    def _initialize_resource(self, resource, skip_init=False):
        """Try to initialize the resource.

        Note:
            Initialization failure will cause a finalization attempt.

        Args:
            resource(BaseResource): resource to initialize.
            skip_init (bool): True to skip initialize and validation.
        """
        try:
            resource.connect()

        except Exception:
            self.logger.exception("Connecting to %r failed", resource.name)
            raise

        if skip_init:
            self.logger.debug("Skipping validation and initialization")
            return

        try:
            self.logger.debug("Initializing resource %r", resource.name)
            self._validate_resource(resource)
            self.logger.debug("Resource %r was initialized", resource.name)

        except Exception:
            self.logger.exception("Failed initializing %r, calling finalize",
                                  resource.name)
            resource.finalize()
            raise

    def _validate_resource(self, resource):
        """Validate and initialize if needed the resource and its subresources.

        Args:
            resource (BaseResource): resource to validate and initialize.
        """
        for sub_resource in resource.get_sub_resources():
            self._validate_resource(sub_resource)

        if resource.force_initialize or not resource.validate():
            if not resource.force_initialize:
                self.logger.debug("Resource %r validation failed",
                                  resource.name)

            resource.initialize()

        else:
            self.logger.debug("Resource %r skipped initialization",
                              resource.name)

    def _propagate_attributes(self, resource, config, save_state,
                              force_initialize):
        """Update the resource's config dictionary recursively.

        Args:
            resource (BaseResource): resource to update.
            config (dict): run configuration dictionary.
            save_state (bool): determine if storing state is required.
            force_initialize (bool): determines if the resources will be
                initialized even if their validation succeeds.
        """
        resource.config = config
        resource.logger = self.logger
        resource.save_state = save_state
        resource.force_initialize = force_initialize

        for sub_resource in resource.get_sub_resources():
            if sub_resource is not None:
                self._propagate_attributes(sub_resource, config,
                                           save_state, force_initialize)

    def _setup_resources(self, requests, resources, save_state,
                         force_initialize, base_work_dir, config,
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
            base_work_dir (str): base work directory path.
            config (dict): run configuration dictionary.
            enable_debug (bool): True to wrap the resource's method with debug.
            skip_init (bool): True to skip initialization and validation.

        Yields:
            tuple. pairs of locked and initialized resources (name, resource).

        Raises:
            ServerError. resource manager failed to lock resources.
        """
        for resource, request in izip(resources, requests):

            resource.set_sub_resources()

            self._propagate_attributes(resource=resource, config=config,
               save_state=request.save_state and save_state,
               force_initialize=request.force_initialize or force_initialize)

            resource.set_work_dir(request.name, base_work_dir)
            resource.logger.debug("Resource %r work dir was created under %r",
                                  request.name, base_work_dir)

            if enable_debug:
                resource.enable_debug()

            self._initialize_resource(resource, skip_init)

            yield (request.name, resource)

    def _cleanup_resources(self, resources):
        """Cleanup the resources and release them.

        Iterates over the resources dictionary and tries to cleanup each
        resource then releases them.
        Cleanup includes storing state, and finalizing resources.

        Args:
            resources (AttrDict): dictionary of resources {name: BaseResource}.

        Raises:
            RuntimeError. releasing resources failed.
        """
        exceptions = []

        self.logger.debug("cleaning up the locked resources")

        for name, resource in resources.iteritems():

            try:
                if resource.save_state:

                    try:
                        resource.store_state_dir(self.DEFAULT_STATE_DIR)

                    except Exception as err:
                        exceptions.append("%s: %s" % (str(err), name))
                        self.logger.exception("Resource %r failed to store "
                                              "state", name)

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

    def _lock_resources(self, descriptors, timeout=None):
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

            encoded_requests = [descriptor.encode() for descriptor in
                                server_requests]

            request = messages.LockResources(descriptors=encoded_requests,
                                             timeout=timeout)

            reply = self._request(request, timeout=timeout)

            resources.extend(descriptor.type(data=resource_data) for
                             (descriptor, resource_data) in
                             zip(server_requests, reply.resources))

        for index, descriptor in enumerate(descriptors):
            if descriptor.type.DATA_CLASS is None:
                # it's a service
                resources.insert(index,
                                 descriptor.type(**descriptor.properties))

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
            request = messages.ReleaseResources(requests=release_requests)
            self._request(request)

        for resource in resources:
            if resource in self.locked_resources:
                self.locked_resources.remove(resource)

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

            for field_name, value in descriptor.properties.items():
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
        unused_locked_resources = self.locked_resources[:]
        if len(unused_locked_resources) == 0:
            return retrieved_resources

        for descriptor, request in zip(descriptors[:], requests[:]):
            # Check if the previously locked holds a similar resource
            if any(resource.DATA_CLASS == descriptor.type.DATA_CLASS
                   for resource in unused_locked_resources):

                matching_resources = self._find_matching_resources(
                                                    descriptor,
                                                    unused_locked_resources)

                if len(matching_resources) > 0:
                    previous_resource = matching_resources[0]
                    self.logger.info("Retrieved previously locked "
                                      "resource %r for %r",
                                      previous_resource,
                                      request.name)

                    retrieved_resources[request.name] = previous_resource

                    unused_locked_resources.remove(previous_resource)
                    descriptors.remove(descriptor)
                    requests.remove(request)

        if len(unused_locked_resources) > 0:
            self.logger.debug("Releasing unused locked resources %r",
                              unused_locked_resources)

            self.release_resources({res.name: res for
                                    res in unused_locked_resources},
                                   force_release=True)

        return retrieved_resources

    def request_resources(self, requests,
                          config=None,
                          skip_init=False,
                          save_state=False,
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
            save_state (bool): Determine if storing state is required.
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
        locked_resources = self._lock_resources(descriptors)
        self.logger.info("Locked resources %s", locked_resources)

        try:
            self.logger.debug("Setting up the locked resources")

            for name, resource in self._setup_resources(requests,
                                                        locked_resources,
                                                        save_state,
                                                        force_initialize,
                                                        base_work_dir,
                                                        config,
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
        Cleanup includes storing state, and finalizing resources.

        Args:
            resources (AttrDict): resources AttrDict {name: BaseResource}.
            dirty (bool): the resources requested dirty state.
            force_release (bool): release even if the client is supposed
                to keep the resources.

        Raises:
            RuntimeError. releasing resources failed.
        """
        if self.keep_resources and not force_release and not dirty:
            self.logger.debug("Refraining from releasing the resources")
            return

        try:
            self._cleanup_resources(resources)

        finally:
            self._release_resources(resources=resources.values())

    def query_resources(self, descriptor):
        """Query the content of the server's DB.

        Args:
            descriptor (ResourceDescriptor): descriptor of the query
                (containing model class and query filter kwargs).
        """
        request = messages.QueryResources(descriptors=descriptor.encode())
        try:
            reply = self._request(request)

        except ResourceDoesNotExistError:
            return []

        return reply.resources
