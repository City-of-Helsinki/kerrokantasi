# Generated by Django 1.9.4 on 2016-03-15 10:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0009_section_type_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="hearingcomment",
            name="authorization_code",
            field=models.CharField(
                blank=True, max_length=32, verbose_name="authorization code"
            ),
        ),
        migrations.AddField(
            model_name="sectioncomment",
            name="authorization_code",
            field=models.CharField(
                blank=True, max_length=32, verbose_name="authorization code"
            ),
        ),
    ]
