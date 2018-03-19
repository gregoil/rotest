from rotest.core.runner import main
from rotest.core.case import TestCase, request

from playground.book.book import Book


class BookCase(TestCase):
    resources = [request("book", Book)]

    def setUp(self):
        self.logger.info("You can do stuff before every test.")

    def test_clockwork_orange(self):
        """You can access the resource's methods."""
        self.assertFalse(self.book.is_clockwork_orange(), "Book was A "
                                                          "Clockwork Orange "
                                                          "when it shouldn't "
                                                          "have been.")

    def test_display_for_library(self):
        """ResourceData's attributes are injected into the Resource object."""
        expected_name = "%s by %s" % (self.book.title,
                                      self.book.author)
        actual_name = str(self.book)

        self.assertEqual(expected_name, actual_name, "__str__ method of Book "
                                                     "parses incorrectly.")

    def test_the_bible(self):
        """You can skip tests, meaning they won't fail but also won't pass."""
        if self.book.title != "The Holy Bible":
            self.skipTest("{title} is not a holy book."
                          .format(title=self.book.title))

        self.assertEqual(self.book.author, "God",
                         "This is not the true Bible.")

    def tearDown(self):
        self.logger.info("You can do stuff after every test.")

if __name__ == "__main__":
    main(BookCase)
