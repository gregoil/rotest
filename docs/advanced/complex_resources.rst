=================
Complex Resources
=================

Sometimes we want our resources to contain sub-resources or sub-services
(the difference is that sub-resources have `ResourceData` models in the DB and
services does not). This can easily be achieved with `Rotest`.


Creating sub-resource model
===========================

In case we want to create a sub-resource, to `Calcuator` for example, we first
need to point to it in the `CalculatorData` model.

(Skip this part if you want a sub-service, i.e. you don't need to hold data
on the sub-resource in the server's DB, like when all its data is derived
from the containing resource's data)

.. code-block:: python

    from django.db import models
    from rotest.management.models.resource_data import ResourceData


    class SubCalculatorData(ResourceData):
        class Meta:
            app_label = "resources_app"

        process_id = models.IntegerField()


    class CalculatorData(ResourceData):
        class Meta:
            app_label = "resources_app"

        ip_address = models.IPAddressField()
        sub_process = models.ForeignKey(SubCalculatorData)

In this example we created the `ResourceData` model for the sub-resource
(like we'd do to any new resource), and pointed to it in the original
`CalculatorData` model, declaring we intend to use a sub-resource here.

Don't forget to add a reference to the model and the new field in ``admin.py``:

.. code-block:: python

    from rotest.management.admin import register_resource_to_admin

    from . import models

    register_resource_to_admin(models.SubCalculatorData, attr_list=['process_id'])
    register_resource_to_admin(models.CalculatorData, attr_list=['ip_address'],
                                                      link_list=['sub_process'])

Note that we used the `link_list` to point to the sub-resource and not `attr-list`,
since its a model and not a regular field.

Don't forget to run ``makemigrations`` and ``migrate`` again after changing the models!


Declaring sub-resources
=======================

Let's continue to modify the Calculator resource, where we want to add
sub-resources.

For now, let's assume we already wrote the sub-resource under
:file:`resources_app/sub_process.py`.

Now, edit the file :file:`resources_app/resources.py`:

.. code-block:: python

    import rpyc
    from rotest.management.base_resource import BaseResource

    from .models import CalculatorData, SubCalculatorData


    class SubProcess(BaseResource):
        DATA_CLASS = SubCalculatorData

        def container_calculate(self, expression):
            return self.parent.calculate(expression)

        def get_ip_address(self):
            return self.parent.data.ip_address


    class Calculator(BaseResource):
        DATA_CLASS = CalculatorData

        PORT = 1357

        sub_process = SubProcess.request(data=CalculatorData.sub_process)

        def connect(self):
            super(Calculator, self).connect()
            self._rpyc = rpyc.classic.connect(self.data.ip_address, self.PORT)

        def finalize(self):
            super(Calculator, self).finalize()
            if self._rpyc is not None:
                self._rpyc.close()
                self._rpyc = None

        def calculate(self, expression):
            return self._rpyc.eval(expression)

        def get_sub_process_id(self, expression):
            return self.sub_process.data.process_id

Note the following:

* Declaring the sub-resource:

  .. code-block:: python

    sub_process = SubProcess.request(data=CalculatorData.sub_process)

  The syntax is the same as requesting resources for a test.

  We assigned the `SubCalculatorData` model instance (pointed from the
  containing resource's `CalculatorData`) as the ``data`` for out sub-resource.

  Alternatively, in case `SubProcess` was a service and not a full-fledged
  resource, we could have passed parameters to it in a similar way:

  .. code-block:: python

    sub_process = SubProcess.request(ip_address=CalculatorData.ip_address,
                                     process_id=CalculatorData.sub_process.process_id)

  Alternatively, you can also use rotest.management.DataPointer to point to data
  fields. This can be used to pass data from one service to its child:

  .. code-block:: python

    from rotest.management import BaseResource, DataPointer

    class SubProcess(BaseResource):

        DATA_CLASS = None

        def __init__(self, process_id, *args, **kwargs):
            super(SubProcess, self).__init__(*args, process_id=process_id, **kwargs)


    class Calculator(BaseResource):

        DATA_CLASS = None

        sub_process = SubProcess.request(process_id=DataPointer("process_id"))

        def __init__(self, process_id, *args, **kwargs):
            super(Calculator, self).__init__(*args, process_id=process_id, **kwargs)


* The usage of the sub-resource

  .. code-block:: python

    def get_sub_process_id(self, expression):
        return self.sub_process.process_id

  Once the sub-resource or service is declared, it can be accessed from any
  of the containing resource's methods, using the assigned name (in this case,
  the declaration line name it `sub_process`).


Note that we have access to the containing resource via `parent`.

This also applies when we write sub-services, which can use the parent's methods,
data, and even fields (e.g. `self.parent._rpyc`).

When writing sub-resources and services, remember:

 * Always call `super` when overriding BaseResource's methods (connect, initialize,
   validate, finalize, store_state), since the basic method propagate the call to
   sub-resources.

 * It is ok to use `self.parent` and `self.<sub-resource-name>` , but mind the context.
   E.g. `self.parent._rpyc` in the above example is accessible from the sub-resource,
   but only after the ``connect()`` method (since firstly the sub-resource connects,
   and only afterwards the containing resource connects). The same applies for the
   other basic methods (first the sub-resources initialize, then the containing).

 * Since python 3.7, the declaration order of sub-resources is the order in
   which the basic methods are called (connect, finalize, etc.). You can use this
   to break complex procedures into services that would do those actions.


Parallel initialization
=======================

Usually, the initialization process of resources takes a long time.
In order to speed things up, each resource has a ``PARALLEL_INITIALIZATION`` flag.

This flag defaults to `False`, but when it is set to `True` each sub-resource
would be validated and initialized in its own thread, before joining back to the
containing resource for the parent's custom validate-initialization code.

To activate it, simply write in the class scope of your complex resource:

.. code-block:: python

    class Calculator(BaseResource):
        DATA_CLASS = CalculatorData

        PARALLEL_INITIALIZATION = True

        sub_resource1 = SubResource.request()
        sub_resource2 = SubResource.request()
        sub_resource3 = SubResource.request()


Or you can point it to a variable which you can set/unset using an entry point
(see :ref:`custom_entry_points` to learn how to add CLI entry points).


Resource adapter
================

Sometimes, you'd want the resource class (in tests or sub-resources) to vary.
For example, if you have a resource that changes behavior according to the
current project or context, but still want the two behaviors to be inter-changable.

This is where the option to create a resource adapter helps you.

Generally, you can derive from the class ``rotest.management.ResourceRequest``
and implement yourself the `get_type` and `__init__` methods in accordance with
your specific needs. In most cases the environmental context you need exists
in the run config file, which is the argument to the `get_type` method.

Example for a resource adapter:

.. code-block:: python

    from rotest.management.base_resource import ResourceRequest


    class ResourceAdapter(ResourceRequest):
        """Holds the data for a resource request."""
        def get_type(self, config):
            """Get the requested resource class.

            Args:
                config (dict): the configuration file being used.
            """
            if config.get('project') == 'A':
                return ResourceA

            else:
                return ResourceB


    class AdaptiveTest(TestCase):

        res = ResourceAdapter()


This will give the test a resource named 'res' that would be either an instance
of `ResourceA` or of `ResourceB` depending on the value of the field 'project'
in the run config json file.

You can also pass kwargs to the adapter the same way you would to BaseResource.request().

Similarly, you can also declare adaptive sub-resources:

.. code-block:: python

    from rotest.management import ResourceAdapter

    class AdaptiveResource(BaseResource):
        DATA_CLASS = CalculatorData

        sub_resource = ResourceAdapter(data=CalculatorData.sub_process)

