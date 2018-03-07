# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0013_auto_20170308_1248'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcedata',
            name='dirty',
        ),
    ]
