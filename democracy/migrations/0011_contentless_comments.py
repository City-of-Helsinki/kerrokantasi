# Generated by Django 1.9.2 on 2016-03-17 13:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('democracy', '0010_auto_20160315_1026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hearingcomment',
            name='content',
            field=models.TextField(blank=True, verbose_name='content'),
        ),
        migrations.AlterField(
            model_name='sectioncomment',
            name='content',
            field=models.TextField(blank=True, verbose_name='content'),
        ),
    ]
