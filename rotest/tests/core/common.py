"""Defines mock classes that will be used in the tests."""
import unittest


class SuccessCase(unittest.TestCase):
    """Mock test case, contains one test that will always be successful."""
    def test_success(self):
        """Success test function"""
        pass


class FailureCase(unittest.TestCase):
    """Mock test case, contains one test that will always fail."""
    def test_failure(self):
        """Failure test function"""
        self.fail()
