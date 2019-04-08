# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20181112_0631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casedata',
            name='exception_type',
            field=models.IntegerField(blank=True, null=True, choices=[(0, 'Success'), (1, 'Error'), (2, 'Failed'), (3, 'Skipped'), (4, 'Expected Failure'), (5, 'Unexpected Success')]),
        ),
        migrations.AlterField(
            model_name='generaldata',
            name='status',
            field=models.IntegerField(default=0, choices=[(0, 'Initialized'), (1, 'In Progress'), (2, 'Finished')]),
        ),
        migrations.AlterField(
            model_name='rundata',
            name='config',
            field=models.TextField(blank=True, null=True, default='{}'),
        ),
    ]
