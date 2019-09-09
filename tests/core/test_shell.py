"""Test Rotest's TestCase class behavior."""
# pylint: disable=missing-docstring,unused-argument,protected-access
# pylint: disable=no-member,no-self-use,too-many-public-methods,invalid-name
from __future__ import absolute_import

from rotest.core import request, BlockInput
from rotest.management.models.ut_resources import DemoResource
from rotest.management.models.ut_models import DemoResourceData
from rotest.management.utils.shell import run_test, create_result

from tests.core.utils import (BasicRotestUnitTest, MockCase, MockBlock,
                              MockFlow, MockTestSuite)

RESOURCE_NAME = 'available_resource1'


class TempResourceCase(MockCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    def test_method(self):
        self.assertEqual(self.test_resource.name, RESOURCE_NAME)


class TempResourceSuite(MockTestSuite):
    """Inherit class and override resources requests."""
    __test__ = False

    components = [TempResourceCase]


class TempResourceBlock(MockBlock):
    """Inherit class and override resources requests."""
    __test__ = False

    test_resource = BlockInput()

    def test_method(self):
        self.assertEqual(self.test_resource.name, RESOURCE_NAME)


class TempResourceFlow(MockFlow):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    blocks = [TempResourceBlock]


class TestShell(BasicRotestUnitTest):
    """Test Rotest shell functionality."""
    fixtures = ['resource_ut.json']

    DEMO_RESOURCE_NAME = 'test_resource'

    def setUp(self):
        create_result()

    def test_case_supplying_config(self):
        config = {'some': 'value'}
        test = run_test(TempResourceCase, config=config)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.config, config, 'Test ran with the wrong config')

    def test_case_supplying_resource_via_kwargs(self):
        resource = DemoResource(
            data=DemoResourceData.objects.get(name=RESOURCE_NAME))

        test = run_test(TempResourceCase, test_resource=resource)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.test_resource, resource,
                         "Test didn't get the supplied resource")

    def test_case_not_supplying_any_resource(self):
        test = run_test(TempResourceCase)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

    def test_block_supplying_config(self):
        config = {'some': 'value'}
        resource = DemoResource(
            data=DemoResourceData.objects.get(name=RESOURCE_NAME))

        test = run_test(TempResourceBlock, config=config,
                        test_resource=resource)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.config, config, 'Test ran with the wrong config')

    def test_block_supplying_resource_via_kwargs(self):
        resource = DemoResource(
            data=DemoResourceData.objects.get(name=RESOURCE_NAME))

        test = run_test(TempResourceBlock, test_resource=resource)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.test_resource, resource,
                         "Test didn't get the supplied resource")

    def test_block_not_supplying_any_resource(self):
        test = run_test(TempResourceBlock)
        self.assertFalse(test.data.success,
                         'Block passed even though no resource was supplied')

    def test_flow_supplying_config(self):
        config = {'some': 'value'}
        test = run_test(TempResourceFlow, config=config)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.config, config, "Test ran with the wrong config")

    def test_flow_supplying_resource_via_kwargs(self):
        resource = DemoResource(
            data=DemoResourceData.objects.get(name=RESOURCE_NAME))

        test = run_test(TempResourceFlow, test_resource=resource)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.test_resource, resource,
                         "Test didn't get the supplied resource")

    def test_flow_not_supplying_any_resource(self):
        test = run_test(TempResourceFlow)
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

    def test_suite_supplying_config(self):
        config = {'some': 'value'}
        test = run_test(TempResourceSuite, config=config)._tests[0]
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.config, config, "Test ran with the wrong config")

    def test_suite_supplying_resource_via_kwargs(self):
        resource = DemoResource(
            data=DemoResourceData.objects.get(name=RESOURCE_NAME))

        test = run_test(TempResourceSuite, test_resource=resource)._tests[0]
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')

        self.assertEqual(test.test_resource, resource,
                         "Test didn't get the supplied resource")

    def test_suite_not_supplying_any_resource(self):
        test = run_test(TempResourceSuite)._tests[0]
        self.assertTrue(test.data.success,
                        'Case failed when it should have succeeded')
