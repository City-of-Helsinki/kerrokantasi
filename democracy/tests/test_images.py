import datetime
import pytest
from django.utils.timezone import now

from democracy.tests.utils import IMAGES, create_default_images, get_data_from_response, get_hearing_detail_url
from democracy.tests.conftest import default_lang_code


def check_entity_images(entity, images_field=True):
    if images_field:
        assert 'images' in entity
    image_list = entity['images'] if images_field else entity
    assert len(image_list) == 3
    assert all([im['url'].startswith("http") for im in image_list])
    assert set(im['title'][default_lang_code] for im in image_list) == set(IMAGES.values())

    for im in image_list:
        assert 'caption' in im
        assert 'title' in im
        assert 'width' in im
        assert 'height' in im
        assert 'url' in im


def set_images_ordering(images, ordered_image_names):
    for image in images:
        image.ordering = ordered_image_names.index(image.title)
        image.save()


@pytest.mark.django_db
def test_38_get_section_with_images(api_client, default_hearing):
    """
    Check images exist in section payloads
    """
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    check_entity_images(first_section)


@pytest.mark.django_db
def test_38_get_hearing_check_section_with_images(api_client, default_hearing):
    """
    Check images exist in sections nested in hearing payloads
    """
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id)))
    assert 'sections' in data
    first_section = data['sections'][0]
    check_entity_images(first_section)


@pytest.mark.django_db
def test_section_images_ordering(api_client, default_hearing):
    """
    Check images order matches ordering-field
    """

    section_images = default_hearing.sections.first().images.all()

    # Test some initial order
    ordered_image_names = list(IMAGES.values())
    set_images_ordering(section_images, ordered_image_names)
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section_data = data[0]
    assert [im['title'][default_lang_code] for im in first_section_data['images']] == ordered_image_names

    # Test same order reversed
    reversed_image_names = list(reversed(ordered_image_names))
    set_images_ordering(section_images, reversed_image_names)
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section_data = data[0]
    assert [im['title'][default_lang_code] for im in first_section_data['images']] == reversed_image_names


@pytest.mark.parametrize('client, expected', [
    ('api_client', False),
    ('jane_doe_api_client', False),
    ('admin_api_client', True)
])
@pytest.mark.django_db
def test_unpublished_section_images_excluded(client, expected, request, default_hearing):
    api_client = request.getfuncargvalue(client)

    image = default_hearing.get_main_section().images.first()
    image.published = False
    image.save(update_fields=('published',))

    image = default_hearing.sections.all()[2].images.get(translations__title=IMAGES['ORIGINAL'])
    image.published = False
    image.save(update_fields=('published',))

    # /v1/hearing/<id>/ main image field
    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    main_image = get_data_from_response(response)['main_image']
    if expected:
        assert main_image['title'][default_lang_code] == default_hearing.get_main_section().images.first().title
    else:
        assert main_image is None

    # /v1/hearing/<id>/ section images field
    image_set_1 = get_data_from_response(response)['sections'][2]['images']

    # /v1/hearing/<id>/section/ images field
    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))
    image_set_2 = get_data_from_response(response)[2]['images']

    response = api_client.get('/v1/image/?section=%s' % default_hearing.sections.all()[2].id)
    image_set_3 = get_data_from_response(response)['results']

    for image_set in (image_set_1, image_set_2, image_set_3):
        assert (IMAGES['ORIGINAL'] in [image['title'][default_lang_code] for image in image_set]) is expected


@pytest.mark.django_db
def test_get_images_root_endpoint(api_client, default_hearing):
    data = get_data_from_response(api_client.get('/v1/image/'))
    assert len(data['results']) == 9

    data = get_data_from_response(api_client.get('/v1/image/?section=%s' % default_hearing.sections.first().id))
    check_entity_images(data['results'], False)


@pytest.mark.django_db
def test_root_endpoint_filters(api_client, default_hearing, random_hearing):

    # random hearing has always atleast one section that is not the main, add images to it
    create_default_images(random_hearing.sections.exclude(type__identifier='main').first())

    url = '/v1/image/'
    section = default_hearing.sections.first()

    response = api_client.get('%s?hearing=%s' % (url, default_hearing.id))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 9

    response = api_client.get('%s?section=%s' % (url, section.id))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 3

    response = api_client.get('%s?section_type=%s' % (url, 'main'))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 3


@pytest.mark.parametrize('hearing_update', [
    ('deleted', True),
    ('published', False),
    ('open_at', now() + datetime.timedelta(days=1))
])
@pytest.mark.django_db
def test_root_endpoint_filtering_by_hearing_visibility(api_client, default_hearing, hearing_update):
    setattr(default_hearing, hearing_update[0], hearing_update[1])
    default_hearing.save()

    response = api_client.get('/v1/image/')
    response_data = get_data_from_response(response)['results']
    assert len(response_data) == 0
