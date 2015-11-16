from .util import get_settings, load_local_settings, load_secret_key
from . import base

settings = get_settings(base)
load_local_settings(settings, "local_settings")
load_secret_key(settings)

if not settings["DEBUG"] and settings["JWT_AUTH"]["JWT_SECRET_KEY"] == "kerrokantasi":
    raise ValueError("Refusing to run out of DEBUG mode with insecure JWT secret key.")

globals().update(settings)  # Export the settings for Django to use.
