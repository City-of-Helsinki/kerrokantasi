from pathlib import PurePath

from django.utils import timezone
from django.utils.crypto import get_random_string


def upload_image_to(_instance, filename):
    extension = PurePath(filename).suffix.lower()
    return f"images/{timezone.now():%Y/%m}/{get_random_string(8)}{extension}"
