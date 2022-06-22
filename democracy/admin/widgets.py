from textwrap import dedent

from django import forms
from django.templatetags.static import static
from django.contrib.admin.widgets import AdminTextareaWidget
from django.forms.widgets import SelectMultiple
from django.utils.safestring import mark_safe


class ShortTextAreaWidget(AdminTextareaWidget):

    def __init__(self, attrs=None):
        final_attrs = {'rows': '3'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(ShortTextAreaWidget, self).__init__(attrs=final_attrs)


class Select2SelectMultiple(SelectMultiple):
    SCRIPT_TEMPLATE = dedent("""
    <script type="text/javascript">
    addEvent(window, "load", function(e) {{
        $("#{id}").select2({{ width: '21em'}});
    }});
    </script>
    """)

    @property
    def media(self):
        return forms.Media(
            js=[static("admin/hoist-jquery.js"), static("admin/select2/select2.min.js")],
            css={"all": [static("admin/select2/select2.min.css")]}
        )

    def render(self, name, value, attrs=None, renderer=None):
        id = attrs.get("id", "id_%s" % name)
        output = [
            super(Select2SelectMultiple, self).render(name, value, attrs, renderer),
            self.SCRIPT_TEMPLATE.format(id=id)
        ]
        return mark_safe(''.join(output))
