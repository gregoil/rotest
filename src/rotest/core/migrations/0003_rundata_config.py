# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20170308_1248'),
    ]

    operations = [
        migrations.AddField(
            model_name='rundata',
            name='config',
            field=models.TextField(default=b'{}', null=True, blank=True),
            preserve_default=True,
        ),
    ]
