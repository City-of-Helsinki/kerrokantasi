from django.db import models
from helusers.models import AbstractUser


class User(AbstractUser):

    nickname = models.CharField(max_length=50, blank=True)
    has_strong_auth = models.BooleanField(default=False)

    def __str__(self):
        return ' - '.join([super().__str__(), self.get_display_name(), self.email])

    def get_real_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name).strip()

    def get_display_name(self):
        return self.nickname or self.get_real_name()

    def get_default_organization(self):
        return self.admin_organizations.order_by('created_at').first()

    def get_has_strong_auth(self):
        return self.has_strong_auth
