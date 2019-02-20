"""Define CaseData model class."""
# pylint: disable=too-many-public-methods,no-init
# pylint: disable=no-member,no-init,too-few-public-methods
from __future__ import absolute_import

from django.db import models
from future.builtins import object, range

from .general_data import GeneralData


class TestOutcome(object):
    """Namespace for the possible outcomes of tests.

    Attributes:
        RESULT_PRIORITY (dict): maps between possible results to their
            priority, where a higher priority means it's more important to
            save that outcome as the result of the test.
    """
    (SUCCESS, ERROR, FAILED, SKIPPED,
     EXPECTED_FAILURE, UNEXPECTED_SUCCESS) = range(6)

    RESULT_PRIORITY = {SUCCESS: 0,
                       SKIPPED: 1,
                       EXPECTED_FAILURE: 2,
                       UNEXPECTED_SUCCESS: 3,
                       FAILED: 4,
                       ERROR: 5}

    POSITIVE_RESULTS = (SUCCESS, SKIPPED, EXPECTED_FAILURE)
    UNCRITICAL_RESULTS = (SUCCESS, SKIPPED, EXPECTED_FAILURE,
                          UNEXPECTED_SUCCESS, FAILED)


class CaseData(GeneralData):
    """Contain information about a test run.

    Attributes:
        resources (list): List of contained resources data.
        traceback (str): Textual description of the test problem.
        exception_type (number): The code of the test exception (0-5),
            which are constants in the class :class:`TestOutcome`:
            SUCCESS, ERROR, FAILED, SKIPPED, EXPECTED_FAILURE,
            UNEXPECTED_SUCCESS.
    """
    MAX_CHAR_LEN = 1000
    TB_SEPARATOR = 80 * '-' + '\n'
    _RUNTIME_ORDER = '-start_time'

    RESULT_CHOICES = {TestOutcome.SUCCESS: 'Success',
                      TestOutcome.ERROR: 'Error',
                      TestOutcome.FAILED: 'Failed',
                      TestOutcome.SKIPPED: 'Skipped',
                      TestOutcome.EXPECTED_FAILURE: 'Expected Failure',
                      TestOutcome.UNEXPECTED_SUCCESS: 'Unexpected Success'}

    resources = models.ManyToManyField('management.ResourceData')
    traceback = models.TextField(max_length=MAX_CHAR_LEN, blank=True)
    exception_type = models.IntegerField(choices=list(RESULT_CHOICES.items()),
                                         blank=True, null=True)

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'core'

    @classmethod
    def should_skip(cls, test_name, run_data=None, exclude_pk=None):
        """Validate given test's last run was successful.

        The given test's last run is searched in the DB while ignoring previous
        skipped runs of the case. If the result of that run is successful,
        the test should be skipped, however, if the result was a failure/error
        or there is no record for a run of that test - it should run.

        Args:
            test_name (str): TestCase name.
            run_data (RunData): test run data object, leave None to not filter
                by run data parameters.
            exclude_pk (number): pk to be excluded from the search. Pass the
                pk of the searched data object if it already been saved.

        Returns:
            bool. True if test's last run was successful, False otherwise.
        """
        if run_data is None or run_data.run_name is None:
            query_set = CaseData.objects.filter(name=test_name,
                                                start_time__isnull=False)

        else:
            query_set = CaseData.objects.filter(name=test_name,
                                         start_time__isnull=False,
                                         run_data__run_name=run_data.run_name)

        if exclude_pk is not None:
            query_set = query_set.exclude(pk=exclude_pk)

        query_set = query_set.exclude(exception_type=TestOutcome.SKIPPED)

        matches = query_set.order_by(cls._RUNTIME_ORDER)

        return matches.count() > 0 and matches.first().success

    def resources_names(self):
        """Return a string representing the resources this test used.

        Returns:
            str. the test's resources.
        """
        return ', '.join(resource.name for resource in self.resources.all())

    def update_result(self, result_type, details=None):
        """Update the case data result.

        If the new result type has higher priority than the previous, the
        exception type value is updated, and any additional details are always
        added to the traceback field.

        Args:
            result_type (number): result type identifier.
            details (str): details of the result (traceback/skip reason)

        Raises:
            ValueError: when the end result is an unsupported one.
        """
        if result_type not in self.RESULT_CHOICES:
            raise ValueError("Unsupported end result: %s" % result_type)

        if (self.exception_type is None or
            TestOutcome.RESULT_PRIORITY[self.exception_type] <
                TestOutcome.RESULT_PRIORITY[result_type]):

            self.exception_type = result_type

        if details is not None:
            details = "{}: {}".format(self.RESULT_CHOICES[result_type].upper(),
                                      details)

            if len(self.traceback) > 0:
                details = self.TB_SEPARATOR.join([self.traceback, details])

            self.traceback = details

        self.end()

    def end(self):
        """Update the data that the test ended and calculate its result."""
        super(CaseData, self).end()
        has_succeeded = None
        if self.exception_type != TestOutcome.SKIPPED:
            has_succeeded = self.exception_type in (TestOutcome.SUCCESS,
                                                TestOutcome.EXPECTED_FAILURE)

        if self.success in (None, True):
            self.success = has_succeeded
