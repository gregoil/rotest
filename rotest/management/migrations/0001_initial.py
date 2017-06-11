# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import rotest.common.django_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', rotest.common.django_utils.fields.NameField(unique=True, max_length=64)),
                ('owner', rotest.common.django_utils.fields.NameField(max_length=64, blank=True)),
                ('reserved', rotest.common.django_utils.fields.NameField(max_length=64, blank=True)),
                ('work_dir', rotest.common.django_utils.fields.PathField(default=b'', max_length=200, blank=True)),
                ('dirty', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ComplexResource',
            fields=[
                ('baseresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.BaseResource')),
            ],
            options={
            },
            bases=('management.baseresource',),
        ),
        migrations.CreateModel(
            name='DemoComplexResource',
            fields=[
                ('complexresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.ComplexResource')),
                ('reset_flag', models.BooleanField(default=False)),
                ('validate_flag', models.NullBooleanField(default=None)),
                ('initialization_flag', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('management.complexresource',),
        ),
        migrations.CreateModel(
            name='DemoResource',
            fields=[
                ('baseresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.BaseResource')),
                ('version', models.PositiveSmallIntegerField()),
                ('ip_address', models.IPAddressField()),
                ('mode', models.IntegerField(default=0, choices=[(0, b'Boot'), (1, b'Production')])),
                ('reset_flag', models.BooleanField(default=False)),
                ('validate_flag', models.NullBooleanField(default=None)),
                ('initialization_flag', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('management.baseresource',),
        ),
        migrations.CreateModel(
            name='NonExistingResource',
            fields=[
                ('baseresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.BaseResource')),
            ],
            options={
            },
            bases=('management.baseresource',),
        ),
        migrations.CreateModel(
            name='ProjectData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', rotest.common.django_utils.fields.NameField(unique=True, max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='democomplexresource',
            name='demo1',
            field=models.ForeignKey(related_name='demo_resource1', to='management.DemoResource'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='democomplexresource',
            name='demo2',
            field=models.ForeignKey(related_name='demo_resource2', to='management.DemoResource'),
            preserve_default=True,
        ),
    ]
