
import json
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry


def get_geometry_from_geojson(geojson):
    gc = GeometryCollection()
    if geojson is None:
        return None
    geometry_data = geojson.get('geometry', None) or geojson
    
    if geometry_data.get('features'):
        for feature in geometry_data.get('features'):
            feature_geometry = feature.get('geometry')
            feature_GEOS = GEOSGeometry(json.dumps(feature_geometry))
            gc.append(feature_GEOS)
    else:
        geometry = GEOSGeometry(json.dumps(geometry_data))
        gc.append(geometry)
    return gc
