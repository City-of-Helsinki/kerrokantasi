from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from kerrokantasi.models import User


class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "uuid",
                    "nickname",
                    "admin_in_organizations",
                )
            },
        ),
    )
    readonly_fields = ("admin_in_organizations",)

    def admin_in_organizations(self, obj):
        return ", ".join([org.name for org in obj.admin_organizations.all()]) or "-"


admin.site.register(User, UserAdmin)
