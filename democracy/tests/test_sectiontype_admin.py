import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_sectiontype_admin_renders(admin_client):
    url = reverse('admin:democracy_sectiontype_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

    url = reverse('admin:democracy_sectiontype_add')
    response = admin_client.get(url)
    assert response.status_code == 200
