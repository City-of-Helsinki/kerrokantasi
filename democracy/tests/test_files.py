import datetime
import pytest
from django.utils.timezone import now

from democracy.tests.utils import IMAGES, FILES, get_data_from_response, get_image_path, get_hearing_detail_url, get_sectionfile_download_url, sectionfile_test_data
from democracy.tests.conftest import default_lang_code


def check_entity_files(entity, files_field=True):
    if files_field:
        assert 'files' in entity
    file_list = entity['files'] if files_field else entity
    assert len(file_list) == 1
    assert all([fi['url'].startswith("http") for fi in file_list])
    assert set(fi['title'][default_lang_code] for fi in file_list) == set(FILES.values())

    for fi in file_list:
        assert 'caption' in fi
        assert 'title' in fi
        assert 'url' in fi
        assert 'download' in fi['url']


@pytest.mark.django_db
def test_get_files_root_endpoint(api_client, default_hearing):
    data = get_data_from_response(api_client.get('/v1/file/'))
    assert len(data['results']) == 3


@pytest.mark.django_db
def test_POST_file_root_endpoint(john_smith_api_client, default_hearing):
    # Check original file count
    data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
    assert len(data['results']) == 3
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_test_data()
    post_data['section'] = first_section['id']
    with open(get_image_path(IMAGES['ORIGINAL']), 'rb') as fp:
        post_data['uploaded_file'] = fp
        data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data, format='multipart'), status_code=201)
        # Save order of the newly created file
        ordering = data['ordering']
        # Make sure new file was created
        data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
        assert len(data['results']) == 4
        # Create another file and make sure it gets higher ordering than the last one
        fp.seek(0)
        data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data, format='multipart'), status_code=201)
        assert data['ordering'] == ordering + 1


@pytest.mark.django_db
def test_get_section_with_files(api_client, default_hearing):
    #Check file exist in section payloads
    data = get_data_from_response(api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    check_entity_files(first_section)


@pytest.mark.parametrize('client, expected', [
    ('api_client', False),
    ('jane_doe_api_client', False),
    ('admin_api_client', True)
])
@pytest.mark.django_db
def test_unpublished_section_files_excluded(client, expected, request, default_hearing):
    api_client = request.getfuncargvalue(client)

    file_obj = default_hearing.sections.all()[2].files.get(translations__title=FILES['TXT'])
    file_obj.published = False
    file_obj.save(update_fields=('published',))

    # /v1/hearing/<id>/ section files field
    response = api_client.get(get_hearing_detail_url(default_hearing.id))
    file_set_1 = get_data_from_response(response)['sections'][2]['files']

    # /v1/hearing/<id>/section/ files field
    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))
    file_set_2 = get_data_from_response(response)[2]['files']

    for set_num, file_set in zip(range(1,3), (file_set_1, file_set_2)):
        assert (FILES['TXT'] in [file_obj['title'][default_lang_code] for file_obj in file_set]) is expected, "Set %d failed" % set_num


@pytest.mark.django_db
def test_published_hearing_section_files_download_link(api_client, default_hearing):
    """
    Files in an published hearing should be downloadable for normal users
    """

    file_obj = default_hearing.sections.all()[2].files.get(translations__title=FILES['TXT'])

    response = api_client.get(get_sectionfile_download_url(file_obj.id))
    assert response.status_code == 200


@pytest.mark.django_db
def test_unpublished_hearing_section_files_download_link(api_client, default_hearing):
    """
    Files in an unpublished hearing should not be downloadable for normal users
    """
    file_obj = default_hearing.sections.all()[2].files.get(translations__title=FILES['TXT'])

    default_hearing.published = False
    default_hearing.save(update_fields=('published',))

    # /v1/hearing/<id>/ section files field
    response = api_client.get(get_sectionfile_download_url(file_obj.id))
    assert response.status_code == 404


@pytest.mark.skip
@pytest.mark.django_db
def test_unpublished_hearing_section_files_download_link_admin(default_hearing, john_smith_api_client):
    """
    Files in an unpublished hearing should be downloadable for organisation admin

    Test currently skipped, john_smith_api_client results in AnonymousUser in request.user instead of john_smith from the fixture, who should be organisation admin of the default_hearing.
    """
    file_obj = default_hearing.sections.all()[2].files.get(translations__title=FILES['TXT'])

    default_hearing.published = False
    default_hearing.save(update_fields=('published',))
    response = john_smith_api_client.get(get_sectionfile_download_url(file_obj.id))
    assert response.status_code == 200


