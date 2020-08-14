import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.timezone import now
from rest_framework.test import APIClient

from democracy.enums import Commenting, InitialSectionType, CommentingMapTools
from democracy.factories.hearing import HearingFactory, LabelFactory
from democracy.models import ContactPerson, Hearing, Label, Project, ProjectPhase, Section, SectionFile, SectionType, Organization
from democracy.tests.utils import FILES, assert_ascending_sequence, create_default_images, create_default_files, get_file_path


default_comment_content = 'I agree with you sir Lancelot. My favourite colour is blue'
red_comment_content = 'Mine is red'
green_comment_content = 'I like green'
default_lang_code = 'en'
default_geojson_geometry = {
        "type": "Point",
        "coordinates": [-104.99404, 39.75621]
    }

def get_feature_with_geometry(geometry):
    return {
        "type": "Feature",
        "properties": {
            "name": "Coors Field",
            "amenity": "Baseball Stadium",
            "popupContent": "This is where the Rockies play!"
        },
        "geometry": geometry
    }

default_geojson_feature = get_feature_with_geometry(default_geojson_geometry)

def pytest_configure():
    # During tests, crypt passwords with MD5. This should make things run faster.
    from django.conf import settings
    settings.PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
        'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
        'django.contrib.auth.hashers.BCryptPasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
        'django.contrib.auth.hashers.CryptPasswordHasher',
    )


@pytest.fixture()
def default_organization():
    return Organization.objects.create(name='The department for squirrel welfare')


@pytest.fixture()
def contact_person(default_organization):
    return ContactPerson.objects.create(
        name='John Contact',
        title='Chief',
        phone='555-555',
        email='john@contact.eu',
        organization=default_organization
    )


@pytest.fixture()
def default_hearing(john_doe, contact_person, default_organization, default_project):
    """
    Fixture for a "default" hearing with three sections (one main, two other sections).
    All objects will have the 3 default images attached.
    All objects will allow open commenting.
    All objects will have commenting_map_tools all
    """
    hearing = Hearing.objects.create(
        title='Default test hearing One',
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
        slug='default-hearing-slug',
        organization=default_organization,
        project_phase=default_project.phases.all()[0],
    )
    for x in range(1, 4):
        section_type = (InitialSectionType.MAIN if x == 1 else InitialSectionType.SCENARIO)
        section = Section.objects.create(
            abstract='Section %d abstract' % x,
            hearing=hearing,
            type=SectionType.objects.get(identifier=section_type),
            commenting=Commenting.OPEN,
            commenting_map_tools=CommentingMapTools.ALL
        )
        create_default_images(section)
        create_default_files(section)
        section.comments.create(created_by=john_doe, content=default_comment_content[::-1])
        section.comments.create(created_by=john_doe, content=red_comment_content[::-1])
        section.comments.create(created_by=john_doe, content=green_comment_content[::-1])

    assert_ascending_sequence([s.ordering for s in hearing.sections.all()])

    hearing.contact_persons.add(contact_person)

    return hearing


@pytest.fixture()
def strong_auth_hearing(john_doe, contact_person, default_organization, default_project):
    """
    Fixture for a "strong auth requiring" hearing with one main section.
    Commenting requires strong auth.
    """
    hearing = Hearing.objects.create(
        title='Strong auth test hearing',
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
        slug='strong-auth-hearing-slug',
        organization=default_organization,
        project_phase=default_project.phases.all()[0],
    )

    section_type = InitialSectionType.MAIN
    Section.objects.create(
        abstract='Section abstract for strong auth',
        hearing=hearing,
        type=SectionType.objects.get(identifier=section_type),
        commenting=Commenting.STRONG
    )

    assert_ascending_sequence([s.ordering for s in hearing.sections.all()])
    hearing.contact_persons.add(contact_person)

    return hearing


@pytest.fixture()
def default_project():
    project_data = {
        'title': 'Default project',
        'identifier': '123456'
    }
    project = Project.objects.create(**project_data)
    for i in range(1, 4):
        phase_data = {
            'project': project,
            'title': 'Phase %d' % i,
            'description': 'Phase %d description' % i,
            'schedule': 'Phase %d schedule' % i,
        }
        ProjectPhase.objects.create(**phase_data)
    return project


@pytest.fixture()
def default_label():
    label = Label.objects.create(label='The Label')
    return label


@pytest.fixture()
def random_hearing():
    if not Label.objects.exists():
        LabelFactory()
    return HearingFactory()


@pytest.fixture()
def random_label():
    return LabelFactory()


@pytest.fixture()
def john_doe():
    """
    John Doe is your average registered user.
    """
    user = get_user_model().objects.filter(username="john_doe").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("john_doe", "john@example.com", password="password")
    return user


@pytest.fixture()
def john_doe_api_client(john_doe):
    """
    John Doe is your average registered user; this is his API client.
    """
    api_client = APIClient()
    api_client.force_authenticate(user=john_doe)
    api_client.user = john_doe
    return api_client


@pytest.fixture()
def jane_doe():
    """
    Jane Doe is another average registered user.
    """
    user = get_user_model().objects.filter(username="jane_doe").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("jane_doe", "jane@example.com", password="password")
    return user


@pytest.fixture()
def jane_doe_api_client(jane_doe):
    """
    Jane Doe is another average registered user; this is her API client.
    """
    api_client = APIClient()
    api_client.force_authenticate(user=jane_doe)
    api_client.user = jane_doe
    return api_client

@pytest.fixture()
def stark_doe():
    """
    Stark Doe is another average registered user.
    """
    user = get_user_model().objects.filter(username="stark_doe").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("stark_doe", "stark@example.com", password="password")
    return user


@pytest.fixture()
def stark_doe_api_client(stark_doe):
    """
    Stark Doe is another average registered user; this is his API client.
    Stark uses strong authentication.
    """
    api_client = APIClient()
    api_client.force_authenticate(user=stark_doe)
    api_client.user = stark_doe
    api_client.user.has_strong_auth = True
    return api_client

@pytest.fixture()
def john_smith(default_organization):
    """
    John Smith is registered user working for an organization.
    """
    user = get_user_model().objects.filter(username="john_smith").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("john_smith", "john_smith@example.com", password="password")
        user.admin_organizations.add(default_organization)
    return user


@pytest.fixture()
def john_smith_api_client(john_smith):
    """
    John Smith is a registered user working for an organization; this is his API client.
    """
    api_client = APIClient()
    api_client.force_authenticate(user=john_smith)
    api_client.user = john_smith
    return api_client


@pytest.fixture()
def admin_api_client(admin_user):
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    return api_client


@pytest.fixture()
def admin_api_client_logged_in(admin_user):
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    admin_user.set_password('foo')
    admin_user.save()
    api_client.login(username=admin_user.username, password='foo')
    return api_client


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def geojson_feature():
    return default_geojson_feature


@pytest.fixture()
def bbox_containing_feature():
    return '-104.9950,39.7554,-104.9930,39.7569'


@pytest.fixture()
def geojson_point():
    return {"type": "Point", "coordinates": [24.9482, 60.1744]}


@pytest.fixture()
def geojson_multipoint():
    return {
        "type": "MultiPoint",
        "coordinates": [
            [24.9386, 60.1849], [24.9389, 60.1831], [24.9407, 60.1845]
        ]
    }


@pytest.fixture()
def geojson_polygon():
    return {"type": "Polygon", "coordinates": [[
        [24.9309, 60.1818], [24.9279, 60.1771], [24.9354, 60.1743],
        [24.9409, 60.1768], [24.9382, 60.1804], [24.9309, 60.1818],
    ]]}


@pytest.fixture()
def geojson_polygon_with_hole():
    return {"type": "Polygon", "coordinates": [
        [
            [24.9416, 60.1710], [24.9328, 60.1685], [24.9353, 60.1658],
            [24.9430, 60.1630], [24.9440, 60.1679], [24.9416, 60.1710],
        ],
        [
            [24.9375, 60.1682], [24.9413, 60.1652], [24.9407, 60.1690],
            [24.9375, 60.1682],
        ],
    ]}


@pytest.fixture()
def geojson_multipolygon():
    return {"type": "MultiPolygon", "coordinates": [
        [[
            [24.9509, 60.1692], [24.9559, 60.1690], [24.9563, 60.1714],
            [24.9508, 60.1715], [24.9509, 60.1692],
        ]],
        [[
            [24.9510, 60.1718], [24.9561, 60.1717], [24.9537, 60.1740],
            [24.9510, 60.1718],
        ]],
    ]}


@pytest.fixture()
def geojson_linestring():
    return {"type": "LineString", "coordinates": [
        [24.9322, 60.1883], [24.9224, 60.1842], [24.9159, 60.1799],
        [24.9157, 60.1746], [24.9252, 60.1703],
    ]}


@pytest.fixture()
def geojson_multilinestring():
    return {"type": "MultiLineString", "coordinates": [
        [[24.9488, 60.1892], [24.9535, 60.1880], [24.9511, 60.1857]],
        [[24.9490, 60.1869], [24.9466, 60.1846], [24.9522, 60.1833]],
        [[24.9498, 60.1821], [24.9546, 60.1813], [24.9569, 60.1840]],
    ]}


@pytest.fixture()
def geojson_geometrycollection(
    geojson_point, geojson_multipoint, geojson_polygon, geojson_polygon_with_hole,
    geojson_multipolygon, geojson_linestring, geojson_multilinestring):
    return {
        "type": "GeometryCollection",
        "geometries": [
            geojson_point,
            geojson_multipoint,
            geojson_polygon,
            geojson_polygon_with_hole,
            geojson_multipolygon,
            geojson_linestring,
            geojson_multilinestring,
        ]
    }


@pytest.fixture()
def geojson_feature_with_geometries(geojson_geometrycollection):
    return {
        "type": "Feature",
        "properties": {
            "name": "Collection of Geometries",
        },
        "geometry": geojson_geometrycollection,
    }


@pytest.fixture()
def bbox_containing_geometries():
    return '24.9034,60.1614,24.9684,60.1920'


@pytest.fixture()
def bbox_all():
    return '-180.0,-90.0,180.0,90.0'


@pytest.fixture()
def geojson_featurecollection(geojson_point, geojson_polygon):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Feature 1",
                    "amenity": "Marker",
                    "popupContent": "This is a marker.",
                },
                "geometry": geojson_point,
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "Feature 2",
                    "amenity": "Area",
                    "popupContent": "This is an area.",
                },
                "geometry": geojson_polygon,
            },
        ]
    }


@pytest.fixture
def section_file_orphan():
    section_file = SectionFile()
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        cf = ContentFile(fp.read())
        section_file.file.save('test/file.txt', cf, save=False)
    section_file.save()
    return section_file
