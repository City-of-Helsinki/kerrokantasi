from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from democracy.models.base import StringIdBaseModel


class Organization(StringIdBaseModel):
    name = models.CharField(verbose_name=_('name'), max_length=255, unique=True)
    admin_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="admin_organizations")
    parent = models.ForeignKey(
        "Organization", on_delete=models.SET_NULL, blank=True, null=True, related_name="children"
    )

    class Meta:
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    def __str__(self):
        return self.name


class ContactPersonOrder(models.Model):
    hearing = models.ForeignKey("Hearing", on_delete=models.CASCADE, related_name="contact_person_orders")
    contact_person = models.ForeignKey("ContactPerson", on_delete=models.CASCADE, related_name="contact_person_orders")
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
        title=models.CharField(verbose_name=_('title'), max_length=255),
    )
    name = models.CharField(verbose_name=_('name'), max_length=50)
    phone = models.CharField(verbose_name=_('phone'), max_length=50)
    email = models.EmailField(verbose_name=_('email'))

    class Meta:
        verbose_name = _('contact person')
        verbose_name_plural = _('contact persons')
        # Use contact_person_orders ordering as default. It may cause duplicate ContactPersons to be returned, which
        # should be fixed elsewhere. If this is not the default ordering, we can't return the ContactPersons in the
        # correct order when used nested serializer field under Hearing in the Rest API
        ordering = ["contact_person_orders__hearing", "contact_person_orders__order", "name"]

    def __str__(self):
        return '%s, %s / %s' % (self.name, getattr(self, "title", ""), self.organization)
