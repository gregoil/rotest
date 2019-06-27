# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import StatisticsRequestModel
from rotest.api.test_control.middleware import session_middleware
from rotest.core.utils.test_statistics import clean_data, collect_durations
from rotest.api.common.responses import (TestStatisticsResponse,
                                         FailureResponseModel)


class GetTestStatistics(DjangoRequestView):
    """Get statistics for a test or component."""
    URI = "tests/get_statistics"
    DEFAULT_MODEL = StatisticsRequestModel
    DEFAULT_RESPONSES = {
        http_client.OK: TestStatisticsResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "get": ["Tests"]
    }

    @session_middleware
    def get(self, request, sessions, *args, **kwargs):
        """Initialize the tests run data."""
        parameters = {"test_name": request.model.test_name}
        if request.model.max_sample_size is not None:
            parameters["max_size"] = request.model.max_sample_size

        test_durations = collect_durations(**parameters)
        if len(test_durations) < 1:
            raise BadRequest("No test history found!")

        parameters = {"durations": test_durations}
        if request.model.min_duration_cut is not None:
            parameters["min_duration_cut"] = request.model.min_duration_cut
        if request.model.max_iterations is not None:
            parameters["max_iterations"] = request.model.max_iterations
        if request.model.acceptable_ratio is not None:
            parameters["acceptable_ratio"] = request.model.acceptable_ratio

        test_durations = clean_data(**parameters)
        if len(test_durations) < 1:
            raise BadRequest("Test history disparity too wide!")

        response = {
            "min": min(test_durations),
            "avg": sum(test_durations) / len(test_durations),
            "max": max(test_durations)
        }

        return Response(response, status=http_client.OK)
