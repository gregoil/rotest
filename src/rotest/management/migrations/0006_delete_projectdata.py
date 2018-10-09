# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0005_auto_20150702_1403'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProjectData',
        ),
    ]
