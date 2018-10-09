# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0015_auto_20180104_0631'),
    ]

    operations = [
        migrations.AddField(
            model_name='demoresourcedata',
            name='validation_result',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
