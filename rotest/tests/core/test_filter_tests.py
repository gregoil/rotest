"""Test tests trimming by tags."""
import unittest

from rotest.core.case import TestCase
from rotest.core.suite import TestSuite
from rotest.core.test_filter import get_tags, match_tags
from rotest.common.colored_test_runner import colored_main
from utils import (SuccessCase, ErrorCase, TwoTestsCase,
                   MockSuite1, MockSuite2, MockTestSuite, MockTestSuite1)


def test_to_dict(test, tags_filter=None):
    """Create a dictionary representation of a test.

    For example:
    {
    Suite1: {
        Suite2: {
            SubSuite1: [Case1.test_method,
                        Case2.test_method],
            SubSuite2: [Case3.test_method,
                        Case4.test1,
                        Case4.test2]}}}

    Args:
        test (TestSuite / TestCase): a test class.
        tags_filter (str): tags filter string, leave None to not filter.

    Returns:
        dict. a dictionary representation of a test
    """
    if isinstance(test, TestCase):
        return test.data.name

    if isinstance(test, TestSuite):
        test_descriptor = {}
        for sub_test in test:
            if sub_test.IS_COMPLEX is True:
                sub_dict = test_to_dict(sub_test, tags_filter)
                if sub_dict is not None:
                    test_descriptor.update(sub_dict)

            else:
                if tags_filter is not None:
                    test_descriptor = [test_to_dict(test_case, tags_filter)
                                       for test_case in test
                                       if match_tags(get_tags(test_case),
                                                     tags_filter)]

                else:
                    test_descriptor = [test_to_dict(test_case, tags_filter)
                                       for test_case in test]

    if len(test_descriptor) == 0:
        return None

    return {test.__class__.__name__: test_descriptor}


class TestTagsMatching(unittest.TestCase):
    """Test the test tree trimming by matching tags."""

    def setUp(self):
        """Define main tests to trim."""
        ErrorCase.TAGS = ["tag12"]
        SuccessCase.TAGS = ["tag13"]
        TwoTestsCase.TAGS = ["tag1"]
        MockSuite1.components = (TwoTestsCase, SuccessCase)

        MockSuite2.TAGS = ["tag2"]
        MockSuite2.components = (ErrorCase,)

        MockTestSuite.TAGS = ["tag3"]
        MockTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite1.components = (MockSuite1, MockSuite2, MockTestSuite)

        self.two_test_case = ["TwoTestsCase.test_1",
                               "TwoTestsCase.test_2"]
        self.error_case_descriptor = ["ErrorCase.test_run"]
        self.trimmed_two_test_case = ["TwoTestsCase.test_1"]
        self.mock_suite1_descriptor = test_to_dict(MockSuite1())
        self.trimmed_mock_suite1 = {"MockSuite1": self.two_test_case}

    def test_suite_matching_tags(self):
        """Test a Suite main test is not trimmed when it matches tags."""
        self.assertEqual(self.mock_suite1_descriptor,
                         test_to_dict(MockSuite1(), "MockSuite1"))

    def test_suite_with_matching_test_methods(self):
        """Test only the required methods appears under a Suite main test."""
        expected_test_descriptor = {
                        "MockSuite1": ["TwoTestsCase.test_1",
                                      "SuccessCase.test_success"]}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockSuite1(), "test_1 or test_success"))

    def test_suite_with_matching_tags(self):
        """Test a Suite main test is not trimmed when it matches tags."""
        expected_test_descriptor = test_to_dict(MockTestSuite1())

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "MockTestSuite1"))

    def test_suite_with_matching_sub_suite(self):
        """Test only the matching Suite appears under a Suite main test."""
        expected_test_descriptor = {"MockTestSuite1":
                                    test_to_dict(MockTestSuite())}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "MockTestSuite"))

    def test_suite_with_joker_match(self):
        """Test it is possible to use jokers in matching."""
        nested_suite_sub_tests = self.trimmed_mock_suite1
        nested_suite_sub_tests["MockSuite2"] = self.error_case_descriptor
        expected_test_descriptor = {"MockTestSuite": nested_suite_sub_tests}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite(), "tag1* and not tag13"))

    def test_suite_with_matching_case(self):
        """Test only the matching Case appears under the Suite main test."""
        expected_test_descriptor = {
                "MockTestSuite1": {
                    "MockTestSuite": self.trimmed_mock_suite1,
                    "MockSuite1": self.two_test_case}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "TwoTestsCase"))

    def test_suite_with_matching_test_method(self):
        """Test only the matching method appears under the Suite main test."""
        expected_test_descriptor = {
            "MockTestSuite1": {
                 "MockTestSuite": {
                    "MockSuite1": self.trimmed_two_test_case},
                    "MockSuite1": self.trimmed_two_test_case}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "test_1"))

    def test_and_matching_complex_filter(self):
        """Test that trimming corresponds to "and" complex filtering."""
        expected_test_descriptor = {"MockSuite1": self.trimmed_two_test_case}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockSuite1(),
                                      "TwoTestsCase and test_1"))

    def test_suite_not_complex_filter(self):
        """Test trimming corresponds to 'not' complex filtering on Suite."""
        expected_test_descriptor = {
            "MockTestSuite1": {
                "MockTestSuite": {
                    "MockSuite1": [
                        "TwoTestsCase.test_1",
                        "SuccessCase.test_success"]},
                "MockSuite1": [
                    "TwoTestsCase.test_1",
                    "SuccessCase.test_success"]}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(),
                                      "MockSuite1 and not test_2"))

    def test_or_complex_filter(self):
        """Test that trimming corresponds to "or" complex filtering."""
        expected_test_descriptor = {
            "MockTestSuite1": {
                "MockTestSuite": {
                    "MockSuite1": self.trimmed_two_test_case,
                                 "MockSuite2": self.error_case_descriptor},
                 "MockSuite1": self.trimmed_two_test_case,
                 "MockSuite2": self.error_case_descriptor}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(),
                                      "test_1 or MockSuite2"))

    def test_no_matches_in_case(self):
        """Test None is returned if no test matches tags under Suite."""
        self.assertEqual(None, test_to_dict(MockSuite1(), "None"))

    def test_no_matches_in_suite(self):
        """Test None is returned if no test matches tags under Suite."""
        self.assertEqual(None, test_to_dict(MockTestSuite1(), "None"))

    def test_no_matching_complex_filter(self):
        """Test None is returned if no test element matches complex filter."""
        self.assertEqual(None, test_to_dict(MockTestSuite1(),
                                            "test1 and test2"))

    def test_user_tags(self):
        """Test trimming by a simple user defined tag."""
        expected_test_descriptor = self.trimmed_mock_suite1

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockSuite1(), "tag1"))

    def test_user_complex_tags_filter(self):
        """Test trimming by a complex condition on user defined tags."""
        expected_test_descriptor = {
            "MockTestSuite1": {"MockTestSuite": self.mock_suite1_descriptor}}

        self.assertEqual(expected_test_descriptor,
                 test_to_dict(MockTestSuite1(), "tag3 and not tag2"))

    def test_user_and_default_tags_filter(self):
        """Test trimming by a combination of user defined and default tags."""
        expected_test_descriptor = {
            "MockTestSuite1": {
                "MockTestSuite": {
                    "MockSuite1": self.trimmed_two_test_case,
                    "MockSuite2": self.error_case_descriptor},
                "MockSuite1": self.trimmed_two_test_case,
                "MockSuite2": self.error_case_descriptor}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "test_1 or tag2"))

    def test_non_case_sensitive_matching(self):
        """Test that tags matching is not case sensitive."""
        expected_test_descriptor = {
            "MockTestSuite1": {
                "MockTestSuite": {
                    "MockSuite1": self.trimmed_two_test_case,
                    "MockSuite2": self.error_case_descriptor},
                "MockSuite1": self.trimmed_two_test_case,
                "MockSuite2": self.error_case_descriptor}}

        self.assertEqual(expected_test_descriptor,
                         test_to_dict(MockTestSuite1(), "TEST_1 or TAG2"))


if __name__ == '__main__':
    colored_main(defaultTest='TestTagsMatching')
