import pytest

from democracy.tests.test_hearing import list_endpoint
from democracy.tests.utils import IMAGES, get_data_from_response, get_hearing_detail_url


def check_entity_images(entity):
    assert 'images' in entity
    image_list = entity['images']
    assert len(image_list) == 3
    assert all([im['url'].startswith("http") for im in image_list])
    assert set(im['title'] for im in image_list) == set(IMAGES.values())

    for im in image_list:
        assert 'caption' in im
        assert 'title' in im
        assert 'width' in im
        assert 'height' in im
        assert 'url' in im


@pytest.mark.django_db
def test_8_list_hearing_images(api_client, default_hearing):
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id)))
    check_entity_images(data)


@pytest.mark.django_db
def test_37_list_hearing_images_check_titles(api_client, default_hearing):
    """
    Check images exist in hearing image payloads
    """
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'images')))
    check_entity_images({"images": data})


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


@pytest.mark.parametrize('client, expected', [
    ('api_client', False),
    ('jane_doe_api_client', False),
    ('admin_api_client', True)
])
@pytest.mark.django_db
def test_unpublished_hearing_images_excluded(client, expected, request, default_hearing):
    api_client = request.getfuncargvalue(client)

    image = default_hearing.images.get(title=IMAGES['ORIGINAL'])
    image.published = False
    image.save(update_fields=('published',))

    # /v1/hearing/ images field
    image_set_1 = get_data_from_response(api_client.get(list_endpoint))[0]['images']

    # /v1/hearing/<id>/ images field
    image_set_2 = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id)))['images']

    # /v1/hearing/<id>/images/
    image_set_3 = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'images')))

    for image_set in (image_set_1, image_set_2, image_set_3):
        assert (IMAGES['ORIGINAL'] in [image['title'] for image in image_set]) is expected


@pytest.mark.parametrize('client, expected', [
    ('api_client', False),
    ('jane_doe_api_client', False),
    ('admin_api_client', True)
])
@pytest.mark.django_db
def test_unpublished_section_images_excluded(client, expected, request, default_hearing):
    api_client = request.getfuncargvalue(client)

    image = default_hearing.sections.first().images.get(title=IMAGES['ORIGINAL'])
    image.published = False
    image.save(update_fields=('published',))

    # /v1/hearing/<id>/ images field
    image_set_1 = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id)))['sections'][0]['images']

    # /v1/hearing/<id>/section/ images field
    image_set_2 = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))[0]['images']

    for image_set in (image_set_1, image_set_2):
        assert (IMAGES['ORIGINAL'] in [image['title'] for image in image_set]) is expected
