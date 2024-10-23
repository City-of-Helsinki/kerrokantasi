from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count

from democracy.models import SectionComment


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--yes-i-know-what-im-doing", dest="nothing_can_go_wrong", action="store_true")

    def _remove_dupes(self, klass):
        # detect the dupes primarily by content
        potential_dupes = (
            klass.objects.values("content")
            .exclude(deleted=True)
            .annotate(Count("content"))
            .filter(content__count__gt=1)
            .order_by("-content__count")
        )

        # further filter by creation time, parent hearing and plugin data
        for d in potential_dupes:
            objs = list(klass.objects.filter(content=d["content"]).order_by("created_at"))
            first = objs.pop(0)
            print(
                "%s %s\n%s\n%s"
                % (getattr(first, klass.parent_field), first.created_at, first.content, first.plugin_data)
            )
            for other in objs:
                if other.plugin_data != first.plugin_data:
                    print("\tplugin data differs %s" % other)
                    continue
                if other.created_at - first.created_at > timedelta(hours=1):
                    print("\ttoo late %s" % (other.created_at - first.created_at))
                    continue
                if getattr(other, klass.parent_field) != getattr(first, klass.parent_field):
                    print("\tdifferent parent %s" % other)
                    continue
                print("\tbye bye %s" % other)
                # transfer any votes to the existing comment
                first.n_legacy_votes += other.n_legacy_votes
                first.voters = first.voters.all() | other.voters.all()
                first.save()
                other.soft_delete()

    def handle(self, *args, **options):
        if not options.pop("nothing_can_go_wrong", False):
            raise Exception("You don't know what you're doing.")

        self._remove_dupes(SectionComment)
