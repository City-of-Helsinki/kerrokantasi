import factory
import pytest
import shutil
from django.contrib.auth import get_user_model
from pytest_factoryboy import register
from rest_framework.test import APIClient

from democracy.factories.organization import OrganizationFactory

default_geojson_geometry = {"type": "Point", "coordinates": [-104.99404, 39.75621]}


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    uuid = factory.Faker("uuid4", cast_to=None)
    first_name = factory.Faker("first_name", locale="fi")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")


register(UserFactory)
register(OrganizationFactory)


def pytest_configure():
    """During tests, crypt passwords with MD5. This should make things run faster."""
    from django.conf import settings

    settings.PASSWORD_HASHERS = (
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
        "django.contrib.auth.hashers.BCryptPasswordHasher",
        "django.contrib.auth.hashers.SHA1PasswordHasher",
        "django.contrib.auth.hashers.CryptPasswordHasher",
    )


@pytest.fixture(autouse=True)
def setup_test_media(settings):
    """Create folder for test media/file uploads."""
    settings.MEDIA_ROOT = "test_media"
    settings.MEDIA_URL = "/media/"
    yield
    shutil.rmtree("test_media", ignore_errors=True)


@pytest.fixture
def api_client():
    return APIClient()


def get_feature_with_geometry(geometry):
    return {
        "type": "Feature",
        "properties": {
            "name": "Coors Field",
            "amenity": "Baseball Stadium",
            "popupContent": "This is where the Rockies play!",
        },
        "geometry": geometry,
    }


default_geojson_feature = get_feature_with_geometry(default_geojson_geometry)


@pytest.fixture
def geojson_feature():
    return default_geojson_feature
