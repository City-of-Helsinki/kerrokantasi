import base64
import hashlib
import hmac

from django.conf import settings


def get_hmac_b64_encoded(name):
    hash = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), name.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(hash).decode().replace("=", "")
