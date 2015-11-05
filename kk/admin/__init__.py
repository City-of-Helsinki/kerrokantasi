from django.contrib import admin

from kk.models import Hearing, Label, Introduction, Scenario, Image

admin.site.register(Label)
admin.site.register(Hearing)
admin.site.register(Image)
admin.site.register(Introduction)
admin.site.register(Scenario)
