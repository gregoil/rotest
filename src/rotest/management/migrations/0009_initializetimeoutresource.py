# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0008_add_owner_reserved_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='InitializeTimeoutResource',
            fields=[
                ('baseresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.BaseResource')),
            ],
            options={
            },
            bases=('management.baseresource',),
        ),
    ]
