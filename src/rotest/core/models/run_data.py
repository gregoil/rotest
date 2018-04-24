"""Define RunData model class."""
# pylint: disable=too-few-public-methods,no-init,old-style-class
from django.db import models

from rotest.common.django_utils import get_sub_model
from rotest.core.models.general_data import GeneralData
from rotest.common.django_utils.fields import NameField, PathField


class RunData(models.Model):
    """Contain information about a tests run.

    Defines the attributes of any tests run and linked it to the main_test
    instance that should be a subclass of
    :class:`rotest.core.models.general_data.GeneralData`.

    Attributes:
        main_test (GeneralData): the main test to be run.
        artifact_path (str): path to the artifact file if one exists.
        run_name (str): the name of the run, this optional field should be used
            to group together test runs (for delta run uses for example).
        run_delta (bool): determine whether to run only tests that failed in
            the last run (according to the results DB).
        GLOBAL_FIELDS (tuple): names of fields that are not local (not foreign
            keys to instances of the local DB for example).
    """
    run_name = NameField(null=True, blank=True)
    artifact_path = PathField(null=True, blank=True)
    run_delta = models.NullBooleanField(default=False)
    main_test = models.ForeignKey(GeneralData, null=True, blank=True,
                                  related_name='+')
    user_name = NameField(null=True, blank=True)

    GLOBAL_FIELDS = ('run_name', 'run_delta', 'artifact_path')

    class Meta:
        """Define the Django application for this model."""
        app_label = 'core'

    def get_fields(self):
        """Extract the fields of the run data.

        Returns:
            dict. dictionary contain the run data's fields.
        """
        return {field_name: getattr(self, field_name) for field_name in
                self.GLOBAL_FIELDS}

    def __unicode__(self):
        """Django version of __str__"""
        return str(self.main_test)

    def __repr__(self):
        """Unique Representation for data"""
        return "<RunData: main_test=%r run_name=%r run_delta=%r>" % (
                                 self.main_test, self.run_name, self.run_delta)

    def delete(self, using=None):
        """Delete the record from the DB and the main_test content.

        The main_test will be deleted from the DB and the FileSystem.
        """
        get_sub_model(self.main_test).delete(using)
        super(RunData, self).delete(using)

    @property
    def main_test_link(self):
        """Return a link to the test admin page.

        Returns:
            str. link to the main test's admin page.
        """
        if self.main_test is not None:
            return get_sub_model(self.main_test).admin_link

        return None

    def get_return_value(self):
        """Return a system return value according to the result.

        Returns:
            number. 0 success, 1 otherwise.
        """
        return int(not self.main_test.success)
