from django.contrib import admin
from kk import models


# Inlines

class SectionInline(admin.StackedInline):
    model = models.Section
    extra = 0


class HearingImageInline(admin.StackedInline):
    model = models.HearingImage
    extra = 0


class SectionImageInline(admin.StackedInline):
    model = models.SectionImage
    extra = 0


# Admins


class HearingAdmin(admin.ModelAdmin):
    inlines = [HearingImageInline, SectionInline]


class SectionAdmin(admin.ModelAdmin):
    inlines = [SectionImageInline]


# Wire it up!


admin.site.register(models.Label)
admin.site.register(models.Hearing, HearingAdmin)
admin.site.register(models.Section, SectionAdmin)
