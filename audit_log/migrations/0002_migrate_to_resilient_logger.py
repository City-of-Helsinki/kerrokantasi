import logging
from datetime import datetime, timezone
from typing import TypedDict, cast

from django.apps.registry import Apps
from django.db import migrations, models


class OriginalAuditEvent(TypedDict):
    origin: str
    status: str
    date_time_epoch: int
    date_time: str
    actor: dict
    operation: str
    target: dict


class OriginalMessage(TypedDict):
    audit_event: OriginalAuditEvent


def migrate_to_resilient_logger(apps: Apps, schema_editor):
    audit_log_entry = cast(
        type[models.Model], apps.get_model("audit_log", "AuditLogEntry")
    )
    resilient_log_entry = cast(
        type[models.Model], apps.get_model("resilient_logger", "ResilientLogEntry")
    )

    for entry in audit_log_entry.objects.all():
        entry_id = entry.id  # type: ignore[attr-defined]
        is_sent = entry.is_sent  # type: ignore[attr-defined]
        message = cast(OriginalMessage, entry.message)  # type: ignore[attr-defined]
        created_at = cast(datetime, entry.created_at).astimezone(timezone.utc)  # type: ignore[attr-defined]
        audit_event = message["audit_event"]

        resilient_log_entry.objects.create(
            is_sent=is_sent,
            level=logging.NOTSET,
            message=audit_event["status"],
            context={
                "actor": audit_event["actor"],
                "operation": audit_event["operation"],
                "target": audit_event["target"],
                "status": audit_event["status"],
                "orig_entry_id": entry_id,
                "orig_created_at": created_at.isoformat().replace("+00:00", "Z"),
            },
        )


class Migration(migrations.Migration):
    dependencies = [("audit_log", "0001_initial"), ("resilient_logger", "0001_initial")]

    operations = [
        migrations.RunPython(migrate_to_resilient_logger),
    ]
