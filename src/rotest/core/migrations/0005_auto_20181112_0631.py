# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20181111_0319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signaturedata',
            name='pattern',
            field=models.TextField(max_length=1000),
        ),
    ]
