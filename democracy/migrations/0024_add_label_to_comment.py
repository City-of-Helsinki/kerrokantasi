# Generated by Django 1.9.6 on 2016-09-19 09:56
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0023_add_comment_location_and_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="sectioncomment",
            name="label",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="democracy.Label",
                verbose_name="label",
            ),
        ),
    ]
