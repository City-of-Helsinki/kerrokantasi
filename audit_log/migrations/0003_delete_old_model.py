from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("audit_log", "0002_migrate_to_resilient_logger")]

    operations = [
        migrations.DeleteModel(
            name="AuditLogEntry",
        ),
    ]
