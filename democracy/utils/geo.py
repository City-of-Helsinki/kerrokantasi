
import json

from django.contrib.gis.geos import GEOSGeometry


def get_geometry_from_geojson(geojson):
    if geojson is None:
        return None
    geometry_data = geojson.get('geometry', None) or geojson
    geometry = GEOSGeometry(json.dumps(geometry_data))
    return geometry
