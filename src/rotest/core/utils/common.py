"""Common result utils."""
# pylint: disable=dangerous-default-value
from termcolor import colored

from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock
from rotest.core.suite import TestSuite
from rotest.common.constants import MAGENTA
from rotest.core.test_filter import match_tags
from rotest.core.flow_component import ClassInstantiator


HIERARCHY_SEPARATOR = " |  "


def print_test_instance(test_name, depth, tag_filter, test_tags, all_tags):
    """Print test, including if it passes the filters or not.

    Args:
        test_name (str): name of the test.
        depth (number): depth of the current test in the tree.
        tag_filter (str): boolean expression composed of tags and boolean
            operators, e.g. "Tag1 and (Tag2 or Tag3 or Tag3)".
        test_tags (list): original tags list of the test.
        all_tags (list): accumulated tags for the test.
    """
    test_format = " ".join([HIERARCHY_SEPARATOR * depth,
                           test_name, str(test_tags)])

    if (tag_filter is not None and
        match_tags(all_tags, tag_filter) is True):

        print colored(test_format, MAGENTA)

    else:
        print test_format


def print_test_hierarchy(test, tag_filter, tags=[], depth=0):
    """Recursively print the test's hierarchy tree and tags.

    Args:
        test (object): test to print.
        tag_filter (str): boolean expression composed of tags and boolean
            operators, e.g. "Tag1 and (Tag2 or Tag3 or Tag3)".
        tags (list): tags list to be verified against the tag_filter,
            e.g. ["Tag1", "Tag2"].
        depth (number): depth of the current test in the tree.
    """
    tags = tags[:]

    actual_test = test
    if isinstance(test, ClassInstantiator):
        actual_test = test.component_class

    if issubclass(actual_test, TestCase):
        tags.extend(test.TAGS)
        for method_name in test.load_test_method_names():
            test_name = test.get_name(method_name)
            method_tags = tags + test_name.split(".")
            print_test_instance(test_name, depth, tag_filter,
                                test.TAGS, method_tags)

        return

    if issubclass(actual_test, TestBlock):
        print HIERARCHY_SEPARATOR * depth, test.get_name()
        return

    tags.extend(actual_test.TAGS)
    if issubclass(actual_test, TestFlow):
        test_name = test.get_name()
        print_test_instance(test_name, depth, tag_filter,
                            actual_test.TAGS, tags)

    tags.append(actual_test.__name__)

    if issubclass(actual_test, TestSuite) is True:
        sub_tests = test.components
        print HIERARCHY_SEPARATOR * depth, test.get_name(), test.TAGS

    else:
        sub_tests = actual_test.blocks

    for sub_test in sub_tests:
        print_test_hierarchy(sub_test, tag_filter, tags, depth + 1)
