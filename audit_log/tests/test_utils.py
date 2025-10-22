from collections import Counter
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from freezegun import freeze_time
from resilient_logger.models import ResilientLogEntry
from resilient_logger.sources import ResilientLogSource
from rest_framework import status

from audit_log.enums import Operation, Role, Status
from audit_log.settings import audit_logging_settings
from audit_log.utils import (
    _get_remote_address,
    _get_target,
    add_audit_logged_object_ids,
    commit_to_audit_log,
    get_response_status,
)
from kerrokantasi.tests.factories import UserFactory

User = get_user_model()


def _assert_basic_log_source_data(log_source: ResilientLogSource):
    current_time = datetime.now(tz=timezone.utc)
    iso_8601_date = f"{current_time.replace(tzinfo=None).isoformat(sep='T', timespec='milliseconds')}Z"

    document = log_source.get_document()
    timestamp = document.get("@timestamp")
    audit_event = document.get("audit_event")

    assert timestamp == iso_8601_date
    assert audit_event["origin"] == settings.RESILIENT_LOGGER["origin"]
    assert audit_event["date_time"] == iso_8601_date


def _create_default_request_mock(user):
    return Mock(
        method="GET",
        user=user,
        path="/v1/endpoint",
        headers={"x-forwarded-for": "1.2.3.4:80"},
    )


def _assert_target_data(target_data, expected_path, expected_object_ids):
    assert len(target_data.keys()) == 2
    assert target_data["path"] == expected_path
    assert Counter(target_data["object_ids"]) == Counter(expected_object_ids)


@pytest.mark.parametrize(
    "status_code,audit_status",
    [
        (status.HTTP_200_OK, Status.SUCCESS.value),
        (status.HTTP_201_CREATED, Status.SUCCESS.value),
        (status.HTTP_204_NO_CONTENT, Status.SUCCESS.value),
        (status.HTTP_401_UNAUTHORIZED, Status.FORBIDDEN.value),
        (status.HTTP_403_FORBIDDEN, Status.FORBIDDEN.value),
        (status.HTTP_302_FOUND, None),
        (status.HTTP_404_NOT_FOUND, None),
        (status.HTTP_502_BAD_GATEWAY, None),
    ],
)
def test_get_response_status(status_code, audit_status):
    res_mock = Mock(status_code=status_code)

    assert get_response_status(res_mock) == audit_status


@freeze_time("2023-10-17 13:30:00+02:00")
@pytest.mark.parametrize(
    "status_code,audit_status",
    [
        (status.HTTP_200_OK, Status.SUCCESS.value),
        (status.HTTP_201_CREATED, Status.SUCCESS.value),
        (status.HTTP_204_NO_CONTENT, Status.SUCCESS.value),
        (status.HTTP_401_UNAUTHORIZED, Status.FORBIDDEN.value),
        (status.HTTP_403_FORBIDDEN, Status.FORBIDDEN.value),
        (status.HTTP_302_FOUND, "Unknown: 302"),
        (status.HTTP_404_NOT_FOUND, "Unknown: 404"),
        (status.HTTP_502_BAD_GATEWAY, "Unknown: 502"),
    ],
)
@pytest.mark.django_db
def test_commit_to_audit_log_response_status(status_code, audit_status):
    user = UserFactory()
    req_mock = _create_default_request_mock(user)
    setattr(req_mock, audit_logging_settings.REQUEST_AUDIT_LOG_VAR, {1})
    res_mock = Mock(status_code=status_code)
    assert ResilientLogEntry.objects.count() == 0

    commit_to_audit_log(req_mock, res_mock)

    assert ResilientLogEntry.objects.count() == 1
    log_entry = ResilientLogEntry.objects.first()
    log_source = ResilientLogSource(log_entry)
    document = log_source.get_document()
    assert document["audit_event"]["message"] == audit_status
    assert document["audit_event"]["extra"]["status"] == audit_status
    _assert_basic_log_source_data(log_source)


@freeze_time("2023-10-17 13:30:00+02:00")
@pytest.mark.parametrize(
    "http_method,audit_operation",
    [
        ("GET", Operation.READ.value),
        ("HEAD", Operation.READ.value),
        ("OPTIONS", Operation.READ.value),
        ("POST", Operation.CREATE.value),
        ("PUT", Operation.UPDATE.value),
        ("PATCH", Operation.UPDATE.value),
        ("DELETE", Operation.DELETE.value),
    ],
)
@pytest.mark.django_db
def test_commit_to_audit_log_crud_operations(http_method, audit_operation):
    user = UserFactory()
    req_mock = Mock(
        method=http_method,
        user=user,
        path="/v1/endpoint",
        headers={"x-forwarded-for": "1.2.3.4:80"},
        **{audit_logging_settings.REQUEST_AUDIT_LOG_VAR: {1}},
    )
    res_mock = Mock(status_code=200)
    assert ResilientLogEntry.objects.count() == 0

    commit_to_audit_log(req_mock, res_mock)

    assert ResilientLogEntry.objects.count() == 1
    log_entry = ResilientLogEntry.objects.first()
    log_source = ResilientLogSource(log_entry)
    document = log_source.get_document()
    assert document["audit_event"]["operation"] == audit_operation
    assert document["audit_event"]["target"]["path"] == "/v1/endpoint"
    assert document["audit_event"]["target"]["object_ids"] == [1]
    _assert_basic_log_source_data(log_source)


@freeze_time("2023-10-17 13:30:00+02:00")
@pytest.mark.parametrize(
    "user_role,audit_role",
    [
        ("staff", Role.ADMIN.value),
        ("superuser", Role.ADMIN.value),
        ("regular_user", Role.USER.value),
        ("anonymous", Role.ANONYMOUS.value),
    ],
)
@pytest.mark.django_db
def test_commit_to_audit_log_actor_data(user_role, audit_role):
    if user_role == "anonymous":
        user = AnonymousUser()
    else:
        user = UserFactory(
            is_staff=user_role == "staff", is_superuser=user_role == "superuser"
        )
    req_mock = _create_default_request_mock(user)
    setattr(req_mock, audit_logging_settings.REQUEST_AUDIT_LOG_VAR, {1})
    res_mock = Mock(status_code=200)
    assert ResilientLogEntry.objects.count() == 0

    commit_to_audit_log(req_mock, res_mock)

    assert ResilientLogEntry.objects.count() == 1
    log_entry = ResilientLogEntry.objects.first()
    log_source = ResilientLogSource(log_entry)
    document = log_source.get_document()

    assert document["audit_event"]["actor"]["role"] == audit_role
    assert document["audit_event"]["actor"]["ip_address"] == "1.2.3.4"
    if hasattr(user, "uuid"):
        assert document["audit_event"]["actor"]["uuid"] == str(user.uuid)

    _assert_basic_log_source_data(log_source)


@pytest.mark.django_db
def test_dont_commit_audit_logs_if_no_loggable_ids():
    user = AnonymousUser()
    req_mock = _create_default_request_mock(user)
    setattr(req_mock, audit_logging_settings.REQUEST_AUDIT_LOG_VAR, set())
    res_mock = Mock(status_code=200)
    assert ResilientLogEntry.objects.count() == 0

    commit_to_audit_log(req_mock, res_mock)

    assert ResilientLogEntry.objects.count() == 0


@pytest.mark.parametrize(
    "remote_address,expected,x_forwarded_for",
    [
        ("1.2.3.4:443", "1.2.3.4", True),
        ("1.2.3.4", "1.2.3.4", True),
        (
            "[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:443",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            True,
        ),
        (
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            True,
        ),
        ("1.2.3.4", "1.2.3.4", False),
        (
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            False,
        ),
    ],
)
def test_get_remote_address(remote_address, expected, x_forwarded_for):
    req_mock = Mock(
        headers={"x-forwarded-for": remote_address} if x_forwarded_for else {},
        META={"REMOTE_ADDR": remote_address} if not x_forwarded_for else {},
    )
    assert _get_remote_address(req_mock) == expected


@pytest.mark.parametrize(
    "queryset_type",
    [
        "queryset",
        "empty_queryset",
    ],
)
@pytest.mark.django_db
def test_get_target_queryset(queryset_type):
    user = UserFactory()
    req_mock = _create_default_request_mock(user)
    req_mock._request = Mock(
        path="/v1/endpoint", **{audit_logging_settings.REQUEST_AUDIT_LOG_VAR: set()}
    )
    if queryset_type == "queryset":
        UserFactory()
        instances = User.objects.all()
        object_ids = [user.pk for user in instances]
    else:
        instances = User.objects.none()
        object_ids = []

    add_audit_logged_object_ids(req_mock, instances)

    target_data = _get_target(req_mock._request, object_ids)
    _assert_target_data(target_data, req_mock.path, object_ids)


@pytest.mark.parametrize(
    "list_type",
    [
        "list",
        "list_of_objects_without_pks",
        "list_of_nones",
        "list_of_strings",
        "empty_list",
    ],
)
@pytest.mark.django_db
def test_get_target_list(list_type):
    user = UserFactory()
    req_mock = _create_default_request_mock(user)
    req_mock._request = Mock(
        path="/v1/endpoint", **{audit_logging_settings.REQUEST_AUDIT_LOG_VAR: set()}
    )
    list_type_mapping = {
        "list": [user, UserFactory()],
        "list_of_objects_without_pks": [User(), User()],
        "list_of_nones": [None, None],
        "list_of_strings": ["test", "", " "],
        "empty_list": [],
    }
    instances = list_type_mapping[list_type]
    object_ids = [user.pk for user in instances] if list_type == "list" else []

    add_audit_logged_object_ids(req_mock, instances)

    target_data = _get_target(req_mock._request, object_ids)
    _assert_target_data(target_data, req_mock.path, object_ids)


@pytest.mark.parametrize(
    "object_type",
    [
        "object",
        "object_without_pk",
        "none",
    ],
)
@pytest.mark.django_db
def test_get_target_object(object_type):
    user = UserFactory()
    req_mock = _create_default_request_mock(user)
    req_mock._request = Mock(
        path="/v1/endpoint", **{audit_logging_settings.REQUEST_AUDIT_LOG_VAR: set()}
    )
    object_type_mapping = {
        "object": user,
        "object_without_pk": User(),
        "none": None,
    }
    instances = object_type_mapping[object_type]
    object_ids = [user.pk] if object_type == "object" else []

    add_audit_logged_object_ids(req_mock, instances)

    target_data = _get_target(req_mock._request, object_ids)
    _assert_target_data(target_data, req_mock.path, object_ids)
