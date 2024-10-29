from unittest.mock import Mock, patch

import pytest
from rest_framework import status

from audit_log.middleware import AuditLogMiddleware


def get_response_function(status_code=200):
    return lambda _request: Mock(status_code=status_code)


@pytest.mark.parametrize("audit_log_enabled", [True, False])
def test_middleware_audit_log_setting(settings, audit_log_enabled):
    settings.AUDIT_LOG = {"ENABLED": audit_log_enabled}

    with patch("audit_log.middleware.commit_to_audit_log") as mocked:
        middleware = AuditLogMiddleware(get_response_function())
        middleware(Mock(path="/v1/"))
        assert mocked.called is audit_log_enabled


@pytest.mark.parametrize(
    "path,expected_called",
    [
        ("/v1/signup/", True),
        ("/gdpr-api/v1/user/uuid/", True),
        ("/admin/", False),
        ("/pysocial/", False),
        ("/helusers/", False),
        ("/", False),
    ],
)
def test_middleware_audit_logged_paths(settings, path, expected_called):
    with patch("audit_log.middleware.commit_to_audit_log") as mocked:
        middleware = AuditLogMiddleware(get_response_function())
        middleware(Mock(path=path))
        assert mocked.called is expected_called


@pytest.mark.parametrize(
    "status_code,expected_called",
    [
        (status.HTTP_200_OK, True),
        (status.HTTP_201_CREATED, True),
        (status.HTTP_204_NO_CONTENT, True),
        (status.HTTP_401_UNAUTHORIZED, True),
        (status.HTTP_403_FORBIDDEN, True),
        (status.HTTP_302_FOUND, False),
        (status.HTTP_404_NOT_FOUND, False),
        (status.HTTP_502_BAD_GATEWAY, False),
    ],
)
def test_middleware_audit_logged_statuses(settings, status_code, expected_called):
    with patch("audit_log.middleware.commit_to_audit_log") as mocked:
        middleware = AuditLogMiddleware(get_response_function(status_code=status_code))
        middleware(Mock(path="/v1/endpoint"))
        assert mocked.called is expected_called
