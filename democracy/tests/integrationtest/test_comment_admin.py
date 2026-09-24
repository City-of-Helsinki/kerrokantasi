import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from reversion.models import Version

from democracy.factories.hearing import SectionCommentFactory
from democracy.models.section import SectionComment


@pytest.mark.django_db
def test_comment_delete_action(admin_client, admin_user, default_hearing):
    default_hearing.created_by = admin_user
    default_hearing.save()
    comment = default_hearing.get_main_section().comments.all()[0]
    url = f"/admin/democracy/sectioncomment/{comment.id}/delete/"

    response = admin_client.delete(url)

    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.deleted is False


@pytest.mark.django_db
def test_comment_edit_action(admin_client, admin_user, default_hearing):
    default_hearing.created_by = admin_user
    default_hearing.save()
    comment = default_hearing.get_main_section().comments.all()[0]
    url = f"/admin/democracy/sectioncomment/{comment.id}/change/"

    response = admin_client.post(url)

    assert response.status_code == 403
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.edited is False


@pytest.mark.django_db
def test_comment_edited_by_admin(admin_client, admin_user, default_hearing):
    comment = default_hearing.get_main_section().comments.all()[0]
    data = {"content": "test_data"}
    url = f"/admin/democracy/sectioncomment/{comment.id}/change/"

    response = admin_client.post(url, data)

    assert response.status_code == 302
    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.content == "test_data"
    assert comment.edited is True
    assert comment.moderated is True


@pytest.mark.django_db
def test_admin_editing_creates_revision(admin_client, default_hearing):
    expected_content = "test_data"
    comment = default_hearing.get_main_section().comments.all()[0]
    data = {"content": expected_content}
    url = f"/admin/democracy/sectioncomment/{comment.id}/change/"

    response = admin_client.post(url, data)

    assert response.status_code == 302
    comment = SectionComment.objects.everything().get(id=comment.id)
    versions = Version.objects.get_for_object(comment)
    assert len(versions) == 1
    assert versions[0].field_dict["content"] == expected_content


@pytest.mark.django_db
def test_comment_changelist_prefetches_section_translations(
    admin_client, default_hearing
):
    sections = list(default_hearing.sections.all())
    url = reverse("admin:democracy_sectioncomment_changelist") + "?deleted__exact=0"

    with CaptureQueriesContext(connection) as small_result:
        response = admin_client.get(url)
    assert response.status_code == 200

    for section in sections:
        SectionCommentFactory.create_batch(3, section=section)

    with CaptureQueriesContext(connection) as large_result:
        response = admin_client.get(url)
    assert response.status_code == 200

    translation_tables = (
        "democracy_section_translation",
        "democracy_hearing_translation",
    )

    def translation_query_count(queries):
        return sum(
            any(table in query["sql"] for table in translation_tables)
            for query in queries
        )

    assert translation_query_count(large_result.captured_queries) == (
        translation_query_count(small_result.captured_queries)
    )
