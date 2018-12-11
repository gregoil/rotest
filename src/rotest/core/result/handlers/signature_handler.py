"""Known issues result handler."""
from __future__ import absolute_import

from rotest.core import skip_if_not_main
from rotest.core.result.handlers.stream.base_handler import BaseStreamHandler
from rotest.management.client.signatures_client import ClientSignatureManager


class SignatureHandler(BaseStreamHandler):
    """Failures and errors signatures result handler.

    Matches the tests' exceptions with a given pattern,
    and reports it to the user.
    """
    NAME = 'signature'

    def __init__(self, *args, **kwargs):
        """Initialize the signature handler and connect to the server."""
        super(SignatureHandler, self).__init__(*args, **kwargs)
        self.client = ClientSignatureManager()
        self.client.connect()
        self.encounters = []

    def handle_response(self, test_item, response_data):
        """Handle signature match response.

        Args:
            test_item (AbstractTest): test item instance.
            response_data (SignatureResponse): signature match response.
        """
        if response_data.is_new:
            encounter = "Encountered new issue. Assigned ID={}".format(
                                                            response_data.id)

        else:
            encounter = "Encountered known issue ID={}, link={}".format(
                                        response_data.id, response_data.link)

        self.encounters.append(encounter)
        test_item.logger.warning(encounter)

    @skip_if_not_main
    def add_error(self, test, exception_str):
        """Check if the test error matches any known issues.

        Args:
            test (AbstractTest): test item instance.
            exception_str (str): exception traceback string.
        """
        response = self.client.get_or_create_signature(exception_str)
        self.handle_response(test, response)

    @skip_if_not_main
    def add_failure(self, test, exception_str):
        """Check if the test failure matches any known issues.

        Args:
            test (AbstractTest): test item instance.
            exception_str (str): exception traceback string.
        """
        response = self.client.get_or_create_signature(exception_str)
        self.handle_response(test, response)

    def print_errors(self, *_args):
        """Called by TestRunner after test run."""
        self.stream.writeln("Signatures summary:")
        for encounter in self.encounters:
            self.stream.writeln('\t' + encounter)

        self.stream.writeln()
