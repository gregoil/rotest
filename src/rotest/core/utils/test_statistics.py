"""Module for statistics collection on tests."""
from __future__ import absolute_import
from statistics import mean, median, pstdev

from rotest.core.models import CaseData


CUT_OFF_FACTOR = 1.5


def collect_durations(test_name, max_size=300):
    """Return re durations of successful runs tests with the given name.

    Args:
        test_name (str): name of the test to search, e.g. "MyTest.test_method".
        max_size (number): maximal number of tests to collect.

    Returns:
        list. collected tests after filtering.
    """
    latest_tests = CaseData.objects.filter(name=test_name,
                                           exception_type=0,
                                           start_time__isnull=False,
                                           end_time__isnull=False)

    latest_tests = latest_tests.order_by('-id')
    durations = ((test.end_time - test.start_time).total_seconds()
                 for test in latest_tests)

    durations = [x for x in durations if x > 0]

    return durations[:max_size]


def remove_anomalies(durations):
    """Return a list with less anomalies in the numeric values.

    Args:
        durations (list): list of numeric values.

    Returns:
        list. list with less anomalies.
    """
    avg = (mean(durations) + median(durations)) / 2
    deviation = pstdev(durations)
    cut_off = deviation * CUT_OFF_FACTOR
    lower_limit = avg - cut_off
    upper_limit = avg + cut_off
    return [x for x in durations if lower_limit < x < upper_limit]


def clean_data(durations, min_duration_cut=0.5,
               max_iterations=3, acceptable_ratio=2):
    """Return a list with less anomalies in the numeric values.

    Args:
        durations (list): list of numeric values.
        min_duration_cut (number): ignore tests under the given duration.
        max_iterations (number): max anomalies removal iterations.
        acceptable_ratio (number): acceptable ration between max and min
            values, under which don't try to remove anomalies.

    Returns:
        list. filtered list of durations.
    """
    durations = [x for x in durations if x > min_duration_cut]
    iteration_index = 0
    while len(durations) > 1 and iteration_index < max_iterations:
        if min(durations) * acceptable_ratio >= max(durations):
            break

        durations = remove_anomalies(durations)
        iteration_index += 1

    return durations
