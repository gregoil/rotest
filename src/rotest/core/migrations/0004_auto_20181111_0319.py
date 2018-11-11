# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_rundata_config'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signaturedata',
            name='name',
        ),
        migrations.AlterField(
            model_name='signaturedata',
            name='link',
            field=models.CharField(max_length=200),
        ),
    ]
