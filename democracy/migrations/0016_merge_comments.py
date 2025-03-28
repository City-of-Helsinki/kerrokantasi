# Generated by Django 1.9.2 on 2016-05-18 13:18
from __future__ import unicode_literals

from django.core.management.base import CommandError
from django.db import migrations
from django.db.models import Sum


def forwards(apps, schema_editor):
    """
    Convert Hearing comments to introduction Section comments
    """
    hearing_comments = apps.get_model("democracy", "HearingComment").objects.filter(
        hearing__deleted=False
    )
    section_comment_model = apps.get_model("democracy", "SectionComment")

    for hearing_comment in hearing_comments:
        data = {
            field: getattr(hearing_comment, field)
            for field in (
                "content",
                "author_name",
                "n_votes",
                "created_by",
                "created_at",
                "modified_at",
                "modified_by",
            )
        }

        section = hearing_comment.hearing.sections.filter(
            type__identifier="introduction", deleted=False
        ).first()
        if not section:
            raise CommandError(
                "Hearing '%s' has HearingComment(s) but not an introduction section for those."
                % hearing_comment.hearing_id
            )

        data["section"] = section
        section_comment_model.objects.create(**data)

        new_n_comments = section.comments.count()
        if new_n_comments != section.n_comments:
            section.n_comments = new_n_comments
            section.save(update_fields=("n_comments",))

    for hearing in apps.get_model("democracy", "Hearing").objects.all():
        new_n_comments = (
            hearing.sections.all().aggregate(Sum("n_comments")).get("n_comments__sum")
            or 0
        )
        if new_n_comments != hearing.n_comments:
            hearing.n_comments = new_n_comments
            hearing.save(update_fields=("n_comments",))


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0015_add_organization_model"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="hearingcomment",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="hearingcomment",
            name="hearing",
        ),
        migrations.RemoveField(
            model_name="hearingcomment",
            name="modified_by",
        ),
        migrations.RemoveField(
            model_name="hearingcomment",
            name="voters",
        ),
        migrations.DeleteModel(
            name="HearingComment",
        ),
    ]
