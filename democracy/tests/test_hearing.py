import datetime
import json

import pytest
from django.utils.encoding import force_text
from django.utils.timezone import now

from democracy.enums import InitialSectionType
from democracy.factories.organization import OrganizationFactory
from democracy.models import (
    Hearing, Label, Organization, Project, ProjectPhase, Section, SectionComment, SectionImage, SectionType
)
from democracy.models.utils import copy_hearing
from democracy.tests.utils import (
    assert_common_keys_equal, assert_datetime_fuzzy_equal, get_data_from_response,
    get_hearing_detail_url, sectionimage_test_json, sectionfile_base64_test_data
)
from democracy.tests.conftest import default_lang_code, get_feature_with_geometry

endpoint = '/v1/hearing/'
list_endpoint = endpoint


@pytest.fixture
def valid_hearing_json(contact_person, default_label):
    return {
        "title": {
            "en": "My first hearing",
            "fi": "Finnish title (yes it is in Finnish...)",
            "sv": "Swedish title (don't speak swedish either ...)",
        },
        "id": "nD6aC5herQM3X1yi9aNQf6rGm6ZogAlC",
        "borough": {
            "en": "Punavuori",
            "fi": "Punavuori",
            "sv": "Rooperi",
        },
        "n_comments": 0,
        "published": True,
        "labels": [{"id": default_label.id, "label": {default_lang_code: default_label.label}}],
        "open_at": "2016-09-29T11:39:12Z",
        "close_at": "2016-09-29T11:39:12Z",
        "created_at": "2016-10-04T10:30:38.066436Z",
        "servicemap_url": "",
        "sections": [
            {
                "type": "closure-info",
                "commenting": 'none',
                "commenting_map_tools": 'none',
                "title": {
                    "en": "Section 3",
                },
                "abstract": {},
                "content": {
                    "en": "<p>Enter the introduction text for the hearing here.</p>",
                    "fi": "<p>Enter the finnish text for the hearing here.</p>",
                },
                "created_at": "2016-10-04T12:12:06.798574Z",
                "created_by": None,
                "images": [],
                "n_comments": 0,
                "plugin_identifier": "",
                "plugin_data": "",
                "type_name_singular": "sulkeutumistiedote",
                "type_name_plural": "sulkeutumistiedotteet",
            },
            {
                "commenting": 'none',
                "commenting_map_tools": 'none',
                "title": {
                    "en": "Section 1",
                },
                "abstract": {},
                "content": {
                    "en": "<p>Enter the introduction text for the hearing here.</p>",
                    "fi": "<p>Enter the Finnish introduction text for the hearing here.</p>",
                },
                "created_at": "2016-10-04T11:33:37.430091Z",
                "created_by": None,
                "images": [
                    sectionimage_test_json(title_en='1'),
                    sectionimage_test_json(title_en='2'),
                    sectionimage_test_json(title_en='3'),
                ],
                "n_comments": 0,
                "plugin_identifier": "",
                "plugin_data": "",
                "type_name_singular": "pääosio",
                "type_name_plural": "pääosiot",
                "type": "main"
            },
            {
                "id": "3adn7MGkOJ8e4NlhsElxKggbfdmrSmVE",
                "type": "part",
                "commenting": 'none',
                "commenting_map_tools": 'none',
                "title": {
                    "en": "Section 2",
                },
                "abstract": {},
                "content": {
                    "en": "<p>Enter the introduction text for the hearing here.eve</p>",
                    "fi": "something in Finnish",
                },
                "created_at": "2016-10-04T12:09:16.818364Z",
                "created_by": None,
                "images": [
                    sectionimage_test_json(),
                ],
                "files": [
                    sectionfile_base64_test_data(),
                ],
                "n_comments": 0,
                "plugin_identifier": "",
                "plugin_data": "",
                "type_name_singular": "osa-alue",
                "type_name_plural": "osa-alueet"
            },
        ],
        "closed": True,
        "organization": None,
        "geojson": None,
        "main_image": None,
        "contact_persons": [{
            "id": contact_person.id,
        }],
        "slug": "test-hearing",
    }


def _update_hearing_data(data):
    data.update({
        "n_comments": 10,
        "published": False,
        "open_at": "2016-10-29T11:39:12Z",
        "close_at": "2016-10-29T11:39:12Z",
        "created_at": "2015-06-04T10:30:38.066436Z",
        "servicemap_url": "url",
    })
    data["title"]["en"] = "Updating my first hearing"
    data["borough"]["en"] = "Eira"

    data['sections'][0]['title']['en'] = 'First section'
    data['sections'][1]['images'][0]['caption']['en'] = 'New image caption'


@pytest.fixture
def unpublished_hearing_json(valid_hearing_json):
    valid_hearing_json.update({'published': False})
    return valid_hearing_json


@pytest.fixture
def valid_hearing_json_with_project(valid_hearing_json):
    valid_hearing_json.update({
        "project": {
            "id": "",
            "title": {
                "en": "Default project"
            },
            "phases": [
                {
                    "schedule": {
                        "en": "Phase 1 schedule"
                    },
                    "has_hearings": True,
                    "id": "",
                    "title": {
                        "en": "Phase 1"
                    },
                    "is_active": True,
                    "description": {
                        "en": "Phase 1 description"
                    }
                },
                {
                    "schedule": {
                        "en": "Phase 2 schedule"
                    },
                    "has_hearings": False,
                    "id": "",
                    "title": {
                        "en": "Phase 2"
                    },
                    "is_active": False,
                    "description": {
                        "en": "Phase 2 description"
                    }
                },
                {
                    "schedule": {
                        "en": "Phase 3 schedule"
                    },
                    "has_hearings": False,
                    "id": "",
                    "title": {
                        "en": "Phase 3"
                    },
                    "is_active": False,
                    "description": {
                        "en": "Phase 3 description"
                    }
                }
            ],
        },
    })
    return valid_hearing_json


@pytest.fixture
def default_project_json(default_project):
    project_data = {
        "project": {
            "id": default_project.pk,
            "title": {
                "en": default_project.title
            },
            "phases": [],
        }
    }
    is_first_loop = True
    for phase in default_project.phases.all():
        project_data['project']['phases'].append({
            "schedule": {
                "en": phase.schedule
            },
            "has_hearings": phase.hearings.exists(),
            "id": phase.pk,
            "title": {
                "en": phase.title
            },
            "is_active": is_first_loop,
            "description": {
                "en": phase.description
            }

        })
        is_first_loop = False
    return project_data


def get_detail_url(id):
    return '%s%s/' % (endpoint, id)


def create_hearings(n, organization=None):
    # Get rid of all other hearings:
    SectionImage.objects.all().delete()
    SectionComment.objects.all().delete()
    Section.objects.all().delete()
    Hearing.objects.all().delete()
    hearings = []

    # Depending on the database backend, created_at dates (which are used for ordering)
    # may be truncated to the closest second, so we purposefully backdate these
    # to ensure ordering on all platforms.
    for i in range(n):
        hearings.append(
            Hearing.objects.create(
                title='Test purpose created hearing title %s' % (i + 1),
                created_at=now() - datetime.timedelta(seconds=1 + (n - i)),
                organization=organization
            )
        )
    return hearings


@pytest.mark.django_db
def test_list_all_hearings_no_objects(api_client):
    create_hearings(0)
    response = api_client.get(list_endpoint)

    data = get_data_from_response(response)
    assert len(data['results']) == 0


@pytest.mark.django_db
def test_list_all_hearings_check_number_of_objects(api_client):
    response = api_client.get(list_endpoint)

    data = get_data_from_response(response)
    assert len(data['results']) == Hearing.objects.count()


@pytest.mark.django_db
def test_list_all_hearings_check_title(api_client):
    hearings = create_hearings(3)
    response = api_client.get(list_endpoint)
    data = get_data_from_response(response)
    assert data['results'][0]['title'][default_lang_code] == hearings[2].title
    assert data['results'][1]['title'][default_lang_code] == hearings[1].title
    assert data['results'][2]['title'][default_lang_code] == hearings[0].title


@pytest.mark.django_db
def test_list_top_5_hearings_check_number_of_objects(api_client):
    create_hearings(10)
    response = api_client.get(list_endpoint, data={"limit": 5})

    data = get_data_from_response(response)
    assert len(data['results']) == 5


@pytest.mark.django_db
def test_list_top_5_hearings_check_title(api_client):
    create_hearings(10)
    response = api_client.get(list_endpoint, data={"limit": 5})

    data = get_data_from_response(response)
    objects = data['results']
    # We expect data to be returned in this, particular order
    assert '10' in objects[0]['title'][default_lang_code]
    assert '9' in objects[1]['title'][default_lang_code]
    assert '8' in objects[2]['title'][default_lang_code]
    assert '7' in objects[3]['title'][default_lang_code]
    assert '6' in objects[4]['title'][default_lang_code]


@pytest.mark.django_db
def test_filter_hearings_by_title(api_client):
    hearings = create_hearings(3)
    response = api_client.get(list_endpoint, data={"title": "title 1"})
    data = get_data_from_response(response)
    assert len(data['results']) == 1
    assert data['results'][0]['title'][default_lang_code] == hearings[0].title


@pytest.mark.parametrize('plugin_fullscreen', [
    True,
    False,
])
@pytest.mark.django_db
def test_list_hearings_check_default_to_fullscreen(api_client, default_hearing, plugin_fullscreen):
    main_section = default_hearing.get_main_section()
    main_section.plugin_fullscreen = plugin_fullscreen
    main_section.save()

    response = api_client.get(list_endpoint)
    data = get_data_from_response(response)
    hearing = data['results'][0]
    assert hearing['default_to_fullscreen'] == plugin_fullscreen


@pytest.mark.django_db
def test_get_next_closing_and_open_hearings(api_client):
    create_hearings(0)  # Clear out old hearings
    closed_hearing_1 = Hearing.objects.create(title='Gone', close_at=now() - datetime.timedelta(days=1))
    closed_hearing_2 = Hearing.objects.create(title='Gone too', close_at=now() - datetime.timedelta(days=2))
    future_hearing_1 = Hearing.objects.create(title='Next up', close_at=now() + datetime.timedelta(days=1))
    future_hearing_2 = Hearing.objects.create(title='Next up', close_at=now() + datetime.timedelta(days=5))
    response = api_client.get(list_endpoint, {"next_closing": now().isoformat()})
    data = get_data_from_response(response)
    assert len(data['results']) == 1
    assert data['results'][0]['title'][default_lang_code] == future_hearing_1.title
    response = api_client.get(list_endpoint, {"next_closing": future_hearing_1.close_at.isoformat()})
    data = get_data_from_response(response)
    assert len(data['results']) == 1
    assert data['results'][0]['title'][default_lang_code] == future_hearing_2.title
    response = api_client.get(list_endpoint, {"open": 'true'})
    data = get_data_from_response(response)
    assert len(data['results']) == 2
    assert data['results'][0]['title'][default_lang_code].startswith('Next')
    assert data['results'][1]['title'][default_lang_code].startswith('Next')
    response = api_client.get(list_endpoint, {"open": 'false'})
    data = get_data_from_response(response)
    assert len(data['results']) == 2
    assert data['results'][0]['title'][default_lang_code].startswith('Gone')
    assert data['results'][1]['title'][default_lang_code].startswith('Gone')


@pytest.mark.django_db
def test_8_get_detail_check_properties(api_client, default_hearing):
    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert set(data.keys()) >= {
        'abstract', 'borough', 'close_at', 'closed', 'created_at', 'id', 'labels',
        'n_comments', 'open_at', 'sections', 'servicemap_url',
        'title', 'organization'
    }


@pytest.mark.django_db
def test_8_get_detail_title(api_client):
    hearing = Hearing(title='Lorem Ipsum Title')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['title'][default_lang_code] == hearing.title


@pytest.mark.django_db
def test_8_get_detail_borough(api_client):
    hearing = Hearing(borough='Itäinen', title="is required")
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['borough'][default_lang_code] == hearing.borough


@pytest.mark.django_db
def test_8_get_detail_n_comments(api_client):
    hearing = Hearing(n_comments=1, title='title')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['n_comments'] == hearing.n_comments


@pytest.mark.django_db
def test_8_get_detail_closing_time(api_client):
    hearing = Hearing(title='title')
    hearing.save()

    response = api_client.get(get_detail_url(hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert_datetime_fuzzy_equal(data['close_at'], hearing.close_at)


@pytest.mark.django_db
def test_8_get_detail_labels(api_client):
    hearing = Hearing(title='')
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
    assert {'id': label_one.id, 'label': {'en': label_one.label}} in data['labels']


@pytest.mark.django_db
def test_8_get_detail_organization(api_client, default_hearing, default_organization):
    default_hearing.organization = default_organization
    default_hearing.save()
    response = api_client.get(get_detail_url(default_hearing.id))

    data = get_data_from_response(response)

    assert 'results' not in data
    assert data['organization'] == default_organization.name


@pytest.mark.django_db
def test_get_detail_contact_person(api_client, default_hearing, default_organization, contact_person):
    response = api_client.get(get_detail_url(default_hearing.id))
    data = get_data_from_response(response)

    cp = data['contact_persons'][0]
    assert cp['name'] == contact_person.name
    assert cp['title'][default_lang_code] == contact_person.title
    assert cp['phone'] == contact_person.phone
    assert cp['email'] == contact_person.email
    assert cp['organization'] == default_organization.name


@pytest.mark.django_db
def test_7_get_detail_servicemap(api_client):
    hearing = Hearing(
        servicemap_url='http://servicemap.hel.fi/embed/?bbox=60.19276,24.93300,60.19571,24.94513&city=helsinki',
        title='Title is required',
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
def test_get_hearing_check_section_type(api_client, default_hearing):
    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    data = get_data_from_response(response)
    main = data['sections'][0]
    assert main['type'] == InitialSectionType.MAIN
    assert main['type_name_singular'] == 'pääosio'
    assert main['type_name_plural'] == 'pääosiot'


@pytest.mark.django_db
def test_hearing_stringification(random_hearing):
    assert force_text(random_hearing) == random_hearing.title


@pytest.mark.django_db
def test_admin_can_see_unpublished_and_published(api_client, john_doe_api_client, john_smith_api_client, default_organization):
    hearings = create_hearings(5, organization=default_organization)
    not_own_organization = OrganizationFactory()
    own_organization = OrganizationFactory()
    john_smith_api_client.user.admin_organizations.add(own_organization)
    unpublished_hearing = hearings[0]
    unpublished_hearing.published = False  # This one should be visible to admin only
    unpublished_hearing.save()
    hearing_outside_organization = hearings[1]
    hearing_outside_organization.organization = None  # This one should be visible to J. Doe too, n'est ce pas?
    hearing_outside_organization.save()
    future_hearing = hearings[2]
    future_hearing.open_at = now() + datetime.timedelta(days=1)  # This one should be visible to admin only
    future_hearing.close_at = now() + datetime.timedelta(days=2)
    future_hearing.save()
    not_own_organization_unpublished_hearing = hearings[3]
    not_own_organization_unpublished_hearing.published = False
    not_own_organization_unpublished_hearing.organization = not_own_organization
    not_own_organization_unpublished_hearing.save()
    own_organization_unpublished_hearing = hearings[4]
    own_organization_unpublished_hearing.published = False
    own_organization_unpublished_hearing.organization = own_organization
    own_organization_unpublished_hearing.save()
    data = get_data_from_response(api_client.get(list_endpoint))
    assert len(data['results']) == 1  # Can't see them as anon
    data = get_data_from_response(john_doe_api_client.get(list_endpoint))
    assert len(data['results']) == 1  # Can't see them as registered
    data = get_data_from_response(john_smith_api_client.get(list_endpoint))
    assert len(data['results']) == 4  # Can all as admin, except unpublished from other orgs
    assert len([1 for h in data['results'] if not h["published"]]) == 2  # Two unpublished


@pytest.mark.django_db
def test_can_see_unpublished_with_preview_code(api_client):
    hearings = create_hearings(1)
    unpublished_hearing = hearings[0]
    unpublished_hearing.published = False
    unpublished_hearing.open_at = now() + datetime.timedelta(hours=1)
    unpublished_hearing.save()
    get_data_from_response(api_client.get(get_detail_url(unpublished_hearing.id)), status_code=404)
    preview_url = "{}?preview={}".format(get_detail_url(unpublished_hearing.id), unpublished_hearing.preview_code)
    get_data_from_response(api_client.get(preview_url), status_code=200)


@pytest.mark.django_db
def test_can_see_published_with_preview_code(api_client):
    hearings = create_hearings(1)
    published_hearing = hearings[0]
    published_hearing.published = True
    published_hearing.open_at = now() + datetime.timedelta(hours=1)
    published_hearing.save()
    get_data_from_response(api_client.get(get_detail_url(published_hearing.id)), status_code=404)
    preview_url = "{}?preview={}".format(get_detail_url(published_hearing.id), published_hearing.preview_code)
    response = api_client.get(preview_url)
    get_data_from_response(response, status_code=200)


@pytest.mark.django_db
def test_preview_code_in_unpublished(john_smith_api_client, default_organization):
    hearings = create_hearings(1, organization=default_organization)
    unpublished_hearing = hearings[0]
    unpublished_hearing.published = False
    unpublished_hearing.save()
    hearing_data = get_data_from_response(john_smith_api_client.get(get_detail_url(unpublished_hearing.pk)), status_code=200)
    assert hearing_data['preview_url'] == unpublished_hearing.preview_url


@pytest.mark.django_db
def test_preview_code_not_in_published(john_smith_api_client, default_organization):
    hearings = create_hearings(1, organization=default_organization)
    published_hearing = hearings[0]
    published_hearing.published = True
    published_hearing.open_at = now() - datetime.timedelta(hours=1)
    published_hearing.save()
    hearing_data = get_data_from_response(john_smith_api_client.get(get_detail_url(published_hearing.pk)), status_code=200)
    print(hearing_data)
    assert hearing_data['preview_url'] == None


@pytest.mark.django_db
@pytest.mark.parametrize('geometry_fixture_name', [
    'geojson_point',
    'geojson_multipoint',
    'geojson_polygon',
    'geojson_polygon_with_hole',
    'geojson_multipolygon',
    'geojson_linestring',
    'geojson_multilinestring',
])
def test_hearing_geojson_feature(request, john_smith_api_client, valid_hearing_json, geometry_fixture_name):
    geometry = request.getfixturevalue(geometry_fixture_name)
    feature = get_feature_with_geometry(geometry)
    valid_hearing_json['geojson'] = feature
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    hearing_data = get_data_from_response(response, status_code=201)
    hearing = Hearing.objects.get(pk=hearing_data['id'])
    hearing_geometry = json.loads(hearing.geometry.geojson)
    assert hearing.geojson == feature
    assert hearing_data['geojson'] == feature
    assert hearing_data['geojson']['geometry'] == hearing_geometry
    geojson_data = get_data_from_response(john_smith_api_client.get(get_detail_url(hearing.pk), {'format': 'geojson'}))
    assert geojson_data['id'] == hearing.pk
    assert_common_keys_equal(geojson_data['geometry'], feature['geometry'])
    assert_common_keys_equal(geojson_data['properties'], feature['properties'])
    map_data = get_data_from_response(john_smith_api_client.get(list_endpoint + 'map/'))
    assert map_data['results'][0]['geojson'] == feature


@pytest.mark.django_db
@pytest.mark.parametrize('geometry_fixture_name', [
    'geojson_point',
    'geojson_multipoint',
    'geojson_polygon',
    'geojson_polygon_with_hole',
    'geojson_multipolygon',
    'geojson_linestring',
    'geojson_multilinestring',
])
def test_hearing_geojson_geometry_only(request, john_smith_api_client, valid_hearing_json, geometry_fixture_name):
    geojson_geometry = request.getfixturevalue(geometry_fixture_name)
    valid_hearing_json['geojson'] = geojson_geometry
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    hearing_data = get_data_from_response(response, status_code=201)
    hearing = Hearing.objects.get(pk=hearing_data['id'])
    hearing_geometry = json.loads(hearing.geometry.geojson)
    assert hearing.geojson == geojson_geometry
    assert hearing_data['geojson'] == geojson_geometry
    assert hearing_data['geojson'] == hearing_geometry
    geojson_data = get_data_from_response(john_smith_api_client.get(get_detail_url(hearing.pk), {'format': 'geojson'}))
    assert geojson_data['id'] == hearing.pk
    assert_common_keys_equal(geojson_data['geometry'], geojson_geometry)
    assert_common_keys_equal(geojson_data['properties'], hearing_data)
    map_data = get_data_from_response(john_smith_api_client.get(list_endpoint + 'map/'))
    assert map_data['results'][0]['geojson'] == geojson_geometry


@pytest.mark.django_db
@pytest.mark.parametrize('geojson_fixture_name', [
    'geojson_geometrycollection',
    'geojson_featurecollection',
])
def test_hearing_geojson_unsupported_types(request, john_smith_api_client, valid_hearing_json, geojson_fixture_name):
    geojson = request.getfixturevalue(geojson_fixture_name)
    valid_hearing_json['geojson'] = geojson
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert data['geojson'][0].startswith('Invalid geojson format. Type is not supported.')


@pytest.mark.django_db
def test_hearing_bbox_filtering(
        request, api_client, random_hearing, geojson_feature,
        bbox_containing_feature, bbox_containing_geometries, bbox_all):
    random_hearing.geojson = geojson_feature
    random_hearing.save()
    containing_query = '?bbox=%s' % bbox_containing_feature
    not_containing_query = '?bbox=%s' % bbox_containing_geometries
    bbox_all_query = '?bbox=%s' % bbox_all
    data = get_data_from_response(api_client.get(list_endpoint + containing_query))
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == random_hearing.pk
    data = get_data_from_response(api_client.get(list_endpoint + not_containing_query))
    assert len(data['results']) == 0
    data = get_data_from_response(api_client.get(list_endpoint + bbox_all_query))
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == random_hearing.pk


@pytest.mark.django_db
@pytest.mark.parametrize('geometry_fixture_name', [
    'geojson_point',
    'geojson_multipoint',
    'geojson_polygon',
    'geojson_polygon_with_hole',
    'geojson_multipolygon',
    'geojson_linestring',
    'geojson_multilinestring',
])
def test_hearing_bbox_filtering_geometries(
        request, api_client, random_hearing,
        geometry_fixture_name, bbox_containing_geometries):
    geometry = request.getfixturevalue(geometry_fixture_name)
    feature = get_feature_with_geometry(geometry)
    random_hearing.geojson = feature
    random_hearing.save()
    bbox_query = '?bbox=%s' % bbox_containing_geometries
    data = get_data_from_response(api_client.get(list_endpoint + bbox_query))
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == random_hearing.pk


@pytest.mark.django_db
def test_hearing_copy(default_hearing, random_label):
    Section.objects.create(
        type=SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO),
        hearing=default_hearing,
        title='',
        abstract='',
        content='',
    )
    default_hearing.labels.add(random_label)
    new_hearing = copy_hearing(default_hearing, published=False, title='overridden title')
    assert Hearing.objects.count() == 2

    # check that num of sections and images has doubled
    assert Section.objects.count() == 7  # 3 sections per hearing + 1 old closure info section
    assert SectionImage.objects.count() == 18  # 3 section images per non closure section

    # check that num of labels hasn't changed
    assert Label.objects.count() == 1

    # check hearing model fields
    for field_name in ('open_at', 'close_at', 'force_closed', 'borough',
                       'servicemap_url', 'geojson'):
        assert getattr(new_hearing, field_name) == getattr(default_hearing, field_name)

    # check overridden fields
    assert new_hearing.published is False
    assert new_hearing.title == 'overridden title'

    assert new_hearing.sections.count() == 3
    for i, new_section in enumerate(new_hearing.sections.all().order_by('translations__abstract'), 1):
        # each section should have 3 images, the correct abstract and no comments
        new_section.images.count() == 3
        assert new_section.abstract == 'Section %d abstract' % i
        assert new_section.comments.count() == 0
        assert new_section.n_comments == 0

    assert random_label in new_hearing.labels.all()

    # there should be no comments for the new hearing
    assert new_hearing.n_comments == 0

    # closure info section should not have been copied
    assert not new_hearing.sections.filter(type__identifier=InitialSectionType.CLOSURE_INFO).exists()


@pytest.mark.parametrize('client, expected', [
    ('api_client', False),
    ('jane_doe_api_client', False),
    ('admin_api_client', True)
])
@pytest.mark.django_db
def test_hearing_open_at_filtering(default_hearing, request, client, expected):
    api_client = request.getfixturevalue(client)

    default_hearing.open_at = now() + datetime.timedelta(hours=1)
    default_hearing.save(update_fields=('open_at',))

    response = api_client.get(list_endpoint)
    data = get_data_from_response(response)
    ids = [hearing['id'] for hearing in data['results']]
    assert bool(default_hearing.id in ids) == expected

    expected_code = (200 if expected else 404)
    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    assert response.status_code == expected_code


@pytest.mark.django_db
def test_slug():
    hearings = create_hearings(3)
    hearing = hearings[0]

    slug = hearing.slug
    assert slug == 'test-purpose-created-hearing-title-1'

    # test that saving won't autopopulate the slug
    hearing.title = 'foo'
    hearing.save()
    hearing.refresh_from_db()
    assert hearing.slug == slug

    hearings[1].slug = 'slug'
    hearings[1].save()
    hearings[2].slug = 'slug'  # this becomes slug-2
    hearings[2].deleted = True
    hearings[2].save()

    # slug collision with 2 hearings, one of those is also deleted
    hearing.slug = 'slug'
    hearing.save()
    hearing.refresh_from_db()
    assert hearing.slug == 'slug-3'


@pytest.mark.django_db
def test_access_hearing_using_slug(api_client, default_hearing):
    default_hearing.slug = 'new-slug'
    default_hearing.save()

    endpoint = list_endpoint + 'new-slug/'
    data = get_data_from_response(api_client.get(endpoint))
    assert data['id'] == default_hearing.id

    endpoint += 'sections/'
    get_data_from_response(api_client.get(endpoint))

    endpoint += '%s/' % default_hearing.sections.all()[0].id
    get_data_from_response(api_client.get(endpoint))


@pytest.mark.django_db
def test_abstract_is_populated_from_main_abstract(api_client, default_hearing):
    main_section = default_hearing.get_main_section()
    main_section.abstract = 'very abstract'
    main_section.save()

    response = api_client.get(list_endpoint)
    data = get_data_from_response(response)
    assert data['results'][0]['abstract'] == {default_lang_code: 'very abstract'}

    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    data = get_data_from_response(response)
    assert data['abstract'] == {default_lang_code: 'very abstract'}


@pytest.mark.parametrize('updates, filters, expected_count', [
    ({'open_at': now()-datetime.timedelta(days=1)}, {'open_at_lte': now()}, 1),
    ({'open_at': now()-datetime.timedelta(days=1)}, {'open_at_gt': now()}, 0),
    ({'open_at': now()+datetime.timedelta(days=1)}, {'open_at_lte': now()}, 0),
    ({'open_at': now()+datetime.timedelta(days=1)}, {'open_at_gt': now()}, 1),
    ({'published': True}, {'published': False}, 0),
    ({'published': False}, {'published': False}, 1),
])
@pytest.mark.django_db
def test_hearing_filters(admin_api_client, default_hearing, updates, filters, expected_count):
    Hearing.objects.filter(id=default_hearing.id).update(**updates)

    response = admin_api_client.get(list_endpoint, filters)
    data = get_data_from_response(response)
    assert data['count'] == expected_count


def assert_hearing_equals(data, posted, user, create=True):
    # posted contact person data need only contain the id, even though the api returns all fields
    persons_included = data.pop('contact_persons')
    persons_posted = posted.pop('contact_persons')
    for person_included, person_posted in zip(persons_included, persons_posted):
        assert_common_keys_equal(person_included, person_posted)
    posted.pop('id')
    created_at = data.pop('created_at')
    if create:
        assert_datetime_fuzzy_equal(created_at, now())
    organization = data.pop('organization')
    assert organization == user.get_default_organization().name
    assert len(data['sections']) == len(posted['sections'])
    sections_created = data.pop('sections')
    sections_posted = posted.pop('sections')
    assert_common_keys_equal(data, posted)
    for section_created, section_posted in zip(sections_created, sections_posted):
        section_created.pop('id', None)
        created_at = section_created.pop('created_at')
        if create:
            assert_datetime_fuzzy_equal(created_at, now())
            images = section_created.pop('images')
            assert len(images) == len(section_posted['images'])
            for created_image, posted_image in zip(images, section_posted['images']):
                assert created_image['title']['en'] == posted_image['title']['en']
            files = section_created.pop('files')
            if 'files' in section_posted:
                assert len(files) == len(section_posted['files'])
                for created_file, posted_file in zip (files, section_posted['files']):
                    assert created_file['title']['en'] == posted_file['title']['en']
        assert_common_keys_equal(section_created, section_posted)


@pytest.mark.django_db
def test_POST_hearing_anonymous_user(valid_hearing_json, api_client):
    response = api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=401)
    assert data == {'detail': 'Authentication credentials were not provided.'}


@pytest.mark.django_db
def test_POST_hearing_unauthorized_user(valid_hearing_json, john_doe_api_client):
    response = john_doe_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {"status": "User without organization cannot POST hearings."}


# Test that a user can POST a hearing
@pytest.mark.django_db
def test_POST_hearing(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert data['organization'] == john_smith_api_client.user.get_default_organization().name
    assert_hearing_equals(data, valid_hearing_json, john_smith_api_client.user)


@pytest.mark.django_db
def test_POST_hearing_no_title(valid_hearing_json, john_smith_api_client):
    del valid_hearing_json['title']
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'Title is required at least in one locale' in data['non_field_errors']


@pytest.mark.django_db
def test_POST_hearing_with_new_project(valid_hearing_json_with_project, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json_with_project, format='json')
    data = get_data_from_response(response, status_code=201)
    assert data['organization'] == john_smith_api_client.user.get_default_organization().name
    assert 'project' in data
    project = data['project']
    assert 'phases' in project
    assert len(data['project']['phases']) == 3
    assert project['title'] == valid_hearing_json_with_project['project']['title']
    projects = Project.objects.all()
    assert projects.exists() is True
    project = projects.first()
    assert project.phases.count() == 3


@pytest.mark.django_db
def test_POST_hearing_with_null_project(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['project'] = None
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert data['organization'] == john_smith_api_client.user.get_default_organization().name
    assert_hearing_equals(data, valid_hearing_json, john_smith_api_client.user)


@pytest.mark.django_db
def test_POST_hearing_with_existing_project(valid_hearing_json, default_project, default_project_json, john_smith_api_client):
    valid_hearing_json.update(default_project_json)
    default_project_phase_ids = set(default_project.phases.values_list('id', flat=True))
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert 'project' in data
    project = data['project']
    assert project['id'] == default_project.pk
    assert 'phases' in project
    assert len(data['project']['phases']) == 3
    assert default_project.phases.count() == 3
    for phase in project['phases']:
        assert phase['id'] in default_project_phase_ids, "Phase ids return must match original default_project phase ids"


@pytest.mark.django_db
def test_POST_hearing_with_updated_project(valid_hearing_json, default_project, default_project_json, john_smith_api_client):
    updated_title = 'updated title'
    default_project_json['project']['title'] = {'en': updated_title}
    default_project_json['project']['phases'][0]['title'] = {'en': updated_title}
    updated_phase_id = default_project_json['project']['phases'][0]['id']
    default_project_json['project']['phases'].append({
        'title': {'en': 'new title'},
        'description': {'en': 'new description'},
        'schedule': {'en': 'new schedule'},
        'is_active': False,
    })

    valid_hearing_json.update(default_project_json)
    default_project_phase_ids = set(default_project.phases.values_list('id', flat=True))
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert 'project' in data
    project = data['project']
    assert project['id'] == default_project.pk
    assert 'phases' in project
    assert len(project['phases']) == 4
    assert default_project.phases.count() == 4
    for ordering, phase in enumerate(project['phases']):
        if ordering == 0:
            assert phase['id'] == updated_phase_id
            assert phase['title']['en'] == updated_title
        if ordering == 3:
            assert phase['title']['en'] == 'new title'
            assert phase['description']['en'] == 'new description'
            assert phase['schedule']['en'] == 'new schedule'


@pytest.mark.django_db
def test_POST_hearing_with_updated_project_add_translation(valid_hearing_json, default_project, default_project_json, john_smith_api_client):
    # replace English with Finnish translation in project
    default_project_json['project']['title'] = {'fi': 'Oletusprojekti'}
    default_project_json['project']['phases'][2]['title'] = {'fi': 'Vaihe 3'}
    valid_hearing_json.update(default_project_json)
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert 'project' in data
    project = data['project']
    assert project['id'] == default_project.pk
    assert 'phases' in project
    assert len(project['phases']) == 3
    assert default_project.phases.count() == 3
    # check that the original translations remain even if they are not posted!
    assert project['title']['en'] == 'Default project'
    assert project['title']['fi'] == 'Oletusprojekti'
    assert project['phases'][2]['title']['en'] == 'Phase 3'
    assert project['phases'][2]['title']['fi'] == 'Vaihe 3'


@pytest.mark.django_db
def test_POST_hearing_with_updated_project_delete_phase(valid_hearing_json, default_project, default_project_json, john_smith_api_client):
    deleted_phase_id = default_project_json['project']['phases'][2]['id']
    del(default_project_json['project']['phases'][2])
    valid_hearing_json.update(default_project_json)
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    project = data['project']
    assert len(data['project']['phases']) == 2
    assert default_project.phases.count() == 2
    assert deleted_phase_id not in (p['id'] for p in project['phases'])
    assert deleted_phase_id not in default_project.phases.values_list('pk', flat=True)


@pytest.mark.django_db
def test_POST_hearing_delete_phase_with_hearings(default_hearing, valid_hearing_json, default_project, default_project_json, john_smith_api_client):
    initial_default_project_phase_count = default_project.phases.count()
    default_hearing_phase = default_hearing.project_phase
    deleted_phase_data = None
    for idx, phase in enumerate(default_project_json['project']['phases']):
        if phase['id'] == default_hearing_phase.pk:
            deleted_phase_data = default_project_json['project']['phases'].pop(idx)
    assert deleted_phase_data is not None, "Test fixture error: Default hearing should contain a project phase from default project"
    default_project_json['project']['phases'][0]['is_active'] = True
    valid_hearing_json.update(default_project_json)
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    assert response.status_code == 400, "Should not be able to delete phase with default_hearing associated to it"
    assert default_project.phases.count() == initial_default_project_phase_count, "Project phase count should not change"
    deleted_phase = ProjectPhase.objects.everything().get(pk=deleted_phase_data['id'])
    assert deleted_phase.deleted is False, "Phase should not be soft-deleted"


@pytest.mark.django_db
def test_POST_hearing_no_title_locale(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['title'] = {'fi': ''}
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'Title is required at least in one locale' in data['non_field_errors']


@pytest.mark.django_db
def test_PUT_hearing_no_title(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    del data1['title']
    response = john_smith_api_client.put('%s%s/' % (endpoint, data1['id']), data=data1, format='json')
    data2 = get_data_from_response(response, status_code=400)
    assert 'Title is required at least in one locale' in data2['non_field_errors']


@pytest.mark.django_db
def test_PUT_hearing_no_title_locale(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    data1['title'] = {'fi': ''}
    response = john_smith_api_client.put('%s%s/' % (endpoint, data1['id']), data=data1, format='json')
    data2 = get_data_from_response(response, status_code=400)
    assert 'Title is required at least in one locale' in data2['non_field_errors']


@pytest.mark.django_db
def test_PATCH_hearing_no_title(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data1['id']), data={}, format='json')
    get_data_from_response(response, status_code=200)


@pytest.mark.django_db
def test_PATCH_hearing_no_title_locale(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    data = {'title': {'fi': ''}}
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data1['id']), data=data, format='json')
    data2 = get_data_from_response(response, status_code=400)
    assert 'Title is required at least in one locale' in data2['non_field_errors']


@pytest.mark.django_db
def test_POST_hearing_no_slug(valid_hearing_json, john_smith_api_client):
    del valid_hearing_json['slug']
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'This field is required' in data['slug'][0]
    # With empty value
    valid_hearing_json['slug'] = ''
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'This field may not be blank' in data['slug'][0]


@pytest.mark.django_db
def test_POST_hearing_invalid_slug(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['slug'] = 'foo-bar-´'
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'Enter a valid "slug"' in data['slug'][0]


@pytest.mark.django_db
def test_PUT_hearing_no_slug(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    del data1['slug']
    response = john_smith_api_client.put('%s%s/' % (endpoint, data1['id']), data=data1, format='json')
    data2 = get_data_from_response(response, status_code=400)
    assert 'This field is required' in data2['slug'][0]
    # with empty value
    data1['slug'] = ''
    response = john_smith_api_client.put('%s%s/' % (endpoint, data1['id']), data=data1, format='json')
    data3 = get_data_from_response(response, status_code=400)
    assert 'This field may not be blank' in data3['slug'][0]


@pytest.mark.django_db
def test_PATCH_hearing_no_slug(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data1 = get_data_from_response(response, status_code=201)
    # first with empty data with no slug key
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data1['id']), data={}, format='json')
    get_data_from_response(response, status_code=200)
    # with empty value
    data = {'slug': ''}
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data1['id']), data=data, format='json')
    data2 = get_data_from_response(response, status_code=400)
    assert 'This field may not be blank' in data2['slug'][0]


# Test that a user cannot POST a hearing without the translation
@pytest.mark.django_db
def test_POST_hearing_untranslated(valid_hearing_json, john_smith_api_client):
    valid_hearing_json["title"] = valid_hearing_json["title"]["en"]
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'Not a valid translation format. Expecting {"lang_code": %s}' % valid_hearing_json['title'] in data['title']


# Test that a user cannot POST a hearing with an unsupported language
@pytest.mark.django_db
def test_POST_hearing_unsupported_language(valid_hearing_json, john_smith_api_client):
    valid_hearing_json["title"]["fr"] = valid_hearing_json["title"]["en"]
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert "fr is not a supported languages (['en', 'fi', 'sv'])" in data['title']


# Test that an anonymous user fails to update a hearing
@pytest.mark.django_db
def test_PUT_hearing_anonymous_user(valid_hearing_json, api_client, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    response = api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=401)
    assert data == {'detail': 'Authentication credentials were not provided.'}


# Test that a user without organization fails to update a hearing
@pytest.mark.django_db
def test_PUT_hearing_unauthorized_user(valid_hearing_json, john_doe_api_client, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    response = john_doe_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {'status': 'User without organization cannot PUT hearings.'}


# Test that a user cannot update a hearing from another organization
@pytest.mark.django_db
def test_PUT_hearing_other_organization_hearing(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    hearing = Hearing.objects.first()
    hearing.organization = Organization.objects.create(name='The department for squirrel warfare')
    hearing.save()
    _update_hearing_data(data)
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {'detail': "Only organization admins can update organization hearings."}


# Test that a user can update a hearing
@pytest.mark.django_db
def test_PUT_hearing_success(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    created_at = data['created_at']
    _update_hearing_data(data)
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=200)
    assert updated_data['created_at'] == created_at
    assert_hearing_equals(data, updated_data, john_smith_api_client.user, create=False)


# Test that a user cannot PUT a hearing without the translation
@pytest.mark.django_db
def test_PUT_hearing_untranslated(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    data["title"] = data["title"]["en"]
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=400)
    assert 'Not a valid translation format. Expecting {"lang_code": %s}' % data['title'] in updated_data['title']


# Test that a user cannot PUT a hearing with an unsupported language
@pytest.mark.django_db
def test_PUT_hearing_unsupported_language(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    data["title"]["fr"] = data["title"]["en"]
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=400)
    assert "fr is not a supported languages (['en', 'fi', 'sv'])" in data['title']


# Test that a user can PUT a hearing with less translations
@pytest.mark.django_db
def test_PUT_hearing_remove_translation(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    data["title"].pop("sv")
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=200)
    assert updated_data['title'].get('sv') is None
    assert updated_data['title']['en'] == data['title']['en']
    assert updated_data['title']['fi'] == data['title']['fi']

# Test that a user cannot update a hearing having no organization
@pytest.mark.django_db
def test_PUT_hearing_no_organization(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    _update_hearing_data(data)
    hearing = Hearing.objects.filter(id=data['id']).first()
    hearing.organization = None
    hearing.save()
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {'detail': "Only organization admins can update organization hearings."}


# Test that a user cannot steal an section while updating a hearing
@pytest.mark.django_db
def test_PUT_hearing_steal_section(valid_hearing_json, john_smith_api_client, default_hearing):
    hearing = default_hearing
    hearing.save()
    other_hearing_section_id = hearing.get_main_section().id
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    data['sections'][0]['id'] = other_hearing_section_id
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=400)
    assert ('The Hearing does not have a section with ID %s' % other_hearing_section_id) in updated_data['sections']


# Test that hearing sections ordering is saved when updating sections
@pytest.mark.django_db
def test_PUT_hearing_section_ordering(valid_hearing_json, john_smith_api_client, default_hearing):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    reordered_sections = [
        data['sections'][0],
        data['sections'][2],
        data['sections'][1],
    ]
    data['sections'] = reordered_sections
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=200)
    assert reordered_sections[0]['id'] == updated_data['sections'][0]['id']
    assert reordered_sections[1]['id'] == updated_data['sections'][1]['id']
    assert reordered_sections[2]['id'] == updated_data['sections'][2]['id']


# Test that the section are deleted upon updating the hearing
@pytest.mark.django_db
def test_PUT_hearing_delete_sections(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)

    closure_section_id = data['sections'][0]['id']
    part_section_id = data['sections'][2]['id']
    image_id = data['sections'][2]['images'][0]['id']
    created_at = data['created_at']
    data['sections'] = [data['sections'][1], ]
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    updated_data = get_data_from_response(response, status_code=200)
    assert updated_data['created_at'] == created_at
    assert_hearing_equals(data, updated_data, john_smith_api_client.user, create=False)
    closure_section = Section.objects.deleted().filter(id=closure_section_id).first()
    part_section = Section.objects.deleted().filter(id=part_section_id).first()
    image = SectionImage.objects.deleted().filter(id=image_id).first()
    assert closure_section
    assert part_section
    assert image


# Test that a hearing cannot be created without 1 main section
@pytest.mark.django_db
def test_POST_hearing_no_main_section(valid_hearing_json, john_smith_api_client):
    del(valid_hearing_json['sections'][1])
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing must have exactly one main section' in data['sections']


# Test that a hearing cannot be created with more than 1 main section
@pytest.mark.django_db
def test_POST_hearing_two_main_sections(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['sections'][2]['type'] = 'main'
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing must have exactly one main section' in data['sections']


# Test that a hearing cannot be created with more than 1 closure-info section
@pytest.mark.django_db
def test_POST_hearing_two_closure_sections(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['sections'][2]['type'] = 'closure-info'
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing cannot have more than one closure info sections' in data['sections']


# Test that a hearing cannot be updated without 1 main section
@pytest.mark.django_db
def test_PUT_hearing_no_main_section(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    data['sections'][1]['type'] = 'part'
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing must have exactly one main section' in data['sections']


# Test that a hearing cannot be updated with more than 1 main section
@pytest.mark.django_db
def test_PUT_hearing_two_main_sections(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    data['sections'][2]['type'] = 'main'
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing must have exactly one main section' in data['sections']


# Test that a hearing cannot be updated with more than 1 closure-info section
@pytest.mark.django_db
def test_PUT_hearing_two_closure_sections(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    data['sections'][2]['type'] = 'closure-info'
    response = john_smith_api_client.put('%s%s/' % (endpoint, data['id']), data=data, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'A hearing cannot have more than one closure info sections' in data['sections']


# Test that an anonymous user cannot GET an unpublished hearing
@pytest.mark.django_db
def test_GET_unpublished_hearing_anon_user(unpublished_hearing_json, john_smith_api_client, api_client):
    response = john_smith_api_client.post(endpoint, data=unpublished_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    response = api_client.get('%s%s/' % (endpoint, data['id']), format='json')
    data = get_data_from_response(response, status_code=404)
    response = api_client.get(endpoint, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data['count'] == 0


# Test that a regular user cannot GET an unpublished hearing
@pytest.mark.django_db
def test_GET_unpublished_hearing_regular_user(unpublished_hearing_json, john_smith_api_client, john_doe_api_client):
    response = john_smith_api_client.post(endpoint, data=unpublished_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    response = john_doe_api_client.get('%s%s/' % (endpoint, data['id']), format='json')
    data = get_data_from_response(response, status_code=404)
    response = john_doe_api_client.get(endpoint, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data['count'] == 0


# Test that a user cannot GET an unpublished hearing from another organization
@pytest.mark.django_db
def test_GET_unpublished_hearing_other_org(unpublished_hearing_json, john_smith_api_client, john_doe_api_client):
    response = john_smith_api_client.post(endpoint, data=unpublished_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    hearing = Hearing.objects.filter(id=data['id']).first()
    hearing.organization = Organization.objects.create(name='The department for squirrel warfare')
    hearing.save()
    response = john_smith_api_client.get('%s%s/' % (endpoint, data['id']), format='json')
    data = get_data_from_response(response, status_code=404)
    response = john_smith_api_client.get(endpoint, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data['count'] == 0


# Test that a user cannot GET unpublished hearing without organization
@pytest.mark.django_db
def test_GET_unpublished_hearing_no_organization(unpublished_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=unpublished_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    hearing = Hearing.objects.filter(id=data['id']).first()
    hearing.organization = None
    hearing.save()
    response = john_smith_api_client.get('%s%s/' % (endpoint, data['id']), format='json')
    data = get_data_from_response(response, status_code=404)
    response = john_smith_api_client.get(endpoint, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data['count'] == 0


# Test that a user can GET unpublished hearing from his organization
@pytest.mark.django_db
def test_GET_unpublished_hearing(unpublished_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=unpublished_hearing_json, format='json')
    data_created = get_data_from_response(response, status_code=201)
    assert data_created['published'] == False
    response = john_smith_api_client.get('%s%s/' % (endpoint, data_created['id']), format='json')
    data = get_data_from_response(response, status_code=200)
    response = john_smith_api_client.get(endpoint, format='json')
    list_data = get_data_from_response(response, status_code=200)
    assert list_data['count'] == 1
    assert list_data['results'][0]['id'] == data['id']
    assert_hearing_equals(data_created, data, john_smith_api_client.user)


@pytest.mark.django_db
def test_PATCH_hearing(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['close_at'] = datetime.datetime.now() + datetime.timedelta(days=1)
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert data['closed'] == False
    before = datetime.datetime.now() - datetime.timedelta(days=1)
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data['id']), data={'close_at': before}, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data['closed'] == True


# Test that a user cannot PATCH a hearing without the translation
@pytest.mark.django_db
def test_PATCH_hearing_untranslated(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    patch_data = {"title": data["title"]["en"]}
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data['id']), data=patch_data, format='json')
    updated_data = get_data_from_response(response, status_code=400)
    assert 'Not a valid translation format. Expecting {"lang_code": %s}' % patch_data['title'] in updated_data['title']


# Test that a user cannot PATCH a hearing with an unsupported language
@pytest.mark.django_db
def test_PATCH_hearing_unsupported_language(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    patch_data = {"title": {"fr":  data["title"]["en"]}}
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data['id']), data=patch_data, format='json')
    data = get_data_from_response(response, status_code=400)
    assert "fr is not a supported languages (['en', 'fi', 'sv'])" in data['title']


# Test that a user can PATCH a translation
@pytest.mark.django_db
def test_PATCH_hearing_patch_language(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    patch_data = {"title": {"fi":  data["title"]["en"]}}
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data['id']), data=patch_data, format='json')
    data = get_data_from_response(response, status_code=200)
    assert data["title"]["fi"] == valid_hearing_json["title"]["en"]
    assert data["title"]["en"] == valid_hearing_json["title"]["en"]
    assert data["title"]["sv"] == valid_hearing_json["title"]["sv"]


@pytest.mark.django_db
def test_PATCH_hearing_update_section(valid_hearing_json, john_smith_api_client):
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    response = john_smith_api_client.patch('%s%s/' % (endpoint, data['id']), data={'sections': [{
        'id': '3adn7MGkOJ8e4NlhsElxKggbfdmrSmVE',
        'title': 'New title',
    }]}, format='json')
    data = get_data_from_response(response, status_code=400)
    assert 'Sections cannot be updated by PATCHing the Hearing' in data['sections']


@pytest.mark.django_db
def test_DELETE_unpublished_hearing(valid_hearing_json, john_smith_api_client):
    valid_hearing_json['published'] = False
    response = john_smith_api_client.post(endpoint, data=valid_hearing_json, format='json')
    data = get_data_from_response(response, status_code=201)
    response = john_smith_api_client.delete('%s%s/' % (endpoint, data['id']), format='json')
    assert response.status_code == 200
    response = john_smith_api_client.get('%s%s/' % (endpoint, data['id']), format='json')
    assert response.status_code == 404


@pytest.mark.django_db
def test_DELETE_unpublished_hearing_with_comments(default_hearing, john_smith_api_client):
    default_hearing.published = False
    default_hearing.save()
    response = john_smith_api_client.delete('%s%s/' % (endpoint, default_hearing.pk), format='json')
    data = get_data_from_response(response, status_code=403)
    assert 'Cannot DELETE hearing with comments.' in data['status']


@pytest.mark.django_db
def test_DELETE_published_hearing(default_hearing, john_smith_api_client):
    response = john_smith_api_client.delete('%s%s/' % (endpoint, default_hearing.pk), format='json')
    data = get_data_from_response(response, status_code=403)
    assert 'Cannot DELETE published hearing.' in data['status']


@pytest.mark.django_db
def test_get_project_data_in_hearing(default_hearing, api_client):
    endpoint = list_endpoint + default_hearing.pk + '/'
    data = get_data_from_response(api_client.get(endpoint))
    assert data['id'] == default_hearing.id
    assert 'project' in data, 'hearing should contain project data'
    assert len(data['project']['phases']) == 3, 'default hearing should contain 3 project phases'
    for phase in data['project']['phases']:
        is_active_phase = (phase['id'] == default_hearing.project_phase_id)
        assert phase['has_hearings'] == is_active_phase
        assert phase['is_active'] == is_active_phase
        if is_active_phase:
            assert default_hearing.slug in phase['hearings']

