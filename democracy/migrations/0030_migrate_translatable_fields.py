# Generated by Django 1.9.10 on 2016-12-08 12:00
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations

IMPORT_LANGUAGE_CODE = "fi"  # Assume that the existing content is in Finnish


def assign(obj_dest, obj_src, fields):
    for field in fields:
        if field in ["id", "master", "language_code"]:
            continue
        setattr(obj_dest, field, getattr(obj_src, field))


def forwards_func_factory(modelname):
    def forwards_func(apps, schema_editor):
        MyModel = apps.get_model("democracy", modelname)
        MyModelTranslation = apps.get_model("democracy", "%sTranslation" % modelname)
        model_fields = [f.name for f in MyModelTranslation._meta.get_fields()]

        for obj in MyModel.objects.all():
            translation = MyModelTranslation(
                master_id=obj.pk,
                language_code=IMPORT_LANGUAGE_CODE,
            )
            assign(translation, obj, model_fields)
            translation.save()

    return forwards_func


def backwards_func_factory(modelname):
    def backwards_func(apps, schema_editor):
        MyModel = apps.get_model("democracy", modelname)
        MyModelTranslation = apps.get_model("democracy", "%sTranslation" % modelname)
        model_fields = [f.name for f in MyModelTranslation._meta.get_fields()]

        for obj in MyModel.objects.all():
            try:
                translation = _get_translation(obj, MyModelTranslation)
                assign(obj, translation, model_fields)
                obj.save()  # Note this only calls Model.save() in South.
            except ObjectDoesNotExist:
                pass

    return backwards_func


def _get_translation(obj, MyModelTranslation):  # noqa: N803
    translations = MyModelTranslation.objects.filter(master_id=obj.pk)
    try:
        # Try default translation
        return translations.get(language_code=IMPORT_LANGUAGE_CODE)
    except ObjectDoesNotExist:
        try:
            # Try default language
            return translations.get(language_code=settings.PARLER_DEFAULT_LANGUAGE_CODE)
        except ObjectDoesNotExist:
            # Maybe the object was translated only in a specific language?
            # Hope there is a single translation
            return translations.get()


class Migration(migrations.Migration):
    dependencies = [
        ("democracy", "0029_add django-parler fields"),
    ]

    operations = [
        migrations.RunPython(
            forwards_func_factory("Label"), backwards_func_factory("Label")
        ),
        migrations.RunPython(
            forwards_func_factory("Section"), backwards_func_factory("Section")
        ),
        migrations.RunPython(
            forwards_func_factory("Hearing"), backwards_func_factory("Hearing")
        ),
        migrations.RunPython(
            forwards_func_factory("SectionImage"),
            backwards_func_factory("SectionImage"),
        ),
        migrations.RunPython(
            forwards_func_factory("ContactPerson"),
            backwards_func_factory("ContactPerson"),
        ),
    ]
