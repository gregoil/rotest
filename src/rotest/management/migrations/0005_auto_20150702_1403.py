# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0004_auto_20150702_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='demoresource',
            name='fails_on_finalize',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='demoresource',
            name='fails_on_initialize',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
