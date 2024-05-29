from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class Operation(TextChoices):
    CREATE = "CREATE", _("Create")
    READ = "READ", _("Read")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")


class Role(TextChoices):
    OWNER = "OWNER", _("Owner")
    USER = "USER", _("User")
    SYSTEM = "SYSTEM", _("System")
    ANONYMOUS = "ANONYMOUS", _("Anonymous")
    ADMIN = "ADMIN", _("Admin")


class Status(TextChoices):
    SUCCESS = "SUCCESS", _("Success")
    FORBIDDEN = "FORBIDDEN", _("Forbidden")
