# -*- coding: utf-8 -*-
from django.apps.config import AppConfig
from django.utils.translation import ugettext_lazy as _


class KkAppConfig(AppConfig):
    name = 'kk'
    verbose_name = _("Participatory Democracy")
