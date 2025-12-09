from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from helsinki_gdpr.models import SerializableMixin
from parler.models import TranslatableModel, TranslatedFields

from democracy.models.base import SerializableBaseModelManager, StringIdBaseModel


class Organization(StringIdBaseModel, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "name"},
    )

    name = models.CharField(verbose_name=_("name"), max_length=255, unique=True)
    admin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="admin_organizations"
    )
    parent = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
    )
    external_organization = models.BooleanField(
        verbose_name=_("external organization"),
        default=False,
        help_text=_(
            "Enable this, if this organization is external from the city, "
            "(e.g. a company) and should be hidden from users."
        ),
    )

    objects = SerializableBaseModelManager()

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name


class ContactPersonOrder(models.Model):
    hearing = models.ForeignKey(
        "Hearing", on_delete=models.CASCADE, related_name="contact_person_orders"
    )
    contact_person = models.ForeignKey(
        "ContactPerson", on_delete=models.CASCADE, related_name="contact_person_orders"
    )
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "democracy_hearing_contact_persons"
        ordering = ["hearing", "order"]

    def __str__(self):
        return f"{self.hearing} - {self.contact_person}"


class ContactPerson(TranslatableModel, StringIdBaseModel):
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("organization"),
        related_name="contact_persons",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    translations = TranslatedFields(
        title=models.CharField(
            verbose_name=_("title"),
            max_length=255,
            help_text=_("Contact person's job title or role"),
        ),
    )
    name = models.CharField(verbose_name=_("name"), max_length=50)
    phone = models.CharField(verbose_name=_("phone"), max_length=50)
    email = models.EmailField(verbose_name=_("email"))
    additional_info = models.CharField(
        verbose_name=_("additional_info"),
        max_length=255,
        help_text=_(
            "Additional info about the contact e.g. which external organization are they part of. This information is "  # noqa: E501
            "visible to users instead of their organization, if they they belong to an external organization."  # noqa: E501
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("contact person")
        verbose_name_plural = _("contact persons")
        # Use contact_person_orders ordering as default. It may cause duplicate ContactPersons to be returned, which  # noqa: E501
        # should be fixed elsewhere. If this is not the default ordering, we can't return the ContactPersons in the  # noqa: E501
        # correct order when used nested serializer field under Hearing in the Rest API
        ordering = [
            "contact_person_orders__hearing",
            "contact_person_orders__order",
            "name",
        ]

    def __str__(self):
        return "%s, %s / %s" % (
            self.name,
            getattr(self, "title", ""),
            self.organization,
        )
