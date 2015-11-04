from django.contrib import admin
from django import forms

from kk.models import Hearing
from kk.models import HearingImage

admin.site.register(Hearing)
admin.site.register(HearingImage)
