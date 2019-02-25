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
            app_label = "resources"

        process_id = models.IntegerField()


    class CalculatorData(ResourceData):
        class Meta:
            app_label = "resources"

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
:file:`resources/sub_process.py`.

Now, edit the file :file:`resources/resources.py`:

.. code-block:: python

    import rpyc
    from rotest.management.base_resource import BaseResource

    from .models import CalculatorData
    from .sub_process import SubProcess


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
                                     process_id=5)

* The usage of the sub-resource

  .. code-block:: python

    def get_sub_process_id(self, expression):
        return self.sub_process.process_id

  Once the sub-resource or service is declared, it can be accessed from any
  of the containing resource's methods, using the assigned name (in this case,
  the declaration line name it `sub_process`).


Lastly, let's show the sub-resource under :file:`resources/sub_process.py`:

.. code-block:: python

    from rotest.management.base_resource import BaseResource

    from .models import SubCalculatorData


    class SubProcess(BaseResource):
        DATA_CLASS = SubCalculatorData

        def container_calculate(self, expression):
            return self.parent.calculate(expression)

        def get_ip_address(self):
            return self.parent.data.ip_address

Note that we have access to the containing resource via `parent`.

This also applies when we write sub-services, which can use the parent's methods,
data, and even fields (e.g. `self.parent._rpyc`).

When writing sub-resources and services, remember two things:

 * Always call `super` when overriding BaseResource's methods (connect, initialize,
   validate, finalize, store_state), since the basic method propagate the call to
   sub-resources.

 * It is ok to use `self.parent` and `self.<sub-resource-name>` , but mind the context.
   E.g. `self.parent._rpyc` in the above example is accessible from the sub-resource,
   but only after the ``connect()`` method (since firstly the sub-resource connects,
   and only afterwards the containing resource connects). The same applies for the
   other basic methods (first the sub-resources initialize, then the containing).
