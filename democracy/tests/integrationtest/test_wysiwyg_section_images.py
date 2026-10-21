import pytest
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from democracy.factories.hearing import SectionImageFactory
from democracy.models import SectionImage
from democracy.tests.utils import (
    IMAGES,
    get_data_from_response,
    get_hearing_detail_url,
    get_image_path,
)
from democracy.views.section import (
    SectionCreateUpdateSerializer,
    get_inline_image_name,
)


def test_inline_image_name_is_none_when_media_url_has_no_path(settings):
    settings.MEDIA_URL = "https://media.example.com"

    assert get_inline_image_name("https://media.example.com/images/example.png") is None


@pytest.mark.django_db
def test_inline_images_are_associated_from_src_url(
    john_smith_api_client, default_hearing
):
    image_url = reverse("image-list")
    with open(get_image_path(IMAGES["ORIGINAL"]), "rb") as image_file:
        response = john_smith_api_client.post(
            image_url,
            data={"image": image_file, "purpose": SectionImage.PURPOSE_INLINE},
            format="multipart",
        )

    data = get_data_from_response(response, status_code=201)
    image = SectionImage.objects.get(pk=data["id"])
    assert image.purpose == SectionImage.PURPOSE_INLINE
    assert image.ordering == 0
    assert image.section is None

    section = default_hearing.get_main_section()
    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    section_data["content"]["en"] = f'<p><img src="{data["url"]}" alt="Example" /></p>'
    updated_hearing = get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    image.refresh_from_db()
    assert image.section_id == section.pk
    assert image.modified_by_id == john_smith_api_client.user.id
    updated_section = next(
        section_data
        for section_data in updated_hearing["sections"]
        if section_data["id"] == section.id
    )
    assert data["id"] not in [image["id"] for image in updated_section["images"]]

    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    section_data["content"]["en"] = "<p>The image was removed.</p>"
    get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    image.refresh_from_db()
    assert image.section_id == section.pk
    assert image.deleted
    assert image.deleted_by_id == john_smith_api_client.user.id


@pytest.mark.django_db
def test_newest_matching_orphan_inline_image_is_attached(
    john_smith_api_client, default_hearing
):
    with open(get_image_path(IMAGES["ORIGINAL"]), "rb") as image_file:
        response = john_smith_api_client.post(
            reverse("image-list"),
            data={"image": image_file, "purpose": SectionImage.PURPOSE_INLINE},
            format="multipart",
        )
    image_data = get_data_from_response(response, status_code=201)
    first_image = SectionImage.objects.get(pk=image_data["id"])
    second_image = SectionImage.objects.create(
        image=first_image.image.name,
        purpose=SectionImage.PURPOSE_INLINE,
        ordering=5,
        created_by=john_smith_api_client.user,
    )
    assert second_image.ordering == 0

    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section = default_hearing.get_main_section()
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    section_data["content"]["en"] = (
        f'<p><img src="{image_data["url"]}" alt="Example" /></p>'
    )

    response = john_smith_api_client.put(hearing_url, data=hearing, format="json")

    assert response.status_code == 200
    first_image.refresh_from_db()
    second_image.refresh_from_db()
    assert first_image.section_id is None
    assert second_image.section_id == section.pk


@pytest.mark.django_db
def test_existing_section_inline_image_is_preferred_over_matching_orphan(
    john_smith_api_client, default_hearing
):
    section = default_hearing.get_main_section()
    existing_image = SectionImageFactory(
        section=section,
        purpose=SectionImage.PURPOSE_INLINE,
        created_by=john_smith_api_client.user,
    )
    orphan_image = SectionImage.objects.create(
        image=existing_image.image.name,
        purpose=SectionImage.PURPOSE_INLINE,
        created_by=john_smith_api_client.user,
    )
    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    section_data["content"]["en"] = f'<p><img src="{existing_image.image.url}" /></p>'

    get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    existing_image.refresh_from_db()
    orphan_image.refresh_from_db()
    assert existing_image.section_id == section.pk
    assert not existing_image.deleted
    assert orphan_image.section_id is None
    assert not orphan_image.deleted
    assert list(
        section.images.filter(purpose=SectionImage.PURPOSE_INLINE).values_list(
            "pk", flat=True
        )
    ) == [existing_image.pk]


@pytest.mark.django_db
def test_external_inline_image_url_is_rejected(john_smith_api_client, default_hearing):
    section = default_hearing.get_main_section()
    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    original_content = section_data["content"].copy()
    section_data["content"]["en"] = (
        '<p><img src="https://example.com/image.webp" /></p>'
    )

    response = john_smith_api_client.put(hearing_url, data=hearing, format="json")

    data = get_data_from_response(response, status_code=400)
    assert data == ["Inline images must be uploaded to this backend."]

    updated_hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    updated_section = next(
        section_data
        for section_data in updated_hearing["sections"]
        if section_data["id"] == section.id
    )
    assert updated_section["content"] == original_content


@pytest.mark.django_db
def test_legacy_data_uri_inline_image_remains_editable(
    john_smith_api_client, default_hearing
):
    section = default_hearing.get_main_section()
    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    legacy_content = (
        '<p>Legacy image.</p><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" />'
    )
    section_data["content"]["en"] = legacy_content
    get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == section.id
    )
    edited_content = legacy_content.replace("Legacy image.", "Updated text.")
    section_data["content"]["en"] = edited_content
    updated_hearing = get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    updated_section = next(
        section_data
        for section_data in updated_hearing["sections"]
        if section_data["id"] == section.id
    )
    assert updated_section["content"]["en"] == edited_content


@pytest.mark.django_db
@pytest.mark.parametrize("image_reference_field", ["id", "reference_id"])
def test_section_image_validation_rejects_another_users_orphan(
    john_smith, john_doe, image_reference_field
):
    image = SectionImageFactory(
        section=None,
        purpose=SectionImage.PURPOSE_SECTION_LEVEL,
        created_by=john_doe,
    )
    request = APIRequestFactory().post("/")
    request.user = john_smith
    serializer = SectionCreateUpdateSerializer(context={"request": request})

    with pytest.raises(
        ValidationError, match="You do not have access to this unattached image"
    ):
        serializer.validate_images([{image_reference_field: image.pk}])


@pytest.mark.django_db
def test_inline_image_cannot_be_reused_as_section_level_image(default_hearing):
    inline_image = SectionImageFactory(
        section=default_hearing.get_main_section(),
        purpose=SectionImage.PURPOSE_INLINE,
    )
    serializer = SectionCreateUpdateSerializer()

    with pytest.raises(
        ValidationError, match=f"Image {inline_image.pk} does not exist"
    ):
        serializer.validate_images([{"reference_id": inline_image.pk}])


@pytest.mark.django_db
def test_copy_section_creates_image_record_from_matching_url(
    john_smith, john_smith_api_client, default_hearing
):
    with open(get_image_path(IMAGES["ORIGINAL"]), "rb") as image_file:
        response = john_smith_api_client.post(
            reverse("image-list"),
            data={"image": image_file, "purpose": SectionImage.PURPOSE_INLINE},
            format="multipart",
        )
    image_data = get_data_from_response(response, status_code=201)
    source_image = SectionImage.objects.get(pk=image_data["id"])
    source_image.set_current_language("en")
    source_image.alt_text = "Source image alt text"
    source_image.save()
    source_section = default_hearing.get_main_section()

    hearing_url = get_hearing_detail_url(default_hearing.id)
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    source_section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == source_section.id
    )
    source_section_data["content"]["en"] = f'<p><img src="{image_data["url"]}" /></p>'
    get_data_from_response(
        john_smith_api_client.put(hearing_url, data=hearing, format="json"),
        status_code=200,
    )

    source_image.refresh_from_db()
    assert source_image.section_id == source_section.pk
    hearing = get_data_from_response(john_smith_api_client.get(hearing_url))
    source_section_data = next(
        section_data
        for section_data in hearing["sections"]
        if section_data["id"] == source_section.id
    )
    copy_data = {
        **source_section_data,
        "images": [],
        "questions": [],
        "files": [],
    }
    copy_data.pop("id")

    request = APIRequestFactory().post(hearing_url)
    request.user = john_smith
    serializer = SectionCreateUpdateSerializer(
        data=copy_data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    copied_section = serializer.save(hearing=default_hearing)

    copied_image = copied_section.images.get(purpose=SectionImage.PURPOSE_INLINE)
    assert copied_image.pk != source_image.pk
    assert copied_image.section_id == copied_section.pk
    assert copied_image.image.name == source_image.image.name
    assert not copied_image.translations.exists()
    assert source_image.section_id == source_section.pk

    update_data = {
        **copy_data,
        "content": {"en": "<p>The copied image was removed.</p>"},
    }
    update_serializer = SectionCreateUpdateSerializer(
        copied_section,
        data=update_data,
        context={"request": request},
    )
    update_serializer.is_valid(raise_exception=True)
    update_serializer.save()

    copied_image.refresh_from_db()
    source_image.refresh_from_db()
    assert copied_image.deleted
    assert source_image.section_id == source_section.pk
    assert not source_image.deleted
