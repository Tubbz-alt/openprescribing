# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-02-23 15:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0013_auto_20161107_1213'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pct',
            name='managing_group',
        ),
        migrations.RemoveField(
            model_name='practice',
            name='area_team',
        ),
    ]
