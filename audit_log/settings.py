import re

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver

_defaults = dict(
    ENABLED=True,
    ORIGIN="service",
    LOGGED_ENDPOINTS_RE=re.compile(r"^/(v1|gdpr-api)/"),
    REQUEST_AUDIT_LOG_VAR="_audit_logged_object_ids",
    LOG_TO_DB_ENABLED=True,
    LOG_TO_LOGGER_ENABLED=False,
)

_import_strings = []


def _compile_settings():
    class Settings:
        def __init__(self):
            self._load()

        def __getattr__(self, name):
            from django.utils.module_loading import import_string

            try:
                attr = self._settings[name]

                if name in _import_strings and isinstance(attr, str):
                    attr = import_string(attr)
                    self._settings[name] = attr

                return attr
            except KeyError:
                raise AttributeError("Setting '{}' not found".format(name))

        def _load(self):
            self._settings = _defaults.copy()

            user_settings = getattr(settings, "AUDIT_LOG", None)
            self._settings.update(user_settings)

    return Settings()


audit_logging_settings = _compile_settings()


@receiver(setting_changed)
def _reload_settings(setting, **kwargs):
    if setting == "AUDIT_LOG":
        audit_logging_settings._load()
