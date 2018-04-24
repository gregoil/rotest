"""Tags filtering handler."""
from rotest.core.filter import match_tags, get_tags
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class TagsHandler(AbstractResultHandler):
    """Tags filtering result handler.

    Matches the tests' tags with a given pattern. If a case doesn't
    match the pattern, it is skipped.

    Attributes:
        TAGS_PATTERN (str): pattern to match with the tests.
    """
    NAME = 'tags'
    TAGS_PATTERN = ""

    SKIP_MESSAGE = "Filtered by tags"

    def should_skip(self, test):
        """Check if the test passes the tags filtering.

        The test tags composed of the values in its 'TAGS' field, plus
        its name, plus the name and tags of its ancestors.

        Args:
            test (object): test item instance.

        Returns:
            str. Skip reason if the test should be skipped, None otherwise.
        """
        test_tags = get_tags(test)

        if not match_tags(test_tags, self.TAGS_PATTERN):
            return self.SKIP_MESSAGE

        return None
