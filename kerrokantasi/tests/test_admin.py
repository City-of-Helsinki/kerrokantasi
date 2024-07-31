import pytest
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model

from kerrokantasi.admin import UserAdmin


@pytest.fixture
def user_admin():
    return UserAdmin(model=get_user_model(), admin_site=AdminSite())


@pytest.mark.django_db
def test_user_admin_admin_in_organizations_field_no_orgs(user_admin, user):
    assert user_admin.admin_in_organizations(user) == "-"


@pytest.mark.django_db
def test_user_admin_admin_in_organizations_field_single_org(user_admin, user, organization):
    user.admin_organizations.add(organization)
    assert user_admin.admin_in_organizations(user) == organization.name


@pytest.mark.django_db
def test_user_admin_admin_in_organizations_field_multiple_orgs(user_admin, user, organization_factory):
    organization1 = organization_factory()
    organization2 = organization_factory()
    user.admin_organizations.add(organization1, organization2)
    assert user_admin.admin_in_organizations(user) == f"{organization1.name}, {organization2.name}"
