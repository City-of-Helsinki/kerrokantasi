from unittest.mock import Mock

import pytest
from django.contrib.admin import AdminSite

from audit_log.admin import AuditLogEntryAdmin, LargeTablePaginator
from audit_log.models import AuditLogEntry


@pytest.mark.django_db
def test_audit_log_admin_message_prettified(superuser):
    request = Mock(user=superuser)
    model_admin = AuditLogEntryAdmin(AuditLogEntry, AdminSite())
    assert list(model_admin.get_fields(request)) == [
        "id",
        "created_at",
        "is_sent",
        "message_prettified",
    ]


@pytest.mark.django_db
def test_audit_log_admin_permissions(superuser):
    request = Mock(user=superuser)
    audit_log = AuditLogEntry.objects.create(message={})
    model_admin = AuditLogEntryAdmin(AuditLogEntry, AdminSite())
    # The user should have permission to view, but not modify or delete audit logs
    assert model_admin.has_view_permission(request, audit_log)
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request, audit_log)
    assert not model_admin.has_delete_permission(request, audit_log)


@pytest.mark.django_db
def test_large_table_paginator_count_without_data():
    qs = AuditLogEntry.objects.all().order_by("created_at")

    paginator = LargeTablePaginator(qs, per_page=1)

    # Paginator's count is just an estimate, but it should be >= 0
    assert paginator.count >= 0


@pytest.mark.django_db
def test_large_table_paginator_count_with_data():
    AuditLogEntry.objects.bulk_create(
        [AuditLogEntry(message={"test": "test"}) for _ in range(1000)]
    )
    qs = AuditLogEntry.objects.all().order_by("created_at")

    paginator = LargeTablePaginator(qs, per_page=1)

    # Paginator's count is just an estimate, but it should be >= 0
    assert paginator.count >= 0
