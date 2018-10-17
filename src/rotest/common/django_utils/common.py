"""Functions that ease the use of Django."""
# pylint: disable=protected-access
from __future__ import absolute_import

from django.utils.safestring import mark_safe


def get_fields(model_object, ignore_fields=()):
    """Extract the fields of the model.

    Args:
        model_object (django.models.Model): model instance.
        ignore_fields (list): list of field names to ignore.

    Returns:
        dict. dictionary contain the models's fields.
    """
    fields = [(field.name, getattr(model_object, field.name))
              for field in model_object._meta.fields
              if field.name not in ignore_fields and
              not field.name.endswith("_ptr")]

    fields += [(field.name, list(getattr(model_object, field.name).all()))
               for field in model_object._meta.many_to_many
               if field.name not in ignore_fields]

    return dict(fields)


def get_sub_model(model_object):
    """Return the model inherited sub class instance.

    Used as a workaround for Django subclasses issues

    Args:
        model_object (django.models.Model): model instance.

    Returns:
        object: sub model instance. None if there is no sub model.
    """
    for sub_class in model_object.__class__.__subclasses__():
        possible_atter = sub_class.__name__.lower()

        if hasattr(model_object, possible_atter):
            sub_model = getattr(model_object, possible_atter)
            sub_sub_model = get_sub_model(sub_model)

            if sub_sub_model is not None:
                return sub_sub_model

            return sub_model

    return None


def linked_unicode(item):
    """Return a unicode string with a HTML link to given item's page.

    Args:
        item (django.db.models.Model): a link to this item will be returned

    Returns:
        str. the result unicode text
    """
    app = item._meta.app_label
    pagename = item.__class__.__name__.lower()
    return mark_safe("<a href='/admin/%s/%s/%d/'>%s</a>" %
                     (app, pagename, item.id, item))
