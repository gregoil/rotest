import json
import threading

import utils


DELETE_ACTION_FLAG = 3


class Cache(object):
    def __init__(self, factory):
        self._factory = factory
        self.resources_cache = {}
        self.display_list_cache = {}

    def initialize_display_list_cache(self, display_list):
        print("initialize display list cache")
        self.display_list_cache = display_list

    def _insert_resource_to_cache(self, resource):
        """Add the given resource to the cache.

        Arguments:
            resource (django.db.models.Model): a model to save in the cache.
        """
        resource_name = str(resource.__name__)
        self.resources_cache[resource_name] = utils.get_resource_data(resource)

    def initialize_resources_cache(self, resources):
        print("initialize resources cache")
        threads = []
        for resource in resources:
            resource_name = str(resource.__name__)
            if resource_name not in self.resources_cache:
                self.resources_cache[resource_name] = {}

            thread = threading.Thread(target=self._insert_resource_to_cache,
                                      args=(resource,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def update_users_resources_cache(self):
        self._factory.broadcast(json.dumps(
            {
                "event_type": "initialize",
                "content": self.resources_cache
                }
            ), False)

    def update_users_display_list(self):
        self._factory.broadcast(json.dumps(
            {
                "event_type": "initialize-display-list",
                "content": self.display_list_cache
                }
            ), False)

    def delete_from_resources_cache(self, object_id):
        for resource_cache in self.resources_cache.values():
            if object_id in resource_cache:
                del resource_cache[object_id]
                break


    def update_resource(self, sender, resource, **kwargs):
        del kwargs["signal"]
        resource_id = utils.get_object_id(resource)
        resource_name = str(utils.get_leaf(resource).__class__.__name__)
        print("Updating resource {}".format(resource_name))
        if resource_name == "LogEntry":
            if resource.action_flag == DELETE_ACTION_FLAG:
                self.delete_from_resources_cache(resource_id)

            self._factory.broadcast(json.dumps(
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

        if resource_name not in self.resources_cache:
            self.resources_cache[resource_name] = {}

        if resource_id not in self.resources_cache[resource_name]:
            self.resources_cache[resource_name][resource_id] = {}

        self.resources_cache[resource_name][resource_id].update(utils.expand_resource(resource))
        self._factory.broadcast(json.dumps(
            {
                "event_type": "resource_updated",
                "content": {
                    resource_name: {
                        resource_id: self.resources_cache[resource_name][resource_id]
                        }
                    }
                }
            ), False)

        print("Sent to all users")