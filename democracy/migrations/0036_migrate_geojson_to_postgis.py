from __future__ import unicode_literals

import json

import django.contrib.gis.db.models.fields

from django.contrib.gis.geos import GEOSGeometry
from django.db import migrations


def get_geometry_from_geojson(geojson):
    if geojson is None:
        return None
    geometry_data = geojson.get('geometry', None) or geojson
    geometry = GEOSGeometry(json.dumps(geometry_data))
    return geometry


def hearings_data_migration(apps, schema_editor):
    Hearing = apps.get_model('democracy', 'Hearing')
    for hearing in Hearing.objects.filter(geojson__isnull=False):
        hearing.geometry = get_geometry_from_geojson(hearing.geojson)
        hearing.save()


def sectioncomments_data_migration(apps, schema_editor):
    SectionComment = apps.get_model('democracy', 'SectionComment')
    for comment in SectionComment.objects.filter(geojson__isnull=False):
        comment.geometry = get_geometry_from_geojson(comment.geojson)
        comment.save()


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('democracy', '0035_remove_section_plugin_iframe_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='hearing',
            name='geometry',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326, verbose_name='area'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sectioncomment',
            name='geometry',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326, verbose_name='location'),
            preserve_default=False,
        ),
        migrations.RunPython(hearings_data_migration, backwards_noop),
        migrations.RunPython(sectioncomments_data_migration, backwards_noop),
    ]
