import pytest

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

    data = {'content': 'test_data'}
    url = f"/admin/democracy/sectioncomment/{comment.id}/change/"
    response = admin_client.post(url, data)

    comment = SectionComment.objects.everything().get(id=comment.id)
    assert comment.content == 'test_data'
    assert comment.edited is True
    assert comment.moderated is True
