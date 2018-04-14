"""Django utils contains all code and documents that are related to Django,
the settings.py file, urls.py etc.

Django is used in rotest as the test DB. It contains the resources, test cases,
test sets and etc. Django ORM modules are used in Rotest to manipulate the
main tests database, Django's 'AdminPage' is used as a GUI interface for
Rotest's database."""
# pylint: disable=unused-import
from .common import get_sub_model, linked_unicode
