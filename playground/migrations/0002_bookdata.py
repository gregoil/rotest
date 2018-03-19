# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0013_auto_20170308_1248'),
        ('playground', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookData',
            fields=[
                ('resourcedata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.ResourceData')),
                ('title', models.TextField()),
                ('author', models.TextField()),
            ],
            options={
            },
            bases=('management.resourcedata',),
        ),
    ]
