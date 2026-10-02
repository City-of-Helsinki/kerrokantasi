import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from democracy.models import SectionImage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Delete section images that have remained unattached past the retention period."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-seconds",
            type=int,
            default=settings.SECTION_IMAGE_ORPHAN_RETENTION_SECONDS,
            help=(
                "Delete unattached images at least this many seconds old. "
                "Defaults to SECTION_IMAGE_ORPHAN_RETENTION_SECONDS."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report images that would be deleted without deleting them.",
        )

    def handle(self, *args, **options):
        retention_seconds = options["older_than_seconds"]
        if retention_seconds < 0:
            raise CommandError("--older-than-seconds cannot be negative.")

        threshold = timezone.now() - timezone.timedelta(seconds=retention_seconds)
        images = SectionImage.objects.everything().filter(
            section__isnull=True,
            created_at__lt=threshold,
        )
        image_count = images.count()

        if options["dry_run"]:
            for image in images.iterator():
                logger.debug(f"Would delete orphan SectionImage {image.pk}")
            logger.info(f"{image_count} orphan section image(s) would be deleted")
            return

        for image in images.iterator():
            image_name = image.image.name
            image_storage = image.image.storage
            deleted_count, _ = (
                SectionImage.objects.everything()
                .filter(
                    pk=image.pk,
                    section__isnull=True,
                    created_at__lt=threshold,
                )
                .delete()
            )
            if deleted_count:
                logger.debug(f"Deleted orphan SectionImage {image.pk}")
            if image_name and deleted_count:
                if not SectionImage.objects.everything().filter(
                    image=image_name
                ).exists() and image_storage.exists(image_name):
                    image_storage.delete(image_name)

        logger.info(f"Deleted {image_count} orphan section image(s)")
