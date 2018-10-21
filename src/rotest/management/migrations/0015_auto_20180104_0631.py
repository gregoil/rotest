# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0014_remove_resourcedata_dirty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoresourcedata',
            name='validate_flag',
            field=models.NullBooleanField(default=False),
            preserve_default=True,
        ),
    ]
