import os
from optparse import make_option
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management import call_command
from django.core.management.base import BaseCommand
from kk.factories.hearing import HearingFactory, LabelFactory
from kk.factories.user import UserFactory
from kk.models import Hearing, Label


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--nuke", dest="nuke", action="store_true"),
    )

    def handle(self, *args, **options):
        if options.pop("nuke", False):
            if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
                db_file = settings.DATABASES["default"]["NAME"]
                if os.path.isfile(db_file):
                    os.unlink(db_file)
            call_command("migrate", **options.copy())

        User = get_user_model()
        if issubclass(User, AbstractUser):
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
