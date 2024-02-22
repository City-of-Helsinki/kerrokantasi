from django.db import models
from helsinki_gdpr.models import SerializableMixin
from helusers.models import AbstractUser

from democracy.models import SectionComment


class User(AbstractUser, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "uuid"},
        {"name": "username"},
        {"name": "nickname"},
        {"name": "first_name"},
        {"name": "last_name"},
        {"name": "email"},
        {"name": "has_strong_auth"},
        {"name": "sectioncomments"},
        {"name": "voted_sectioncomments"},
        {"name": "followed_hearings"},
        {"name": "admin_organizations"},
        {"name": "hearing_created"},
    )

    nickname = models.CharField(max_length=50, blank=True)
    has_strong_auth = models.BooleanField(default=False)

    # Properties for GDPR api serialization
    @property
    def sectioncomments(self):
        return [s.serialize() for s in SectionComment.objects.everything(created_by=self).iterator()]

    @property
    def voted_sectioncomments(self):
        return [s.serialize() for s in self.voted_democracy_sectioncomment.everything().iterator()]

    def __str__(self):
        return " - ".join([super().__str__(), self.get_display_name(), self.email])

    def get_real_name(self):
        return "{0} {1}".format(self.first_name, self.last_name).strip()

    def get_display_name(self):
        return self.nickname or self.get_real_name()

    def get_default_organization(self):
        return self.admin_organizations.order_by("created_at").first()

    def get_has_strong_auth(self):
        return self.has_strong_auth
