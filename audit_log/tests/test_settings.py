import pytest

from audit_log.settings import audit_logging_settings


@pytest.fixture(autouse=True)
def setup_audit_log_settings(settings):
    settings.AUDIT_LOG = {"ORIGIN": "audit_logging_service"}


def test_defaults_exist_for_settings():
    assert audit_logging_settings.REQUEST_AUDIT_LOG_VAR == "_audit_logged_object_ids"


def test_user_settings_overwrite_defaults():
    assert audit_logging_settings.ORIGIN == "audit_logging_service"
