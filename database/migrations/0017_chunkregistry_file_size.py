# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-05-17 23:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0016_auto_20181210_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='chunkregistry',
            name='file_size',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
