===============
Using Resources
===============

The true power of Rotest is in its client-server infrastructure, which enables
writing resource-oriented tests, running a dedicated server to hold all
resources, and enabling clients run tests.

In this tutorial, you'll learn:

* How to create a resource class.
* How to run the server, that acts as a resource manager.
* How to write tests that use resources.

Creating a Resource Class
=========================

In the root of your project, create a new Django application:

.. code-block:: console

    $ django-admin startapp resources

You'll see a new directory named :file:`resources`, in the following structure:

.. code-block:: console

    .
    ├── manage.py
    ├── resources
    │   ├── admin.py
    │   ├── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    ├── rotest_demo
    │   ├── __init__.py
    │   ├── __init__.pyc
    │   ├── settings.py
    │   ├── settings.pyc
    │   ├── urls.py
    │   └── wsgi.py
    ├── rotest.yml
    └── test_math.py

Don't forget to add the new application as well as ``rotest`` to the
``INSTALLED_APPS`` configuration in the :file:`rotest_demo/settings.py` file:

.. code-block:: python

    ...

    INSTALLED_APPS = (
        'rotest.core',
        'rotest.management',
        'resources',
        'django.contrib.admin',
        'django.contrib.auth',
        ...
    )

We're going to write a simple resource of a calculator. Edit the
:file:`resources/models.py` file to have the following content:

.. code-block:: python

    from django.db import models
    from rotest.management.models import resource_data


    class CalculatorData(resource_data.ResourceData):
        class Meta:
            app_label = "resources"

        ip_address = models.IPAddressField()

The :class:`CalculatorData` class is the database definition of the Calculator
resource. It defines any characteristics it has, as oppose to behaviour it may
have. It's also recommended adding it to the Django admin panel. Edit the
content of the :file:`resources/admin.py` file:

.. code-block:: python

    from rotest.management.admin import register_resource_to_admin

    from . import models

    register_resource_to_admin(models.CalculatorData, attr_list=['ip_address'])

Let's continue to write the Calculator resource, which exposes a simple
calculation action. Edit the file :file:`resources/calculator.py`:

.. code-block:: python

    import rpyc
    from rotest.management.base_resource import BaseResource

    from .models import CalculatorData


    class Calculator(BaseResource):
        DATA_CLASS = CalculatorData

        PORT = 1357

        def connect(self):
            self._rpyc = rpyc.classic.connect(self.data.ip_address, self.PORT)

        def calculate(self, expression):
            return self._rpyc.eval(expression)

        def finalize(self):
            if self._rpyc is not None:
                self._rpyc.close()
                self._rpyc = None

Note the following:

* There is a use in the ``RPyC`` module, which can be installed using:

  .. code-block:: console

    $ pip install rpyc

* The :class:`Calculator` class inherits from
  :class:`rotest.management.base_resource.BaseResource`.

* The previously declared class :class:`CalculatorData` is referenced in this
  class.

* Two methods are used to set up and tear down the connection to the resource:
  :meth:`rotest.management.base_resource.BaseResource.connect`
  and :meth:`rotest.management.base_resource.BaseResource.finalize`.

Running the Resource Management Server
======================================

First, let's initialize the database with the following Django commands:

.. code-block:: console

    $ python manage.py makemigrations
    Migrations for 'resources':
      0001_initial.py:
        - Create model CalculatorData
    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: core, management, sessions, admin, auth, contenttypes, resources
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying auth.0001_initial... OK
      Applying admin.0001_initial... OK
      Applying management.0001_initial... OK
      Applying management.0002_auto_20150224_1427... OK
      Applying management.0003_add_isusable_and_comment... OK
      Applying management.0004_auto_20150702_1312... OK
      Applying management.0005_auto_20150702_1403... OK
      Applying management.0006_delete_projectdata... OK
      Applying management.0007_baseresource_group... OK
      Applying management.0008_add_owner_reserved_time... OK
      Applying management.0009_initializetimeoutresource... OK
      Applying management.0010_finalizetimeoutresource... OK
      Applying management.0011_refactored_to_resourcedata... OK
      Applying management.0012_delete_previous_resources... OK
      Applying core.0001_initial... OK
      Applying core.0002_auto_20170308_1248... OK
      Applying management.0013_auto_20170308_1248... OK
      Applying resources.0001_initial... OK
      Applying sessions.0001_initial... OK

The first command creates a migrations file, that orders changing the database
schemas or contents. The second command changes the database according to
those orders. If the database does not already exist, it creates it.

Let's run the Rotest server, using the :program:`rotest-server` command:

.. program:: rotest-server

.. code-block:: console

    $ rotest-server --run-django-server --django-port 8080 --daemon
    Running in detached mode (as daemon)

.. warning::

    The :option:`--daemon` option is not implemented in Windows.

A few explanations about this command:

* If given the :option:`--run-django-server` option, it runs the Django admin
  panel as well. We'll access it in the next section.

* If given the :option:`--django-port` option, it uses this value as the
  port of the Django admin panel. If not given, it defaults to ``8000``.

* If given the :option:`--daemon` or :option:`-D` option, the program runs in
  the background.

Adding a Resource on Django Admin Panel
=======================================

To sum this up, let's add a Calculator resource. Run the `createsuperuser`
command to get access to the admin panel:

.. code-block:: console

    $ python manage.py createsuperuser
    Username (leave blank to use 'user'): <choose a user in here>
    Email address: <choose your email address>
    Password: <type in your password>
    Password (again): <type password again>
    Superuser created successfully.

Now, Just enter the Django admin panel (via `<http://127.0.0.1:8080/admin>`_),
access it using the above credentials, and add a resource with the name
``calc`` and a local IP address like ``127.0.0.1``:

.. figure:: adding_resource.png
    :target: ../_images/adding_resource.png

    Adding a resource via Dango admin

Writing a Resource-Based Test
=============================

In this section, we are going to add a resource request to our existing test.
The first thing we need to do, is setting up our resource named ``calc``. We
need to run the RPyC server of the calculator, using the following command:

.. code-block:: console

    $ rpyc_classic.py --port 1357
    INFO:SLAVE/1357:server started on [0.0.0.0]:1357

This way, we have a way to communicate to our resource, which is running on
our local computer (or may run on other computer, assuming you've set the
corresponding IP address in the Django admin).

Now, let's change the previously written module :file:`test_math.py` with the
following content:

.. code-block:: python

    from rotest.core.runner import main
    from rotest.core.case import TestCase

    from resources.calculator import Calculator


    class AddTest(TestCase):
        calc = Calculator()

        def test_add(self):
            result = self.calc.calculate("1 + 1")
            self.assertEqual(result, 2)


    if __name__ == "__main__":
        main(AddTest)

Now, let's run the test:

.. code-block:: console

    $ python test_math.py
    AnonymousSuite
      AddTest.test_add ... OK

    Ran 1 test in 0.160s

    OK

Well done! You've just written your first resource oriented test, that asserts
the behaviour of a simple addition of a Calculator resource.
