from django.contrib import admin
from nested_admin.nested import NestedAdmin, NestedStackedInline

from democracy import models


# Inlines


class HearingImageInline(NestedStackedInline):
    model = models.HearingImage
    extra = 0


class SectionImageInline(NestedStackedInline):
    model = models.SectionImage
    extra = 0


class SectionInline(NestedStackedInline):
    model = models.Section
    extra = 1
    inlines = [SectionImageInline]


# Admins


class HearingAdmin(NestedAdmin):
    inlines = [HearingImageInline, SectionInline]
    list_display = ("id", "published", "title", "open_at", "close_at", "force_closed")
    list_filter = ("published",)
    search_fields = ("id", "title")


# Wire it up!


admin.site.register(models.Label)
admin.site.register(models.Hearing, HearingAdmin)
