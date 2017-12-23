from django.db import models
from rotest.management.base_resource import BaseResource
from rotest.management.models.resource_data import ResourceData


class BookData(ResourceData):
    class Meta(type):
        # In the django admin page you divide your resources into categories,
        # The category chosen is the metaclass's app_label member.
        app_label = "playground"

    title = models.TextField()
    author = models.TextField()


class Book(BaseResource):
    DATA_CLASS = BookData

    # This is just an example so there is not need to hook any methods
    # in this example. however; connect(), initialize() and finalize() are
    # very important lifecycle-methods to know and we'll get to them a bit
    # later.
    # The point of this example is to understand the conceptual meaning of
    # Resource and ResourceData

    def __str__(self):
        return "{title} by {author}".format(**vars(self.data))

    def is_clockwork_orange(self):
        return self.data.title == "A Clockwork Orange"
