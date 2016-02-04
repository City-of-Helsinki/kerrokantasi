# -*- coding: utf-8 -*-
import json
from copy import deepcopy

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.widgets import AdminTextareaWidget
from django.forms.widgets import SelectMultiple, Textarea
from django.utils.safestring import mark_safe
from textwrap import dedent

TINYMCE_CONFIG = {
    "height": 450,
    "width": 800,
    "plugins": ["paste", "autosave", "table", "media", "wordcount", "searchreplace", "link"],
    "toolbar": "undo redo paste | styleselect | bold italic underline link | bullist numlist outdent indent | table",
    "style_formats": [
        {"title": 'Headings', "items": [
            {"title": 'Heading 1', "format": 'h1'},
            {"title": 'Heading 2', "format": 'h2'},
            {"title": 'Heading 3', "format": 'h3'},
        ]},
        {"title": 'Inline', "items": [
            {"title": 'Bold', "icon": 'bold', "format": 'bold'},
            {"title": 'Italic', "icon": 'italic', "format": 'italic'},
            {"title": 'Underline', "icon": 'underline', "format": 'underline'},
        ]},
        {"title": 'Blocks', "items": [
            {"title": 'Paragraph', "format": 'p'},
            {"title": 'Blockquote', "format": 'blockquote'},
            {"title": 'Pre', "format": 'pre'}
        ]},
    ]
}


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

    def render(self, name, value, attrs=None, choices=()):
        id = attrs.get("id", "id_%s" % name)
        output = [
            super(Select2SelectMultiple, self).render(name, value, attrs, choices),
            self.SCRIPT_TEMPLATE.format(id=id)
        ]
        return mark_safe(''.join(output))


class TinyMCE(Textarea):
    SCRIPT_TEMPLATE = dedent("""
    <script type="text/javascript">
    addEvent(window, "load", function(e) {{
        var config = {config_json};
        config.selector = "#" + document.querySelector("textarea[name={name}]").id;
        tinymce.init(config);
    }});
    </script>
    """)

    @property
    def media(self):
        return forms.Media(
            js=[static("admin/tinymce4/tinymce.min.js")],
            css={"all": [static("admin/tinymce-fixes.css")]}
        )

    def render(self, name, value, attrs=None):
        config = deepcopy(TINYMCE_CONFIG)
        output = [
            super().render(name, value, attrs),
            self.SCRIPT_TEMPLATE.format(name=name, config_json=json.dumps(config))
        ]
        return mark_safe(''.join(output))
