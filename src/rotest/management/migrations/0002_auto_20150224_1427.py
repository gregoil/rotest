# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth import models as auth_models

ADMIN_USERNAME = "rotest"
ADMIN_PASSWORD = "rotest"


def create_users(apps, schema_editor):
    qa_group, _ = auth_models.Group.objects.get_or_create(name="QA")
    localhost, _ = auth_models.User.objects.get_or_create(username="localhost",
                                                          password="localhost",
                                                          email="l@l.com")
    qa_group.user_set.add(localhost)

    try:
        auth_models.User.objects.get(username=ADMIN_USERNAME)
    except auth_models.User.DoesNotExist:
        auth_models.User.objects.create_superuser(ADMIN_USERNAME,
                                                  "rotest@rotest.com",
                                                  ADMIN_PASSWORD)


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
    ]

    operations = [migrations.RunPython(create_users)
    ]
