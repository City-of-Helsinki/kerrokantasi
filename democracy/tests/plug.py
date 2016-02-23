from django.core.exceptions import ValidationError

from democracy.plugins import Plugin


class TestPlugin(Plugin):
    display_name = "Test Plugin"

    def clean_client_data(self, data):
        if "6" not in data:
            raise ValidationError("The data must contain a 6.")
        return data[::-1]
