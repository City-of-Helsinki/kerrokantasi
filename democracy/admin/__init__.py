from functools import partial

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import TextField
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from djgeojson.fields import GeoJSONFormField
from leaflet.admin import LeafletGeoAdmin
from nested_admin.nested import NestedModelAdmin, NestedStackedInline

from democracy import models
from democracy.admin.widgets import Select2SelectMultiple, ShortTextAreaWidget
from democracy.enums import InitialSectionType
from democracy.models.utils import copy_hearing
from democracy.plugins import get_implementation


class FixedModelForm(forms.ModelForm):
    # Taken from https://github.com/asyncee/django-easy-select2/blob/master/easy_select2/forms.py
    """
    Simple child of ModelForm that removes the 'Hold down "Control" ...'
    message that is enforced in select multiple fields.
    See https://github.com/asyncee/django-easy-select2/issues/2
    and https://code.djangoproject.com/ticket/9321

    Removes also help_texts of GeoJSONFormFields as those will have maps.
    """

    def __init__(self, *args, **kwargs):
        super(FixedModelForm, self).__init__(*args, **kwargs)

        msg = force_text(_('Hold down "Control", or "Command" on a Mac, to select more than one.'))

        for name, field in self.fields.items():
            if isinstance(field, GeoJSONFormField):
                field.help_text = ''
            else:
                field.help_text = field.help_text.replace(msg, '')


# Inlines


class SectionImageInline(NestedStackedInline):
    model = models.SectionImage
    extra = 0
    exclude = ("public", "title")
    formfield_overrides = {
        TextField: {'widget': ShortTextAreaWidget}
    }


class SectionInline(NestedStackedInline):
    model = models.Section
    extra = 1
    inlines = [SectionImageInline]
    exclude = ("public", )
    formfield_overrides = {
        TextField: {'widget': ShortTextAreaWidget}
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        obj = kwargs.pop("obj", None)
        if db_field.name == "content":
            kwargs["widget"] = CKEditorUploadingWidget
            # Some initial value is needed for every section to workaround a bug in nested inlines
            # that causes an integrity error to be raised when a section image is added but the parent
            # section isn't saved.
            kwargs["initial"] = _("Enter text here.")
        if not getattr(obj, "pk", None):
            if db_field.name == "type":
                kwargs["initial"] = models.SectionType.objects.get(identifier=InitialSectionType.MAIN)
            elif db_field.name == "content":
                kwargs["initial"] = _("Enter the introduction text for the hearing here.")
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "plugin_identifier":
            widget = self._get_plugin_selection_widget(hearing=obj)
            field.label = _("Plugin")
            field.widget = widget
        if db_field.name == "id" and not (obj and obj.pk):
            field.widget = forms.HiddenInput()
        return field

    def _get_plugin_selection_widget(self, hearing):
        choices = [("", "------")]
        plugins = getattr(settings, "DEMOCRACY_PLUGINS")
        if hearing and hearing.pk:
            current_plugin_identifiers = set(hearing.sections.values_list("plugin_identifier", flat=True))
        else:
            current_plugin_identifiers = set()
        for plugin_identifier in sorted(current_plugin_identifiers):
            if plugin_identifier and plugin_identifier not in plugins:
                # The plugin has been unregistered or something?
                choices.append((plugin_identifier, plugin_identifier))
        for idfr, classpath in sorted(plugins.items()):
            choices.append((idfr, get_implementation(idfr).display_name or idfr))
        widget = forms.Select(choices=choices)
        return widget

    def get_formset(self, request, obj=None, **kwargs):
        kwargs["formfield_callback"] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        if getattr(obj, "pk", None):
            kwargs['extra'] = 0
        return super().get_formset(request, obj, **kwargs)


# Admins


class HearingGeoAdmin(LeafletGeoAdmin):
    settings_overrides = {
        'DEFAULT_CENTER': (60.192059, 24.945831),  # Helsinki
        'DEFAULT_ZOOM': 11,
    }


class HearingAdmin(NestedModelAdmin, HearingGeoAdmin):

    class Media:
        js = ("admin/ckeditor-nested-inline-fix.js",)

    inlines = [SectionInline]
    list_display = ("slug", "published", "title", "open_at", "close_at", "force_closed")
    list_filter = ("published",)
    search_fields = ("slug", "title")
    readonly_fields = ("preview_url",)
    fieldsets = (
        (None, {
            "fields": ("title", "labels", "slug", "preview_url")
        }),
        (_("Availability"), {
            "fields": ("published", "open_at", "close_at", "force_closed")
        }),
        (_("Area"), {
            "fields": ("geojson",)
        })
    )
    formfield_overrides = {
        TextField: {'widget': ShortTextAreaWidget}
    }
    form = FixedModelForm
    actions = ("copy_as_draft", "delete_selected")
    ordering = ("slug",)

    def copy_as_draft(self, request, queryset):
        for hearing in queryset:
            copy_hearing(hearing, published=False)
            self.message_user(request, _('Copied Hearing "%s" as a draft.' % hearing.title))

    def preview_url(self, obj):
        return obj.preview_url
    preview_url.short_description = _('Preview URL')

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "labels":
            kwargs["widget"] = Select2SelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def delete_selected(self, request, queryset):
        if not self.has_delete_permission(request):
            raise PermissionDenied

        hearing_count = queryset.count()
        if hearing_count:
            for hearing in queryset:
                hearing.soft_delete()
            self.message_user(request, _('Successfully deleted %(count)d %(items)s.') % {
                'count': hearing_count, 'items': model_ngettext(self.opts, hearing_count)
            })
    delete_selected.short_description = _('Delete selected %(verbose_name_plural)s')

    def save_formset(self, request, form, formset, change):
        objects = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.soft_delete()

        for obj in objects:
            obj.save()

        formset.save_m2m()


class LabelAdmin(admin.ModelAdmin):
    exclude = ("public",)


class SectionTypeAdmin(admin.ModelAdmin):
    fields = ("name_singular", "name_plural")

    def get_queryset(self, request):
        return super().get_queryset(request).exclude_initial()


# Wire it up!


admin.site.register(models.Label, LabelAdmin)
admin.site.register(models.Hearing, HearingAdmin)
admin.site.register(models.SectionType, SectionTypeAdmin)
