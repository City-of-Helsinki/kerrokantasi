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
def test_unpublished_section_images_excluded(client, expected, request, default_hearing):
    api_client = request.getfuncargvalue(client)

    image = default_hearing.sections.first().images.get(title=IMAGES['ORIGINAL'])
    image.published = False
    image.save(update_fields=('published',))

    # /v1/hearing/<id>/ images field
    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    image_set_1 = get_data_from_response(response)['sections'][0]['images']

    # /v1/hearing/<id>/section/ images field
    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))
    image_set_2 = get_data_from_response(response)[0]['images']

    for image_set in (image_set_1, image_set_2):
        assert (IMAGES['ORIGINAL'] in [image['title'] for image in image_set]) is expected
