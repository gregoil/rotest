from rotest.core.runner import main
from rotest.core.case import TestCase, request

from playground.book.book import Book


class BookCase(TestCase):
    resources = [request("book", Book)]

    def setUp(self):
        self.logger.info("You can do stuff before every test.")

    def test_clockwork_orange(self):
        self.assertFalse(self.book.is_clockwork_orange(), "Book was A "
                                                          "Clockwork Orange "
                                                          "when it shouldn't "
                                                          "have been.")

    def test_display_for_library(self):
        expected_name = "%s by %s" % (self.book.data.title,
                                      self.book.data.author)
        actual_name = str(self.book)

        self.assertEqual(expected_name, actual_name, "__str__ method of Book "
                                                     "parses incorrectly.")

    def tearDown(self):
        self.logger.info("You can do stuff after every test.")

if __name__ == "__main__":
    main(BookCase)
q