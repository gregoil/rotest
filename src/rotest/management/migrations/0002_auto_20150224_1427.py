# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.auth import models as auth_models


USERNAME = 'rotest'
PASSWORD = 'rotest'


def create_super_user(apps, schema_editor):
    try:
        auth_models.User.objects.get(username=USERNAME)
    except auth_models.User.DoesNotExist:
        auth_models.User.objects.create_superuser(USERNAME, 'rotest@rotest.com', PASSWORD)


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
    ]

    operations = [migrations.RunPython(create_super_user)
    ]
