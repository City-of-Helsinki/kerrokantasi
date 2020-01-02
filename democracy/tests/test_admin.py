import pytest
from django.urls import reverse
from django.test.utils import override_settings

from democracy.models import Hearing


@pytest.mark.django_db
def test_hearing_delete_action(admin_client, default_hearing):
    change_url = reverse('admin:democracy_hearing_changelist')
    data = {'action': 'delete_selected', '_selected_action': [default_hearing.pk]}
    response = admin_client.post(change_url, data, follow=True)

    assert response.status_code == 200
    assert 'Successfully deleted 1 hearing.' in response.rendered_content

    default_hearing = Hearing.objects.everything().get(pk=default_hearing.pk)
    assert default_hearing.deleted is True


# TODO test section / section image inline soft delete somehow? it seems a bit complicated
