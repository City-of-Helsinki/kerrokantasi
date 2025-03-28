# Generated by Django 1.9.2 on 2016-05-11 13:33
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0012_add_hearing_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hearing",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                verbose_name="slug",
                editable=True,
                populate_from="title",
                unique=True,
                blank=True,
            ),
        ),
    ]
