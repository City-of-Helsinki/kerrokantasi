import datetime

import pytest
from django.utils.encoding import force_text
from django.utils.timezone import now

from kk.models import Hearing, HearingComment, HearingImage, Label, Section, SectionComment, SectionImage
from kk.tests.utils import assert_datetime_fuzzy_equal, get_data_from_response, get_geojson, get_hearing_detail_url

endpoint = '/v1/hearing/'
list_endpoint = endpoint


def get_detail_url(id):
    return '%s%s/' % (endpoint, id)


def create_hearings(n):
    # Get rid of all other hearings:
    SectionImage.objects.all().delete()
    SectionComment.objects.all().delete()
    Section.objects.all().delete()
    HearingImage.objects.all().delete()
    HearingComment.objects.all().delete()
    Hearing.objects.all().delete()
    hearings = []

    # Depending on the database backend, created_at dates (which are used for ordering)
    # may be truncated to the closest second, so we purposefully backdate these
    # to ensure ordering on all platforms.
    for i in range(n):
        hearings.append(
            Hearing.objects.create(
                abstract='Test purpose created hearing %s' % (i + 1),
                created_at=now() - datetime.timedelta(seconds=1 + (n - i))
            )
        )
    return hearings


@pytest.mark.django_db
def test_list_all_hearings_no_objects(api_client):
    create_hearings(0)
    response = api_client.get(list_endpoint)

    data = get_data_from_response(response)
    assert len(data) == 0


@pytest.mark.django_db
def test_list_all_hearings_check_number_of_objects(api_client):
    response = api_client.get(list_endpoint)

    data = get_data_from_response(response)
    assert len(data) == Hearing.objects.count()


@pytest.mark.django_db
def test_list_all_hearings_check_abstract(api_client):
    hearings = create_hearings(3)
    response = api_client.get(list_endpoint)
    data = get_data_from_response(response)
    assert data[0]['abstract'] == hearings[2].abstract
    assert data[1]['abstract'] == hearings[1].abstract
    assert data[2]['abstract'] == hearings[0].abstract


@pytest.mark.django_db
def test_list_top_5_hearings_check_number_of_objects(api_client):
    create_hearings(10)
    response = api_client.get(list_endpoint, data={"limit": 5})

    data = get_data_from_response(response)
    assert len(data['results']) == 5


@pytest.mark.django_db
def test_list_top_5_hearings_check_abstract(api_client):
    create_hearings(10)
    response = api_client.get(list_endpoint, data={"limit": 5})

    data = get_data_from_response(response)
    objects = data['results']
    # We expect data to be returned in this, particular order
    assert '10' in objects[0]['abstract']
    assert '9' in objects[1]['abstract']
    assert '8' in objects[2]['abstract']
    assert '7' in objects[3]['abstract']
    assert '6' in objects[4]['abstract']


@pytest.mark.django_db
def test_get_next_closing_hearings(api_client):
    create_hearings(0)  # Clear out old hearings
    closed_hearing_1 = Hearing.objects.create(abstract='Gone', close_at=now() - datetime.timedelta(days=1))
    closed_hearing_2 = Hearing.objects.create(abstract='Gone too', close_at=now() - datetime.timedelta(days=2))
    future_hearing_1 = Hearing.objects.create(abstract='Next up', close_at=now() + datetime.timedelta(days=1))
    future_hearing_2 = Hearing.objects.create(abstract='Next up', close_at=now() + datetime.timedelta(days=5))
    response = api_client.get(list_endpoint, {"next_closing": now().isoformat()})
    data = get_data_from_response(response)
    assert len(data) == 1
    assert data[0]['abstract'] == future_hearing_1.abstract
    response = api_client.get(list_endpoint, {"next_closing": future_hearing_1.close_at.isoformat()})
    data = get_data_from_response(response)
    assert len(data) == 1
    assert data[0]['abstract'] == future_hearing_2.abstract


@pytest.mark.django_db
def test_8_get_detail_check_properties(api_client, default_hearing):
    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert set(data.keys()) >= {
        'abstract', 'borough', 'close_at', 'closed', 'created_at', 'id', 'images', 'labels',
        'latitude', 'longitude', 'n_comments', 'open_at', 'sections', 'servicemap_url',
        'title'
    }


@pytest.mark.django_db
def test_8_get_detail_abstract(api_client):
    hearing = Hearing(abstract='Lorem Ipsum Abstract')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['abstract'] == hearing.abstract


@pytest.mark.django_db
def test_8_get_detail_title(api_client):
    hearing = Hearing(title='Lorem Ipsum Title')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['title'] == hearing.title


@pytest.mark.django_db
def test_8_get_detail_borough(api_client):
    hearing = Hearing(borough='Itäinen')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['borough'] == hearing.borough


@pytest.mark.django_db
def test_8_get_detail_n_comments(api_client):
    hearing = Hearing(n_comments=1)
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['n_comments'] == hearing.n_comments


@pytest.mark.django_db
def test_8_get_detail_closing_time(api_client):
    hearing = Hearing()
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert_datetime_fuzzy_equal(data['close_at'], hearing.close_at)


@pytest.mark.django_db
def test_8_get_detail_labels(api_client):
    hearing = Hearing()
    hearing.save()

    label_one = Label(label='Label One')
    label_one.save()
    label_two = Label(label='Label Two')
    label_two.save()
    label_three = Label(label='Label Three')
    label_three.save()

    hearing.labels.add(label_one, label_two, label_three)

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert len(data['labels']) is 3
    assert label_one.label in data['labels']


@pytest.mark.django_db
def test_7_get_detail_location(api_client):
    hearing = Hearing(latitude=60.19276, longitude=24.93300)
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert abs(data['latitude'] - hearing.latitude) < 0.1
    assert abs(data['longitude'] - hearing.longitude) < 0.1


@pytest.mark.django_db
def test_7_get_detail_servicemap(api_client):
    hearing = Hearing(
        servicemap_url='http://servicemap.hel.fi/embed/?bbox=60.19276,24.93300,60.19571,24.94513&city=helsinki'
    )
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['servicemap_url'] == hearing.servicemap_url


@pytest.mark.django_db
def test_24_get_report(api_client, default_hearing):
    response = api_client.get('%s%s/report/' % (endpoint, default_hearing.id))
    assert response.status_code == 200
    assert len(response.content) > 0


@pytest.mark.django_db
def test_hearing_stringification(random_hearing):
    assert force_text(random_hearing) == random_hearing.title


@pytest.mark.django_db
def test_admin_can_see_unpublished(api_client, john_doe_api_client, admin_api_client):
    hearings = create_hearings(3)
    unpublished_hearing = hearings[0]
    unpublished_hearing.published = False
    unpublished_hearing.save()
    data = get_data_from_response(api_client.get(list_endpoint))
    assert len(data) == 2  # Can't see it as anon
    data = get_data_from_response(john_doe_api_client.get(list_endpoint))
    assert len(data) == 2  # Can't see it as registered
    data = get_data_from_response(admin_api_client.get(list_endpoint))
    assert len(data) == 3  # Can see it as admin
    assert len([1 for h in data if not h["published"]]) == 1  # Only one unpublished, yeah?


@pytest.mark.django_db
def test_hearing_geo(api_client, random_hearing):
    random_hearing.geojson = get_geojson()
    random_hearing.save()
    data = get_data_from_response(api_client.get(get_detail_url(random_hearing.id)))
    assert data["geojson"] == random_hearing.geojson
    map_data = get_data_from_response(api_client.get(list_endpoint + "map/"))
    assert map_data[0]["geojson"] == random_hearing.geojson
