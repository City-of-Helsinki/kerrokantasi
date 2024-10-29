import pytest
from django.contrib.auth import get_user_model


@pytest.fixture(autouse=True)
def setup_audit_logging(settings):
    settings.AUDIT_LOG = {"ENABLED": True}


@pytest.fixture
def superuser():
    User = get_user_model()  # noqa: N806
    return User.objects.create_superuser("admin", "admin@example.com", "admin")
