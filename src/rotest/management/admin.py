"""Define the Django administrator web interface for Rotest core.

Used in order to modify the appearance of tables in the admin site.
"""
# pylint: disable=too-many-public-methods
from __future__ import absolute_import
from django.contrib import admin
from django.utils.translation import ugettext_lazy as utext

from rotest.management.models import ResourceData
from rotest.common.django_utils.common import linked_unicode


class IsUsableFilter(admin.SimpleListFilter):
    """Filter for showing or hiding the unusable resources.

    Attributes:
        title (str): filter title.
        parameter_name (str): name of the field to filter by.
        DEFAULT_VALUE (str): default option code for the filter.
    """
    title = 'Is usable'
    parameter_name = 'is_usable'

    YES, NO, ALL = 'yes', 'no', 'all'
    _LOOK_UPS = [(option, utext(option.capitalize()))
                for option in (YES, NO, ALL)]

    DEFAULT_VALUE = YES

    def lookups(self, request, model_admin):
        """Define the selection options the filter will present.

        Returns:
            list. a tuple of tuples. each sub-tuple represents an option in
                the format (option code, diplayable name).
        """
        return self._LOOK_UPS

    def choices(self, change_list):
        """Generate the options dictionary for the filtering instance.

        Args:
            change_list (ChangeList): Django interior list filtering object.

        Yields:
            dict. options' state and functionality.
        """
        value = self.value()

        for lookup, title in self.lookup_choices:

            # Calculate the values for the option.
            selected = (lookup == value or
                        (value is None and lookup == self.DEFAULT_VALUE))
            query_string = change_list.get_query_string(
                                            {self.parameter_name: lookup}, [])

            yield {'selected': selected,
                   'query_string': query_string,
                   'display': title}

    def queryset(self, request, queryset):
        """Perform the filtering on the queryset of resources.

        Args:
            request (WSGIRequest): http request object.
            queryset (QuerySet): the relevant resources to filter.

        Returns:
            QuerySet. the filtered set of resources.
        """
        value = self.value()
        if value is None:
            value = self.DEFAULT_VALUE

        if value == self.YES:
            return queryset.filter(is_usable=True)

        if value == self.NO:
            return queryset.filter(is_usable=False)

        return queryset


class ResourceDataAdmin(admin.ModelAdmin):
    """Basic ModelAdmin for all :class:`rotest.ResourceData` models."""
    list_display = ['name', 'owner', "is_available", 'reserved', 'comment',
                    'group']
    list_filter = (IsUsableFilter, 'group')
    ordering = ['owner']

    def has_add_permission(self, request):
        """Disable the addition of a base resource object."""
        return False


# Register the Models & corresponding AdminModels to Django admin site
admin.site.register(ResourceData, ResourceDataAdmin)


def register_resource_to_admin(resource_type, attr_list=(), link_list=()):
    """Create a admin-view class using the given arguments.

    Args:
        resource_type (class): resource model class.
        attr_list (list): attributes to be displayed.
        link_list (list): relation to other models to be displayed.

    Returns:
        ResourceAdmin. resource admin view class.
    """
    # Create link properties to be displayed for the relations.
    link_properties = []
    for field_name in link_list:
        @property
        def link_method(self, field_to_convert=field_name):
            """Return a link to the model's admin page."""
            instance = getattr(self, field_to_convert)
            if instance is None:
                return '(None)'

            return linked_unicode(instance)

        property_name = '%s_link' % field_name
        link_properties.append(property_name)
        setattr(resource_type, property_name, link_method)

    class ResourceAdmin(admin.ModelAdmin):
        """Define the administrator model for the resource model.

        Used in order to modify the appearance of tables in the admin site.
        """
        list_display = (['name', 'owner', 'is_available', 'reserved',
                         'comment', 'group'] + list(attr_list) +
                        link_properties)
        readonly_fields = ('owner_time', 'reserved_time')

        list_filter = (IsUsableFilter, 'group')

    admin.site.register(resource_type, ResourceAdmin)
