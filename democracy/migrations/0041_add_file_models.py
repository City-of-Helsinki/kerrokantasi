# Generated by Django 1.11.10 on 2018-02-22 13:46
from __future__ import unicode_literals

import django.core.files.storage
import django.db.models.deletion
import django.utils.timezone
import parler.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("democracy", "0040_add_hearing_project_phase"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="time of creation",
                    ),
                ),
                (
                    "modified_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="time of last modification",
                    ),
                ),
                (
                    "published",
                    models.BooleanField(
                        db_index=True, default=True, verbose_name="public"
                    ),
                ),
                (
                    "deleted",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        editable=False,
                        verbose_name="deleted",
                    ),
                ),
                (
                    "uploaded_file",
                    models.FileField(
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/heikkjus/code/helsinki/kerrokantasi/var/protected"
                        ),
                        upload_to="files/%Y/%m",
                        verbose_name="file",
                    ),
                ),
                (
                    "ordering",
                    models.IntegerField(
                        db_index=True,
                        default=1,
                        help_text="The ordering position for this object. Objects with smaller numbers appear first.",
                        verbose_name="ordering",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sectionfile_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sectionfile_modified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="last modified by",
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="democracy.Section",
                    ),
                ),
            ],
            options={
                "verbose_name": "section file",
                "verbose_name_plural": "section files",
                "ordering": ("ordering",),
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="SectionFileTranslation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language_code",
                    models.CharField(
                        db_index=True, max_length=15, verbose_name="Language"
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True, default="", max_length=255, verbose_name="title"
                    ),
                ),
                (
                    "caption",
                    models.TextField(blank=True, default="", verbose_name="caption"),
                ),
                (
                    "master",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="democracy.SectionFile",
                    ),
                ),
            ],
            options={
                "verbose_name": "section file Translation",
                "db_tablespace": "",
                "default_permissions": (),
                "managed": True,
                "db_table": "democracy_sectionfile_translation",
            },
        ),
        migrations.AlterModelOptions(
            name="contactperson",
            options={
                "ordering": ["name"],
                "verbose_name": "contact person",
                "verbose_name_plural": "contact persons",
            },
        ),
        migrations.AlterModelOptions(
            name="sectionimage",
            options={
                "ordering": ("ordering",),
                "verbose_name": "section image",
                "verbose_name_plural": "section images",
            },
        ),
        migrations.AlterUniqueTogether(
            name="sectionfiletranslation",
            unique_together=set([("language_code", "master")]),
        ),
    ]
