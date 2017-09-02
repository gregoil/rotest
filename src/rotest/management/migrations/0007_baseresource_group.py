# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('management', '0006_delete_projectdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
            preserve_default=True,
        ),
    ]
