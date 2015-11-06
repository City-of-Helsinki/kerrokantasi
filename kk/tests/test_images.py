import pytest
from kk.tests.utils import get_data_from_response, IMAGES


def get_hearing_detail_url(id, element=None):
    url = '/v1/hearing/%s/' % id
    if element:
        url += "%s/" % element
    return url


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
def test_38_get_introduction_with_images(client, default_hearing):
    """
    Check images exist in introduction payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id, 'introductions')))
    first_intro = data[0]
    check_entity_images(first_intro)


@pytest.mark.django_db
def test_38_get_hearing_check_introduction_with_images(client, default_hearing):
    """
    Check images exist in introductions nested in hearing payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id)))
    assert 'introductions' in data
    check_entity_images(data['introductions'][0])


@pytest.mark.django_db
def test_38_get_scenario_with_images(client, default_hearing):
    """
    Check images exist in scenario payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id, 'scenarios')))
    first_scenario = data[0]
    check_entity_images(first_scenario)


@pytest.mark.django_db
def test_38_get_hearing_check_scenario_with_images(client, default_hearing):
    """
    Check images exist in scenarios nested in hearing payloads
    """
    data = get_data_from_response(client.get(get_hearing_detail_url(default_hearing.id)))
    assert 'scenarios' in data
    first_scenario = data['scenarios'][0]
    check_entity_images(first_scenario)
