import pytest
import requests_mock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from typing import List

from democracy.factories.hearing import (
    CommentImageFactory,
    HearingFactory,
    SectionCommentFactory,
    SectionFileFactory,
    SectionImageFactory,
)
from democracy.factories.organization import OrganizationFactory
from democracy.factories.poll import SectionPollFactory
from democracy.factories.user import UserFactory
from democracy.models import Hearing, Organization, SectionComment, SectionPollAnswer
from democracy.models.section import CommentImage, Section, SectionFile, SectionImage, SectionPoll, SectionPollOption
from democracy.utils.file_to_base64 import file_to_base64
from kerrokantasi.tests.gdpr.conftest import get_api_token_for_user_with_scopes

User = get_user_model()


def do_query(user, id_value, scopes=(settings.GDPR_API_QUERY_SCOPE,)):
    api_client = APIClient()

    with requests_mock.Mocker() as req_mock:
        auth_header = get_api_token_for_user_with_scopes(user, scopes, req_mock)
        api_client.credentials(HTTP_AUTHORIZATION=auth_header)

        return api_client.get(reverse("helsinki_gdpr:gdpr_v1", kwargs={settings.GDPR_API_MODEL_LOOKUP: id_value}))


def _format_datetime(dt):
    return dt.isoformat().replace("+00:00", "Z") if dt else dt


def _get_section_poll_option_data(section_poll_option: SectionPollOption) -> dict:
    return {
        "key": "SECTIONPOLLOPTION",
        "children": [
            {"key": "ID", "value": section_poll_option.id},
            {"key": "ORDERING", "value": section_poll_option.ordering},
            {"key": "TEXT", "value": section_poll_option.text},
        ],
    }


def _get_section_poll_data(section_poll: SectionPoll) -> dict:
    return {
        "key": "SECTIONPOLL",
        "children": [
            {"key": "ID", "value": section_poll.id},
            {"key": "TYPE", "value": section_poll.type},
            {"key": "ORDERING", "value": section_poll.ordering},
            {"key": "IS_INDEPENDENT_POLL", "value": section_poll.is_independent_poll},
            {"key": "TEXT", "value": section_poll.text},
            {
                "key": "OPTIONS",
                "children": [_get_section_poll_option_data(option) for option in section_poll.options.all()],
            },
        ],
    }


def _get_section_image_data(section_image: SectionImage) -> dict:
    return {
        "key": "SECTIONIMAGE",
        "children": [
            {"key": "ID", "value": section_image.id},
            {"key": "TITLE", "value": section_image.title},
            {"key": "CAPTION", "value": section_image.caption},
            {"key": "ALT_TEXT", "value": section_image.alt_text},
            {"key": "IMAGE", "value": file_to_base64(section_image.image.file)},
            {"key": "PUBLISHED", "value": section_image.published},
            {"key": "CREATED_AT", "value": _format_datetime(section_image.created_at)},
            {"key": "MODIFIED_AT", "value": _format_datetime(section_image.modified_at)},
            {"key": "DELETED", "value": section_image.deleted},
            {"key": "DELETED_AT", "value": _format_datetime(section_image.deleted_at)},
        ],
    }


def _get_section_file_data(section_file: SectionFile) -> dict:
    return {
        "key": "SECTIONFILE",
        "children": [
            {"key": "ID", "value": section_file.id},
            {"key": "TITLE", "value": section_file.title},
            {"key": "CAPTION", "value": section_file.caption},
            {"key": "FILE", "value": file_to_base64(section_file.file.file)},
            {"key": "PUBLISHED", "value": section_file.published},
            {"key": "CREATED_AT", "value": _format_datetime(section_file.created_at)},
            {"key": "MODIFIED_AT", "value": _format_datetime(section_file.modified_at)},
            {"key": "DELETED", "value": section_file.deleted},
            {"key": "DELETED_AT", "value": _format_datetime(section_file.deleted_at)},
        ],
    }


def _get_section_data(section: Section) -> dict:
    return {
        "key": "SECTION",
        "children": [
            {"key": "ID", "value": section.id},
            {"key": "ORDERING", "value": section.ordering},
            {"key": "TITLE", "value": section.title},
            {"key": "ABSTRACT", "value": section.abstract},
            {"key": "CONTENT", "value": section.content},
            {"key": "FILES", "children": [_get_section_file_data(file) for file in section.files.all()]},
            {"key": "IMAGES", "children": [_get_section_image_data(image) for image in section.images.all()]},
            {"key": "POLLS", "children": [_get_section_poll_data(poll) for poll in section.polls.all()]},
        ],
    }


def _get_hearing_data(hearing: Hearing) -> dict:
    return {
        "key": "HEARING",
        "children": [
            {"key": "ID", "value": hearing.id},
            {"key": "TITLE", "value": hearing.title},
            {"key": "GEOJSON", "value": hearing.geojson},
            {"key": "SECTIONS", "children": [_get_section_data(section) for section in hearing.sections.all()]},
        ],
    }


def _get_organization_data(organization: Organization) -> dict:
    return {
        "key": "ORGANIZATION",
        "children": [
            {"key": "ID", "value": organization.id},
            {"key": "NAME", "value": organization.name},
        ],
    }


def _get_comment_image_data(comment_image: CommentImage) -> dict:
    return {
        "key": "COMMENTIMAGE",
        "children": [
            {"key": "ID", "value": comment_image.id},
            {"key": "TITLE", "value": comment_image.title},
            {"key": "CAPTION", "value": comment_image.caption},
            {"key": "IMAGE", "value": file_to_base64(comment_image.image.file)},
            {"key": "PUBLISHED", "value": comment_image.published},
            {"key": "CREATED_AT", "value": _format_datetime(comment_image.created_at)},
            {"key": "MODIFIED_AT", "value": _format_datetime(comment_image.modified_at)},
            {"key": "DELETED", "value": comment_image.deleted},
            {"key": "DELETED_AT", "value": _format_datetime(comment_image.deleted_at)},
        ],
    }


def _get_poll_answer_data(poll_answer: SectionPollAnswer) -> dict:
    return {
        "key": "SECTIONPOLLANSWER",
        "children": [
            {"key": "ID", "value": poll_answer.id},
            {"key": "OPTION", "value": poll_answer.option.text},
        ],
    }


def _get_section_comment_data(section_comment: SectionComment) -> dict:
    return {
        "key": "SECTIONCOMMENT",
        "children": [
            {"key": "ID", "value": section_comment.id},
            {"key": "SECTION_ID", "value": section_comment.section_id},
            {"key": "AUTHOR_NAME", "value": section_comment.author_name},
            {"key": "COMMENT_ID", "value": section_comment.comment_id},
            {"key": "TITLE", "value": section_comment.title},
            {"key": "CONTENT", "value": section_comment.content},
            {"key": "PUBLISHED", "value": section_comment.published},
            {"key": "CREATED_AT", "value": _format_datetime(section_comment.created_at)},
            {"key": "MODIFIED_AT", "value": _format_datetime(section_comment.modified_at)},
            {"key": "DELETED", "value": section_comment.deleted},
            {"key": "DELETED_AT", "value": _format_datetime(section_comment.deleted_at)},
            {"key": "IMAGES", "children": [_get_comment_image_data(image) for image in section_comment.images.all()]},
            {
                "key": "POLL_ANSWERS",
                "children": [_get_poll_answer_data(answer) for answer in section_comment.poll_answers.all()],
            },
            {"key": "GEOJSON", "value": section_comment.geojson},
        ],
    }


def _get_user_data(user: User) -> List[dict]:
    return [
        {"key": "ID", "value": user.id},
        {"key": "UUID", "value": str(user.uuid)},
        {"key": "USERNAME", "value": user.username},
        {"key": "NICKNAME", "value": user.nickname},
        {"key": "FIRST_NAME", "value": user.first_name},
        {"key": "LAST_NAME", "value": user.last_name},
        {"key": "EMAIL", "value": user.email},
        {"key": "HAS_STRONG_AUTH", "value": user.has_strong_auth},
        {
            "key": "SECTIONCOMMENTS",
            "value": [_get_section_comment_data(comment) for comment in user.sectioncomment_created.everything()],
        },
        {
            "key": "VOTED_SECTIONCOMMENTS",
            "value": [
                _get_section_comment_data(comment) for comment in user.voted_democracy_sectioncomment.everything()
            ],
        },
        {
            "key": "FOLLOWED_HEARINGS",
            "children": [_get_hearing_data(hearing) for hearing in user.followed_hearings.all()],
        },
        {
            "key": "ADMIN_ORGANIZATIONS",
            "children": [_get_organization_data(organization) for organization in user.admin_organizations.all()],
        },
        {"key": "HEARING_CREATED", "children": [_get_hearing_data(hearing) for hearing in user.hearing_created.all()]},
    ]


def _assert_user_data_in_response(response, user: User):
    profile_data = {"key": "USER", "children": _get_user_data(user)}
    assert response.json() == profile_data


@pytest.mark.django_db
def test_get_user_information_from_gdpr_api(user, geojson_feature):
    user.nickname = "Nick Name"
    user.save()
    organization = OrganizationFactory()
    organization.admin_users.add(user)
    hearing = HearingFactory()
    SectionComment.objects.all().delete()
    section = hearing.get_main_section()
    poll = SectionPollFactory(section=section)
    poll_option = poll.options.first()
    comment = SectionCommentFactory(
        section=section, created_by=user, author_name="Author Name", geojson=geojson_feature
    )
    comment_voted = SectionCommentFactory(section=section)
    comment_voted.voters.add(user)
    SectionPollAnswer.objects.create(comment=comment, created_by=user, option=poll_option)

    deleted_comment = SectionCommentFactory(
        section=section, created_by=user, author_name="Name of the Author", geojson=geojson_feature
    )
    deleted_comment.soft_delete()

    CommentImageFactory(comment=comment, created_by=user)
    hearing_followed = HearingFactory()
    hearing_followed.followers.add(user)
    hearing_created = HearingFactory(created_by=user, geojson=geojson_feature)
    section_created = hearing_created.get_main_section()
    SectionFileFactory(section=section_created, created_by=user)
    SectionImageFactory(section=section_created, created_by=user)
    SectionPollFactory(section=section_created, created_by=user)

    response = do_query(user, user.uuid)

    assert response.status_code == status.HTTP_200_OK
    _assert_user_data_in_response(response, user)


@pytest.mark.django_db
def test_user_can_only_access_his_own_information(user):
    other_user = UserFactory()

    response = do_query(user, other_user.uuid)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_gdpr_api_requires_authentication(api_client, user):
    response = api_client.get(reverse("helsinki_gdpr:gdpr_v1", kwargs={settings.GDPR_API_MODEL_LOOKUP: user.uuid}))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
