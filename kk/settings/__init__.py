from .base import *

try:
    import local_settings
except ImportError:
    local_settings = None

if local_settings:
    if hasattr(local_settings, "configure"):  # Support a `configure(current_settings_dict)` function
        globals().update(local_settings.configure(globals()) or {})
    # And also copy all UPPER_CASE values here
    globals().update((setting, value) for (setting, value) in vars(local_settings).items() if setting.isupper())
