# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth import models as auth_models


def create_users(apps, schema_editor):
    try:
        auth_models.User.objects.get(username='rotest')
    except auth_models.User.DoesNotExist:
        auth_models.User.objects.create_superuser('rotest',
                                                  'rotest@rotest.com',
                                                  'rotest')

    try:
        auth_models.User.objects.get(username='localhost')
    except auth_models.User.DoesNotExist:
        auth_models.User.objects.create_user('localhost',
                                             'localhost@rotest.com',
                                             'localhost')


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
    ]

    operations = [migrations.RunPython(create_users)]
