# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0016_demoresourcedata_validation_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoresourcedata',
            name='ip_address',
            field=models.GenericIPAddressField(),
        ),
    ]
