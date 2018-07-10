import json
import threading

import utils

DELETE_ACTION_FLAG = 3


def initialize_resources(resources, cache):
    threads = []
    for resource in resources:
        resource_name = str(resource.__name__)
        if resource_name not in cache:
            cache[resource_name] = {}

        thread = threading.Thread(target=utils.insert_resource_to_cache,
                                  args=(resource,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def update_users_display_list(factory, display_list):
    factory.broadcast(json.dumps(
        {
            "event_type": "initialize-display-list",
            "content": display_list
        }
    ), False)


def update_users_cache(factory, cache):
    factory.broadcast(json.dumps(
        {
            "event_type": "initialize",
            "content": cache
        }
    ), False)


def delete_from_cache(cache, object_id):
    for resource_cache in cache.values():
        if object_id in resource_cache:
            del resource_cache[object_id]
            break


def update_resource(cache, factory, sender, resource, **kwargs):
    del kwargs["signal"]
    resource_id = utils.get_object_id(resource)
    resource_name = str(utils.get_leaf(resource).__class__.__name__)
    if resource_name == "LogEntry":
        if resource.action_flag == DELETE_ACTION_FLAG:
            delete_from_cache(cache, resource_id)

        factory.broadcast(json.dumps(
            {
                "event_type": "resource_updated",
                "content": {
                    resource_name: {
                        resource_id: utils.expand_resource(resource)
                    }
                }
            }
        ), False)
        return

    if resource_name not in cache:
        cache[resource_name] = {}

    if resource_id not in cache[resource_name]:
        cache[resource_name][resource_id] = {}

    cache[resource_name][resource_id].update(utils.expand_resource(resource))
    factory.broadcast(json.dumps(
        {
            "event_type": "resource_updated",
            "content": {
                resource_name: {
                    resource_id: cache[resource_name][resource_id]
                }
            }
        }
    ), False)

    print "Sent to all users"
