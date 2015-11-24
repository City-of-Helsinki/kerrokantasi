import pytest

from kk.tests.utils import IMAGES, get_data_from_response, get_hearing_detail_url


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
def test_8_list_hearing_images(client, default_hearing):
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id)))
    check_entity_images(data)


@pytest.mark.django_db
def test_37_list_hearing_images_check_titles(client, default_hearing):
    """
    Check images exist in hearing image payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id, 'images')))
    check_entity_images({"images": data})


@pytest.mark.django_db
def test_38_get_section_with_images(client, default_hearing):
    """
    Check images exist in section payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    check_entity_images(first_section)


@pytest.mark.django_db
def test_38_get_hearing_check_section_with_images(client, default_hearing):
    """
    Check images exist in sections nested in hearing payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id)))
    assert 'sections' in data
    first_section = data['sections'][0]
    check_entity_images(first_section)
