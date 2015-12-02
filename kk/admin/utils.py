# -*- coding: utf-8 -*-
from django.forms.widgets import Textarea


class WymEditorWidget(Textarea):
    class Media:
        css = {
            'all': ('admin/wymeditor/skins/djangoadmin/skin.css',),
        }
        js = (
            'admin/wym-shim.js',
            'admin/wymeditor/jquery.wymeditor.min.js',
        )

    def render(self, name, value, attrs=None):
        attrs = (attrs or {})
        attrs["data-wym"] = "true"
        return super(WymEditorWidget, self).render(name=name, value=value, attrs=attrs)


class WymifyMixin(object):
    wymify_fields = ()

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        :type db_field: django.db.models.fields.Field
        :rtype: django.forms.fields.Field
        """
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in self.wymify_fields:
            formfield.widget = WymEditorWidget(attrs=formfield.widget.attrs)
        return formfield
