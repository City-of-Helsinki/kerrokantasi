from django.contrib import admin

from kk.models import Hearing, Label, Introduction, Scenario, Comment

admin.site.register(Label)
admin.site.register(Hearing)
admin.site.register(Introduction)
admin.site.register(Scenario)
admin.site.register(Comment)
