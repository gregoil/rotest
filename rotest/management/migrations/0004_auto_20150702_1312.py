# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0003_add_isusable_and_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='democomplexresource',
            name='finalization_flag',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='demoresource',
            name='finalization_flag',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
