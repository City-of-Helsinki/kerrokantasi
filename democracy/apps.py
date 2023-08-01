from django.apps.config import AppConfig
from django.utils.translation import gettext_lazy as _


class DemocracyAppConfig(AppConfig):
    name = 'democracy'
    verbose_name = _("Participatory Democracy")
