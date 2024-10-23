import datetime

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils.timezone import now
from freezegun import freeze_time

from democracy.factories.hearing import MinimalHearingFactory
from democracy.factories.organization import OrganizationFactory
from democracy.models import Hearing
from democracy.tests.utils import instance_ids
from democracy.views.hearing import HearingFilterSet
from kerrokantasi.tests.factories import UserFactory

endpoint = "/v1/hearing/"


@pytest.mark.django_db
def test_filter_created_by_as_anonymous_user_should_return_unmodified_queryset(rf):
    organization = OrganizationFactory.create()
    another_organization = OrganizationFactory.create()
    MinimalHearingFactory.create_batch(5, organization=another_organization)
    request = rf.get(endpoint)
    request.user = AnonymousUser()

    hearing_filter_set = HearingFilterSet(
        queryset=Hearing.objects.all(),
        data={"created_by": organization.name},
        request=request,
    )

    assert hearing_filter_set.qs.count() == 5


@pytest.mark.django_db
def test_filter_created_by_with_me_should_return_hearings_created_by_user(rf):
    user = UserFactory.create()
    expected_hearing = MinimalHearingFactory(created_by=user)
    MinimalHearingFactory(created_by=UserFactory.create())
    request = rf.get(endpoint)
    request.user = user

    hearing_filter_set = HearingFilterSet(
        queryset=Hearing.objects.all(), data={"created_by": "me"}, request=request
    )

    assert hearing_filter_set.qs.count() == 1
    assert hearing_filter_set.qs.first() == expected_hearing


@pytest.mark.django_db
def test_filter_created_by_with_organization_name_should_return_hearings_created_by_organization(
    rf,
):
    organization = OrganizationFactory.create()
    expected_hearing = MinimalHearingFactory(organization=organization)
    MinimalHearingFactory(organization=OrganizationFactory.create())
    request = rf.get(endpoint)
    request.user = UserFactory.create()

    hearing_filter_set = HearingFilterSet(
        queryset=Hearing.objects.all(),
        data={"created_by": organization.name},
        request=request,
    )

    assert hearing_filter_set.qs.count() == 1
    assert hearing_filter_set.qs.first() == expected_hearing


@pytest.mark.django_db
def test_filter_created_by_with_non_existing_organization_should_return_unmodified_queryset(
    rf,
):
    MinimalHearingFactory.create_batch(5, organization=OrganizationFactory.create())
    request = rf.get(endpoint)
    request.user = UserFactory.create()

    hearing_filter_set = HearingFilterSet(
        queryset=Hearing.objects.all(),
        data={"created_by": "non_existing"},
        request=request,
    )

    assert hearing_filter_set.qs.count() == 5


@freeze_time("2000-01-01T00:00:00Z")
@pytest.mark.django_db
def test_filter_open_with_true():
    next_day = now() + datetime.timedelta(days=1)
    previous_day = now() - datetime.timedelta(days=1)
    next_second = now() + datetime.timedelta(seconds=1)
    previous_second = now() - datetime.timedelta(seconds=1)

    # Hearings that should show up.
    expected_hearings = [
        MinimalHearingFactory(open_at=previous_second, close_at=next_second),
        MinimalHearingFactory(open_at=now(), close_at=next_second),
        MinimalHearingFactory(open_at=previous_day, close_at=next_day),
    ]

    # Hearings that should not show up.
    MinimalHearingFactory(open_at=previous_day, close_at=now())
    MinimalHearingFactory(open_at=previous_day, close_at=previous_second)
    MinimalHearingFactory(open_at=next_second, close_at=next_day)
    MinimalHearingFactory(open_at=previous_day, close_at=next_day, force_closed=True)

    hearing_filter_set = HearingFilterSet(
        data={"open": True}, queryset=Hearing.objects.all()
    )

    # Should return the expected hearings.
    assert hearing_filter_set.qs.count() == len(expected_hearings)
    assert instance_ids(hearing_filter_set.qs) == instance_ids(expected_hearings)


@freeze_time("2000-01-01T00:00:00Z")
@pytest.mark.django_db
def test_filter_open_with_false():
    next_day = now() + datetime.timedelta(days=1)
    previous_day = now() - datetime.timedelta(days=1)
    next_second = now() + datetime.timedelta(seconds=1)
    previous_second = now() - datetime.timedelta(seconds=1)

    # Hearings that should show up.
    expected_hearings = [
        MinimalHearingFactory(open_at=previous_day, close_at=now()),
        MinimalHearingFactory(open_at=previous_day, close_at=previous_second),
        MinimalHearingFactory(open_at=next_second, close_at=next_day),
        MinimalHearingFactory(
            open_at=previous_day, close_at=next_day, force_closed=True
        ),
    ]

    # Hearings that should not show up.
    MinimalHearingFactory(open_at=previous_second, close_at=next_second)
    MinimalHearingFactory(open_at=now(), close_at=next_second)
    MinimalHearingFactory(open_at=previous_day, close_at=next_day)

    hearing_filter_set = HearingFilterSet(
        data={"open": False}, queryset=Hearing.objects.all()
    )

    # Should return the expected hearings.
    assert hearing_filter_set.qs.count() == len(expected_hearings)
    assert instance_ids(hearing_filter_set.qs) == instance_ids(expected_hearings)
