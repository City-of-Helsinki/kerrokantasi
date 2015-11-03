from django.core.management.base import BaseCommand
from kk.factories.hearing import HearingFactory, LabelFactory
from kk.models import Hearing, Label


class Command(BaseCommand):
    def handle(self, *args, **options):
        while Label.objects.count() < 5:
            label = LabelFactory()
            print("Created label %s" % label.pk)
        while Hearing.objects.count() < 10:
            hearing = HearingFactory()
            print("Created hearing %s" % hearing.pk)
