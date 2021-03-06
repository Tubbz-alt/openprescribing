# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-07 13:43


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='amp',
            options={'ordering': ['descr'], 'verbose_name': 'Actual Medicinal Product'},
        ),
        migrations.AlterModelOptions(
            name='ampp',
            options={'ordering': ['nm'], 'verbose_name': 'Actual Medicinal Product Pack'},
        ),
        migrations.AlterModelOptions(
            name='vmp',
            options={'ordering': ['nm'], 'verbose_name': 'Virtual Medicinal Product'},
        ),
        migrations.AlterModelOptions(
            name='vmpp',
            options={'ordering': ['nm'], 'verbose_name': 'Virtual Medicinal Product Pack'},
        ),
        migrations.AlterModelOptions(
            name='vtm',
            options={'ordering': ['nm'], 'verbose_name': 'Virtual Therapeutic Moiety', 'verbose_name_plural': 'Virtual Therapeutic Moieties'},
        ),
        migrations.AddField(
            model_name='amp',
            name='bnf_code',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='ampp',
            name='bnf_code',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='vmp',
            name='bnf_code',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='vmpp',
            name='bnf_code',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
