# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0002_auto_20150224_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='comment',
            field=models.CharField(default=b'', max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseresource',
            name='is_usable',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
