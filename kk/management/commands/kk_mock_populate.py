from django.conf import settings
from django.core.management.base import BaseCommand
from kk.factories.hearing import HearingFactory, LabelFactory
from kk.factories.user import UserFactory
from kk.models import Hearing, Label


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.AUTH_USER_MODEL == "auth.User":
            from django.contrib.auth.models import User
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(username="admin", email="admin@example.com", password="admin")
                print("Admin user 'admin' (password 'admin') created")
            while User.objects.count() < 25:
                user = UserFactory()
                print("Created user %s" % user.pk)
        while Label.objects.count() < 5:
            label = LabelFactory()
            print("Created label %s" % label.pk)
        while Hearing.objects.count() < 10:
            hearing = HearingFactory()
            print("Created hearing %s" % hearing.pk)
