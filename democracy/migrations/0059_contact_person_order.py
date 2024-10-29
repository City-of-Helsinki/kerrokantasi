# Generated by Django 3.2.13 on 2022-07-28 18:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0058_poll_answer_cascade"),
    ]

    operations = [
        # refs. https://stackoverflow.com/a/40654521/12730861
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="ContactPersonOrder",
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
                            "contactperson",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="democracy.contactperson",
                            ),
                        ),
                        (
                            "hearing",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="democracy.hearing",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "democracy_hearing_contact_persons",
                    },
                ),
                migrations.AlterField(
                    model_name="hearing",
                    name="contact_persons",
                    field=models.ManyToManyField(
                        related_name="hearings",
                        through="democracy.ContactPersonOrder",
                        to="democracy.ContactPerson",
                        verbose_name="contact persons",
                    ),
                ),
            ]
        )
    ]
