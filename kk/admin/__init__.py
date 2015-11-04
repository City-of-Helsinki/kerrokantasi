from django.contrib import admin

from kk.models import Hearing, HearingImage, Label

admin.site.register(Label)
admin.site.register(Hearing)
admin.site.register(HearingImage)
