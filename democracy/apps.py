from django.apps.config import AppConfig
from django.utils.translation import ugettext_lazy as _


class DemocracyAppConfig(AppConfig):
    name = 'democracy'
    verbose_name = _("Participatory Democracy")
