# -*- coding: utf-8 -*-
import json
import os
from django.utils.dateparse import parse_datetime
from kk.models.images import BaseImage

IMAGES = {
    "ORIGINAL": 'original.jpg',
    "SMALL": 'small.jpg',
    "THUMBNAIL": 'thumbnail.jpg'
}

IMAGE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "images")


def create_image(instance, filename):
    image_class = BaseImage.find_subclass(parent_model=instance)
    image_field = image_class._meta.get_field("image")
    image_path = image_field.generate_filename(instance, filename)
    if not image_field.storage.exists(image_path):  # Copy the image into the storage if it isn't there
        with open(os.path.join(IMAGE_SOURCE_PATH, filename), "rb") as infp:
            image_field.storage.save(image_path, infp)
    image_file = image_field.storage.open(image_path)
    return instance.images.create(image=image_file, title=filename)


def create_default_images(instance):
    for key, filename in IMAGES.items():
        create_image(instance, filename)


def get_data_from_response(response, status_code=200):
    if status_code:
        assert response.status_code == status_code, "Status code mismatch"
    return json.loads(response.content.decode('utf-8'))


def assert_datetime_fuzzy_equal(dt1, dt2, fuzziness=1):
    if isinstance(dt1, str):
        dt1 = parse_datetime(dt1)
    if isinstance(dt2, str):
        dt2 = parse_datetime(dt2)

    assert abs(dt1 - dt2).total_seconds() < fuzziness
