# -*- coding: utf-8 -*-
import base64
import json
import os
from io import BytesIO

from django.utils.dateparse import parse_datetime
from PIL import Image

from democracy.models.images import BaseImage

IMAGES = {
    "ORIGINAL": 'original.jpg',
    "SMALL": 'small.jpg',
    "THUMBNAIL": 'thumbnail.jpg'
}

IMAGE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "images")


def image_to_base64(filename):
    buffered = BytesIO()
    image = Image.open(os.path.join(IMAGE_SOURCE_PATH, filename))
    image.save(buffered, format="JPEG")
    return 'data:image/jpg;base64,%s' % base64.b64encode(buffered.getvalue()).decode('ascii')


def create_image(instance, filename):
    image_class = BaseImage.find_subclass(parent_model=instance)
    image_field = image_class._meta.get_field("image")
    image_path = image_field.generate_filename(instance, filename)
    # Copy the image into the storage if it isn't there:
    if not image_field.storage.exists(image_path):  # pragma: no cover
        with open(os.path.join(IMAGE_SOURCE_PATH, filename), "rb") as infp:
            image_field.storage.save(image_path, infp)
    image = image_class(title=filename, **{image_class.parent_field: instance})
    image.image.name = image_path
    image.save()
    assert image.image.name == image_path
    return image


def create_default_images(instance):
    for key, filename in IMAGES.items():
        create_image(instance, filename)


def get_data_from_response(response, status_code=200):
    if status_code:  # pragma: no branch
        assert response.status_code == status_code, (
            "Status code mismatch (%s is not the expected %s)" % (response.status_code, status_code)
        )
    return json.loads(response.content.decode('utf-8'))


def assert_datetime_fuzzy_equal(dt1, dt2, fuzziness=1):
    if isinstance(dt1, str):
        dt1 = parse_datetime(dt1)
    if isinstance(dt2, str):
        dt2 = parse_datetime(dt2)

    assert abs(dt1 - dt2).total_seconds() < fuzziness


def assert_ascending_sequence(seq):
    last = None
    for x in seq:
        if last is not None:
            assert x > last
        last = x


def get_hearing_detail_url(id, element=None):
    url = '/v1/hearing/%s/' % id
    if element:
        url += "%s/" % element
    return url


def get_geojson():
    return {
        "type": "Feature",
        "properties": {
            "name": "Coors Field",
            "amenity": "Baseball Stadium",
            "popupContent": "This is where the Rockies play!"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [-104.99404, 39.75621]
        }
    }


def assert_id_in_results(id, results, expected=True):
    included = id in [value['id'] for value in results]
    assert included is expected


def assert_common_keys_equal(dict1, dict2):
    for key in set(dict1) & set(dict2):
        assert dict1[key] == dict2[key]
