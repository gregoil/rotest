"""Define SignatureData model class."""
# pylint: disable=no-init,old-style-class
from __future__ import absolute_import

import re

from django.db import models
from future.builtins import object


class SignatureData(models.Model):
    """Contain & manage signatures about test exceptions.

    Note:
        Signature is a regular expression that matches a part of a traceback
        or an exception message of a failure or error.
        A signature match allows us identify known issues and bugs,
        and avoid investigating them again.

    Attributes:
        name (str): name of signature.
        link (str): link to the issue page.
        pattern (str): pattern of the signature.
    """
    MAX_LINK_LENGTH = 200
    MAX_PATTERN_LENGTH = 1000

    link = models.CharField(max_length=MAX_LINK_LENGTH)
    pattern = models.TextField(max_length=MAX_PATTERN_LENGTH)

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'core'

    @staticmethod
    def create_pattern(error_message):
        """Create a pattern from a failure or error message.

        args:
            error_message (str): error message to parse.

        returns:
            str. pattern for the given error message.
        """
        return re.sub(r"\d+(\\.\d+)?(e\\-?\d+)?", ".+",
                      re.escape(error_message))

    def __unicode__(self):
        return "Signature {}".format(self.id)

    def __repr__(self):
        return self.__unicode__()

    def save(self, *args, **kwargs):
        """Override Django's 'save' to normalize newline char."""
        self.pattern = self.pattern.replace("\r\n", "\n")
        super(SignatureData, self).save(*args, **kwargs)
