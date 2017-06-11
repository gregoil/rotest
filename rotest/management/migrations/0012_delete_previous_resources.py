# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0011_refactored_to_resourcedata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='democomplexresource',
            name='complexresource_ptr',
        ),
        migrations.RemoveField(
            model_name='democomplexresource',
            name='demo1',
        ),
        migrations.RemoveField(
            model_name='democomplexresource',
            name='demo2',
        ),
        migrations.DeleteModel(
            name='DemoComplexResource',
        ),
        migrations.RemoveField(
            model_name='demoresource',
            name='baseresource_ptr',
        ),
        migrations.DeleteModel(
            name='DemoResource',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='group',
        ),
        migrations.DeleteModel(
            name='ComplexResource',
        ),
        migrations.DeleteModel(
            name='FinalizeTimeoutResource',
        ),
        migrations.DeleteModel(
            name='InitializeTimeoutResource',
        ),
        migrations.DeleteModel(
            name='NonExistingResource',
        ),
        migrations.DeleteModel(
            name='BaseResource',
        ),
    ]
