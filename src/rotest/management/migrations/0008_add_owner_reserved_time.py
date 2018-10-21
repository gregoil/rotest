# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0007_baseresource_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='owner_time',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseresource',
            name='reserved_time',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
