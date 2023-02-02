import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_contactperson_admin_renders(admin_client, contact_person):
    url = reverse('admin:democracy_contactperson_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

    url = reverse('admin:democracy_contactperson_change', args=[contact_person.id])
    response = admin_client.get(url)
    assert response.status_code == 200
