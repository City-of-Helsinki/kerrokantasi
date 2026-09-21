import datetime
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from democracy.factories.hearing import SectionFactory, SectionImageFactory
from democracy.models import SectionImage


@pytest.mark.django_db(transaction=True)
def test_cleanup_orphan_section_images_deletes_old_images(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    old_image = SectionImageFactory(section=None)
    old_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    old_image.save(update_fields=("created_at",))
    image_name = old_image.image.name

    call_command("cleanup_orphan_section_images", "--older-than-seconds", "60")
    assert not SectionImage.objects.filter(pk=old_image.pk).exists()
    assert not old_image.image.storage.exists(image_name)


@pytest.mark.django_db(transaction=True)
def test_cleanup_orphan_section_images_deletes_old_soft_deleted_images(
    tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    old_image = SectionImageFactory(section=None)
    old_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    old_image.save(update_fields=("created_at",))
    old_image.soft_delete()
    image_name = old_image.image.name

    call_command("cleanup_orphan_section_images", "--older-than-seconds", "60")

    assert not SectionImage.objects.everything().filter(pk=old_image.pk).exists()
    assert not old_image.image.storage.exists(image_name)


@pytest.mark.django_db
def test_cleanup_orphan_section_images_keeps_files_referenced_by_other_images(
    tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    old_image = SectionImageFactory(section=None)
    image_name = old_image.image.name
    old_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    old_image.save(update_fields=("created_at",))
    referenced_image = SectionImage.objects.create(
        image=image_name,
        section=SectionFactory(create_random_comments=False),
    )

    call_command("cleanup_orphan_section_images", "--older-than-seconds", "60")

    assert not SectionImage.objects.everything().filter(pk=old_image.pk).exists()
    assert SectionImage.objects.filter(pk=referenced_image.pk).exists()
    assert old_image.image.storage.exists(image_name)


@pytest.mark.django_db
def test_cleanup_orphan_section_images_deletes_row_when_storage_delete_fails(
    tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    old_image = SectionImageFactory(section=None)
    old_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    old_image.save(update_fields=("created_at",))
    image_name = old_image.image.name

    with (
        patch.object(old_image.image.storage, "delete", side_effect=OSError),
        pytest.raises(OSError),
    ):
        call_command("cleanup_orphan_section_images", "--older-than-seconds", "60")

    assert not SectionImage.objects.filter(pk=old_image.pk).exists()
    assert old_image.image.storage.exists(image_name)


@pytest.mark.django_db
def test_cleanup_orphan_section_images_keeps_recent_and_attached_images(
    tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    recent_image = SectionImageFactory(section=None)
    attached_image = SectionImageFactory(
        section=SectionFactory(create_random_comments=False)
    )
    attached_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    attached_image.save(update_fields=("created_at",))

    call_command("cleanup_orphan_section_images", "--older-than-seconds", "60")

    assert SectionImage.objects.filter(pk=recent_image.pk).exists()
    assert SectionImage.objects.filter(pk=attached_image.pk).exists()


@pytest.mark.django_db
def test_cleanup_orphan_section_images_dry_run_keeps_images(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    old_image = SectionImageFactory(section=None)
    old_image.created_at = timezone.now() - datetime.timedelta(seconds=120)
    old_image.save(update_fields=("created_at",))

    call_command(
        "cleanup_orphan_section_images",
        "--older-than-seconds",
        "60",
        "--dry-run",
    )

    assert SectionImage.objects.filter(pk=old_image.pk).exists()
