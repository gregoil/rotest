"""Define SignatureData model class."""
# pylint: disable=no-init,old-style-class
from django.db import models
from rotest.common.django_utils.fields import NameField


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
    MAX_LINK_LENGTH = 100
    MAX_PATTERN_LENGTH = 1000

    name = NameField(unique=True)
    link = models.CharField(max_length=MAX_LINK_LENGTH)
    pattern = models.CharField(max_length=MAX_PATTERN_LENGTH)

    class Meta:
        """Define the Django application for this model."""
        app_label = 'core'

    def __unicode__(self):
        """Django version of __str__"""
        return self.name

    def __repr__(self):
        """Unique Representation for data"""
        return self.name
