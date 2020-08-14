import datetime
import pytest
import re
from django.urls import reverse
from django.utils.timezone import now

from democracy.models import SectionFile
from democracy.tests.utils import IMAGES, FILES, get_data_from_response, get_image_path, get_file_path, get_image_path, get_hearing_detail_url, get_sectionfile_download_url, sectionfile_multipart_test_data, sectionfile_base64_test_data
from democracy.tests.conftest import default_lang_code


def check_entity_files(entity, files_field=True):
    if files_field:
        assert 'files' in entity
    file_list = entity['files'] if files_field else entity
    assert len(file_list) == 1
    assert all([fi['url'].startswith("http") for fi in file_list])
    assert set(fi['title'][default_lang_code] for fi in file_list) == set(FILES.values())

    for fi in file_list:
        assert 'id' in fi
        assert 'caption' in fi
        assert 'title' in fi
        assert 'url' in fi
        assert 'download' in fi['url']
        if files_field:
            # don't serve the upload field when inlined, the directory is wrong anyway
            assert 'file' not in fi


@pytest.mark.django_db
def test_get_files_root_endpoint(api_client, default_hearing):
    data = get_data_from_response(api_client.get('/v1/file/'))
    assert len(data['results']) == 3


@pytest.mark.django_db
def test_POST_file_multipart_root_endpoint(john_smith_api_client, default_hearing):
    # Check original file count
    data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
    assert len(data['results']) == 3
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_multipart_test_data()
    post_data['section'] = first_section['id']
    with open(get_image_path(IMAGES['ORIGINAL']), 'rb') as fp:
        post_data['file'] = fp
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
def test_POST_file_base64_root_endpoint(john_smith_api_client, default_hearing):
    # Check original file count
    data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
    assert len(data['results']) == 3
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_base64_test_data()
    post_data['section'] = first_section['id']
    data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data), status_code=201)
    # Save order of the newly created file
    ordering = data['ordering']
    # Make sure new file was created
    data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
    assert len(data['results']) == 4
    # Create another file and make sure it gets higher ordering than the last one
    data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data), status_code=201)
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
    api_client = request.getfixturevalue(client)

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


@pytest.mark.django_db
def test_POST_file_root_endpoint_empty_section(john_smith_api_client, default_hearing):
    """
    File should be able to be uploaded without section data
    """
    # Check original file count
    data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
    assert len(data['results']) == 3
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_multipart_test_data()
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        post_data['file'] = fp
        data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data, format='multipart'), status_code=201)
        assert data['section'] is None
        assert data['hearing'] is None
        # Make sure new file was created
        data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
        assert len(data['results']) == 4


@pytest.mark.django_db
def test_PUT_file_multipart_section(john_smith_api_client, default_hearing):
    """
    File with empty section should be able to be updated with section data
    """
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_multipart_test_data()
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        post_data['file'] = fp
        data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data, format='multipart'), status_code=201)
    file_obj_id = data['id']
    put_data = sectionfile_multipart_test_data()
    put_data['section'] = first_section['id']
    data = get_data_from_response(john_smith_api_client.put('/v1/file/%s/' % file_obj_id, data=put_data, format='multipart'), status_code=200)
    assert data['section'] == first_section['id']
    assert data['hearing'] == default_hearing.pk


@pytest.mark.django_db
def test_PUT_file_json_section(john_smith_api_client, default_hearing):
    """
    File with empty section should be able to be updated with section data
    """
    # Get some section
    data = get_data_from_response(john_smith_api_client.get(get_hearing_detail_url(default_hearing.id, 'sections')))
    first_section = data[0]
    # POST new file to the section
    post_data = sectionfile_base64_test_data()
    data = get_data_from_response(john_smith_api_client.post('/v1/file/', data=post_data), status_code=201)
    file_obj_id = data['id']
    data['section'] = first_section['id']
    data = get_data_from_response(john_smith_api_client.put('/v1/file/%s/' % file_obj_id, data=data), status_code=200)
    assert data['section'] == first_section['id']
    assert data['hearing'] == default_hearing.pk


@pytest.mark.django_db
def test_GET_file(john_doe_api_client, default_hearing):
    url = '/v1/file/%s/' % default_hearing.sections.first().files.first().pk
    data = get_data_from_response(john_doe_api_client.get(url), status_code=200)


@pytest.mark.django_db
def test_PUT_file_no_access(john_doe_api_client, default_hearing):
    """
    File should not accept PUT from unpriviledged user
    """
    url = '/v1/file/%s/' % default_hearing.sections.first().files.first().pk
    put_data = sectionfile_multipart_test_data()
    data = get_data_from_response(john_doe_api_client.put(url, data=put_data, format='multipart'), status_code=403)


@pytest.mark.parametrize('client, expected', [
    ('api_client', 401),
    ('jane_doe_api_client', 403),
    ('john_smith_api_client', 204)
])
@pytest.mark.django_db
def test_DELETE_section_files(client, expected, request, default_hearing):
    api_client = request.getfixturevalue(client)
    file_obj = default_hearing.sections.first().files.first()
    url = '/v1/file/%s/' % file_obj.pk
    response = api_client.delete(url)
    assert response.status_code == expected
    if expected == 204:
        file_obj = SectionFile.objects.deleted(pk=file_obj.pk).get()
        assert file_obj.deleted is True


@pytest.mark.django_db
def test_POST_first_file(john_smith_api_client, default_hearing):
    """
    POST a file to hearing with no files
    """
    SectionFile.objects.filter(section__in=default_hearing.sections.all()).delete()
    url = '/v1/file/'
    section = default_hearing.sections.first()
    # POST new file to the section
    post_data = sectionfile_multipart_test_data()
    post_data['section'] = section.pk
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        post_data['file'] = fp
        data = get_data_from_response(john_smith_api_client.post(url, data=post_data, format='multipart'), status_code=201)
        assert data['ordering'] == 1
        assert data['section'] == section.pk
        assert data['hearing'] == default_hearing.pk
        # Make sure new file was created
        data = get_data_from_response(john_smith_api_client.get('/v1/file/'))
        assert len(data['results']) == 1


@pytest.mark.django_db
def test_ckeditor_file_upload_orphan(admin_api_client_logged_in):
    """
    CKEditor file upload should create files protected by sendfile.
    The user can upload files when still being in the process of
    creating the Hearing, so the section id is not known yet.
    """
    ckeditor_params = '?CKEditor=id_sections-0-content&CKEditorFuncNum=1&langCode=en'
    url = '/upload/' + ckeditor_params
    post_data = {}
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        post_data['upload'] = fp
        response = admin_api_client_logged_in.post(url, data=post_data, format='multipart')
    assert response.status_code == 200, 'expected status_code 200, received %s' % response.status_code
    assert SectionFile.objects.count() == 1
    sectionfile_id = SectionFile.objects.first().pk
    expected = r"window.parent.CKEDITOR.tools.callFunction\(1, 'https?://.+/v1/download/sectionfile/%s/'\);" % sectionfile_id
    assert re.search(expected, response.content.decode('utf-8'))


@pytest.mark.django_db
def test_ckeditor_file_upload_image_orphan(admin_api_client_logged_in):
    """
    CKEditor file upload should create files protected by sendfile.
    The user can upload files when still being in the process of
    creating the Hearing, so the section id is not known yet.
    """
    ckeditor_params = '?CKEditor=id_sections-0-content&CKEditorFuncNum=1&langCode=en'
    url = '/upload/' + ckeditor_params
    post_data = {}
    with open(get_image_path(IMAGES['SMALL']), 'rb') as fp:
        post_data['upload'] = fp
        response = admin_api_client_logged_in.post(url, data=post_data, format='multipart')
    assert response.status_code == 200, 'expected status_code 200, received %s' % response.status_code
    assert SectionFile.objects.count() == 1
    sectionfile_id = SectionFile.objects.first().pk
    expected = r"window.parent.CKEDITOR.tools.callFunction\(1, 'https?://.+/v1/download/sectionfile/%s/'\);" % sectionfile_id
    assert re.search(expected, response.content.decode('utf-8'))


@pytest.mark.django_db
def test_ckeditor_get_uploaded_orphan(admin_api_client_logged_in):
    """
    CKEditor file upload should create files protected by sendfile.
    The user can upload files when still being in the process of
    creating the Hearing, so the section id is not known yet.

    Uploaded file should be accessible to the uploader immediately
    for CKEditor preview to work.
    """
    ckeditor_params = '?CKEditor=id_sections-0-content&CKEditorFuncNum=1&langCode=en'
    url = '/upload/' + ckeditor_params
    post_data = {}
    with open(get_file_path(FILES['TXT']), 'rb') as fp:
        post_data['upload'] = fp
        response = admin_api_client_logged_in.post(url, data=post_data, format='multipart')
    assert response.status_code == 200, 'expected status_code 200, received %s' % response.status_code
    assert SectionFile.objects.count() == 1

    section_file = SectionFile.objects.first()
    url = reverse('serve_file', kwargs={'filetype': 'sectionfile', 'pk': section_file.pk})
    response = admin_api_client_logged_in.get(url)
    assert response.status_code == 200, 'expected status_code 200 when accessing uploaded file'


@pytest.mark.django_db
def test_bind_orphan_file_to_section(default_hearing, section_file_orphan):
    """
    File uploaded via CKEditor will be orphaned. When saving a section, any
    orphaned files linked in the text content should be linked to the section,
    so the sendfile-protected files will be visible to viewers of the hearing.
    """
    section = default_hearing.sections.first()
    download_url = reverse('serve_file', kwargs={'filetype': 'sectionfile', 'pk': section_file_orphan.pk})
    section.content = '<a href="{}">fileupload</a>'.format(download_url)
    section.save()
    section_file_orphan.refresh_from_db()
    assert section_file_orphan.section_id == section.pk


@pytest.mark.django_db
def test_access_section_file(default_hearing, section_file_orphan, john_doe_api_client):
    """
    Normal user should be able to access a SectionFile tied to a Section
    """
    section = default_hearing.sections.first()
    section_file_orphan.section = section
    section_file_orphan.save()
    response = john_doe_api_client.get(reverse('serve_file', kwargs={'filetype': 'sectionfile', 'pk': section_file_orphan.pk}))
    assert response.status_code == 200, 'normal user should be be able to get section file'


