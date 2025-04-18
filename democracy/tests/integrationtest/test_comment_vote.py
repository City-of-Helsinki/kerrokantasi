import pytest

from democracy.enums import Commenting, InitialSectionType
from democracy.models import Section, SectionComment, SectionType
from democracy.tests.integrationtest.test_images import get_hearing_detail_url
from democracy.tests.utils import assert_audit_log_entry

default_content = "Awesome comment to vote."
comment_data = {"content": default_content, "section": None}


def add_default_section_and_comment(hearing):
    section = Section.objects.create(
        title="Section title",
        hearing=hearing,
        type=SectionType.objects.get(identifier=InitialSectionType.PART),
    )
    comment = SectionComment.objects.create(content="Comment text", section=section)
    return [section, comment]


def get_section_comment_vote_url(hearing_id, section_id, comment_id):
    # /v1/hearings/<hearingID>/sections/<sectionID>/comments/<commentID>/votes/
    return get_hearing_detail_url(
        hearing_id, "sections/%s/comments/%s/vote" % (section_id, comment_id)
    )


def get_section_comment_unvote_url(hearing_id, section_id, comment_id):
    # /v1/hearings/<hearingID>/sections/<sectionID>/comments/<commentID>/unvote/
    return get_hearing_detail_url(
        hearing_id, "sections/%s/comments/%s/unvote" % (section_id, comment_id)
    )


@pytest.mark.django_db
def test_31_section_comment_vote_without_authentication(api_client, default_hearing):
    section, comment = add_default_section_and_comment(default_hearing)
    response = api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_anonymous_vote_section_comment_vote_without_authentication(
    api_client, default_hearing
):
    section, comment = add_default_section_and_comment(default_hearing)
    section.voting = Commenting.OPEN
    section.save()
    response = api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_vote_section_comment_vote_add_vote_check_amount_of_votes(
    api_client, default_hearing
):
    section, comment = add_default_section_and_comment(default_hearing)
    section.voting = Commenting.OPEN
    section.save()
    response = api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 200

    comment = SectionComment.objects.get(id=comment.id)
    assert comment.n_votes == 1
    response = api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 200

    comment = SectionComment.objects.get(id=comment.id)
    assert comment.n_votes == 2


@pytest.mark.django_db
def test_31_section_comment_vote_add_vote(john_doe_api_client, default_hearing):
    section, comment = add_default_section_and_comment(default_hearing)
    response = john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_31_section_comment_vote_add_vote_check_voter(
    john_doe_api_client, default_hearing
):
    section, comment = add_default_section_and_comment(default_hearing)
    response = john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 201

    comments = SectionComment.objects.filter(
        id=comment.id, voters=john_doe_api_client.user
    )
    assert len(comments) == 1


@pytest.mark.django_db
def test_31_section_comment_vote_add_vote_check_amount_of_votes(
    john_doe_api_client, default_hearing
):
    section, comment = add_default_section_and_comment(default_hearing)
    response = john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 201

    comment = SectionComment.objects.get(id=comment.id, voters=john_doe_api_client.user)
    assert comment.voters.all().count() == 1
    assert comment.n_votes == 1


@pytest.mark.django_db
def test_31_section_comment_vote_add_second_vote(john_doe_api_client, default_hearing):
    section, comment = add_default_section_and_comment(default_hearing)
    response = john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 201
    # Add vote again. Expect error, because vote has been given already.
    response = john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 304


@pytest.mark.django_db
def test_section_comment_unvote(john_doe_api_client, default_hearing):
    section, comment = add_default_section_and_comment(default_hearing)

    john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    response = john_doe_api_client.post(
        get_section_comment_unvote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 204
    comment.refresh_from_db()
    assert comment.n_votes == 0

    # User cannot unvote if he/she hasn't voted
    response = john_doe_api_client.post(
        get_section_comment_unvote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 304


@pytest.mark.django_db
def test_section_comment_unvote_without_authentication(api_client, default_hearing):
    section, comment = add_default_section_and_comment(default_hearing)
    response = api_client.post(
        get_section_comment_unvote_url(default_hearing.id, section.id, comment.id)
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_vote_appears_in_user_data(john_doe_api_client, default_hearing):
    section, sc_comment = add_default_section_and_comment(default_hearing)
    john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, sc_comment.id)
    )
    response = john_doe_api_client.get("/v1/users/")
    assert sc_comment.id in response.data[0]["voted_section_comments"]


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_vote(
    john_doe_api_client, default_hearing, audit_log_configure
):
    section, comment = add_default_section_and_comment(default_hearing)

    john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )

    assert_audit_log_entry("/vote", [comment.pk])


@pytest.mark.django_db
def test_comment_id_is_audit_logged_on_unvote(
    api_client, john_doe_api_client, default_hearing, audit_log_configure
):
    section, comment = add_default_section_and_comment(default_hearing)

    john_doe_api_client.post(
        get_section_comment_vote_url(default_hearing.id, section.id, comment.id)
    )
    john_doe_api_client.post(
        get_section_comment_unvote_url(default_hearing.id, section.id, comment.id)
    )

    assert_audit_log_entry("/unvote", [comment.pk], 2)
