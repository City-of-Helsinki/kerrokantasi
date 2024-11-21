from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from democracy.utils import user_data_remover


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--remove-user-data-from-old-objects",
            action="store_true",
            help="Remove user reference from old objects.",
        )
        parser.add_argument(
            "--delete-comment-version-history",
            action="store_true",
            help="Delete old comments version history.",
        )
        parser.add_argument(
            "--delete-users",
            action="store_true",
            help="Delete users without activity created before threshold.",
        )
        parser.add_argument(
            "--older-than-days",
            default=settings.DEFAULT_USER_DATA_REMOVAL_THRESHOLD_DAYS,
            type=int,
            help=f"Specify the number of days for removal; "
            f"defaults to {settings.DEFAULT_USER_DATA_REMOVAL_THRESHOLD_DAYS}."
            f"Data as old or older than this will be removed.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        threshold_time = timezone.now() - timezone.timedelta(
            days=options["older_than_days"]
        )

        if options["remove_user_data_from_old_objects"]:
            user_data_remover.remove_old_objects_user_data(threshold_time)
            user_data_remover.remove_user_from_old_comments(threshold_time)
            user_data_remover.remove_user_votes_from_old_comments(threshold_time)
            user_data_remover.remove_user_from_old_poll_answers(threshold_time)
            user_data_remover.remove_user_from_old_hearings(threshold_time)
            user_data_remover.remove_contact_persons_from_old_hearings(threshold_time)

            if options["delete_comment_version_history"]:
                user_data_remover.delete_old_comments_versions(threshold_time)

        if options["delete_users"]:
            user_data_remover.delete_old_users_without_activity(threshold_time)
