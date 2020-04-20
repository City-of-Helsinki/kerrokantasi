# -*- coding: utf-8 -*-
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_label_admin_renders(admin_client, default_label):
    url = reverse('admin:democracy_label_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

    url = reverse('admin:democracy_label_change', args=[default_label.id])
    response = admin_client.get(url)
    assert response.status_code == 200
