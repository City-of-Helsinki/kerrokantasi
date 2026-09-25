import pytest
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from democracy.factories.hearing import SectionImageFactory
from democracy.models import SectionImage
from democracy.tests.utils import (
    IMAGES,
    get_data_from_response,
    get_hearing_detail_url,
    get_image_path,
)
from democracy.views.section import SectionCreateUpdateSerializer


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

    response = john_smith_api_client.put(
        hearing_url, data=hearing, format="json"
    )

    assert response.status_code == 200
    first_image.refresh_from_db()
    second_image.refresh_from_db()
    assert first_image.section_id is None
    assert second_image.section_id == section.pk
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
