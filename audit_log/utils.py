import json
import logging
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import status

from audit_log.enums import Operation, Role, Status
from audit_log.models import AuditLogEntry
from audit_log.settings import audit_logging_settings

_OPERATION_MAPPING = {
    "GET": Operation.READ.value,
    "HEAD": Operation.READ.value,
    "OPTIONS": Operation.READ.value,
    "POST": Operation.CREATE.value,
    "PUT": Operation.UPDATE.value,
    "PATCH": Operation.UPDATE.value,
    "DELETE": Operation.DELETE.value,
}


def get_response_status(response) -> Optional[str]:
    if 200 <= response.status_code < 300:
        return Status.SUCCESS.value
    elif (
        response.status_code == status.HTTP_401_UNAUTHORIZED
        or response.status_code == status.HTTP_403_FORBIDDEN
    ):
        return Status.FORBIDDEN.value

    return None


def _get_operation_name(request):
    return _OPERATION_MAPPING.get(request.method, f"Unknown: {request.method}")


def _get_remote_address(request):
    if not (x_forwarded_for := request.headers.get("x-forwarded-for")):
        return request.META.get("REMOTE_ADDR")

    remote_addr = x_forwarded_for.split(",")[0]

    # Remove port number from remote_addr
    if "." in remote_addr and ":" in remote_addr:
        # IPv4 with port (`x.x.x.x:x`)
        remote_addr = remote_addr.split(":")[0]
    elif "[" in remote_addr:
        # IPv6 with port (`[:::]:x`)
        remote_addr = remote_addr[1:].split("]")[0]

    return remote_addr


def _get_user_role(user):
    if user is None or not user.is_authenticated:
        return Role.ANONYMOUS.value
    elif user.is_staff or user.is_superuser:
        return Role.ADMIN.value

    return Role.USER.value


def _get_actor_data(request):
    user = getattr(request, "user", None)
    uuid = getattr(user, "uuid", None)

    return {
        "role": _get_user_role(user),
        "uuid": str(uuid) if uuid else None,
        "ip_address": _get_remote_address(request),
    }


def _get_target(request, audit_logged_object_ids):
    return {"path": request.path, "object_ids": list(audit_logged_object_ids)}


def commit_to_audit_log(request, response):
    audit_logged_object_ids = getattr(
        request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR, None
    )
    if not audit_logged_object_ids:
        return

    delattr(request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR)

    current_time = timezone.now()
    iso_8601_datetime = f"{current_time.replace(tzinfo=None).isoformat(sep='T', timespec='milliseconds')}Z"  # noqa: E501

    message = {
        "audit_event": {
            "origin": audit_logging_settings.ORIGIN,
            "status": get_response_status(response)
            or f"Unknown: {response.status_code}",
            "date_time_epoch": int(current_time.timestamp() * 1000),
            "date_time": iso_8601_datetime,
            "actor": _get_actor_data(request),
            "operation": _get_operation_name(request),
            "target": _get_target(request, audit_logged_object_ids),
        }
    }

    if audit_logging_settings.LOG_TO_LOGGER_ENABLED:
        logger = logging.getLogger("audit")
        logger.info(json.dumps(message))

    if audit_logging_settings.LOG_TO_DB_ENABLED:
        AuditLogEntry.objects.create(message=message)


def add_audit_logged_object_ids(request, instances):
    request = getattr(request, "_request", request)
    audit_logged_object_ids = set()

    def add_instance(instance):
        if not hasattr(instance, "pk") or not instance.pk:
            return

        audit_logged_object_ids.add(instance.pk)

    if isinstance(instances, QuerySet) or isinstance(instances, list):
        for instance in instances:
            add_instance(instance)
    else:
        add_instance(instances)

    if hasattr(request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR):
        getattr(request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR).update(
            audit_logged_object_ids
        )
    else:
        setattr(
            request,
            audit_logging_settings.REQUEST_AUDIT_LOG_VAR,
            audit_logged_object_ids,
        )
