from kerrokantasi.utils import get_current_request


class FileFieldUrlSerializerMixin:
    field_to_use_as_url_field = None  # Override in subclass.

    @property
    def url(self):
        field = getattr(self, self.field_to_use_as_url_field, None)

        if request := get_current_request():
            return request.build_absolute_uri(field.url)

        return field.url
