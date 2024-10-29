import json
import logging

from django.contrib import admin
from django.core.paginator import Paginator
from django.db import connection
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import mark_safe

from audit_log.models import AuditLogEntry

logger = logging.getLogger(__name__)


class LargeTablePaginator(Paginator):
    """
    Paginator that uses PostgreSQL `reltuples` for queryset size.

    The reltuples values is just an estimate, but it's much faster than
    the COUNT(*) which is used by the default paginator. Therefore, this
    should work better for tables containing millions of rows.

    See https://wiki.postgresql.org/wiki/Count_estimate for details.
    """

    @cached_property
    def count(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples::bigint FROM pg_class WHERE relname = %s",
                [self.object_list.query.model._meta.db_table],
            )
            estimate = cursor.fetchone()[0]
            if estimate == -1:
                # If the table has not yet been analyzed/vacuumed,
                # reltuples will return -1.  In this case we fall back to
                # the default paginator.
                logger.warning(
                    "Can't estimate count of table %s, using COUNT(*) instead",
                    self.object_list.query.model._meta.db_table,
                )
                return super().count
            return estimate


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    exclude = ("message",)
    readonly_fields = ("id", "created_at", "is_sent", "message_prettified")
    list_display = ("id", "__str__", "created_at", "is_sent")
    list_filter = ("created_at", "is_sent")

    # For increasing listing performance
    show_full_result_count = False
    paginator = LargeTablePaginator

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="message")
    def message_prettified(self, instance):
        """Format the message to be a bit a more user-friendly."""
        message = json.dumps(instance.message, indent=2, sort_keys=True)
        content = f"<pre>{escape(message)}</pre>"
        return mark_safe(content)
