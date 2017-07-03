"""Resource management tests.

We test resource management behavior under different scenarios.

TODO: add tests for complex resources.
5. Lock/Release a complex resource and other resources.
7. Cleaned Up a complex resource.
8. Dirty tests
"""
# pylint: disable=invalid-name,too-many-public-methods,protected-access
import time
from itertools import izip
from threading import Thread

import django
from django.db.models.query_utils import Q
from django.contrib.auth.models import User

from rotest.management.common.utils import LOCALHOST
from rotest.common.colored_test_runner import colored_main
from rotest.management.common.utils import HOST_PORT_SEPARATOR
from rotest.management.client.manager import (ClientResourceManager,
                                              ResourceRequest)
from rotest.tests.management.resource_base_test import \
                                            BaseResourceManagementTest
from rotest.management.common.resource_descriptor import \
                                            ResourceDescriptor as Descriptor
from rotest.management.models.ut_models import (DemoResource,
                                                DemoResourceData,
                                                DemoComplexResource,
                                                DemoComplexResourceData)
from rotest.management.common.errors import (ServerError,
                                             UnknownUserError,
                                             ResourceReleaseError,
                                             ResourcePermissionError,
                                             ResourceUnavailableError,
                                             ResourceDoesNotExistError,
                                             ResourceAlreadyAvailableError)


class TestResourceManagement(BaseResourceManagementTest):
    """Resource management tests."""
    fixtures = ['resource_ut.json']

    NON_EXISTING_NAME1 = 'kuki1'
    NON_EXISTING_NAME2 = 'kuki2'
    LOCKED1_NAME = 'locked_resource1'
    LOCKED2_NAME = 'locked_resource2'
    FREE1_NAME = 'available_resource1'
    FREE2_NAME = 'available_resource2'
    COMPLEX_NAME = 'complex_resource1'
    NON_EXISTING_FIELD = 'illegal_field'
    NO_GROUP_RESOURCE = 'resource_with_no_group'
    OTHER_GROUP_RESOURCE = 'other_group_resource'

    LOCK_TIMEOUT = 4
    CLEANUP_TIME = 1.5

    def setUp(self):
        """Initialize and connect a client to the resource manager."""
        super(TestResourceManagement, self).setUp()

        self.client = ClientResourceManager(LOCALHOST)
        self.client.connect()

    def tearDown(self):
        """Disconnect the client from the resource manager."""
        self.client.disconnect()

        super(TestResourceManagement, self).tearDown()

    def get_resource(self, name, **kwargs):
        """Get a resource by conditions, and assert existence of exactly one.

        Args:
            name (str): the name field of the DemoResource.
            **kwargs (dict): additional filtering values.

        Returns:
            QuerySet. filtered resources that match the conditions.

        Raises:
            AssertionError. if the DB doesn't have exactly one resource that
                match the conditions.
        """
        resources = DemoResourceData.objects.filter(name=name, **kwargs)
        resources_num = resources.count()

        self.assertEqual(resources_num, 1, "Expected 1 available "
                         "resource with name %r in DB, found %d"
                         % (name, resources_num))

        return resources

    def test_lock_reserved_resource(self):
        """Lock a reserved resource.

        * Validates the DB initial state.
        * Update the reserved flag and save the resource.
        * Locks an existing resource, using resource client.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates that there is 1 locked resource with this name in DB.
        """
        resources = self.get_resource(self.FREE1_NAME, owner="")

        host = LOCALHOST
        resources.update(reserved=host)

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        locked_resource, = resources
        self.assertEquals(locked_resource.name, self.FREE1_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.FREE1_NAME, locked_resource.name))

        self.assertIsInstance(locked_resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 locked_resource.__class__.__name__))

        resources = descriptor.type.DATA_CLASS.objects.filter(
                                                         name=self.FREE1_NAME)

        resources = [resource for resource in resources
                     if resource.owner.split(HOST_PORT_SEPARATOR)[0] == host]

        self.assertEquals(len(resources), 1, "Expected 1 locked resource "
                          "with name %r and owner %r in DB, found %d"
                          % (self.FREE1_NAME, host, resources_num))

    def test_lock_reserved_for_other_resource(self):
        """Try to lock a resource that reserved for other.

        * Validates the DB initial state.
        * Update the reserved flag and save the resource.
        * Tries to Lock the resource, using resource client.
        * Validates that a ResourceUnavailableError is raised.
        """
        resources = self.get_resource(self.FREE1_NAME, owner="")
        resources.update(reserved='other')

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        self.assertRaises(ResourceUnavailableError,
                          self.client._lock_resources,
                          descriptors=[descriptor],
                          timeout=self.LOCK_TIMEOUT)

    def test_lock_release_available_resource(self):
        """Lock existing resource, release it & validate the success.

        * Validates the DB initial state.
        * Locks an existing resource, using resource client.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates that there is 1 locked resource with this name in DB.
        * Releases a locked resource, using resource client.
        * Validates that the above resource is now available.
        """
        self.get_resource(self.FREE1_NAME, owner="")

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.FREE1_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.FREE1_NAME, resource.name))

        self.assertIsInstance(resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 resource.__class__.__name__))

        resources_num = \
            descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                           name=self.FREE1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.FREE1_NAME, resources_num))

        self.client._release_resources(resources=[resource])

        self.get_resource(self.FREE1_NAME, owner="")

    def test_lock_multiple_available_resources_and_release_them(self):
        """Lock 2 available resources, release them & validate the success.

        * Validates the DB initial state.
        * Locks 2 available resources, using resource client.
        * Validates 2 resources returned.
        * Validates the name of the returned resources.
        * Validates the type of the returned resources.
        * Validates that the above resources are not available.
        * Releases the above 2 locked resources, using resource client.
        * Validates that the above resources are now available.
        """
        self.get_resource(self.FREE1_NAME, owner="")
        self.get_resource(self.FREE2_NAME, owner="")

        descriptors = [Descriptor(DemoResource, name=self.FREE1_NAME),
                       Descriptor(DemoResource, name=self.FREE2_NAME)]
        resources = self.client._lock_resources(descriptors=descriptors,
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 2, "Expected list with 2 "
                          "resources in it but found %d" % resources_num)

        for resource, descriptor in izip(resources, descriptors):
            expected_name = descriptor.properties['name']
            self.assertEquals(expected_name, resource.name,
                              "Expected resource with name %r but got %r"
                              % (expected_name, resource.name))

            self.assertIsInstance(resource, descriptor.type,
                                  "Expected resource of type %r, but got %r"
                                  % (descriptor.type.__name__,
                                     resource.__class__.__name__))

            resources_num = descriptor.type.DATA_CLASS.objects.filter(
 ~Q(owner=""), name=expected_name).count()

            self.assertEquals(resources_num, 1, "Expected 1 locked "
                              "resource with name %r in DB, found %d"
                              % (expected_name, resources_num))

        self.client._release_resources(resources=resources)

        for locked_name in (self.FREE1_NAME, self.FREE2_NAME):
            self.get_resource(locked_name, owner="")

    def test_lock_non_existing_name_resource(self):
        """Try to Lock a resource that dosen't exist & validate failure.

        * Validates the DB initial state.
        * Tries to Lock a resource that dosen't exist, using resource client.
        * Validates that a ResourceDoesNotExistError is raised.
        """
        resources_num = DemoResourceData.objects.filter(
                                        name=self.NON_EXISTING_NAME1).count()

        self.assertEqual(resources_num, 0,
                         "Expected 0 resource with name %r in DB, found %d"
                         % (self.NON_EXISTING_NAME1, resources_num))

        descriptor = Descriptor(DemoResource, name=self.NON_EXISTING_NAME1)
        self.assertRaises(ResourceDoesNotExistError,
                          self.client._lock_resources,
                          descriptors=[descriptor],
                          timeout=self.LOCK_TIMEOUT)

    def test_lock_non_existing_field_resource(self):
        """Try to Lock using a field that dosen't exist & validate failure.

        * Validates the DB initial state.
        * Tries to Lock a resource using a property that dosen't exist.
        * Validates that a ResourceDoesNotExistError is raised.
        """
        self.get_resource(self.FREE1_NAME)

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        descriptor.properties[self.NON_EXISTING_FIELD] = 0

        self.assertRaises(ServerError,
                          self.client._lock_resources,
                          descriptors=[descriptor],
                          timeout=self.LOCK_TIMEOUT)

    def test_lock_already_locked_resource(self):
        """Lock an already locked resource & validate failure.

        * Validates the DB initial state.
        * Locks an already locked resource, using resource client.
        * Validates a ResourceUnavailableError is raised.
        """
        resources_num = DemoResourceData.objects.filter(~Q(owner=""),
                                  name=self.LOCKED1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB found %d"
                          % (self.LOCKED1_NAME, resources_num))

        descriptor = Descriptor(DemoResource, name=self.LOCKED1_NAME)
        self.assertRaises(ResourceUnavailableError,
                          self.client._lock_resources,
                          descriptors=[descriptor],
                          timeout=self.LOCK_TIMEOUT)

    def test_lock_unavailable_resource_timeout(self):
        """Lock an already locked resource & validate failure after timeout.

        * Validates the DB initial state.
        * Locks an already locked resource, using resource client.
        * Validates a ResourceUnavailableError is raised.
        * Validates 'lock_resources' duration is greater then the timeout.
        """
        resources_num = DemoResourceData.objects.filter(~Q(owner=""),
                                  name=self.LOCKED1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB found %d"
                          % (self.LOCKED1_NAME, resources_num))

        descriptor = Descriptor(DemoResource, name=self.LOCKED1_NAME)

        start_time = time.time()
        self.assertRaises(ResourceUnavailableError,
                          self.client._lock_resources,
                          descriptors=[descriptor],
                          timeout=self.LOCK_TIMEOUT)

        duration = time.time() - start_time
        self.assertGreaterEqual(duration, self.LOCK_TIMEOUT, "Waiting for "
                                "resources took %.2f seconds, but should take "
                                "at least %d" % (duration, self.LOCK_TIMEOUT))

    def _test_wait_for_unavailable_resource(self, timeout, release_time):
        """Lock a locked resource, wait for it to release & validate success.

        * Validates the DB initial state.
        * Locks a resource, using resource client.
        * Executes a thread that wait 2 seconds and then release the resource.
        * Locks the resource above, using another resource client.
        * Validates resources locking time is greater then the release time.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates that there is 1 locked resource with this name in DB.

        Args:
            timeout (number): seconds to wait for resource. None - no timeout.
            release_time (number): seconds to wait before releasing the locked
                resource.
        """
        def release_locked_resource(client, resource):
            """Wait and release a resource."""
            time.sleep(release_time)
            client._release_resources(resources=[resource])

        self.get_resource(self.FREE1_NAME, owner="")

        new_client = ClientResourceManager(LOCALHOST)
        new_client.connect()

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        resources = new_client._lock_resources(descriptors=[descriptor],
                                               timeout=self.LOCK_TIMEOUT)

        releaser_thread = Thread(target=release_locked_resource,
                                 args=(new_client, resources[0]))
        releaser_thread.start()

        start_time = time.time()
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=timeout)
        duration = time.time() - start_time
        self.assertGreater(ClientResourceManager.REPLY_OVERHEAD_TIME,
                           duration - release_time, "Although Resource was "
                           "locked for %d seconds, we manage to lock it after "
                           "%.2f seconds, which is less than expected or above"
                           " the overhead time of %d seconds" % (release_time,
                            duration, new_client.REPLY_OVERHEAD_TIME))

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.FREE1_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.FREE1_NAME, resource.name))

        self.assertIsInstance(resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 resource.__class__.__name__))

        resources_num = \
            descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                           name=self.FREE1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.FREE1_NAME, resources_num))

    def test_wait_for_unavailable_resource_with_timeout(self):
        """Wait for a locked resource with timeout & validate success."""
        self._test_wait_for_unavailable_resource(self.LOCK_TIMEOUT, 2)

    def test_lock_multiple_matches(self):
        """Lock a resource, parameters matching more then one result.

        * Validates the DB initial state.
        * Locks a resource using parameters that match more than one resource,
          using resource client.
        * Validates only one resource returned.
        * Validates the returned resource is now marked as locked.
        * Validates there is still 1 available resource with same parameters.
        """
        common_parameters = {'ip_address': "1.1.1.1"}
        resources_num = DemoResourceData.objects.filter(owner="",
                                                **common_parameters).count()

        self.assertEquals(resources_num, 2, "Expected 2 available "
                          "resources with parameters %r in DB found %d"
                          % (common_parameters, resources_num))

        descriptor = Descriptor(DemoResource, **common_parameters)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        locked_resource_name = resources[0].name

        resources_num = descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                  name=locked_resource_name).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (locked_resource_name, resources_num))

        resources_num = descriptor.type.DATA_CLASS.objects.filter(owner="",
                                    **common_parameters).count()

        self.assertGreaterEqual(resources_num, 1, "Expected at least 1 "
                                "available resource with the same parameters "
                                "in DB found %d" % resources_num)

    def test_lock_available_and_locked_resources(self):
        """Lock both available and locked resources & validate failure.

        * Validates the DB initial state.
        * Locks both available and locked resources, using resource client.
        * Validates a ResourceUnavailableError is raised.
        * Validates the locked resource is still locked.
        * Validates the available resource is still available.
        """
        self.get_resource(name=self.FREE1_NAME, owner="")

        resources_num = DemoResourceData.objects.filter(~Q(owner=""),
                                            name=self.LOCKED1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB found %d"
                          % (self.LOCKED1_NAME, resources_num))

        descriptors = [Descriptor(DemoResource, name=self.FREE1_NAME),
                       Descriptor(DemoResource, name=self.LOCKED1_NAME)]

        self.assertRaises(ResourceUnavailableError,
                          self.client._lock_resources,
                          descriptors=descriptors,
                          timeout=self.LOCK_TIMEOUT)

        resources_num = DemoResourceData.objects.filter(~Q(owner=""),
                                  name=self.LOCKED1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.LOCKED1_NAME, resources_num))

        self.get_resource(name=self.FREE1_NAME, owner="")

    def test_lock_release_complex_resource(self):
        """Lock existing complex resource, release it & validate the success.

        * Validates the DB initial state.
        * Locks an existing complex resource, using resource client.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates the above resource and it sub-resources are now locked.
        * Releases a locked resource, using resource client.
        * Validates the above resource and it sub-resources are now available.
        """
        resources = DemoComplexResourceData.objects.filter(
                                                       name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEqual(resources_num, 1, "Expected 1 complex "
                         "resource with name %r in DB, found %d"
                         % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        self.assertTrue(resource.is_available(), "Expected available "
                        "complex resource with name %r in DB, found %d"
                        % (self.COMPLEX_NAME, resources_num))

        descriptor = Descriptor(DemoComplexResource, name=self.COMPLEX_NAME)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.COMPLEX_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.COMPLEX_NAME, resource.name))

        self.assertIsInstance(resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 resource.__class__.__name__))

        resources = descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                                   name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        for sub_resource in resource.get_sub_resources():
            self.assertFalse(sub_resource.is_available(),
                             "Sub-resource %r should be locked but "
                             "found available" % sub_resource.name)

        resource_instace = DemoResource(resources.get())
        self.client._release_resources(resources=[resource_instace])

        resources = DemoComplexResourceData.objects.filter(
                                                       name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEqual(resources_num, 1, "Expected 1 complex "
                         "resource with name %r in DB, found %d"
                         % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        self.assertTrue(resource.is_available(), "Expected available "
                        "complex resource with name %r in DB, found %d"
                        % (self.COMPLEX_NAME, resources_num))

    def test_lock_complex_resource_and_sub_resource(self):
        """Lock a complex resource and it sub-resource & validate failure.

        * Validates the DB initial state.
        * Locks a complex resource and one of it sub resources.
        * Validates a ResourceUnavailableError is raised.
        """
        resources = DemoComplexResourceData.objects.filter(
                                                       name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEqual(resources_num, 1, "Expected 1 complex "
                         "resource with name %r in DB, found %d"
                         % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        self.assertTrue(resource.is_available(), "Expected available "
                        "complex resource with name %r in DB, found %d"
                        % (self.COMPLEX_NAME, resources_num))

        sub_resource = resource.demo1
        descriptors = [Descriptor(DemoComplexResource, name=self.COMPLEX_NAME),
                       Descriptor(DemoResource, name=sub_resource.name)]

        self.assertRaises(ResourceUnavailableError,
                          self.client._lock_resources,
                          descriptors=descriptors,
                          timeout=self.LOCK_TIMEOUT)

    def test_release_free_resource(self):
        """Release a free resource & validate failure.

        * Validates the DB initial state.
        * Release a free resource, using resource client.
        * Validates a ResourceAlreadyAvailableError is raised.
        """
        resources = DemoResource(
                         self.get_resource(self.FREE1_NAME, owner="").get())

        with self.assertRaises(ResourceReleaseError) as cm:
            self.client._release_resources(resources=[resources])

        error_list = cm.exception.errors
        num_of_errors = len(error_list)

        self.assertEqual(num_of_errors, 1, "Expected 1 inner error in "
                         "ResourceReleaseError, found %d" % num_of_errors)

        self.assertIn(self.FREE1_NAME, error_list, "%r wasn't found "
                      "in the error list" % self.FREE1_NAME)

        error_code = error_list[self.FREE1_NAME][0]
        self.assertEqual(error_code, ResourceAlreadyAvailableError.ERROR_CODE,
                         "Resource %r raised error of type %r, expected %r" %
                         (self.FREE1_NAME, error_code,
                          ResourceAlreadyAvailableError.ERROR_CODE))

    def test_release_non_existing_resource(self):
        """Release a non existing resource & validate failure.

        * Validates the DB initial state.
        * Create an instance of a non-existing resource.
        * Release a free resource, using resource client.
        * Validates a ResourceDoesNotExistError is raised.
        """
        resources_num = DemoResourceData.objects.filter(
                                        name=self.NON_EXISTING_NAME1).count()

        self.assertEqual(resources_num, 0, "Expected 1 available "
                         "resource with name %r in DB, found %d"
                         % (self.NON_EXISTING_NAME1, resources_num))

        non_existing_resource = DemoResource(
                             DemoResourceData(name=self.NON_EXISTING_NAME1))

        with self.assertRaises(ResourceReleaseError) as cm:
            self.client._release_resources(resources=[non_existing_resource])

        error_list = cm.exception.errors
        num_of_errors = len(error_list)

        self.assertEqual(num_of_errors, 1, "Expected 1 inner error in "
                         "ResourceReleaseError, found %d" % num_of_errors)

        self.assertIn(self.NON_EXISTING_NAME1, error_list, "%r wasn't found "
                      "in the error list" % self.NON_EXISTING_NAME1)

        error_code = error_list[self.NON_EXISTING_NAME1][0]
        self.assertEqual(error_code, ResourceDoesNotExistError.ERROR_CODE,
                         "Resource %r raised error of type %r, expected %r" %
                         (self.NON_EXISTING_NAME1, error_code,
                          ResourceDoesNotExistError.ERROR_CODE))

    def test_release_resources_multiple_failures(self):
        """Release a free and a non-existing resources & validate failure.

        * Validates the DB initial state.
        * Create an instance of a non-existing resource.
        * Releases a free and a non-existing resources, using resource client.
        * Validates a ResourceAlreadyAvailableError was raised for the free
            resource.
        * Validates a ResourceDoesNotExistError was raised for the non-existing
            resource.
        """
        resources = DemoResource(
                         self.get_resource(self.FREE1_NAME, owner="").get())

        resources_num = DemoResourceData.objects.filter(
                                        name=self.NON_EXISTING_NAME1).count()

        self.assertEqual(resources_num, 0, "Expected 1 available "
                         "resource with name %r in DB, found %d"
                         % (self.NON_EXISTING_NAME1, resources_num))

        non_existing_resource = DemoResource(
                             DemoResourceData(name=self.NON_EXISTING_NAME1))

        resources = [resources] + [non_existing_resource]

        with self.assertRaises(ResourceReleaseError) as cm:
            self.client._release_resources(resources=resources)

        error_list = cm.exception.errors
        num_of_errors = len(error_list)

        self.assertEqual(num_of_errors, 2, "Expected 2 inner errors in "
                         "ResourceReleaseError, found %d" % num_of_errors)

        resources_error_names = [self.FREE1_NAME, self.NON_EXISTING_NAME1]
        resources_error_codes = [ResourceAlreadyAvailableError.ERROR_CODE,
                                 ResourceDoesNotExistError.ERROR_CODE]

        for name, expected_code in izip(resources_error_names,
                                        resources_error_codes):

            self.assertIn(name, error_list, "%r wasn't found "
                          "in the error list" % name)

            error_code = error_list[name][0]
            self.assertEqual(error_code, expected_code, "Resource %r "
                             "raised error of type %r, expected %r" %
                             (name, error_code, expected_code))

    def test_one_lock_other_release(self):
        """Release a resource that locked by other client & validate failure.

        * Validates the DB initial state.
        * Releases a locked resource which locked by other user,
          using a resource client.
        * Validates a ResourcePermissionError is raised.
        * Validates the resource is still locked.
        """
        resources = DemoResourceData.objects.filter(~Q(owner=""),
                                                    name=self.LOCKED1_NAME)
        resources_num = resources.count()

        self.assertEqual(resources_num, 1, "Expected 1 locked "
                         "resource with name %r in DB, found %d"
                         % (self.LOCKED1_NAME, resources_num))

        resource = DemoResource(resources.get())
        with self.assertRaises(ResourceReleaseError) as cm:
            self.client._release_resources(resources=[resource])

        resources_num = DemoResourceData.objects.filter(~Q(owner=""),
                                  name=self.LOCKED1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.FREE1_NAME, resources_num))

        error_list = cm.exception.errors
        num_of_errors = len(error_list)

        self.assertEqual(num_of_errors, 1, "Expected 1 inner errors in "
                         "ResourceReleaseError, found %d" % num_of_errors)

        self.assertIn(self.LOCKED1_NAME, error_list, "%r wasn't found "
                      "in the error list" % self.LOCKED1_NAME)

        error_code, _ = error_list[self.LOCKED1_NAME]
        self.assertEqual(error_code, ResourcePermissionError.ERROR_CODE,
                         "Resource %r raised error of type %r, expected %r" %
                         (self.LOCKED1_NAME, error_code,
                          ResourcePermissionError.ERROR_CODE))

    def test_disconnection_after_locking_available_resource(self):
        """Lock a resource, disconnect from server & validate its release.

        * Validates the DB initial state.
        * Locks an existing resource, using resource client.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates that there is 1 locked resource with this name in DB.
        * Disconnect from resource manager server.
        * Validates that the above resource is now available.
        """
        self.get_resource(self.FREE1_NAME, owner="")

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.FREE1_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.FREE1_NAME, resource.name))

        self.assertIsInstance(resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 resource.__class__.__name__))

        resources_num = \
            descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                           name=self.FREE1_NAME).count()

        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.FREE1_NAME, resources_num))

        locked_resource = self.FREE1_NAME
        self.client.disconnect()
        time.sleep(self.CLEANUP_TIME)

        self.get_resource(locked_resource, owner="")

    def test_disconnection_after_locking_available_complex_resource(self):
        """Lock complex resource, disconnect and validate its release.

        * Validates the DB initial state.
        * Locks an existing complex resource, using resource client.
        * Validates that 1 resource returned.
        * Validates the name of the returned resource.
        * Validates the type of the returned resource.
        * Validates the above resource and it sub-resources are now locked.
        * Disconnect from resource manager server.
        * Validates the above resource and it sub resources are now available.
        """
        resources = DemoComplexResourceData.objects.filter(
                                                       name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEqual(resources_num, 1, "Expected 1 complex "
                         "resource with name %r in DB, found %d"
                         % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        self.assertTrue(resource.is_available(), "Expected available "
                        "complex resource with name %r in DB, found %d"
                        % (self.COMPLEX_NAME, resources_num))

        descriptor = Descriptor(DemoComplexResource, name=self.COMPLEX_NAME)
        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.COMPLEX_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.COMPLEX_NAME, resource.name))

        self.assertIsInstance(resource, descriptor.type,
                              "Expected resource of type %r, but got %r"
                              % (descriptor.type.__name__,
                                 resource.__class__.__name__))

        resources = descriptor.type.DATA_CLASS.objects.filter(~Q(owner=""),
                                                   name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected 1 locked "
                          "resource with name %r in DB, found %d"
                          % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        for sub_resource in resource.get_sub_resources():
            self.assertFalse(sub_resource.is_available(),
                             "Sub-resource %r should be locked but "
                             "found available" % sub_resource.name)

        self.client.disconnect()
        time.sleep(self.CLEANUP_TIME)

        resources = DemoComplexResourceData.objects.filter(owner="",
                                                       name=self.COMPLEX_NAME)

        resources_num = len(resources)
        self.assertEqual(resources_num, 1, "Expected 1 complex "
                         "resource with name %r in DB, found %d"
                         % (self.COMPLEX_NAME, resources_num))

        resource, = resources
        self.assertTrue(resource.is_available(), "Expected available "
                        "complex resource with name %r in DB, found %d"
                        % (self.COMPLEX_NAME, resources_num))

    def test_encounter_unknown_user(self):
        """Lock resource by a non identified user & validate failure.

        * Validates the DB initial state.
        * Locks an existing resource, by client which doesn't exist in the DB.
        * Validates that an error is raised.
        """
        User.objects.all().delete()
        self.get_resource(self.FREE1_NAME)

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)

        with self.assertRaises(UnknownUserError):
            self.client._lock_resources(descriptors=[descriptor],
                                        timeout=self.LOCK_TIMEOUT)

    def test_locking_resource_with_a_matching_group(self):
        """Lock resource with a valid group & validate success.

        * Validates the DB initial state.
        * Locks resource with no group, which means that the resource is
          available to everyone.
        * Validates that the resource was locked successfully.
        """
        self.get_resource(self.FREE1_NAME)

        descriptor = Descriptor(DemoResource, name=self.FREE1_NAME)

        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.FREE1_NAME,
                          "Expected resource with name %r but got %r"
                          % (self.FREE1_NAME, resource.name))

        expected_host = LOCALHOST
        actual_host, _ = resource.owner.split(":")
        self.assertEquals(actual_host, expected_host,
                          "Expected 1 locked resource with owner %r in DB. "
                          "Got %r" % (expected_host, actual_host))

    def test_locking_other_group_resource(self):
        """Lock another group resource & validate failure.

        * Validates the DB initial state.
        * Locks an existing resource, by a client that is in a different group
          than the resource's group.
        * Validates that an error is raised.
        """
        self.get_resource(self.OTHER_GROUP_RESOURCE)

        descriptor = Descriptor(DemoResource, name=self.OTHER_GROUP_RESOURCE)

        with self.assertRaises(ResourceDoesNotExistError):
            self.client._lock_resources(descriptors=[descriptor],
                                        timeout=self.LOCK_TIMEOUT)

    def test_locking_resource_with_group_none(self):
        """Lock resource with no group & validate success.

        * Validates the DB initial state.
        * Locks resource with no group, which means that the resource is
          available to everyone.
        * Validates that the resource was locked successfully.
        """
        self.get_resource(self.NO_GROUP_RESOURCE)

        descriptor = Descriptor(DemoResource, name=self.NO_GROUP_RESOURCE)

        resources = self.client._lock_resources(descriptors=[descriptor],
                                                timeout=self.LOCK_TIMEOUT)

        resources_num = len(resources)
        self.assertEquals(resources_num, 1, "Expected list with 1 "
                          "resource in it but found %d" % resources_num)

        resource, = resources
        self.assertEquals(resource.name, self.NO_GROUP_RESOURCE,
                          "Expected resource with name %r but got %r"
                          % (self.NO_GROUP_RESOURCE, resource.name))

        expected_host = LOCALHOST
        actual_host, _ = resource.owner.split(":")
        self.assertEquals(actual_host, expected_host,
                          "Expected 1 locked resource with owner %r in DB. "
                          "Got %r" % (expected_host, actual_host))

    def test_update_fields(self):
        """Test the UpdateFields message.

        * Checks a value in the DB.
        * Requests a change in the value.
        * Validates that the change occurred.
        """
        # Validate initial state.
        resource1 = DemoResourceData.objects.get(name='available_resource1')
        resource2 = DemoResourceData.objects.get(name='available_resource2')
        self.assertEquals(resource1.version, 1,
                          "Unexpected initial resource1 state (%r != %r)" %
                          (resource1.version, 1))
        self.assertEquals(resource2.version, 2,
                          "Unexpected initial resource2 state (%r != %r)" %
                          (resource2.version, 2))

        # Change version of a single resource.
        self.client.update_fields(DemoResourceData,
                                  {'name': 'available_resource1'},
                                  version=3)

        # Validate change.
        resource1 = DemoResourceData.objects.get(name='available_resource1')
        resource2 = DemoResourceData.objects.get(name='available_resource2')
        self.assertEquals(resource1.version, 3,
                          "Failed to change fields in resource1 (%r != %r)" %
                          (resource1.version, 3))
        self.assertEquals(resource2.version, 2,
                          "Unexpected change fields in resource2 (%r != %r)" %
                          (resource2.version, 2))

        # Change version of all resources.
        self.client.update_fields(DemoResourceData,
                                  version=4)

        # Validate change.
        resource1 = DemoResourceData.objects.get(name='available_resource1')
        resource2 = DemoResourceData.objects.get(name='available_resource2')
        self.assertEquals(resource1.version, 4,
                          "Failed to change fields in resource1 (%r != %r)" %
                          (resource1.version, 4))
        self.assertEquals(resource2.version, 4,
                          "Failed to change fields in resource2 (%r != %r)" %
                          (resource2.version, 4))

    def test_keeping_locked_resources(self):
        """Test work with keeping previously locked resources.

        * Checks that the client keeps the resources.
        * Checks that the client uses previously locked resources.
        * Checks that the client doesn't initialize them again.
        * Checks that the client doesn't finalize them in between.
        * Checks that the client releases them when their not needed anymore.
        """
        self.client.keep_resources = True

        requests = [ResourceRequest('res1', DemoResource,
                                    name=self.FREE1_NAME)]

        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Make sure the client has no locked resources
        self.assertEqual(len(self.client.locked_resources), 0)
        # Request the free resource
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource1 = resources.values()[0]
        self.client.release_resources(resources)
        # Check that the resource is saved in the client
        self.assertEqual(self.client.locked_resources, [resource1])
        self.assertEqual(resource1.name, db_res.name)
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the locked resource was initialized
        self.assertTrue(db_res.initialization_flag)
        # Check that the locked resource wasn't finalized
        self.assertFalse(db_res.finalization_flag)

        db_res.initialization_flag = False
        db_res.save()
        # Make a similar request
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource2 = resources.values()[0]
        self.client.release_resources(resources)
        # Check that the resource is the only saved resource in the client
        self.assertEqual(self.client.locked_resources, [resource2])
        # Check that it's the same resource that was saved before
        self.assertTrue(resource1 is resource2)
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the resource wasn't initialized again or finalized
        self.assertFalse(db_res.initialization_flag)
        self.assertFalse(db_res.finalization_flag)

        requests = [ResourceRequest('res2', DemoResource,
                                    name=self.FREE2_NAME)]

        # Make a non-similar request
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource3 = resources.values()[0]
        self.client.release_resources(resources)
        # Check that the new resource is the only saved resource in the client
        self.assertEqual(self.client.locked_resources, [resource3])
        # Check that it's not the same resource from before
        self.assertNotEqual(resource1.name, resource3.name)
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the previous resource was finalized
        self.assertTrue(db_res.finalization_flag)

        self.client.disconnect()
        db_res = self.get_resource(self.FREE2_NAME)[0]
        # Check that the new resource was finalized after disconnection
        self.assertTrue(db_res.finalization_flag)

    def test_releasing_locked_resources_on_disconnect(self):
        """Test that disconnecting the client releases the locked resources.

        Client disconnection happens after all the tests are done.
        """
        self.client.keep_resources = True

        requests = [ResourceRequest('res1', DemoResource,
                                    name=self.FREE1_NAME)]

        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Make sure the client has no locked resources
        self.assertEqual(len(self.client.locked_resources), 0)
        # Request the free resource
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource1 = resources.values()[0]
        # Check that the resource is saved in the client
        self.assertEqual(self.client.locked_resources, [resource1])
        # Check that the resource was not finalized yet
        self.assertFalse(db_res.finalization_flag)

        self.client.disconnect()
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the new resource was finalized after disconnection
        self.assertTrue(db_res.finalization_flag)

    def test_releasing_locked_resources_on_dirty(self):
        """Test that the client doesn't keep dirty resources.

        Resources are marked as dirty when there was an error during the test.
        """
        self.client.keep_resources = True

        requests = [ResourceRequest('res1', DemoResource,
                                    name=self.FREE1_NAME)]

        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Make sure the client has no locked resources
        self.assertEqual(len(self.client.locked_resources), 0)
        # Request the free resource
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        self.client.release_resources(resources, dirty=True)
        # Check that the resource is saved in the client
        self.assertEqual(self.client.locked_resources, [])
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the resource was finalized
        self.assertTrue(db_res.finalization_flag)

    def test_not_keeping_locked_resources(self):
        """Test work without keeping the locked resources.

        * Checks that the client doesn't keeps the resources.
        * Checks that the client doesn't use previously locked resources.
        * Checks that the client finalizes them in between.
        """
        self.client.keep_resources = False

        requests = [ResourceRequest('res1', DemoResource,
                                    name=self.FREE1_NAME)]

        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Make sure the client has no locked resources
        self.assertEqual(len(self.client.locked_resources), 0)
        # Request the free resource
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource1 = resources.values()[0]
        self.client.release_resources(resources)
        # Check that the resource isn't saved in the client
        self.assertEqual(self.client.locked_resources, [])
        self.assertEqual(resource1.name, db_res.name)
        db_res = self.get_resource(self.FREE1_NAME)[0]
        # Check that the resource was initialized
        self.assertTrue(db_res.initialization_flag)
        # Check that the resource was finalized
        self.assertTrue(db_res.finalization_flag)

        # Make a similar request
        resources = self.client.request_resources(requests, use_previous=True)
        # Check that it locked 1 resource
        self.assertEqual(len(resources), 1)
        resource2 = resources.values()[0]
        self.client.release_resources(resources)
        # Check that the resource isn't saved in the client
        self.assertEqual(self.client.locked_resources, [])
        # Check that it's not the same resource that was saved before
        self.assertFalse(resource1 is resource2)


if __name__ == '__main__':
    django.setup()
    colored_main()
