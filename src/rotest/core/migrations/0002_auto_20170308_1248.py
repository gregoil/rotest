# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import rotest.common.django_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaldata',
            name='name',
            field=rotest.common.django_utils.fields.NameField(max_length=150),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rundata',
            name='run_name',
            field=rotest.common.django_utils.fields.NameField(max_length=150, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rundata',
            name='user_name',
            field=rotest.common.django_utils.fields.NameField(max_length=150, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='signaturedata',
            name='name',
            field=rotest.common.django_utils.fields.NameField(unique=True, max_length=150),
            preserve_default=True,
        ),
    ]
