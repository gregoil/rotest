"""Protal's Basic Tutorial."""
# pylint: disable=too-many-public-methods
# pylint: disable=undefined-variable,no-member,fixme,invalid-name

# case0 start

from rotest.core import runner
from rotest.core.suite import TestSuite
from rotest.core.case import TestCase, request
from django.core.exceptions import ValidationError

from my_app import ExampleResource

# case0 end
# case1 start


class TutorialFirstCase(TestCase):
    """Test ExampleResource (version=1)."""
    resources = (request('my_resource', ExampleResource, version=1),)

    def test_requested_resource(self):
        """Validate that we got the right resource and it was initialized."""
        self.assertEqual(self.my_resource.version, 1)

# case1 end
# case2 start


class TutorialSecondCase(TestCase):
    """Test ExampleResource.clean method."""
    resources = (request('my_resource', ExampleResource),)

    def test_negative_version(self):
        """Validate that the clean method rejects negative versions."""
        self.my_resource.version = -1

        # Negative version is illegal.
        self.assertRaises(ValidationError,
                          self.my_resource.clean)

    def test_zero_version(self):
        """Validate that the clean method rejects zero versions."""
        self.my_resource.version = 0

        # Zero version is illegal.
        self.assertRaises(ValidationError,
                          self.my_resource.clean)

# case2 end
# suite start


class TutorialSuite(TestSuite):
    """Sample TestSuite composed of 2 TestCases."""

    components = (TutorialFirstCase,
                  TutorialSecondCase)

# suite end
# main start

if __name__ == '__main__':
    runner.main(TutorialSuite)

# main end
# block0 start

from rotest.core.case import request
from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock, MODE_OPTIONAL

from my_app import ExampleResource

# block0 end
# block1 start


class TutorialActionBlock(TestBlock):
    """Test change version."""
    inputs = ('my_resource', 'version')
    outputs = ('previous_version')

    def test_set_version(self):
        """Change the version of the resource and save the previous value."""
        self.common.previous_version = self.my_resource.version
        self.my_resource.version = self.version

# block1 end
# block2 start


class TutorialValidationFailureBlock(TestBlock):
    """Test ExampleResource.clean method failures."""
    inputs = ('my_resource',)

    def test_clean_failure(self):
        """Validate that the clean method rejects the version put in it."""
        self.assertRaises(ValidationError,
                          self.my_resource.clean)

# block2 end
# block3 start


class TutorialVersionRevertBlock(TestBlock):
    """Test that reverts the value and cleans."""
    inputs = ('my_resource', 'previous_version')

    def test_revert_version(self):
        """Revert version value and validate that the clean method passes."""
        self.my_resource.version = self.common.previous_version
        self.my_resource.clean()

# block3 end
# flows start


class TutorialZeroVersionFlow(TestFlow):
    """Sample TestFlow to test behavior on zero version value."""
    resources = (request('my_resource', ExampleResource),)

    blocks = (TutorialActionBlock.params(version=0),
              TutorialValidationFailureBlock.params(mode=MODE_OPTIONAL),
              TutorialVersionRevertBlock)


class TutorialNegativeVersionFlow(TestFlow):
    """Sample TestFlow to test behavior on negative version value."""
    resources = (request('my_resource', ExampleResource),)

    blocks = (TutorialActionBlock.params(version=-1),
              TutorialValidationFailureBlock.params(mode=MODE_OPTIONAL),
              TutorialVersionRevertBlock)

# flows end
