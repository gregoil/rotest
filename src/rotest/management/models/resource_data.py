"""Define resources model classes.

Defines the basic attributes & interface of any resource type class,
responsible for the resource static & dynamic information.
"""
# pylint: disable=access-member-before-definition,no-init
# pylint: disable=attribute-defined-outside-init,invalid-name
# pylint: disable=no-self-use,too-many-public-methods,too-few-public-methods
from __future__ import absolute_import

from datetime import datetime

from future.builtins import object
from future.utils import itervalues
from django.db import models
from django.utils import six
from django.db.models.base import ModelBase
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rotest.common.django_utils.fields import NameField
from rotest.common.django_utils.common import get_fields
from rotest.common.django_utils import get_sub_model, linked_unicode


class DataPointer(object):
    """Pointer to a field in the resource's data."""
    def __init__(self, field_name):
        self.field_name = field_name


class DataBase(ModelBase):
    """Metaclass that creates data pointers for django fields.

    This allows requesting sub-resources with dependency on the parent's data,
    e.g:
        class AlterDemoComplexResource(BaseResource):
            DATA_CLASS = DemoResourceData
            demo1 = DemoService.request(name=DemoResourceData.name).
    """
    def __getattr__(cls, key):
        if '_meta' in vars(cls) and \
                key in (field.name for field in cls._meta.fields):

            return DataPointer(key)

        raise AttributeError(key)


class ResourceData(six.with_metaclass(DataBase, models.Model)):
    """Represent a container for a resource's global data.

    Inheriting resource datas may add more fields, specific to the resource.
    Note that fields pointing to objects inheriting from ResourceData are
    considered 'sub resources', and will be considered when checking
    availability, reserving or releasing the resource, etc.

    Warning:
        ResourceData subclasses cannot contain any unique fields.

    Attributes:
        name (str): name of the test containing the data.
        group (auth_models.Group): group to associate the resource with.
        owner (str): name of the locking user.
        reserved (str): name of the user allow to lock the resource.
            Empty string means available to all.
        is_usable (bool): a flag to indicate if the resource is a duplication.
        comment (str): general comment for the resource.
        owner_time (datetime): timestamp of the last ownership event.
        reserved_time (datetime): timestamp of the last reserve event.
    """
    NAME_SEPERATOR = '_'
    MAX_COMMENT_LENGTH = 200

    # Fields that shouldn't be transmitted to the client:
    IGNORED_FIELDS = ["group", "owner_time", "reserved_time"]

    name = NameField(unique=True)
    is_usable = models.BooleanField(default=True)
    group = models.ForeignKey(auth_models.Group, blank=True, null=True)
    comment = models.CharField(default='', blank=True,
                               max_length=MAX_COMMENT_LENGTH)

    owner = NameField(blank=True)
    reserved = NameField(blank=True)
    owner_time = models.DateTimeField(null=True, blank=True)
    reserved_time = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'management'

    def __eq__(self, obj):
        return (self.__class__ == obj.__class__ and
                self.name == obj.name)

    def get_sub_resources(self):
        """Return an iterable to the resource's sub-resources."""
        return (field_value
                for field_value in itervalues(self.get_fields())
                if isinstance(field_value, ResourceData))

    def _is_sub_resources_available(self, user_name=""):
        """Check if all the sub resources are available.

        Args:
            user_name (str): user name to be checked. Empty string means
                available to all.

        Returns:
            bool. whether the sub resources are available.
        """
        return all(sub_resource.is_available(user_name)
                   for sub_resource in self.get_sub_resources())

    def is_available(self, user_name=""):
        """Return whether resource is available for the given user.

        Args:
            user_name (str): user name to be checked. Empty string means
                available to all.

        Returns:
            bool. determine whether resource is available for the given user.

        Note:
            If this method is called from code then leaf is equal to 'self'.
            If it is being called by BaseResources table in DB then leaf's
            'is_available' method will be called.
        """
        leaf = self.leaf  # 'leaf' is a property.
        if leaf == self:
            leaf_available = (self.reserved in [user_name, ""] and
                              self.owner == "")

        else:
            leaf_available = leaf.is_available(user_name)

        return leaf_available and self._is_sub_resources_available(user_name)

    def __unicode__(self):
        """Django version of __str__"""
        return self.name

    @property
    def admin_link(self):
        """Return a link to the resource admin page.

        Returns:
            str. link to the resource's admin page.
        """
        return linked_unicode(self.leaf)

    @property
    def leaf(self):
        """Return the leaf resource-data inheriting from self."""
        sub_model = get_sub_model(self)
        if sub_model is None:
            return self

        return sub_model.leaf

    def get_fields(self):
        """Extract the fields of the resource.

        Returns:
            dict. dictionary contain resource's fields.
        """
        return get_fields(self, self.IGNORED_FIELDS)

    def duplicate(self):
        """Create a copy of the resource, save it to DB and return it.

        Create an exact copy of the resource instance, rename it to the
        original name + current date-time and return it.

        Note:
            The duplication is performed by shallow copy.

        Returns:
            rotest.common.models.base_resource.BaseResource. a copy of the
                instance.
        """
        # A simple copy does'nt work so we had to hack it.

        # Clone the class instance.
        resource_properties = self.get_fields()
        for key, value in list(resource_properties.items()):
            if isinstance(value, ResourceData):
                resource_properties[key] = value.duplicate()

        list_field_names = [key for
                            key, value in list(resource_properties.items())
                            if isinstance(value, list)]

        list_fields = [(field_name, resource_properties.pop(field_name))
                       for field_name in list_field_names]

        resource_copy = self.__class__(**resource_properties)

        resource_copy.id = None
        resource_copy.name = '%s%s%s' % (self.name, self.NAME_SEPERATOR,
                                         datetime.now())
        resource_copy.is_usable = False
        resource_copy.save()

        if len(list_fields) > 0:
            list_fields = [value.duplicate() if isinstance(value, ResourceData)
                           else value for value in list_fields]

            for field_name, field_values in list_fields:
                setattr(resource_copy, field_name, field_values)

            resource_copy.save()

        return resource_copy

    def _was_reserved_changed(self):
        """Check if the user is trying to change the value of 'Reserved'.

        Returns:
            bool. whether 'Reserved' was changed.
        """
        try:
            pre_reserved = ResourceData.objects.get(pk=self.pk).reserved

        except ObjectDoesNotExist:
            pre_reserved = ''

        return pre_reserved != self.reserved

    def clean(self):
        """Block reserving and releasing if sub-resources are not available.

        Disable only if the resource is not available for neither the previous
        and the current user.
        """
        try:
            pre_reserved = ResourceData.objects.get(pk=self.pk).reserved

            if pre_reserved != self.reserved:
                cur_available = self._is_sub_resources_available(self.reserved)
                pre_available = self._is_sub_resources_available(pre_reserved)
                if (self.reserved != "" and
                        not cur_available and not pre_available):
                    raise ValidationError('Cannot reserve a resource if its '
                                          'sub-resources are not available')

        except ObjectDoesNotExist:
            pass

        super(ResourceData, self).clean()

    def _unreserve_sub_resources(self, user):
        """Unreserve all sub-resources that are available to the given user.

        Args:
            user (str): the user to remove from reserved.
        """
        for sub_resource in self.get_sub_resources():
            if sub_resource.is_available(user):
                sub_resource.reserved = ''
                sub_resource.save()

    def _reserve_sub_resources(self, reserved_text):
        """Set the 'Reserved' field of all the sub resources.

        Args:
            reserved_text (str): the text to put in 'Reserved' field.
        """
        for sub_resource in self.get_sub_resources():
            sub_resource.reserved = reserved_text
            sub_resource.save()

    def save(self, *args, **kwargs):
        """Propagate reservation change to sub-resources of the resource."""
        if self._was_reserved_changed():
            if self.reserved == '':
                self.reserved_time = None
                pre_reserved = ResourceData.objects.get(pk=self.pk).reserved
                self._unreserve_sub_resources(pre_reserved)

            else:
                self.reserved_time = datetime.now()
                self._reserve_sub_resources(self.reserved)

        return super(ResourceData, self).save(*args, **kwargs)
