# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import rotest.common.django_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0012_delete_previous_resources'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcedata',
            name='name',
            field=rotest.common.django_utils.fields.NameField(unique=True, max_length=150),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourcedata',
            name='owner',
            field=rotest.common.django_utils.fields.NameField(max_length=150, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourcedata',
            name='reserved',
            field=rotest.common.django_utils.fields.NameField(max_length=150, blank=True),
            preserve_default=True,
        ),
    ]
