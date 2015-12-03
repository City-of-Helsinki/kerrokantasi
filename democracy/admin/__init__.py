from django.contrib import admin
from democracy import models


# Inlines

class SectionInline(admin.StackedInline):
    model = models.Section
    extra = 0
    show_change_link = True


class HearingImageInline(admin.StackedInline):
    model = models.HearingImage
    extra = 0


class SectionImageInline(admin.StackedInline):
    model = models.SectionImage
    extra = 0


# Admins


class HearingAdmin(admin.ModelAdmin):
    inlines = [HearingImageInline, SectionInline]
    list_display = ("id", "published", "title", "open_at", "close_at", "force_closed")
    list_filter = ("published",)
    search_fields = ("id", "title")


class SectionAdmin(admin.ModelAdmin):
    list_filter = ("hearing", "published", "type")
    list_display = ("id", "published", "type", "hearing", "title")
    list_display_links = list_display
    inlines = [SectionImageInline]


# Wire it up!


admin.site.register(models.Label)
admin.site.register(models.Hearing, HearingAdmin)
admin.site.register(models.Section, SectionAdmin)
