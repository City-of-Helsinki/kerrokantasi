# Generated by Django 1.9.6 on 2016-10-28 14:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0026_add_plugin_iframe_url_to_section"),
    ]

    operations = [
        migrations.AddField(
            model_name="section",
            name="plugin_fullscreen",
            field=models.BooleanField(default=False),
        ),
    ]
