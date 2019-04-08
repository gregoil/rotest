# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0017_auto_20181202_0752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoresourcedata',
            name='mode',
            field=models.IntegerField(default=0, choices=[(0, 'Boot'), (1, 'Production')]),
        ),
        migrations.AlterField(
            model_name='resourcedata',
            name='comment',
            field=models.CharField(max_length=200, blank=True, default=''),
        ),
    ]
