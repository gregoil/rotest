"""Abstract Testing class for any kind of parser."""
from abc import ABCMeta, abstractmethod

import django
from django.test.testcases import TransactionTestCase

from rotest.common.colored_test_runner import colored_main
from rotest.management.common.parsers.xml_parser import XMLParser
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.management.models.ut_models import (DemoResource,
                                                DemoResourceData,
                                                DemoComplexResourceData)
from rotest.management.common.messages import (ErrorReply,
                                               SuccessReply,
                                               LockResources,
                                               ResourcesReply,
                                               ParsingFailure,
                                               ReleaseResources)


class AbstractTestParser(TransactionTestCase):
    """An abstract class to test any parser.

    Attributes:
        PARSER (AbstractParser): the parser to be tested.
            Should be initiated under setUpClass method in any derived class.
    """
    __metaclass__ = ABCMeta

    PARSER = NotImplemented
    LOCK_RESOURCES_TIMEOUT = 10

    @classmethod
    @abstractmethod
    def setUpClass(cls):
        """Initializing the tested parser.

        Should be overridden in any derived class.
        """
        pass

    def validate(self, msg):
        """Validate encoding & decoding a message using the parser.

        * Encode the given message.
        * Decode the encoded message.
        * Compare between the original message and the decoded one.

        Args:
            msg (rotest.management.common.messages.AbstractMessage):
                message to validate the parser on.

        Raises:
            AssertionError: decoded message differs from original message.
        """
        msg.msg_id = 1
        encoded_data = self.PARSER.encode(msg)
        decoded_msg = self.PARSER.decode(encoded_data)
        self.assertEqual(msg, decoded_msg, "Original msg %r differs from "
                         "decoded msg %r." % (msg, decoded_msg))

    def test_parsing_failure_message(self):
        """Test encoding & decoding of ParsingFailure message."""
        msg = ParsingFailure(reason="exception: bla bla.")
        self.validate(msg)

    def test_success_reply_message(self):
        """Test encoding & decoding of SuccessReply message."""
        msg = SuccessReply(request_id=0)
        self.validate(msg)

    def test_error_reply_message(self):
        """Test encoding & decoding of ErrorReply message."""
        msg = ErrorReply(request_id=0,
                         code="SystemError", content="error occurred")
        self.validate(msg)

    def test_resources_reply_message(self):
        """Test encoding & decoding of ResourcesReply message."""
        data = DemoResourceData(name='demo1', version=1, ip_address="1.2.3.4")
        data.save()

        msg = ResourcesReply(request_id=0, resources=[data])
        self.validate(msg)

    def test_complex_resources_reply_message(self):
        """Test encoding & decoding of ResourcesReply message."""
        data1 = DemoResourceData(name='demo1', version=1, ip_address="1.2.3.4")
        data2 = DemoResourceData(name='demo2', version=2, ip_address="1.2.3.5")
        data1.save()
        data2.save()

        resource_data = DemoComplexResourceData(name="complex",
                                                demo1=data1,
                                                demo2=data2)
        resource_data.save()

        msg = ResourcesReply(request_id=0, resources=[resource_data])
        self.validate(msg)

    def test_lock_resource_message(self):
        """Test encoding & decoding of LockResources message."""
        resource1 = ResourceDescriptor(DemoResource, name="my_resource1",
                                       ip_address="1.2.3.4", version=1)
        resource2 = ResourceDescriptor(DemoResource, name="my_resource2",
                                       ip_address="1.2.3.5", version=2)

        descriptors = [resource1.encode(), resource2.encode()]

        msg = LockResources(descriptors=descriptors,
                            timeout=self.LOCK_RESOURCES_TIMEOUT)
        self.validate(msg)

    def test_release_resource_message(self):
        """Test encoding & decoding of ReleaseResources message."""
        request1 = {"name": "resource1", "dirty": True}
        request2 = {"name": "resource2", "dirty": False}
        msg = ReleaseResources(requests=[request1, request2])
        self.validate(msg)


class TestXMLParser(AbstractTestParser):
    """Test the XML parser module."""

    @classmethod
    def setUpClass(cls):
        """Initialize the parser."""
        cls.PARSER = XMLParser()


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestXMLParser')
