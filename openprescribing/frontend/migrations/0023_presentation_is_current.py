# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-04-03 07:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0022_auto_20170324_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentation',
            name='is_current',
            field=models.BooleanField(default=True),
        ),
    ]
