# -*- coding: utf-8 -*-
import json
import os

from kk.models import Image

IMAGES = {
    "ORIGINAL": 'original.jpg',
    "SMALL": 'small.jpg',
    "THUMBNAIL": 'thumbnail.jpg'
}

IMAGE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "images")


def create_image(instance, filename):
    image_field = Image._meta.get_field("image")
    image_path = image_field.generate_filename(instance, filename)
    if not image_field.storage.exists(image_path):  # Copy the image into the storage if it isn't there
        with open(os.path.join(IMAGE_SOURCE_PATH, filename), "rb") as infp:
            image_field.storage.save(image_path, infp)
    image_file = image_field.storage.open(image_path)
    image = Image.objects.create(image=image_file, title=filename)
    instance.images.add(image)


def create_default_images(instance):
    for key, filename in IMAGES.items():
        create_image(instance, filename)


def get_data_from_response(response, status_code=200):
    if status_code:
        assert response.status_code == status_code, "Status code mismatch"
    return json.loads(response.content.decode('utf-8'))
