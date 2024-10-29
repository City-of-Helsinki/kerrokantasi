# Generated by Django 1.11.10 on 2018-03-21 12:28
from __future__ import unicode_literals

import django.db.models.deletion
import django.utils.timezone
import parler.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("democracy", "0037_change_djgeojson_field_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionPoll",
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
                    "type",
                    models.CharField(
                        choices=[
                            ("single-choice", "single choice poll"),
                            ("multiple-choice", "multiple choice poll"),
                        ],
                        max_length=255,
                        verbose_name="poll type",
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
                    "is_independent_poll",
                    models.BooleanField(
                        default=False, verbose_name="poll may be used independently"
                    ),
                ),
                (
                    "n_answers",
                    models.IntegerField(
                        default=0,
                        editable=False,
                        help_text="number of answers given to this poll",
                        verbose_name="answer count",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sectionpoll_created",
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
                        related_name="sectionpoll_modified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="last modified by",
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polls",
                        to="democracy.Section",
                    ),
                ),
            ],
            options={
                "verbose_name": "section poll",
                "verbose_name_plural": "section polls",
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="SectionPollAnswer",
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
                    "source_client",
                    models.CharField(
                        max_length=255, verbose_name="name for sender client"
                    ),
                ),
                (
                    "comment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="poll_answers",
                        to="democracy.SectionComment",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sectionpollanswer_created",
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
                        related_name="sectionpollanswer_modified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="last modified by",
                    ),
                ),
            ],
            options={
                "verbose_name": "section poll answer",
                "verbose_name_plural": "section poll answers",
            },
        ),
        migrations.CreateModel(
            name="SectionPollOption",
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
                    "ordering",
                    models.IntegerField(
                        db_index=True,
                        default=1,
                        help_text="The ordering position for this object. Objects with smaller numbers appear first.",
                        verbose_name="ordering",
                    ),
                ),
                (
                    "n_answers",
                    models.IntegerField(
                        default=0,
                        editable=False,
                        help_text="number of answers given with this option",
                        verbose_name="answer count",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sectionpolloption_created",
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
                        related_name="sectionpolloption_modified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="last modified by",
                    ),
                ),
                (
                    "poll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="options",
                        to="democracy.SectionPoll",
                    ),
                ),
            ],
            options={
                "verbose_name": "section poll option",
                "verbose_name_plural": "section poll options",
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="SectionPollOptionTranslation",
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
                ("text", models.TextField(verbose_name="option text")),
                (
                    "master",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="democracy.SectionPollOption",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
                "db_tablespace": "",
                "db_table": "democracy_sectionpolloption_translation",
                "managed": True,
                "verbose_name": "section poll option Translation",
            },
        ),
        migrations.CreateModel(
            name="SectionPollTranslation",
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
                ("text", models.TextField(verbose_name="text")),
                (
                    "master",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="democracy.SectionPoll",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
                "db_tablespace": "",
                "db_table": "democracy_sectionpoll_translation",
                "managed": True,
                "verbose_name": "section poll Translation",
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
        migrations.AddField(
            model_name="sectionpollanswer",
            name="option",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="answers",
                to="democracy.SectionPollOption",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="sectionpolltranslation",
            unique_together=set([("language_code", "master")]),
        ),
        migrations.AlterUniqueTogether(
            name="sectionpolloptiontranslation",
            unique_together=set([("language_code", "master")]),
        ),
    ]
