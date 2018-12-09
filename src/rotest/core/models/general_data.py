"""Define GeneralData model class."""
# pylint: disable=no-init,unused-argument
from __future__ import absolute_import

from datetime import datetime

from django.db import models
from future.builtins import range, object

from rotest.common.django_utils import linked_unicode
from rotest.common.django_utils.fields import NameField
from rotest.common.django_utils.common import get_sub_model


class GeneralData(models.Model):
    """Contain & manage general information about test runs.

    Defines the basic attributes of any test run. Responsible for holding and
    managing any information about the containing tests run.

    Attributes:
        parent (GeneralData): pointer to the container test data.
        name (str): name of the test containing the data.
        status (number): code of the test status, can be either
            INITIALIZED,IN_PROGRESS or FINISHED. In order to get the string
            representing the status use 'get_status_display' method.
        start_time (datetime): date and time of the test start.
        end_time (datetime): date and time of the test end.
        success (bool): indicate if the test was successful.
        run_data (RunData): run data of the test.
    """
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='tests')

    (INITIALIZED, IN_PROGRESS, FINISHED) = list(range(3))

    STATUS_CHOICES = ((INITIALIZED, 'Initialized'),
                      (IN_PROGRESS, 'In Progress'),
                      (FINISHED, 'Finished'))

    name = NameField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=INITIALIZED)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    success = models.NullBooleanField(null=True)

    run_data = models.ForeignKey('core.RunData', null=True, blank=True,
                                 related_name='tests')

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'core'

    def __unicode__(self):
        """Django version of __str__"""
        return "%s" % self.name

    def __repr__(self):
        """Unique Representation for data"""
        return "%s_%s" % (self.name, self.id)

    def delete(self, using=None):
        """Delete the record from the DB and its content from the file_system

        Raises:
            SystemError: When trying to remove an object contained by another
        """
        if self.parent is not None:
            raise SystemError("Invalid operation. object '%s' is contained by "
                              "another: (%s)" % (self, self.parent))

        self._force_delete()

    @property
    def admin_link(self):
        """Return a link to the test admin page.

        Returns:
            str. link to the test admin page.
        """
        if self.id is None:
            return ""

        return linked_unicode(self)

    @property
    def parent_link(self):
        """Return a link to the test's parent's admin page.

        Returns:
            str. link to the test's parent's admin page.
        """
        if self.parent is None:
            return ''

        return linked_unicode(self.get_parent())

    def children_link(self):
        """Return links to the sub test's admin page.

        Returns:
            str. links to the sub test's admin page.
        """
        return ', '.join(linked_unicode(sub_test)
                         for sub_test in self.get_sub_tests_data())

    # Enable the links in the admin page.
    children_link.allow_tags = True

    def start(self):
        """Update the data that the test started."""
        self.status = self.IN_PROGRESS
        self.start_time = datetime.now()

    def end(self):
        """Update the data that the test ended."""
        self.status = self.FINISHED
        self.end_time = datetime.now()

    def add_sub_test_data(self, sub_test_data):
        """Add the sub test data as a child.

        Args:
            sub_test_data (GeneralData): sub test data to add.
        """
        sub_test_data.parent = self

    def get_parent(self):
        """When overridden, gets the parent field's value."""
        return get_sub_model(self.parent)

    def get_sub_tests_data(self):
        """Get the sub tests' data.

        Returns:
            list. list of the sub tests' data.

        Raises:
            NotImplementedError: calling on abstract class.
            RuntimeError: calling on a non-complex test.
        """
        return [get_sub_model(test_data)
                for test_data in self.tests.order_by("id")]

    @classmethod
    def should_skip(cls, test_name, run_data=None, exclude_pk=None):
        """Validate given test's last run was successful.

        The given test's last run is searched in the DB. If the result of that
        run is successful, the test should be skipped, however, if the result
        was a failure/error or there is no record for a run of that test -
        it should run.

        TODO: Consider Rotest's and Project's version when filtering tests.
            Also, consider revision validation.

        Args:
            test_name (str): Test instance or container name.
            run_data (RunData): test run data object, leave None to not filter
                by run data parameters.
            exclude_pk (number): pk to be excluded from the search. Pass the
                pk of the searched data object if it already been saved.

        Returns:
            bool. True if test's last run was successful, False otherwise.
        """
        return False

    def __iter__(self):
        """Iterate over the sub tests of the data.

        Returns:
            iterator. iterator that runs over that sub tests.
        """
        return iter(self.tests.all())
