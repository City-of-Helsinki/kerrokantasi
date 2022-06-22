import copy
from importlib.util import find_spec


def load_local_settings(settings, module_name):
    """
    Load local settings from `module_name`.

    Search for a `local_settings` module, load its code and execute it in the
    `settings` dict. All of the settings declared in the sertings dict are thus available
    to the local_settings module. The settings dict is updated.
    """

    local_settings_spec = find_spec(module_name)
    if local_settings_spec:
        local_settings_code = local_settings_spec.loader.get_code(module_name)
        exec(local_settings_code, settings)


def get_settings(settings_module):
    """
    Get a copy of the settings (upper-cased variables) declared in the given settings module.

    :param settings_module: A settings module
    :type settings_module: module
    :return: Dict of settings
    :rtype: dict[str, object]
    """
    return copy.deepcopy({k: v for (k, v) in vars(settings_module).items() if k.isupper()})
