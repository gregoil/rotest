import httplib

from django.http import JsonResponse
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.responses import EmptyResponse
from rotest.api.common.models import UpdateResourcesModel
from rotest.api.test_control.middleware import session_middleware
from rotest.management.common.resource_descriptor import ResourceDescriptor

# pylint: disable=unused-argument, no-self-use


class UpdateResources(DjangoRequestView):
    """Update the resources list for a test data.

    Args:
        test_id (number): the identifier of the test.
        descriptors (list): the resources the test used.
        token (str): token of the session.
    """
    URI = "tests/update_resources"
    DEFAULT_MODEL = UpdateResourcesModel
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: EmptyResponse,
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Update the resources list for a test data.

        Args:
            test_id (number): the identifier of the test.
            descriptors (list): the resources the test used.
        """
        session_token = request.model.test_details.token
        session_data = sessions[session_token]
        test_data = session_data.all_tests[request.model.test_details.test_id]
        test_data.resources.clear()

        for resource_descriptor in request.model.descriptors:
            resource_dict = ResourceDescriptor.decode(resource_descriptor)
            test_data.resources.add(resource_dict.type.objects.get(
                **resource_dict.properties))

        test_data.save()

        return JsonResponse({}, status=httplib.NO_CONTENT)
