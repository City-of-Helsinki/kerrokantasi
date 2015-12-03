from optparse import make_option

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management.base import BaseCommand

from democracy.factories.hearing import HearingFactory, LabelFactory
from democracy.factories.user import UserFactory
from democracy.management.commands.utils import nuke
from democracy.models import Hearing, Label


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--nuke", dest="nuke", action="store_true"),
    )

    def handle(self, *args, **options):
        if options.pop("nuke", False):
            nuke(command_options=options)

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
