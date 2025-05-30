from rest_framework.renderers import JSONRenderer


class GeoJSONRenderer(JSONRenderer):
    format = "geojson"

    def get_paginated_response(self, data):
        geojson = {
            "type": "FeatureCollection",
            "count": data["count"],
            "next": data["next"],
            "previous": data["previous"],
            "features": [],
        }
        for item in data["results"]:
            geojson["features"].append(self.geojsonify(item))
        return geojson

    def get_single_response(self, data):
        geojson = data.get("geojson")
        if not geojson:
            # missing geometry is indicated by null in the GeoJSON specification
            geojson = {"type": "Feature", "geometry": None}
        if geojson["type"] not in ["Feature", "FeatureCollection"]:
            # the object must be embedded in feature
            geojson = {"type": "Feature", "geometry": geojson}
        geojson["id"] = data["id"]
        if "properties" not in geojson:
            geojson["properties"] = {}
        for key, value in data.items():
            # the elements to include
            if key not in ("geojson",):
                geojson["properties"][key] = value
        return geojson

    def get_list_response(self, data):
        geojson = {"type": "FeatureCollection", "features": []}
        for item in data:
            geojson["features"].append(self.geojsonify(item))
        return geojson

    def geojsonify(self, data):
        if "results" in data:
            return self.get_paginated_response(data)
        elif isinstance(data, dict):
            return self.get_single_response(data)
        elif isinstance(data, list):
            return self.get_list_response(data)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return super().render(
            self.geojsonify(data), accepted_media_type, renderer_context
        )
