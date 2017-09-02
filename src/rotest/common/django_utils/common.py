"Functions that ease the use of Django."""
# pylint: disable=protected-access
from django.core import serializers
from django.utils.safestring import SafeUnicode
from django.core.exceptions import ObjectDoesNotExist


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
    return SafeUnicode("<a href='/admin/%s/%s/%d/'>%s</a>" %
                       (app, pagename, item.id, item))


def load_fixture(app_name, fixture_file, apps):
    """Deserialize and save the objects in a fixture.

    This loads the json fixture file to the db using the historical models,
    thus enables loading fixtures in migrations.

    Args:
        app_name (str): name of the django application.
        fixture_filename (str): fixture file name.
        apps(django.apps.registry.Apps): historical version of the application.
    """
    with open(fixture_file, "rb") as fixture:
        objects = serializers.deserialize('json',
                                          fixture,
                                          ignorenonexistent=True)

        # Create the instance based on historical model.
        for obj in objects:
            model = apps.get_model(app_name, obj.object.__class__.__name__)
            parent = None

            try:
                instance = model.objects.get(pk=obj.object.pk)

            except model.DoesNotExist:
                instance = model(pk=obj.object.pk)
                try:
                    parent = model.__base__.objects.get(pk=obj.object.pk)

                except ObjectDoesNotExist:
                    # No base class instance found
                    pass

            for field, value in obj.object.__dict__.iteritems():
                if hasattr(instance, field):
                    setattr(instance, field, value)

            # In case the resource's model hierarchies are presented separately
            # in the fixture, we'd want to update the instance and not replace
            # it (which might cause loss of data or integrity errors)
            if parent is not None:
                for field, value in parent.__dict__.iteritems():
                    setattr(instance, field, value)

            instance.save()
