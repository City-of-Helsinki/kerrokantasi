from ckeditor_uploader.widgets import CKEditorUploadingWidget
from collections import Counter
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import NestedObjects
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.gis.db.models import ManyToManyField
from django.core.exceptions import ValidationError
from django.db import router
from django.db.models import TextField
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from djgeojson.fields import GeoJSONFormField
from functools import partial
from leaflet.admin import LeafletGeoAdmin
from nested_admin.nested import NestedModelAdminMixin, NestedStackedInline
from parler.admin import TranslatableAdmin, TranslatableStackedInline
from parler.forms import TranslatableBaseInlineFormSet, TranslatableModelForm

from democracy import models
from democracy.admin.widgets import Select2SelectMultiple, ShortTextAreaWidget
from democracy.enums import InitialSectionType
from democracy.models.utils import copy_hearing
from democracy.plugins import get_implementation


class FixedModelForm(TranslatableModelForm):
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


class SectionImageInline(TranslatableStackedInline, NestedStackedInline):
    model = models.SectionImage
    extra = 0
    exclude = ("title",)
    formfield_overrides = {
        TextField: {"widget": ShortTextAreaWidget},
    }


class SectionInlineFormSet(TranslatableBaseInlineFormSet):
    def clean(self):
        super().clean()

        # validate that there is exactly one main and no more than one closure info sections
        mains = 0
        closure_infos = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or form.cleaned_data.get('DELETE'):
                continue

            section_type = form.cleaned_data.get('type')
            if not section_type:
                continue

            if section_type.identifier == InitialSectionType.MAIN:
                mains += 1
            elif section_type.identifier == InitialSectionType.CLOSURE_INFO:
                closure_infos += 1

        if mains != 1:
            raise ValidationError(_('There must be exactly one main section.'))

        if closure_infos > 1:
            raise ValidationError(_('There cannot be more than one closure info section.'))


class SectionInline(NestedStackedInline, TranslatableStackedInline):
    model = models.Section
    extra = 1
    inlines = [SectionImageInline]
    exclude = ("published",)
    formfield_overrides = {
        TextField: {"widget": ShortTextAreaWidget},
    }
    formset = SectionInlineFormSet

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


class ContactPersonInline(NestedStackedInline):
    verbose_name = _("contact person")
    verbose_name_plural = _("contact persons")
    model = models.ContactPersonOrder
    extra = 1


# Admins


class HearingGeoAdmin(LeafletGeoAdmin):
    settings_overrides = {
        'DEFAULT_CENTER': settings.DEFAULT_MAP_COORDINATES,
        'DEFAULT_ZOOM': settings.DEFAULT_MAP_ZOOM,
    }


class HearingAdmin(NestedModelAdminMixin, HearingGeoAdmin, TranslatableAdmin):
    class Media:
        js = ("admin/ckeditor-nested-inline-fix.js",)

    inlines = [SectionInline, ContactPersonInline]
    list_display = ("slug", "published", "title", "open_at", "close_at", "force_closed")
    list_filter = ("published",)
    search_fields = ("slug", "translations__title")
    readonly_fields = ("preview_url",)
    raw_id_fields = ("project_phase",)
    fieldsets = (
        (None, {"fields": ("title", "labels", "slug", "preview_url", "organization")}),
        (_("Project"), {"fields": ("project_phase",)}),
        (_("Availability"), {"fields": ("published", "open_at", "close_at", "force_closed")}),
        (_("Area"), {"fields": ("geometry",)}),
    )
    formfield_overrides = {
        TextField: {'widget': ShortTextAreaWidget},
    }
    form = FixedModelForm
    actions = ["copy_as_draft"]  # delete_selected is built_in, should not be added
    ordering = ("slug",)

    def copy_as_draft(self, request, queryset):
        for hearing in queryset:
            copy_hearing(hearing, published=False)
            self.message_user(request, _('Copied Hearing "%s" as a draft.' % hearing.title))

    def preview_url(self, obj):
        if not obj.preview_url:
            return ''
        return format_html('<a href="%s">%s</a>' % (obj.preview_url, obj.preview_url))

    preview_url.short_description = _('Preview URL')

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "labels":
            kwargs["widget"] = Select2SelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_deleted_objects(self, objs, request):
        # we override here to allow soft_delete, modified from
        # https://github.com/django/django/blob/master/django/contrib/admin/utils.py
        """
        Find all objects related to ``objs`` that should also be deleted. ``objs``
        must be a homogeneous iterable of objects (e.g. a QuerySet).
        Return a nested list of strings suitable for display in the
        template with the ``unordered_list`` filter.
        """
        try:
            obj = objs[0]
        except IndexError:
            return [], {}, set(), []
        else:
            using = router.db_for_write(obj._meta.model)
        collector = NestedObjects(using=using)
        collector.collect(objs)

        def format_callback(obj):
            return '%s: %s' % (capfirst(obj._meta.verbose_name), obj)

        to_delete = collector.nested(format_callback)
        model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}
        # we need to display count by model of the protected items too
        protected = [format_callback(obj) for obj in collector.protected]
        protected_model = {obj._meta.verbose_name_plural for obj in collector.protected}
        protected_model_count = dict(Counter(protected_model))
        # since we are only performing soft delete, we may soft delete the protected objects later
        return to_delete + protected, {**model_count, **protected_model_count}, set(), []

    def delete_queryset(self, request, queryset):
        # this method is called by delete_selected and can be overridden
        try:
            obj = queryset[0]
        except IndexError:
            return
        else:
            using = router.db_for_write(obj._meta.model)
        collector = NestedObjects(using=using)
        collector.collect(queryset)
        to_delete = []
        for item, value in collector.model_objs.items():
            to_delete += value
        to_delete += collector.protected
        # since we are only performing soft delete, we must soft_delete related objects too, if possible
        for obj in to_delete:
            if hasattr(obj, 'soft_delete'):
                obj.soft_delete(user=request.user)

    def delete_model(self, request, obj):
        using = router.db_for_write(obj._meta.model)
        collector = NestedObjects(using=using)
        collector.collect([obj])
        to_delete = []
        for item, value in collector.model_objs.items():
            to_delete += value
        to_delete += collector.protected
        # since we are only performing soft delete, we must soft_delete related objects too, if possible
        for obj in to_delete:
            if hasattr(obj, 'soft_delete'):
                obj.soft_delete()

    def save_formset(self, request, form, formset, change):
        objects = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.soft_delete()

        for obj in objects:
            obj.save()

        formset.save_m2m()


class LabelAdmin(TranslatableAdmin, admin.ModelAdmin):
    exclude = ("published",)


class SectionTypeAdmin(admin.ModelAdmin):
    fields = ("name_singular", "name_plural")

    def get_queryset(self, request):
        return super().get_queryset(request).exclude_initial()


class OrganizationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        ManyToManyField: {'widget': FilteredSelectMultiple("ylläpitäjät", is_stacked=False)},
    }
    exclude = ('published',)


class ContactPersonAdmin(TranslatableAdmin, admin.ModelAdmin):
    list_display = ('name', 'title', 'organization', 'phone', 'email')
    exclude = ('published',)
    ordering = ("name",)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'section', 'author_name', 'content', 'is_published', 'flagged_at')
    list_filter = (
        'deleted',
        'flagged_at',
        'section__hearing__slug',
    )
    search_fields = ('section__id', 'author_name', 'title', 'content')
    readonly_fields = (
        'reply_to',
        'author_name',
        'organization',
        'geojson',
        'plugin_identifier',
        'plugin_data',
        'label',
        'language_code',
        'voters',
        'section',
        'created_by_user',
        'deleted_at',
        'deleted_by',
        'flagged_at',
        'flagged_by',
        'edited',
        'moderated',
    )
    change_form_template = 'admin/comment_change_form.html'

    def get_fields(self, request, obj=None):
        """Display deleted-related fields only if comment is deleted"""

        fields = [
            'title',
            'content',
            'reply_to',
            'author_name',
            'organization',
            'geojson',
            'map_comment_text',
            'plugin_identifier',
            'plugin_data',
            'pinned',
            'label',
            'language_code',
            'voters',
            'section',
            'created_by_user',
            'edited',
            'moderated',
            'edit_reason',
            'delete_reason',
        ]
        if obj and obj.flagged_at:
            fields += ['flagged_at', 'flagged_by']
        if obj and obj.deleted:
            fields += ['deleted_at', 'deleted_by']
        return fields

    def is_published(self, obj):
        """Invert deleted field for readability in admin"""

        return not obj.deleted

    is_published.boolean = True  # Make field use green/red icons in list view

    def created_by_user(self, obj):
        # returns a link to the user that created the comment.
        if obj.created_by_id and get_user_model().objects.get(id=obj.created_by_id):
            user_url = reverse("admin:app_list", args=['kerrokantasi'])
            user_url += "user/{}/change/".format(obj.created_by_id)
            user_info = "{} - {}".format(
                obj.created_by.get_display_name(), get_user_model().objects.get(id=obj.created_by_id).email
            )
            return format_html('<a href="{}">{}</a>', user_url, user_info)

    def delete_queryset(self, request, queryset):
        # this method is called by delete_selected and can be overridden
        for comment in queryset:
            comment.soft_delete(user=request.user)

    def delete_model(self, request, obj):
        # this method is called by the admin form and can be overridden
        obj.soft_delete(user=request.user)

    def get_queryset(self, request):
        """Override parent's method in order to return even deleted comments"""
        qs = self.model._default_manager.everything()

        if not request.user.is_superuser:
            # Only show comments for user's organizations hearings
            organizations = request.user.admin_organizations.all()
            qs = qs.filter(section__hearing__organization__in=organizations)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def response_change(self, request, obj):
        # Handle undeleting of comment
        if "_undeleteobject" in request.POST:
            obj.undelete()
        return super().response_change(request, obj)

    def changelist_view(self, request, extra_context=None):
        """Use deleted=False filter by default"""
        if not request.META['QUERY_STRING'] and not request.META.get('HTTP_REFERER', '').startswith(
            request.build_absolute_uri()
        ):
            return HttpResponseRedirect(request.path + "?deleted__exact=0")
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        obj.edited = True
        # If admin edits their own comment, don't mark as moderated
        if obj.created_by_id != request.user.id:
            obj.moderated = request.user.is_staff
        super().save_model(request, obj, form, change)


class ProjectPhaseInline(TranslatableStackedInline, NestedStackedInline):
    model = models.ProjectPhase
    extra = 1


class ProjectAdmin(TranslatableAdmin, admin.ModelAdmin):
    list_display = ('title_localized', 'identifier')
    search_fields = ('title', 'identifier')
    inlines = (ProjectPhaseInline,)

    def title_localized(self, obj):
        return get_any_language(obj, 'title')

    title_localized.short_description = 'Title'


class ProjectPhaseAdmin(TranslatableAdmin, admin.ModelAdmin):
    list_display = ('title_localized', 'project')
    list_filter = ('project',)
    search_fields = ('title', 'project__title')

    def title_localized(self, obj):
        return get_any_language(obj, 'title')

    title_localized.short_description = 'Title'


def get_any_language(obj, attr_name):
    """
    Get a string of at least some language, if the attribute is not
    translated to the current language or the translations are empty strings.
    """
    translation = obj.safe_translation_getter(attr_name)
    if not translation:
        for lang in settings.PARLER_LANGUAGES[None]:
            translation = obj.safe_translation_getter(attr_name, language_code=lang['code'])
            if translation:
                break
    return translation


# Wire it up!


admin.site.register(models.Label, LabelAdmin)
admin.site.register(models.Hearing, HearingAdmin)
admin.site.register(models.SectionType, SectionTypeAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.ContactPerson, ContactPersonAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.ProjectPhase, ProjectPhaseAdmin)
admin.site.register(models.SectionComment, CommentAdmin)
