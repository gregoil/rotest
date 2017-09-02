# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import rotest.common.django_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0012_delete_previous_resources'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', rotest.common.django_utils.fields.NameField(max_length=64)),
                ('status', models.IntegerField(default=0, choices=[(0, b'Initialized'), (1, b'In Progress'), (2, b'Finished')])),
                ('start_time', models.DateTimeField(null=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('success', models.NullBooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CaseData',
            fields=[
                ('generaldata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.GeneralData')),
                ('traceback', models.TextField(max_length=1000, blank=True)),
                ('exception_type', models.IntegerField(blank=True, null=True, choices=[(0, b'OK'), (1, b'Error'), (2, b'Failed'), (3, b'Skipped'), (4, b'Expected Failure'), (5, b'Unexpected Success')])),
                ('resources', models.ManyToManyField(to='management.ResourceData')),
            ],
            options={
            },
            bases=('core.generaldata',),
        ),
        migrations.CreateModel(
            name='RunData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('run_name', rotest.common.django_utils.fields.NameField(max_length=64, null=True, blank=True)),
                ('artifact_path', rotest.common.django_utils.fields.PathField(max_length=200, null=True, blank=True)),
                ('run_delta', models.NullBooleanField(default=False)),
                ('user_name', rotest.common.django_utils.fields.NameField(max_length=64, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SignatureData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', rotest.common.django_utils.fields.NameField(unique=True, max_length=64)),
                ('link', models.CharField(max_length=100)),
                ('pattern', models.CharField(max_length=1000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SuiteData',
            fields=[
                ('generaldata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.GeneralData')),
            ],
            options={
            },
            bases=('core.generaldata',),
        ),
        migrations.AddField(
            model_name='rundata',
            name='main_test',
            field=models.ForeignKey(related_name='+', blank=True, to='core.GeneralData', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='generaldata',
            name='parent',
            field=models.ForeignKey(related_name='tests', blank=True, to='core.GeneralData', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='generaldata',
            name='run_data',
            field=models.ForeignKey(related_name='tests', blank=True, to='core.RunData', null=True),
            preserve_default=True,
        ),
    ]
