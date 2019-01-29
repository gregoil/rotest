"""Define Rotest UT model classes."""
# pylint: disable=no-self-use,no-init,no-member,too-few-public-methods
# pylint: disable=attribute-defined-outside-init,too-many-public-methods
from __future__ import absolute_import

from django.db import models
from future.builtins import range, object

from rotest.management.models.resource_data import ResourceData


class DemoResourceData(ResourceData):
    """Fake resource class, used in resource manager tests.

    Attributes:
        version (number): version identifier.
        ip_address (str): ip address identifier.
        mode (number): mode identifier (boot/ production).

        reset_flag (bool): tells if the resource was reset.
        validate_flag (bool): tells if the resource was validated.
        finalization_flag (bool): tells if the resource was finalized.
        initialization_flag (bool): tells if the resource was initialized.

        fails_on_finalize (bool): the resource should fail on finalization.
        fails_on_initialize (bool): the resource should fail on initialization.
    """
    BOOT_MODE, PROD_MODE = range(2)

    MODE_CHOICE = ((BOOT_MODE, 'Boot'),
                   (PROD_MODE, 'Production'))

    version = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField()
    mode = models.IntegerField(choices=MODE_CHOICE, default=BOOT_MODE)

    validation_result = models.BooleanField(default=False)
    reset_flag = models.BooleanField(default=False)
    validate_flag = models.NullBooleanField(default=False)
    finalization_flag = models.BooleanField(default=False)
    initialization_flag = models.BooleanField(default=False)

    fails_on_finalize = models.BooleanField(default=False)
    fails_on_initialize = models.BooleanField(default=False)

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'management'


class DemoComplexResourceData(ResourceData):
    """Fake complex resource class, used in resource manager tests.

    Attributes:
        reset_flag (bool): tells if the resource was reset.
        validate_flag (bool): tells if the resource was validated.
        finalization_flag (bool): tells if the resource was finalized.
        initialization_flag (bool): tells if the resource was initialized.
        demo1 (DemoResourceData): sub resource data pointer.
        demo2 (DemoResourceData): sub resource data pointer.
    """
    reset_flag = models.BooleanField(default=False)
    validate_flag = models.NullBooleanField(default=None)
    finalization_flag = models.BooleanField(default=False)
    initialization_flag = models.BooleanField(default=False)

    demo1 = models.ForeignKey(DemoResourceData, related_name="demo_resource1")
    demo2 = models.ForeignKey(DemoResourceData, related_name="demo_resource2")

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'management'
