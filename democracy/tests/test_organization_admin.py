# -*- coding: utf-8 -*-
import pytest
from django.core.urlresolvers import reverse


@pytest.mark.django_db
def test_organization_admin_renders(admin_client, default_organization):
    url = reverse('admin:democracy_organization_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

    url = reverse('admin:democracy_organization_change', args=[default_organization.id])
    response = admin_client.get(url)
    assert response.status_code == 200
