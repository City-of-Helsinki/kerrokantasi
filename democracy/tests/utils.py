import json
import os
from collections import Counter
from io import BytesIO
from typing import Iterable, Mapping

from django.utils.dateparse import parse_datetime
from PIL import Image

from audit_log.enums import Operation, Status
from audit_log.models import AuditLogEntry
from democracy.models.files import BaseFile
from democracy.models.images import BaseImage
from democracy.utils.file_to_base64 import file_to_base64

IMAGES = {
    "ORIGINAL": "original.jpg",
    "SMALL": "small.jpg",
    "THUMBNAIL": "thumbnail.jpg",
}

FILES = {
    "PDF": "dummy.pdf",
}

IMAGE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "images")
FILE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "files")


def test_file_to_base64():
    file = BytesIO(b"Binary")
    file.name = "funny.gif"

    assert file_to_base64(file) == "data:image/gif;base64,QmluYXJ5"


def image_to_bytesio(filename):
    buffered = BytesIO()
    image = Image.open(os.path.join(IMAGE_SOURCE_PATH, filename))
    image.save(buffered, format="JPEG")
    buffered.name = filename
    buffered.seek(0)
    return buffered


def file_to_bytesio(filename):
    file = open(os.path.join(FILE_SOURCE_PATH, filename), "rb")
    buffered = BytesIO(file.read())
    buffered.name = filename
    buffered.seek(0)
    return buffered


def image_test_json():
    return {
        "caption": "Test",
        "title": "Test title",
        "image": file_to_base64(image_to_bytesio(IMAGES["ORIGINAL"])),
    }


def sectionimage_test_json(title_en="Test title"):
    return {
        "caption": {
            "en": "Test",
            "fi": "Testi",
        },
        "title": {
            "en": title_en,
            "fi": "Finnish test title",
        },
        "alt_text": {
            "en": "Map of the area",
            "fi": "Rakennettavan alueen kartta",
        },
        "image": file_to_base64(image_to_bytesio(IMAGES["ORIGINAL"])),
    }


def sectionfile_multipart_test_data(title_en="Test title"):
    # multipart POST requires dumping subobjects as strings
    return {
        "caption": json.dumps(
            {
                "en": "Test",
                "fi": "Testi",
            }
        ),
        "title": json.dumps(
            {
                "en": title_en,
                "fi": "Finnish test title",
            }
        ),
    }


def sectionfile_base64_test_data(title_en="Test title"):
    return {
        "caption": {
            "en": "Test",
            "fi": "Testi",
        },
        "title": {
            "en": title_en,
            "fi": "Finnish test title",
        },
        "file": file_to_base64(file_to_bytesio(FILES["PDF"])),
    }


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
    for _key, filename in IMAGES.items():
        create_image(instance, filename)


def get_file_path(filename):
    return os.path.join(FILE_SOURCE_PATH, filename)


def get_image_path(filename):
    return os.path.join(IMAGE_SOURCE_PATH, filename)


def create_file(instance, filename):
    file_class = BaseFile.find_subclass(parent_model=instance)
    file_field = file_class._meta.get_field("file")
    file_path = file_field.generate_filename(instance, filename)
    # Copy the file into the storage if it isn't there:
    if not file_field.storage.exists(file_path):  # pragma: no cover
        with open(os.path.join(FILE_SOURCE_PATH, filename), "rb") as infp:
            file_field.storage.save(file_path, infp)
    file_obj = file_class(title=filename, **{file_class.parent_field: instance})
    file_obj.file.name = file_path
    file_obj.save()
    assert file_obj.file.name == file_path
    return file_obj


def create_default_files(instance):
    for _key, filename in FILES.items():
        create_file(instance, filename)


def get_data_from_response(response, status_code=200):
    if status_code:  # pragma: no branch
        assert response.status_code == status_code, (
            "Status code mismatch (%s is not the expected %s)"
            % (
                response.status_code,
                status_code,
            )
        )
    return json.loads(response.content.decode("utf-8"))


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
    url = "/v1/hearing/%s/" % id
    if element:
        url += "%s/" % element
    return url


def get_sectionfile_download_url(id):
    return "/v1/download/sectionfile/%s/" % id


def assert_id_in_results(id, results, expected=True):
    included = id in [value["id"] for value in results]
    assert included is expected


def assert_common_keys_equal(dict1, dict2):
    for key in set(dict1) & set(dict2):
        assert dict1[key] == dict2[key], (
            'dict1["%(key)s"] = %(v1)s while dict2["%(key)s"] = %(v2)s'
            % {
                "key": key,
                "v1": dict1[key],
                "v2": dict2[key],
            }
        )


def get_nested(data: Mapping, keys: Iterable):
    """Get a nested value from a mapping using an iterable of keys."""
    val = data
    for key in keys:
        val = val[key]
    return val


def instance_ids(instances: Iterable) -> set:
    """Get a set of unique IDs from an iterable of model instances, e.g. a list, queryset."""
    return {instance.id for instance in instances}


def assert_audit_log_entry(
    path: str,
    object_ids: list,
    count: int = 1,
    status: Status = Status.SUCCESS,
    operation: Operation = Operation.CREATE,
):
    assert AuditLogEntry.objects.count() == count
    audit_log_entry = AuditLogEntry.objects.order_by("-created_at").first()
    assert path in audit_log_entry.message["audit_event"]["target"]["path"]
    assert Counter(
        audit_log_entry.message["audit_event"]["target"]["object_ids"]
    ) == Counter(object_ids)
    assert audit_log_entry.message["audit_event"]["status"] == status.value
    assert audit_log_entry.message["audit_event"]["operation"] == operation.value
