from django.conf import settings
from django.utils.module_loading import import_string


class Plugin(object):
    """
    Base class for backend implementations of hearing section plugins.
    """

    #: The user-friendly displayable name for this plugin.
    display_name = None

    def clean_client_data(self, data):
        """
        Validate and transmogrify client (comment) data.

        By default, does no validation and just returns the
        data as-is.

        :param data: str
        :return: str
        """

        return data


def get_implementation(plugin_identifier):
    """
    Get a plugin implementation instance for the given plugin identifier.

    The map of identifier to plugin class lives in `settings.DEMOCRACY_PLUGINS`.

    :param plugin_identifier: Plugin identifier string
    :return: An object instance deriving from `Plugin`.
    :rtype: Plugin
    """
    classpath = settings.DEMOCRACY_PLUGINS.get(plugin_identifier)
    if classpath:
        cls = import_string(classpath)
    else:
        cls = Plugin
    return cls()
