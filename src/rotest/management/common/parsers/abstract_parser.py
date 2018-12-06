"""An interface of a typical parser."""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import six

from rotest.management.common.messages import AbstractMessage


class ParsingError(Exception):
    pass


class AbstractParser(six.with_metaclass(ABCMeta, object)):
    """Basic parser class."""

    def encode(self, message):
        """Encode a message.

        Args:
            message (AbstractMessage): a message to encode.

        Returns:
            object. encoded data, depends on the parser type.

        Raises:
            TypeError: given 'message' is not of type 'AbstractMessage'.
            ParsingError: encoding failure.
        """
        if not isinstance(message, AbstractMessage):
            raise TypeError("message %r type is not of AbstractMessage."
                            % message)

        try:
            return self._encode_message(message)

        except Exception as err:
            raise ParsingError("Encoding message %r has failed. Reason: %s." %
                               (message, err))

    def decode(self, data):
        """Decode a message.

        Args:
            data (object): data to decode, encoded data of 'AbstractMessage',
                depends on the parser type.

        Returns:
            AbstractMessage. decoded message.

        Raises:
            ParsingError: decoding failure.
        """
        try:
            return self._decode_message(data)

        except Exception as err:
            raise ParsingError("Decoding data %r has failed. Reason: %s." %
                               (data, err))

    @abstractmethod
    def _encode_message(self, message):
        """Encode a message.

        Args:
            message (AbstractMessage): a message to encode.

        Returns:
            object. encoded data, depends on the parser type.
        """
        pass

    @abstractmethod
    def _decode_message(self, data):
        """Decode a message.

        Args:
            data (object): data to decode, encoded data of 'AbstractMessage',
                depends on the parser type.

        Returns:
            AbstractMessage. decoded message.
        """
        pass
