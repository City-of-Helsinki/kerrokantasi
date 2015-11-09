from django.contrib import admin
from kk import models


### Inlines

class IntroductionInline(admin.StackedInline):
    model = models.Introduction
    extra = 0
    exclude = ["id"]


class ScenarioInline(admin.StackedInline):
    model = models.Scenario
    extra = 0
    exclude = ["id"]


class HearingImageInline(admin.StackedInline):
    model = models.HearingImage
    extra = 0


class IntroductionImageInline(admin.StackedInline):
    model = models.IntroductionImage
    extra = 0


class ScenarioImageInline(admin.StackedInline):
    model = models.ScenarioImage
    extra = 0


### Admins


class HearingAdmin(admin.ModelAdmin):
    inlines = [HearingImageInline, IntroductionInline, ScenarioInline]


class IntroductionAdmin(admin.ModelAdmin):
    inlines = [IntroductionImageInline]


class ScenarioAdmin(admin.ModelAdmin):
    inlines = [ScenarioImageInline]


### Wire it up!


admin.site.register(models.Label)
admin.site.register(models.Hearing, HearingAdmin)
admin.site.register(models.Introduction, IntroductionAdmin)
admin.site.register(models.Scenario, ScenarioAdmin)
