"""Common result utils."""
# pylint: disable=dangerous-default-value
from __future__ import print_function, absolute_import

import json
from future.builtins import str

from attrdict import AttrDict
from jsonschema import validate

from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock
from rotest.core.suite import TestSuite
from rotest.core.filter import match_tags


PASS_ALL_FILTER = "*"
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

    Returns:
        bool. whether the test passed the filter or not.
    """
    test_format = " ".join([HIERARCHY_SEPARATOR * depth,
                           test_name, str(test_tags)])
    print(test_format)

    return tag_filter is not None and match_tags(all_tags, tag_filter)


def print_test_hierarchy(test, tag_filter, tags=[], depth=0):
    """Recursively print the test's hierarchy tree and tags.

    Args:
        test (rotest.core.AbstractTest): test to print.
        tag_filter (str): boolean expression composed of tags and boolean
            operators, e.g. "Tag1 and (Tag2 or Tag3 or Tag3)".
        tags (list): tags list to be verified against the tag_filter,
            e.g. ["Tag1", "Tag2"].
        depth (number): depth of the current test in the tree.
    """
    tags = tags[:]

    actual_test = test
    if issubclass(actual_test, TestCase):
        tags.extend(test.TAGS)
        for method_name in test.load_test_method_names():
            test_name = test.get_name(method_name)
            method_tags = tags + test_name.split(".")
            print_test_instance(test_name, depth, tag_filter,
                                test.TAGS, method_tags)

    elif issubclass(actual_test, TestBlock):
        print_test_instance(test.get_name(), depth, tag_filter, [], tags)

    elif issubclass(actual_test, TestSuite):
        tags.extend(actual_test.TAGS)
        tags.append(actual_test.__name__)
        sub_tests = test.components
        print(HIERARCHY_SEPARATOR * depth, test.get_name(), test.TAGS)
        for sub_test in sub_tests:
            print_test_hierarchy(sub_test, tag_filter, tags, depth + 1)

    elif issubclass(actual_test, TestFlow):
        tags.extend(actual_test.TAGS)
        tags.append(actual_test.__name__)
        test_name = test.get_name()
        is_colored = print_test_instance(test_name, depth, tag_filter,
                                         actual_test.TAGS, tags)

        sub_tests = actual_test.blocks
        for sub_test in sub_tests:
            print_test_hierarchy(sub_test,
                                 PASS_ALL_FILTER if is_colored else None,
                                 tags, depth + 1)


def parse_json(json_path, schema_path=None):
    """Parse the Json file into attribute dictionary.

    Args:
        json_path (str): path of the Json file.
        schema_path (str): path of the schema file - optional.

    Returns:
        AttrDict. representing the Json file .

    Raises:
        jsonschema.ValidationError: Json file does not comply with the schema.
    """
    with open(json_path) as config_file:
        json_content = json.load(config_file)

    if schema_path is not None:
        with open(schema_path) as schema:
            schema_content = json.load(schema)

        validate(json_content, schema_content)

    return AttrDict(json_content)
