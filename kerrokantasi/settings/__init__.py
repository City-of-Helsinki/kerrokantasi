from kerrokantasi.settings import base
from kerrokantasi.settings.util import get_settings, load_local_settings

print("reading settings")  # noqa: T201
settings = get_settings(base)
print("read base settings")  # noqa: T201
load_local_settings(settings, "local_settings")
print("read local settings")  # noqa: T201

globals().update(settings)  # Export the settings for Django to use.
