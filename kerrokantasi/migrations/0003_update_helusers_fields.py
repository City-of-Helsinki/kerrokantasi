# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-15 10:39
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helusers', '0001_add_ad_groups'),
        ('kerrokantasi', '0002_user_nickname'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('id',)},
        ),
        migrations.AddField(
            model_name='user',
            name='ad_groups',
            field=models.ManyToManyField(blank=True, to='helusers.ADGroup'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
    ]