import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_hearing_admin_renders(admin_client):
    url = reverse("admin:democracy_hearing_add")
    admin_client.get(url)
