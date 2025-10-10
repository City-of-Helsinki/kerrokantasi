import json
import logging
from typing import Any, Optional, TypedDict

from django.db.models import QuerySet
from resilient_logger.sources import ResilientLogSource
from rest_framework import status

from audit_log.enums import Operation, Role, Status
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


class ActorDetails(TypedDict):
    role: str
    uuid: Optional[str]
    ip_address: str


class TargetDetails(TypedDict):
    path: str
    object_ids: list[Any]


class AuditLogContext(TypedDict):
    actor: dict
    operation: str
    target: dict
    status: str


def get_response_status(response) -> Optional[str]:
    if 200 <= response.status_code < 300:
        return Status.SUCCESS.value
    elif (
        response.status_code == status.HTTP_401_UNAUTHORIZED
        or response.status_code == status.HTTP_403_FORBIDDEN
    ):
        return Status.FORBIDDEN.value

    return None


def _get_operation_name(request) -> str:
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


def _get_actor_data(request) -> ActorDetails:
    user = getattr(request, "user", None)
    uuid = getattr(user, "uuid", None)

    return {
        "role": _get_user_role(user),
        "uuid": str(uuid) if uuid else None,
        "ip_address": _get_remote_address(request),
    }


def _get_target(request, audit_logged_object_ids) -> TargetDetails:
    return {"path": request.path, "object_ids": list(audit_logged_object_ids)}


def commit_to_audit_log(request, response):
    audit_logged_object_ids = getattr(
        request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR, None
    )
    if not audit_logged_object_ids:
        return

    delattr(request, audit_logging_settings.REQUEST_AUDIT_LOG_VAR)
    status = get_response_status(response) or f"Unknown: {response.status_code}"

    entry = ResilientLogSource.create_structured(
        level=logging.NOTSET,
        message=status,
        actor=_get_actor_data(request),
        operation=_get_operation_name(request),
        target=_get_target(request, audit_logged_object_ids),
        extra={"status": status},
    )

    if audit_logging_settings.LOG_TO_LOGGER_ENABLED:
        logger = logging.getLogger("audit")
        logger.info(json.dumps(entry.get_document()))


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
