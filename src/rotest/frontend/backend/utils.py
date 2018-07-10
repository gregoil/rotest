import json

from django.db import models

from rotest.common.django_utils.common import get_fields, get_sub_model


def get_object_id(resource):
    """"Get the id of a given resource."""
    if hasattr(resource, "object_id"):
        return int(resource.object_id)

    return int(resource.id)


def get_leaf(model):
    """"Get the leaf resource data inheriting from model given.

    Arguments:
        model (django.db.models.Model): a model instance to get its leaf.

    Returns:
        django.db.models.Model. the leaf model of the given instance.
    """
    sub_model = get_sub_model(model)
    if sub_model is None:
        return model

    return get_leaf(sub_model)


def expand_resource(resource):
    """"Expand the given resource to it's fields.

    Arguments:
        resource (models.Model): a instance of a model to expand.

    Note:
        if a model has a reference to other model a `link` is created to
        the other model:

        Examples:
            {
               "id": model_id,
               "type": model_class_type
            }

    Returns:
        dict. the resource representation as a dict.
    """
    fields = get_fields(resource)
    for field_name, field_value in fields.items():
        if isinstance(field_value, models.Model):
            fields[field_name] = {
                "link": {
                    "id": get_object_id(field_value),
                    "type": get_leaf(field_value).__class__.__name__
                }
            }

        if isinstance(field_value, list):
            new_list = []
            for sub_element in field_value:
                if isinstance(sub_element, models.Model):
                    new_list.append({
                        "link": {
                            "id": get_object_id(field_value),
                            "type": get_leaf(field_value).__class__.__name__
                        }
                    })

                else:
                    new_list.append(sub_element)

        try:
            json.dumps(fields[field_name])

        except TypeError:
            fields[field_name] = str(fields[field_name])

    return fields


def get_resource_data(resource_type):
    """Get all data of the given resource list from the db.

    Arguments:
        resource_type (django.db.models.Model): fetch all objects of a given
            resource.

    Returns:
        dict. all the objects of the given model.
            keys are the object id and values are dictionaries that represent
            the objects' datas.
    """
    resources = resource_type.objects.all()
    data_dict = {}
    for resource in resources:
        data_dict[get_object_id(resource)] = expand_resource(resource)

    return data_dict


def insert_resource_to_cache(cache, resource):
    """Add the given resource to the cache.

    Arguments:
        resource (django.db.models.Model): a model to save in the cache.
    """
    resource_name = str(resource.__name__)
    cache[resource_name] = get_resource_data(resource)