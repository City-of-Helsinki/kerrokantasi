import datetime
import urllib
from copy import deepcopy
from urllib.parse import urlparse

import pytest
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_str as force_text
from django.utils.timezone import now
from rest_framework import status
from reversion.models import Version

from audit_log.enums import Operation
from democracy.enums import Commenting, InitialSectionType
from democracy.factories.hearing import SectionCommentFactory
from democracy.factories.poll import SectionPollFactory
from democracy.models import Hearing, Label, Section, SectionType
from democracy.models.section import SectionComment, SectionPoll, SectionPollAnswer
from democracy.tests.conftest import default_comment_content, default_lang_code
from democracy.tests.utils import (
    assert_audit_log_entry,
    assert_common_keys_equal,
    get_data_from_response,
    get_hearing_detail_url,
    image_test_json,
)
from kerrokantasi.tests.conftest import default_geojson_feature

root_list_url = "/v1/comment/"


def get_root_detail_url(comment):
    return root_list_url + str(comment.pk) + "/"


def get_nested_detail_url(comment):
    return "/v1/hearing/%s/sections/%s/comments/%s/" % (
        comment.section.hearing.id,
        comment.section.id,
        comment.id,
    )


@pytest.fixture(params=["nested", "root"])
def get_detail_url(request):
    return {
        "nested": get_nested_detail_url,
        "root": get_root_detail_url,
    }[request.param]


def get_comment_data(**extra):
    return dict(
        {
            "content": default_comment_content,
            "geojson": default_geojson_feature,
            "map_comment_text": "",
            "section": None,
        },
        **extra,
    )


def get_main_comments_url(hearing, lookup_field="id"):
    return "/v1/hearing/%s/sections/%s/comments/" % (
        getattr(hearing, lookup_field),
        hearing.get_main_section().id,
    )


def get_section_comment_flag_url(hearing_id, section_id, comment_id):
    return get_hearing_detail_url(
        hearing_id, "sections/%s/comments/%s/flag" % (section_id, comment_id)
    )


@pytest.fixture(params=["nested_by_id", "nested_by_slug", "root"])
def get_comments_url_and_data(request):
    """
    A fixture to test three different comment endpoints:
    - /v1/hearing/<hearing id>/sections/<section id>/comments/
    - /v1/hearing/<hearing slug>/sections/<section id>/comments/
    - /v1/comments/?section=<section id>

    Returns the URL and comment data which contains also section ID in case
    the current endpoint is the root endpoint.
    """
    nested_url = "/v1/hearing/%s/sections/%s/comments/"
    return {
        "nested_by_id": lambda hearing, section: (
            nested_url % (hearing.id, section.id),
            get_comment_data(),
        ),
        "nested_by_slug": lambda hearing, section: (
            nested_url % (hearing.id, section.id),
            get_comment_data(),
        ),
        "root": lambda hearing, section: (
            "/v1/comment/?section=%s" % section.id,
            get_comment_data(section=section.id),
        ),
    }[request.param]


@pytest.fixture(params=["id", "slug"])
def lookup_field(request):
    return request.param


@pytest.mark.django_db
def test_56_add_comment_to_section_without_authentication(
    api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    response = api_client.post(url, data=data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_56_add_comment_to_section_without_authentication_with_nickname(
    api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    data["author_name"] = "Jane Commenter"
    response = api_client.post(url, data=data)
    assert response.status_code == 201
    assert response.data["author_name"] == "Jane Commenter"


@pytest.mark.django_db
def test_56_add_comment_to_section_without_authentication_with_reply_to(
    api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    data["reply_to"] = "Previous commenter"
    response = api_client.post(url, data=data)
    assert response.status_code == 201
    assert response.data["reply_to"] == "Previous commenter"


@pytest.mark.django_db
def test_56_add_comment_to_section_requiring_strong_auth_without_authentication(
    api_client, strong_auth_hearing, get_comments_url_and_data
):
    section = strong_auth_hearing.sections.first()
    url, data = get_comments_url_and_data(strong_auth_hearing, section)
    response = api_client.post(url, data=data)
    # expect request to not go through
    assert response.status_code == 403


@pytest.mark.django_db
def test_56_add_comment_to_section_requiring_strong_auth_with_weak_auth(
    john_doe_api_client, strong_auth_hearing, get_comments_url_and_data
):
    section = strong_auth_hearing.sections.first()
    url, data = get_comments_url_and_data(strong_auth_hearing, section)
    response = john_doe_api_client.post(url, data=data)
    # expect request to not go through
    assert response.status_code == 403


@pytest.mark.django_db
def test_56_add_comment_to_section_requiring_strong_auth_with_strong_auth(
    stark_doe_api_client, strong_auth_hearing, get_comments_url_and_data
):
    section = strong_auth_hearing.sections.first()
    url, data = get_comments_url_and_data(strong_auth_hearing, section)
    response = stark_doe_api_client.post(url, data=data)
    # expect request to go through
    assert response.status_code == 201


@pytest.mark.django_db
def test_56_add_comment_to_section_requiring_strong_auth_with_organization(
    john_smith_api_client, strong_auth_hearing, get_comments_url_and_data
):
    section = strong_auth_hearing.sections.first()
    url, data = get_comments_url_and_data(strong_auth_hearing, section)
    response = john_smith_api_client.post(url, data=data)
    # expect request to go through
    assert response.status_code == 201


@pytest.mark.django_db
def test_56_add_comment_to_section_without_data(
    api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    post_data = {"section": data["section"]} if "section" in data else None
    response = api_client.post(url, data=post_data)
    # expect bad request, we didn't set any data except section if this request was for the root level endpoint
    assert response.status_code == 400


@pytest.mark.django_db
def test_56_pin_comment_to_section_without_authentication(
    api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    data["pinned"] = True
    response = api_client.post(url, data=data)
    # anonymous users may not pin their comment
    assert response.status_code == 400
    assert "pinned" in response.data


@pytest.mark.django_db
def test_56_pin_comment_to_section_with_authentication(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    data["pinned"] = True
    response = john_doe_api_client.post(url, data=data)
    # regular users may not pin their comment
    assert response.status_code == 400
    assert "pinned" in response.data


@pytest.mark.django_db
def test_56_pin_comment_to_section_as_admin(
    john_smith_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    data["pinned"] = True
    # organization members may pin their comment
    response = john_smith_api_client.post(url, data=data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_56_add_comment_to_section(
    john_doe_api_client, default_hearing, get_comments_url_and_data, geojson_feature
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk)
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)
    assert "section" in data
    assert data["section"] == section.pk

    assert "content" in data
    assert data["content"] == default_comment_content

    assert "geojson" in data
    assert data["geojson"] == geojson_feature

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert_common_keys_equal(new_comment, comment_data)
    assert new_comment["is_registered"] is True
    assert new_comment["author_name"] is None


@pytest.mark.django_db
def test_56_add_comment_to_comment(
    john_doe_api_client, default_hearing, get_comments_url_and_data, geojson_feature
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))
    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set answered comment explicitly
    comment_data = get_comment_data(comment=old_comment_list[0]["id"])
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)
    assert "section" in data
    assert data["section"] == section.pk

    assert "content" in data
    assert data["content"] == default_comment_content

    assert "geojson" in data
    assert data["geojson"] == geojson_feature

    assert "comment" in data
    assert data["comment"] == old_comment_list[0]["id"]

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]

    # Comment data now contains section id too
    comment_data["section"] = section.pk
    assert_common_keys_equal(new_comment, comment_data)
    assert new_comment["is_registered"] is True
    assert new_comment["author_name"] is None


@pytest.mark.django_db
def test_add_comment_to_deleted_comment(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))
    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    SectionComment.objects.get(id=old_comment_list[0]["id"]).soft_delete()

    # set answered comment explicitly
    comment_data = get_comment_data(comment=old_comment_list[0]["id"])
    response = john_doe_api_client.post(url, data=comment_data)
    data = get_data_from_response(response, status_code=201)
    assert data["section"] == section.pk
    assert data["content"] == default_comment_content
    assert data["comment"] == old_comment_list[0]["id"]

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(
        john_doe_api_client.get(f"{url}?comment={old_comment_list[0]['id']}")
    )
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "comment_content",
    [
        ("This is a comment", "en"),
        ("Tämä on kommentti", "fi"),
        ("Detta är en kommentar", "sv"),
        ("10.24", ""),
        ("abc", ""),
    ],
)
def test_226_add_comment_to_section_detect_lang(
    john_doe_api_client,
    default_hearing,
    get_comments_url_and_data,
    comment_content,
):
    section = default_hearing.sections.first()
    translation = section._get_translated_model("sv", auto_create=True)
    translation.save()
    translation = section._get_translated_model("fi", auto_create=True)
    translation.save()
    url, data = get_comments_url_and_data(default_hearing, section)

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, content=comment_content[0])
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)
    assert data["language_code"] == comment_content[1]


@pytest.mark.django_db
def test_56_add_comment_to_section_test_geojson(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(
        john_doe_api_client.get(url, {"format": "geojson"})
    )

    # set section explicitly
    comment_data = get_comment_data(section=section.pk)
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=201)

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(
        john_doe_api_client.get(url, {"format": "geojson"})
    )

    assert len(new_comment_list["features"]) == len(old_comment_list["features"]) + 1
    new_comment = [c for c in new_comment_list["features"] if c["id"] == data["id"]][0]
    assert_common_keys_equal(
        new_comment["geometry"], comment_data["geojson"]["geometry"]
    )
    assert_common_keys_equal(
        new_comment["properties"], comment_data["geojson"]["properties"]
    )


@pytest.mark.django_db
def test_add_empty_comment(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, content="", geojson=None)
    response = john_doe_api_client.post(url, data=comment_data)
    # comment may not be empty
    assert response.status_code == 400


@pytest.mark.django_db
def test_56_add_comment_to_section_with_invalid_geojson(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section and invalid geojson explicitly
    comment_data = get_comment_data(
        section=section.pk, geojson={"type": "Feature", "geometry": {"hello": "world"}}
    )
    response = john_doe_api_client.post(url, data=comment_data, format="json")

    data = get_data_from_response(response, status_code=400)
    assert data["geojson"][0].startswith("Invalid geojson format: ")


@pytest.mark.django_db
def test_56_add_comment_to_section_with_no_geometry_in_geojson(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section and invalid geojson explicitly
    comment_data = get_comment_data(section=section.pk, geojson={"hello": "world"})
    response = john_doe_api_client.post(url, data=comment_data, format="json")

    data = get_data_from_response(response, status_code=400)
    assert (
        data["geojson"][0]
        == "Invalid geojson format. \"type\" field is required. Got {'hello': 'world'}"
    )


@pytest.mark.django_db
def test_56_add_comment_with_label_to_section(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    label_one = Label(id=1, label="The Label")
    label_one.save()

    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, label={"id": 1})
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=201)

    assert "label" in data
    assert data["label"] == {"id": 1, "label": {default_lang_code: "The Label"}}
    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    comment_data = get_comment_data(
        section=section.pk, label={"label": {default_lang_code: "The Label"}, "id": 1}
    )

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert_common_keys_equal(new_comment, comment_data)
    assert new_comment["is_registered"] is True
    assert new_comment["label"] == {"id": 1, "label": {default_lang_code: "The Label"}}
    assert new_comment["author_name"] is None


@pytest.mark.django_db
def test_add_empty_comment_with_label(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    label_one = Label(id=1, label="The Label")
    label_one.save()
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(
        section=section.pk, content="", label={"id": 1}, geojson=None
    )
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=201)

    assert "label" in data
    assert data["label"] == {"id": 1, "label": {default_lang_code: "The Label"}}
    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    comment_data = get_comment_data(
        section=section.pk,
        label={"label": {default_lang_code: "The Label"}, "id": 1},
        content="",
        geojson=None,
    )
    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert_common_keys_equal(new_comment, comment_data)
    assert new_comment["is_registered"] is True
    assert new_comment["label"] == {"id": 1, "label": {default_lang_code: "The Label"}}
    assert new_comment["author_name"] is None
    assert new_comment["content"] == ""


@pytest.mark.django_db
def test_56_add_empty_comment_with_geojson(
    john_doe_api_client, default_hearing, get_comments_url_and_data, geojson_feature
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, content="")
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)
    assert "section" in data
    assert data["section"] == section.pk

    assert "geojson" in data
    assert data["geojson"] == geojson_feature

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert_common_keys_equal(new_comment, comment_data)
    assert new_comment["is_registered"] is True
    assert new_comment["author_name"] is None


@pytest.mark.django_db
def test_56_add_comment_with_inexistant_label(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, label={"id": 1})
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=400)
    assert data["label"][0] == 'Invalid pk "1" - object does not exist.'


@pytest.mark.django_db
def test_56_add_comment_with_no_label_id(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    label_one = Label(id=1, label="The Label")
    label_one.save()
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, label={"pk": 1})
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=400)
    assert data["label"][
        0
    ] == 'The primary key is missing. Expected {"id": id, ...}, received %(data)s.' % {
        "data": {"pk": 1}
    }


@pytest.mark.django_db
def test_56_add_comment_with_images_to_section(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, images=[image_test_json()])
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=201)

    assert "images" in data
    assert data["images"][0]["url"].startswith("http://testserver/media/images/")
    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    # Replace the images with the list of URL returned by the creation
    response_data = deepcopy(comment_data)
    response_data["images"][0].pop("image")
    response_data["images"][0].update(
        {
            "url": data["images"][0]["url"],
            "height": 635,
            "width": 952,
        }
    )

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    new_comment["images"][0].pop("id")
    assert_common_keys_equal(new_comment, response_data)
    assert new_comment["is_registered"] is True
    assert new_comment["author_name"] is None


@pytest.mark.django_db
def test_56_add_comment_with_empty_image_field_to_section(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in old_comment_list:
        old_comment_list = old_comment_list["results"]

    # set section explicitly
    # allow null images field
    comment_data = get_comment_data(section=section.pk, images=None)
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    get_data_from_response(response, status_code=201)

    # allow empty images array
    comment_data = get_comment_data(section=section.pk, images=[])
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    get_data_from_response(response, status_code=201)


@pytest.mark.django_db
def test_56_add_comment_with_invalid_content_as_images(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    invalid_image = image_test_json()
    invalid_image.update({"image": "not a b64 image"})
    comment_data = get_comment_data(section=section.pk, images=[invalid_image])
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=400)
    assert data["images"][0]["image"][0] == 'Invalid content. Expected "data:image"'

    invalid_image.update({"image": "data:image/jpeg;base64,not a b64 image"})
    comment_data = get_comment_data(section=section.pk, images=[invalid_image])
    response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=400)
    error = data["images"][0]["image"][0]
    assert (
        error
        == "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
    )


@pytest.mark.django_db
def test_56_add_comment_with_image_too_big(
    john_doe_api_client, default_hearing, get_comments_url_and_data
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    comment_data = get_comment_data(section=section.pk, images=[image_test_json()])
    # 10 bytes max
    with override_settings(MAX_IMAGE_SIZE=10):
        response = john_doe_api_client.post(url, data=comment_data, format="json")
    data = get_data_from_response(response, status_code=400)
    assert (
        data["images"][0]["image"][0] == "Image size should be smaller than 10 bytes."
    )


@pytest.mark.django_db
def test_add_comment_to_section_user_has_name(
    john_doe_api_client, john_doe, default_hearing, get_comments_url_and_data
):
    john_doe.first_name = "John"
    john_doe.last_name = "Doe"
    john_doe.save()

    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    # set section explicitly
    comment_data = get_comment_data(section=section.pk)
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert new_comment["author_name"] == "John Doe"


@pytest.mark.django_db
def test_add_comment_to_section_user_has_nickname(
    john_doe_api_client, john_doe, default_hearing, get_comments_url_and_data
):
    john_doe.first_name = "John"
    john_doe.last_name = "Doe"
    john_doe.nickname = "Johnny"
    john_doe.save()

    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    # set section explicitly
    comment_data = get_comment_data(section=section.pk)
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert new_comment["author_name"] == "Johnny"


@pytest.mark.django_db
def test_add_comment_to_section_user_update_nickname(
    john_doe_api_client, john_doe, default_hearing, get_comments_url_and_data
):
    john_doe.first_name = "John"
    john_doe.last_name = "Doe"
    john_doe.nickname = "Johnny"
    john_doe.save()

    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    # set section explicitly
    comment_data = get_comment_data(section=section.pk, author_name="Jo")
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if "results" in new_comment_list:
        new_comment_list = new_comment_list["results"]

    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    john_doe.refresh_from_db()
    assert john_doe.nickname == "Jo"
    assert new_comment["author_name"] == "Jo"


@pytest.mark.django_db
def test_56_get_hearing_with_section_check_n_comments_property(
    api_client, get_comments_url_and_data
):
    hearing = Hearing.objects.create(
        title="Test Hearing",
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
    )
    section = Section.objects.create(
        title="Section to comment",
        hearing=hearing,
        commenting=Commenting.OPEN,
        type=SectionType.objects.get(identifier=InitialSectionType.PART),
    )
    url, data = get_comments_url_and_data(hearing, section)

    response = api_client.post(url, data=data)
    assert response.status_code == 201, "response was %s" % response.content

    # get hearing and check sections's n_comments property
    url = get_hearing_detail_url(hearing.id)
    response = api_client.get(url)

    data = get_data_from_response(response)
    assert "n_comments" in data["sections"][0]
    assert data["sections"][0]["n_comments"] == 1


def get_section_comments(hearing, section, api_client):
    url = get_hearing_detail_url(hearing.id, "sections/%s/comments" % section.id)
    response = api_client.get(url)
    return get_data_from_response(response)


@pytest.mark.django_db
def test_get_section_comment_creator_email_as_regular_user_not_public(
    john_doe_api_client, default_hearing, settings
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = False
    section = default_hearing.sections.first()

    data = get_section_comments(default_hearing, section, john_doe_api_client)
    # check no section comment has creator_email when not authorized and the setting is disabled
    for comment in data:
        assert "creator_email" not in comment


@pytest.mark.django_db
def test_get_section_comment_creator_email_as_regular_user_public(
    john_doe_api_client, default_hearing, settings
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = True
    section = default_hearing.sections.first()

    data = get_section_comments(default_hearing, section, john_doe_api_client)
    # check section comment has creator_email when not authorized and the setting is enabled
    for comment in data:
        assert "creator_email" not in comment


@pytest.mark.django_db
def test_get_section_comment_creator_email_as_admin_not_public(
    admin_api_client, default_hearing, settings
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = False
    section = default_hearing.sections.first()

    data = get_section_comments(default_hearing, section, admin_api_client)
    # check all section comments have creator_email when authorized
    for comment in data:
        assert "creator_email" not in comment


@pytest.mark.django_db
def test_get_section_comment_creator_email_as_admin_public(
    admin_api_client, default_hearing, settings
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = True
    section = default_hearing.sections.first()

    data = get_section_comments(default_hearing, section, admin_api_client)

    # check all section comments have creator_email when authorized
    for comment in data:
        assert "creator_email" in comment
        assert comment["creator_email"] != ""


@pytest.mark.django_db
def test_get_section_comment_creator_email_as_admin_public_when_deleted(
    admin_api_client, default_hearing, settings
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = True
    section = default_hearing.sections.first()
    section.comments.update(deleted=True)

    data = get_section_comments(default_hearing, section, admin_api_client)

    # Creator email should not be visible when comment is deleted.
    for comment in data:
        assert "creator_email" in comment
        assert comment["creator_email"] == ""


@pytest.mark.django_db
def test_get_section_comment_author_name_when_posted_by_anon(
    admin_api_client, hearing_without_comments
):
    section = hearing_without_comments.sections.first()
    section.comments.create(created_by=None, content="Anon content")

    data = get_section_comments(hearing_without_comments, section, admin_api_client)
    first_comment = data[0]

    assert "author_name" in first_comment
    assert first_comment.get("author_name") == "Anonymous"


@pytest.mark.django_db
def test_get_section_comment_author_name_when_posted_by_registered_user(
    admin_api_client,
    hearing_without_comments,
    john_doe,
    settings,
):
    settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES = False

    john_doe.first_name = "John"
    john_doe.last_name = "Doe"
    john_doe.save()

    section = hearing_without_comments.sections.first()
    section.comments.create(created_by=john_doe, content="john doe's content")
    url = get_hearing_detail_url(
        hearing_without_comments.id, "sections/%s/comments" % section.id
    )
    response = admin_api_client.get(url)
    data = get_data_from_response(response, 200)
    first_comment = data[0]

    assert "author_name" in first_comment
    assert first_comment.get("author_name") == john_doe.get_full_name()


@pytest.mark.django_db
def test_n_comments_updates(admin_user, default_hearing):
    section = default_hearing.get_main_section()
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 9
    assert section.n_comments == 3
    comment = section.comments.create(created_by=admin_user, content="Hello")
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 10
    assert section.n_comments == 4
    assert comment.n_comments == 0
    subcomment = comment.comments.create(
        created_by=admin_user, content="Hello you!", section=section
    )
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 11
    assert section.n_comments == 5
    assert comment.n_comments == 1
    subcomment.soft_delete()
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 10
    assert section.n_comments == 4
    assert comment.n_comments == 0
    comment.soft_delete()
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 9
    assert section.n_comments == 3


@pytest.mark.django_db
def test_comment_create_versioning(john_doe_api_client, default_hearing, lookup_field):
    expected_content = "A comment"
    url = get_main_comments_url(default_hearing, lookup_field)

    response = john_doe_api_client.post(url, data={"content": expected_content})
    data = get_data_from_response(response, 201)

    comment = SectionComment.objects.get(pk=data["id"])
    assert comment.content == expected_content
    versions = Version.objects.get_for_object(comment)
    assert len(versions) == 1  # Initial revision
    assert versions[0].field_dict["content"] == expected_content


@pytest.mark.django_db
def test_comment_edit_versioning(john_doe_api_client, default_hearing, lookup_field):
    expected_content = "Never mind, it's nice :)"
    url = get_main_comments_url(default_hearing, lookup_field)
    response = john_doe_api_client.post(url, data={"content": "THIS SERVICE SUCKS"})
    data = get_data_from_response(response, 201)
    comment_id = data["id"]
    comment = SectionComment.objects.get(pk=comment_id)
    assert comment.content.isupper()  # Oh my, all that screaming :(
    assert Version.objects.get_for_object(comment).count() == 1  # Initial revision

    response = john_doe_api_client.patch(
        "%s%s/" % (url, comment_id), data={"content": expected_content}
    )

    assert response.status_code == status.HTTP_200_OK
    comment = SectionComment.objects.get(pk=comment_id)
    assert not comment.content.isupper()  # Screaming is gone
    versions = Version.objects.get_for_object(comment)
    assert len(versions) == 2  # Two revisions for two edits
    assert versions[0].field_dict["content"] == expected_content


@pytest.mark.django_db
def test_comment_delete_versioning(john_doe_api_client, default_hearing, lookup_field):
    url = get_main_comments_url(default_hearing, lookup_field)
    response = john_doe_api_client.post(url, data={"content": "A comment"})
    data = get_data_from_response(response, 201)
    comment_id = data["id"]
    comment = SectionComment.objects.get(pk=comment_id)
    assert Version.objects.get_for_object(comment).count() == 1

    response = john_doe_api_client.delete("%s%s/" % (url, comment_id))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    comment = SectionComment.objects.deleted().get(pk=comment_id)
    versions = Version.objects.get_for_object(comment)
    assert len(versions) == 2
    assert versions[0].field_dict["deleted"] is True


@pytest.mark.django_db
def test_correct_m2m_fks(admin_user, default_hearing):
    first_section = default_hearing.sections.first()
    section_comment = first_section.comments.create(
        created_by=admin_user, content="hello"
    )
    sc_voters_query = force_text(section_comment.voters.all().query)
    assert (
        "sectioncomment" in sc_voters_query and "hearingcomment" not in sc_voters_query
    )


comment_status_spec = {
    Commenting.NONE: (403, 403),
    Commenting.REGISTERED: (403, 201),
    Commenting.OPEN: (201, 201),
}


@pytest.mark.django_db
@pytest.mark.parametrize("commenting", comment_status_spec.keys())
def test_commenting_modes(api_client, john_doe_api_client, default_hearing, commenting):
    main_section = default_hearing.get_main_section()
    main_section.commenting = commenting
    main_section.save(update_fields=("commenting",))

    anon_status, reg_status = comment_status_spec[commenting]
    url = get_main_comments_url(default_hearing)
    response = api_client.post(url, data=get_comment_data())
    assert response.status_code == anon_status
    response = john_doe_api_client.post(url, data=get_comment_data())
    assert response.status_code == reg_status


@pytest.mark.django_db
def test_comment_edit_auth(
    john_doe_api_client, jane_doe_api_client, api_client, default_hearing, lookup_field
):
    url = get_main_comments_url(default_hearing, lookup_field)

    # John posts an innocuous comment:
    johns_message = "Hi! I'm John!"
    response = john_doe_api_client.post(url, data={"content": johns_message})
    data = get_data_from_response(response, 201)
    comment_id = data["id"]

    # Now Jane (in the guise of Mallory) attempts a rogue edit:
    response = jane_doe_api_client.patch(
        "%s%s/" % (url, comment_id), data={"content": "hOI! I'M TEMMIE"}
    )

    # But her attempts are foiled!
    data = get_data_from_response(response, 403)
    assert SectionComment.objects.get(pk=comment_id).content == johns_message

    # Jane, thinking she can bamboozle our authentication by logging out, tries again!
    response = api_client.patch(
        "%s%s/" % (url, comment_id), data={"content": "I'm totally John"}
    )

    # But still, no!
    data = get_data_from_response(response, 403)
    assert SectionComment.objects.get(pk=comment_id).content == johns_message


@pytest.mark.django_db
def test_comment_editing_disallowed_after_closure(john_doe_api_client, default_hearing):
    # Post a comment:
    url = "/v1/hearing/%s/sections/%s/comments/" % (
        default_hearing.id,
        default_hearing.get_main_section().id,
    )
    response = john_doe_api_client.post(url, data=get_comment_data())
    data = get_data_from_response(response, status_code=201)
    comment_id = data["id"]
    # Successfully edit the comment:
    response = john_doe_api_client.patch(
        "%s%s/" % (url, comment_id), data={"content": "Hello"}
    )
    data = get_data_from_response(response, status_code=200)
    assert data["content"] == "Hello"
    assert data["can_edit"]
    # Close the hearing:
    default_hearing.close_at = default_hearing.open_at
    default_hearing.save()
    # Futilely attempt to edit the comment:
    response = john_doe_api_client.patch(
        "%s%s/" % (url, comment_id), data={"content": "No"}
    )
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("case", ("plug-valid", "plug-invalid", "noplug"))
def test_add_plugin_data_to_comment(api_client, default_hearing, case):
    with override_settings(
        DEMOCRACY_PLUGINS={"test_plugin": "democracy.tests.plug.TestPlugin"}
    ):
        section = default_hearing.sections.first()
        if case.startswith("plug"):
            section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(
            default_hearing.id, "sections/%s/comments" % section.id
        )
        comment_data = get_comment_data(
            content="", plugin_data=("foo6" if case == "plug-valid" else "invalid555")
        )
        response = api_client.post(url, data=comment_data)
        if case == "plug-valid":
            assert response.status_code == 201
            created_comment = SectionComment.objects.first()
            assert created_comment.plugin_identifier == section.plugin_identifier
            assert (
                created_comment.plugin_data == comment_data["plugin_data"][::-1]
            )  # The TestPlugin reverses data
        elif case == "plug-invalid":
            data = get_data_from_response(response, status_code=400)
            assert data == {"plugin_data": ["The data must contain a 6."]}
        elif case == "noplug":
            data = get_data_from_response(response, status_code=400)
            assert "no plugin data is allowed" in data["plugin_data"][0]
        else:
            raise NotImplementedError("...")


@pytest.mark.django_db
def test_do_not_get_plugin_data_for_comment(api_client, default_hearing):
    with override_settings(
        DEMOCRACY_PLUGINS={"test_plugin": "democracy.tests.plug.TestPlugin"}
    ):
        section = default_hearing.sections.first()
        section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(
            default_hearing.id, "sections/%s/comments" % section.id
        )
        comment_data = get_comment_data(content="", plugin_data="foo6")
        response = api_client.post(url, data=comment_data)
        response_data = get_data_from_response(response, status_code=201)
        comment_list = get_data_from_response(api_client.get(url))
        created_comment = [c for c in comment_list if c["id"] == response_data["id"]][0]
        assert "plugin_data" not in created_comment


@pytest.mark.django_db
def test_get_plugin_data_for_comment(api_client, default_hearing):
    with override_settings(
        DEMOCRACY_PLUGINS={"test_plugin": "democracy.tests.plug.TestPlugin"}
    ):
        section = default_hearing.sections.first()
        section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(
            default_hearing.id, "sections/%s/comments" % section.id
        )
        comment_data = get_comment_data(content="", plugin_data="foo6")
        response = api_client.post(url, data=comment_data)
        response_data = get_data_from_response(response, status_code=201)
        comment_list = get_data_from_response(
            api_client.get(url, {"include": "plugin_data"})
        )
        created_comment = [c for c in comment_list if c["id"] == response_data["id"]][0]
        assert (
            created_comment["plugin_data"] == comment_data["plugin_data"][::-1]
        )  # The TestPlugin reverses data


@pytest.mark.parametrize(
    "data",
    [
        {"section": "nonexistingsection", "content": "blah"},
        {"section": None, "content": "blah"},
        {"content": "blah"},
    ],
)
@pytest.mark.django_db
def test_post_to_root_endpoint_invalid_section(
    john_doe_api_client, default_hearing, data
):
    url = "/v1/comment/"

    response = john_doe_api_client.post(url, data=data)
    assert response.status_code == 400
    assert "section" in response.data


@pytest.mark.parametrize(
    "data",
    [
        {"section": "nonexistingsection", "content": "blah"},
        {"section": None, "content": "blah"},
        {"content": "blah"},
    ],
)
@pytest.mark.django_db
def test_put_to_root_endpoint_invalid_section(
    john_doe_api_client, default_hearing, data
):
    url = "/v1/comment/"
    comment = default_hearing.sections.first().comments.first()
    url = "%s%s/" % (url, comment.id)

    response = john_doe_api_client.put(url, data)

    # with missing or invalid section data, PUT should succeed as the comment already knows its section!
    assert response.status_code == 200
    assert "section" in response.data


@pytest.mark.django_db
def test_root_endpoint_filters(api_client, default_hearing, random_hearing):
    url = "/v1/comment/"
    section = default_hearing.sections.first()
    for i, comment in enumerate(section.comments.all()):
        comment.authorization_code = "auth_code_%s" % i
        label = Label.objects.create(label="Label_%s")
        comment.label = label
        comment.save(update_fields=("authorization_code", "label"))

    response = api_client.get(
        "%s?authorization_code=%s" % (url, section.comments.first().authorization_code)
    )
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == 1

    response = api_client.get("%s?section=%s" % (url, section.id))
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == 3

    response = api_client.get("%s?hearing=%s" % (url, default_hearing.id))
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == 9

    response = api_client.get("%s?label=%s" % (url, section.comments.first().label.pk))
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == 1


@pytest.mark.django_db
def test_root_endpoint_timestamp_filters(api_client, default_hearing):
    url = "/v1/comment/"
    timestamp_now = now()
    timestamp_comment = timestamp_now + datetime.timedelta(days=2)
    timestamp_check = timestamp_now + datetime.timedelta(days=1)
    comment_count = SectionComment.objects.count()
    future_comment = SectionComment.objects.first()
    future_comment.created_at = timestamp_comment
    future_comment.save(update_fields=("created_at",))

    response = api_client.get(
        "%s?created_at__gt=%s" % (url, urllib.parse.quote(timestamp_check.isoformat()))
    )
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == 1

    response = api_client.get(
        "%s?created_at__lt=%s" % (url, urllib.parse.quote(timestamp_check.isoformat()))
    )
    response_data = get_data_from_response(response)
    assert len(response_data["results"]) == comment_count - 1


@pytest.mark.parametrize(
    "hearing_update",
    [
        ("deleted", True),
        ("published", False),
        ("open_at", now() + datetime.timedelta(days=1)),
    ],
)
@pytest.mark.django_db
def test_root_endpoint_filtering_by_hearing_visibility(
    api_client, default_hearing, hearing_update
):
    setattr(default_hearing, hearing_update[0], hearing_update[1])
    default_hearing.save()

    response = api_client.get("/v1/comment/")
    response_data = get_data_from_response(response)["results"]
    assert len(response_data) == 0


@pytest.mark.django_db
def test_comment_put(john_doe_api_client, default_hearing, get_detail_url):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    comment_data = get_comment_data(content="updated content", section=section.id)
    url = get_detail_url(comment)

    response = john_doe_api_client.put(url, data=comment_data)
    assert response.status_code == 200

    comment.refresh_from_db()
    assert comment.content == "updated content"


@pytest.mark.django_db
def test_comment_patch(john_doe_api_client, default_hearing, get_detail_url):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    url = get_detail_url(comment)

    response = john_doe_api_client.patch(url, data={"content": "updated content"})
    assert response.status_code == 200

    comment.refresh_from_db()
    assert comment.content == "updated content"


@pytest.mark.django_db
def test_cannot_change_comment_section(
    john_doe_api_client, default_hearing, get_detail_url
):
    section = default_hearing.sections.all()[0]
    second_section = default_hearing.sections.all()[1]
    comment = section.comments.all()[0]
    comment_data = get_comment_data(section=second_section.id)
    url = get_detail_url(comment)

    response = john_doe_api_client.put(url, data=comment_data)
    assert response.status_code == 200

    # check that the section did not change
    assert response.data["section"] == section.id
    comment.refresh_from_db()
    assert comment.section == section


@pytest.mark.django_db
def test_cannot_change_comment_comment(
    john_doe_api_client, default_hearing, get_detail_url
):
    section = default_hearing.sections.all()[0]
    comment = section.comments.all()[0]
    other_comment = section.comments.all()[1]
    comment_data = get_comment_data(comment=other_comment.id)
    url = get_detail_url(comment)

    response = john_doe_api_client.put(url, data=comment_data)
    assert response.status_code == 400
    assert "comment" in response.data


@pytest.mark.parametrize("anonymous_comment", [True, False])
@pytest.mark.django_db
def test_cannot_modify_others_comments(
    api_client, jane_doe_api_client, default_hearing, get_detail_url, anonymous_comment
):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]

    if anonymous_comment:
        comment.created_by = None
        comment.save(update_fields=("created_by",))

    old_content = comment.content
    comment_data = get_comment_data(content="updated content", section=section.id)
    url = get_detail_url(comment)

    # anonymous user
    response = api_client.put(url, data=comment_data)
    assert response.status_code == 403
    comment.refresh_from_db()
    assert comment.content == old_content

    # wrong user
    response = jane_doe_api_client.put(url, data=comment_data)
    assert response.status_code == 403
    comment.refresh_from_db()
    assert comment.content == old_content


@pytest.mark.django_db
def test_comment_delete(
    john_doe_api_client, default_hearing, comment_image, get_detail_url
):
    # Arrange
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    comment.geojson = default_geojson_feature
    comment.save()
    poll = SectionPollFactory(
        section=section, option_count=3, type=SectionPoll.TYPE_SINGLE_CHOICE
    )
    option = poll.options.all().first()
    answer = SectionPollAnswer.objects.create(option=option, comment=comment)
    url = get_detail_url(comment)

    # Sanity checks
    assert comment_image.deleted is False
    assert answer.deleted is False
    assert comment.images.all().count() == 1
    assert comment.poll_answers.all().count() == 1

    # Delete comment
    response = john_doe_api_client.delete(url)
    assert response.status_code == 204

    # Refresh objects from db
    comment = SectionComment.objects.everything().get(id=comment.id)
    comment_image.refresh_from_db()
    answer.refresh_from_db()

    # Assert at database level
    assert comment.images.all().count() == 0
    assert comment.poll_answers.all().count() == 0
    assert comment_image.deleted is True
    assert comment.deleted is True
    assert answer.deleted is True
    assert comment.geojson == default_geojson_feature

    # Get the comment from the API
    response = john_doe_api_client.get(url)
    assert response.status_code == 200
    comment_data = response.json()

    # Assert at API level
    assert comment_data["deleted"] is True
    assert comment_data["images"] == []
    assert comment_data["geojson"] is None


@pytest.mark.parametrize("anonymous_comment", [True, False])
@pytest.mark.django_db
def test_cannot_delete_others_comments(
    api_client, jane_doe_api_client, default_hearing, get_detail_url, anonymous_comment
):
    comment = default_hearing.get_main_section().comments.all()[0]

    if anonymous_comment:
        comment.created_by = None
        comment.save(update_fields=("created_by",))

    url = get_detail_url(comment)

    # anonymous user
    response = api_client.delete(url)
    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.deleted is False

    # wrong user
    response = jane_doe_api_client.delete(url)
    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.deleted is False


@pytest.mark.parametrize("anonymous_comment", [True, False])
@pytest.mark.django_db
def test_hearing_creator_cannot_delete_others_comments(
    api_client,
    steve_staff_api_client,
    default_hearing,
    get_detail_url,
    anonymous_comment,
):
    default_hearing.created_by_id = steve_staff_api_client.user.id
    default_hearing.save()
    comment = default_hearing.get_main_section().comments.all()[0]

    if anonymous_comment:
        comment.created_by = None
        comment.save(update_fields=("created_by",))

    url = get_detail_url(comment)

    # anonymous user
    response = api_client.delete(url)
    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.deleted is False

    # staff/hearing creator user
    response = steve_staff_api_client.delete(url)
    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.deleted is False


@pytest.mark.parametrize(
    "ordering, expected_order",
    [
        ("created_at", [0, 1, 2]),
        ("-created_at", [2, 1, 0]),
        ("n_votes", [0, 1, 2]),
        ("-n_votes", [2, 1, 0]),
    ],
)
@pytest.mark.django_db
def test_comment_ordering(api_client, ordering, expected_order, default_hearing):
    SectionComment.objects.all().delete()
    section = default_hearing.get_main_section()

    for i in range(3):
        comment = SectionCommentFactory(section=section)
        SectionComment.objects.filter(id=comment.id).update(
            n_votes=i, created_at=datetime.datetime.now()
        )

    response = api_client.get(root_list_url + "?ordering=" + ordering)
    results = get_data_from_response(response)["results"]

    n_votes_list = [comment["n_votes"] for comment in results]
    assert n_votes_list == expected_order


@pytest.mark.django_db
def test_get_comments_created_by_user(
    john_doe_api_client, jane_doe_api_client, get_comments_url_and_data
):
    hearings = []
    sections = []
    # Create 3 hearings with a section that can be commented.
    for i in range(3):
        hearings.append(
            Hearing.objects.create(
                title="Test hearing title %s" % (i + 1),
                open_at=now() - datetime.timedelta(days=1),
                close_at=now() + datetime.timedelta(days=1),
            )
        )
        sections.append(
            Section.objects.create(
                title="Hearing %s Section to comment" % (i + 1),
                hearing=hearings[i],
                commenting=Commenting.OPEN,
                type=SectionType.objects.get(identifier=InitialSectionType.PART),
            )
        )

    # John comments on each hearing.
    expected_john_comment_content = []
    for i in range(len(hearings)):
        url, data = get_comments_url_and_data(hearings[i], sections[i])
        comment_data = get_comment_data(
            section=sections[i].pk,
            author_name="John",
            content="Comment for Hearing %s" % (i + 1),
        )
        expected_john_comment_content.insert(0, "Comment for Hearing %s" % (i + 1))
        john_doe_api_client.post(url, data=comment_data)

    # Jane comments on the first hearing.
    comment_data = get_comment_data(
        section=sections[0].pk, author_name="Jane", content="Jane created this comment"
    )
    jane_doe_api_client.post(url, data=comment_data)

    # John fetches all comments he has made.
    response = john_doe_api_client.get(root_list_url, data={"created_by": "me"})
    assert response.status_code == 200
    data = get_data_from_response(response)

    assert len(data["results"]) == len(hearings)

    # Hearing slug values are added to a list as they are used to test that the comments belong to correct hearings.
    expected_slug_values = []
    for i in range(len(hearings)):
        expected_slug_values.insert(0, hearings[i].slug)

    # Each comment has the expected content and hearing slug.
    for i in range(len(data["results"])):
        assert data["results"][i]["content"] == expected_john_comment_content[i]
        assert data["results"][i]["hearing_data"]["slug"] == expected_slug_values[i]

    # Jane fetches all comments she has made.
    response = jane_doe_api_client.get(root_list_url, data={"created_by": "me"})
    assert response.status_code == 200
    data = get_data_from_response(response)

    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "Jane created this comment"


@pytest.mark.parametrize(
    "query_params,expected", [({"created_by": "me"}, 0), (None, 9)]
)
@pytest.mark.django_db
def test_get_comments_created_by_user__unauthenticated(
    query_params, expected, api_client, default_hearing
):
    """Unauthenticated users get no results with created_by filter."""
    url = reverse("comment-list")
    response = api_client.get(url, query_params)

    assert len(response.data["results"]) == expected


@pytest.mark.django_db
def test_deleted_comments_data_returned(john_doe_api_client, default_hearing):
    """Deleted comment is returned, with contents censored"""

    section = default_hearing.sections.first()
    section.comments.first().soft_delete()

    url = get_hearing_detail_url(
        default_hearing.id, "sections/%s/comments" % section.id
    )
    data = get_data_from_response(john_doe_api_client.get(url), 200)

    comment_data = data[0]
    assert comment_data["deleted"]
    assert comment_data["deleted_at"] is not None
    assert (
        SectionComment.objects.everything().get(pk=comment_data["id"]).content
        != comment_data["content"]
        and "koska se ei noudattanut Kerrokantasi-palvelun sääntöjä"
        in comment_data["content"]
    )
    assert comment_data["author_name"] is None
    assert comment_data["organization"] is None


@pytest.mark.django_db
def test_deleted_comments_data_returned_author_self_deleted(
    john_doe_api_client, default_hearing
):
    """Comments deleted by their creator show a different message"""

    section = default_hearing.sections.first()
    section.comments.first().soft_delete(user=john_doe_api_client.user)

    url = get_hearing_detail_url(
        default_hearing.id, "sections/%s/comments" % section.id
    )
    data = get_data_from_response(john_doe_api_client.get(url), 200)

    comment_data = data[0]
    assert comment_data["deleted"]
    assert comment_data["deleted_at"] is not None
    assert (
        SectionComment.objects.everything().get(pk=comment_data["id"]).content
        != comment_data["content"]
        and "koska se ei noudattanut Kerrokantasi-palvelun sääntöjä"
        not in comment_data["content"]
    )
    assert comment_data["author_name"] is None
    assert comment_data["organization"] is None


@pytest.mark.django_db
def test_section_comment_flag_without_proper_authentication(
    john_doe_api_client, default_hearing
):
    section = default_hearing.sections.first()
    comment = section.comments.first()
    url = get_section_comment_flag_url(default_hearing.id, section.id, comment.id)
    response = john_doe_api_client.post(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_section_comment_flag_with_proper_authentication(
    john_smith_api_client, default_hearing
):
    """User with the same organization as the hearing can flag a comment"""
    section = default_hearing.sections.first()
    comment = section.comments.first()
    url = get_section_comment_flag_url(default_hearing.id, section.id, comment.id)
    response = john_smith_api_client.post(url)
    assert response.status_code == 200

    # Already flagged, nothing is done
    response = john_smith_api_client.post(url)
    assert response.status_code == 304


@pytest.mark.parametrize(
    "user_api_client,comment_creator,hearing_creator,expected_items",
    [
        # Client's own comment in the client's hearing
        (
            "john_doe_api_client",
            "john_doe",
            "john_doe",
            {"can_edit": True, "can_delete": True},
        ),
        # Client's own comment in someone else's hearing
        (
            "john_doe_api_client",
            "john_doe",
            "jane_doe",
            {"can_edit": True, "can_delete": True},
        ),
        # Someone else's comment in client's hearing
        (
            "john_doe_api_client",
            "jane_doe",
            "john_doe",
            {"can_edit": False, "can_delete": False},
        ),
        # Anonymous comment in client's hearing
        (
            "john_doe_api_client",
            None,
            "john_doe",
            {"can_edit": False, "can_delete": False},
        ),
        # Someone else's comment in someone else's hearing as staff user
        (
            "steve_staff_api_client",
            "john_doe",
            "john_doe",
            {"can_edit": False, "can_delete": False},
        ),
        # Someone else's comment in the client's hearing as staff user
        (
            "steve_staff_api_client",
            "john_doe",
            "steve_staff",
            {"can_edit": False, "can_delete": False},
        ),
        # Anonymous comment in the client's hearing as staff user
        (
            "steve_staff_api_client",
            None,
            "steve_staff",
            {"can_edit": False, "can_delete": False},
        ),
    ],
)
@pytest.mark.django_db
def test_get_section_comment_edit_delete_rights(
    user_api_client,
    comment_creator,
    hearing_creator,
    expected_items,
    default_hearing,
    request,
):
    """Test that the can_edit and can_delete properties are correct for different users and comments"""
    # Get fixtures
    user_api_client = request.getfixturevalue(user_api_client)
    comment_creator = comment_creator and request.getfixturevalue(comment_creator)
    hearing_creator = request.getfixturevalue(hearing_creator)

    # Change hearing creator
    default_hearing.created_by = hearing_creator
    default_hearing.save()

    # Create comment
    section = default_hearing.sections.first()
    section.comments.create(created_by=comment_creator, content="test")

    # Get comment data
    url = get_hearing_detail_url(
        default_hearing.id, "sections/%s/comments" % section.id
    )
    response = user_api_client.get(url)
    data = get_data_from_response(response, 200)

    # Check that the properties are correct
    for key, value in expected_items.items():
        assert (
            data[0][key] == value
        ), f"Expected '{key}' to be {value} (was: {data[0][key]})"


@pytest.mark.django_db
def test_delete_comment_comment(john_doe_api_client, hearing_with_comments_on_comments):
    section = hearing_with_comments_on_comments.sections.first()
    comment = section.comments.filter(comment=None).first()
    comment_to_delete = comment.comments.first()

    url = "/v1/comment/?section=%s&comment=%s" % (section.pk, "null")
    response = john_doe_api_client.get(url)
    data = get_data_from_response(response, 200)

    assert len(data["results"][0]["comments"]) == 2

    comment_to_delete.soft_delete()

    response = john_doe_api_client.get(url)
    data = get_data_from_response(response, 200)
    assert len(data["results"][0]["comments"]) == 2


@pytest.mark.parametrize(
    "user_type,query_filter,expect_author_name",
    [
        ("admin", None, True),
        ("regular", None, False),
        ("anonymous", "section", True),
        ("anonymous", "hearing", True),
        ("anonymous", "comment", True),
        ("anonymous", None, False),
    ],
)
@pytest.mark.django_db
def test_comment_author_name_hidden_from_unfiltered_requests(
    user_type,
    query_filter,
    expect_author_name,
    hearing_without_comments,
    api_client,
    john_doe_api_client,
    steve_staff_api_client,
):
    url = reverse("comment-list")
    if user_type == "admin":
        client = steve_staff_api_client
    elif user_type == "regular":
        client = john_doe_api_client
    else:
        client = api_client
    section = hearing_without_comments.sections.first()
    comment = SectionCommentFactory(section=section, author_name="Name")
    SectionCommentFactory(section=section, comment=comment, author_name="Name")
    possible_params = {
        "hearing": section.hearing_id,
        "section": section.id,
        "comment": comment.id,
    }
    query_params = (
        {query_filter: possible_params[query_filter]} if query_filter else None
    )

    response = client.get(url, query_params)

    expected_value = "Name" if expect_author_name else None
    assert response.data["results"][0]["author_name"] == expected_value


@pytest.mark.django_db
def test_comment_author_name_hidden_from_unfiltered_requests__created_by(
    hearing_without_comments, api_client, john_doe_api_client
):
    """Regular authenticated user can see author_name with created_by filter."""
    url = reverse("comment-list")
    client = john_doe_api_client
    user = john_doe_api_client.user
    section = hearing_without_comments.sections.first()
    comment = SectionCommentFactory(
        section=section, created_by=user, author_name="Name"
    )
    SectionCommentFactory(section=section, comment=comment, author_name="Name")

    response = client.get(url, {"created_by": "me"})

    assert response.data["results"][0]["author_name"] == "Name"


@pytest.mark.django_db
def test_section_comment_num_queries(
    django_assert_num_queries, john_doe_api_client, hearing_with_comments_on_comments
):
    url = reverse("comment-list")

    with django_assert_num_queries(10):
        response = john_doe_api_client.get(url)
        get_data_from_response(response, 200)


@pytest.mark.django_db
def test_hearing_sections_comment_num_queries(
    django_assert_num_queries, john_doe_api_client, hearing_with_comments_on_comments
):
    url = reverse(
        "comments-list",
        kwargs={
            "hearing_pk": hearing_with_comments_on_comments.pk,
            "comment_parent_pk": hearing_with_comments_on_comments.sections.first().pk,
        },
    )

    with django_assert_num_queries(7):
        response = john_doe_api_client.get(url)
        get_data_from_response(response, 200)


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_flag(
    john_smith_api_client, default_hearing, audit_log_configure
):
    section = default_hearing.sections.first()
    comment = section.comments.first()
    url = get_section_comment_flag_url(default_hearing.id, section.id, comment.id)

    john_smith_api_client.post(url)

    assert_audit_log_entry("/flag", [comment.pk])


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_create(
    john_doe_api_client, default_hearing, get_comments_url_and_data, audit_log_configure
):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)

    response = john_doe_api_client.post(url, data=data)
    data = get_data_from_response(response, 201)

    assert_audit_log_entry(urlparse(url).path, [data["id"]])


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_edit(
    john_doe_api_client, default_hearing, get_detail_url, audit_log_configure
):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    url = get_detail_url(comment)

    john_doe_api_client.patch(url, data={"content": "B"})

    assert_audit_log_entry(url, [comment.pk], operation=Operation.UPDATE)


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_delete(
    john_doe_api_client, default_hearing, get_detail_url, audit_log_configure
):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    url = get_detail_url(comment)

    john_doe_api_client.delete(url)

    assert_audit_log_entry(url, [comment.pk], operation=Operation.DELETE)


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_retrieve(
    john_doe_api_client, default_hearing, get_detail_url, audit_log_configure
):
    section = default_hearing.get_main_section()
    comment = section.comments.all()[0]
    url = get_detail_url(comment)

    john_doe_api_client.get(url)

    assert_audit_log_entry(url, [comment.pk], operation=Operation.READ)


@pytest.mark.django_db
def test_comment_ids_are_audit_logged_on_list(
    john_doe_api_client, default_hearing, get_comments_url_and_data, audit_log_configure
):
    section = default_hearing.get_main_section()
    url, data = get_comments_url_and_data(default_hearing, section)
    comments = section.comments.all()
    assert comments.count() > 1

    john_doe_api_client.get(url)

    assert_audit_log_entry(
        urlparse(url).path,
        comments.values_list("pk", flat=True),
        operation=Operation.READ,
    )
