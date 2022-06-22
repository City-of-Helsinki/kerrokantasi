from django.utils.encoding import force_text
from rest_framework.fields import ChoiceField


class EnumField(ChoiceField):
    def __init__(self, **kwargs):
        self.enum_type = kwargs.pop("enum_type")
        kwargs["choices"] = self.enum_type.choices()
        super(EnumField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        # Normal logic:
        for choice in self.enum_type:
            if choice.name == data or choice.value == data:
                return choice

        # Case-insensitive logic:
        l_data = force_text(data).lower()
        for choice in self.enum_type:
            if choice.name.lower() == l_data or force_text(choice.value).lower() == l_data:
                return choice

        # Fallback:
        return super(EnumField, self).to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        # If the enum value is an int, assume the name (lowercased in case of CONSTANTS) is more representative:
        if isinstance(value.value, int):
            return value.name.lower()
        else:
            return value.value
