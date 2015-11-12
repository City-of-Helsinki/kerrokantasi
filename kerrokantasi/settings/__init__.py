from .util import get_settings, load_local_settings, load_secret_key
from . import base

settings = get_settings(base)
load_local_settings(settings, "local_settings")
load_secret_key(settings)
globals().update(settings)  # Export the settings for Django to use.
