# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import rotest.common.django_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('management', '0010_finalizetimeoutresource'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', rotest.common.django_utils.fields.NameField(unique=True, max_length=64)),
                ('dirty', models.BooleanField(default=False)),
                ('is_usable', models.BooleanField(default=True)),
                ('comment', models.CharField(default=b'', max_length=200, blank=True)),
                ('owner', rotest.common.django_utils.fields.NameField(max_length=64, blank=True)),
                ('reserved', rotest.common.django_utils.fields.NameField(max_length=64, blank=True)),
                ('owner_time', models.DateTimeField(null=True, blank=True)),
                ('reserved_time', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DemoResourceData',
            fields=[
                ('resourcedata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.ResourceData')),
                ('version', models.PositiveSmallIntegerField()),
                ('ip_address', models.IPAddressField()),
                ('mode', models.IntegerField(default=0, choices=[(0, b'Boot'), (1, b'Production')])),
                ('reset_flag', models.BooleanField(default=False)),
                ('validate_flag', models.NullBooleanField(default=None)),
                ('finalization_flag', models.BooleanField(default=False)),
                ('initialization_flag', models.BooleanField(default=False)),
                ('fails_on_finalize', models.BooleanField(default=False)),
                ('fails_on_initialize', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('management.resourcedata',),
        ),
        migrations.CreateModel(
            name='DemoComplexResourceData',
            fields=[
                ('resourcedata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='management.ResourceData')),
                ('reset_flag', models.BooleanField(default=False)),
                ('validate_flag', models.NullBooleanField(default=None)),
                ('finalization_flag', models.BooleanField(default=False)),
                ('initialization_flag', models.BooleanField(default=False)),
                ('demo1', models.ForeignKey(related_name='demo_resource1', to='management.DemoResourceData')),
                ('demo2', models.ForeignKey(related_name='demo_resource2', to='management.DemoResourceData')),
            ],
            options={
            },
            bases=('management.resourcedata',),
        ),
        migrations.AddField(
            model_name='resourcedata',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
            preserve_default=True,
        ),
    ]
