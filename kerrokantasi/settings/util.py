import copy
import os

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


def load_secret_key(settings):
    """
    Load a secret key from `.django_secret` if one is not already set.

    :param settings: Settings dict
    :type settings: dict
    """
    if settings.get("SECRET_KEY"):
        return
    secret_file = os.path.join(settings.get("BASE_DIR"), '.django_secret')

    if os.path.isfile(secret_file):
        with open(secret_file) as secret:
            settings["SECRET_KEY"] = secret.read().strip()
            return

    from django.utils.crypto import get_random_string
    try:
        settings["SECRET_KEY"] = secret_key = get_random_string(64)
        with open(secret_file, 'w') as secret:
            os.chmod(secret_file, 0o0600)
            secret.write(secret_key)
            secret.close()
        print("Secret key file %s generated." % secret_file)
    except IOError:
        raise Exception(
            'Please create a %s file with random characters to generate your secret key!' % secret_file
        )


def get_settings(settings_module):
    """
    Get a copy of the settings (upper-cased variables) declared in the given settings module.

    :param settings_module: A settings module
    :type settings_module: module
    :return: Dict of settings
    :rtype: dict[str, object]
    """
    return copy.deepcopy({k: v for (k, v) in vars(settings_module).items() if k.isupper()})
