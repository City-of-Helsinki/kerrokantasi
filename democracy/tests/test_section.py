import datetime

import pytest
from django.utils.encoding import force_text
from django.utils.timezone import now

from democracy.enums import InitialSectionType
from democracy.models import Section, SectionType
from democracy.models.section import CLOSURE_INFO_ORDERING
from democracy.tests.utils import assert_id_in_results, get_data_from_response, get_hearing_detail_url
from democracy.views.section import SectionSerializer

hearing_endpoint = '/v1/hearing/'
hearing_list_endpoint = hearing_endpoint


@pytest.fixture()
def closure_info_section(default_hearing):
    return Section.objects.create(
        type=SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO),
        hearing=default_hearing
    )


@pytest.fixture()
def new_section_type():
    return SectionType.objects.create(name_singular='new section type', name_plural='new section types')


@pytest.fixture(params=['nested', 'root'])
def get_sections_url(request):
    """
    A fixture that returns URL for two different section endpoints:
    - /v1/hearing/<hearing id>/sections/
    - /v1/section/?hearing=<hearing id>
    """
    return {
        'nested': lambda hearing: '/v1/hearing/%s/sections/' % hearing.id,
        'root': lambda hearing: '/v1/section/?hearing=%s' % hearing.id
    }[request.param]


@pytest.mark.django_db
def create_sections(hearing, n):
    Section.objects.all().delete()
    sections = []
    for i in range(n):
        section = Section(
            abstract='Test section abstract %s' % str(i + 1),
            content='Test section content %s' % str(i + 1),
            hearing=hearing,
            type=SectionType.objects.get(identifier=InitialSectionType.PART)
        )
        section.save()
        sections.append(section)
    return sections


def get_results_from_response(response):
    data = get_data_from_response(response)
    if 'results' in data:
        return data['results']
    return data


@pytest.mark.django_db
def test_45_get_one_section_check_amount(api_client, default_hearing, get_sections_url):
    create_sections(default_hearing, 1)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    assert len(data) == 1


@pytest.mark.django_db
def test_45_get_one_section_check_abstract(api_client, default_hearing, get_sections_url):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    assert data[0]['abstract'] == sections[0].abstract


@pytest.mark.django_db
def test_45_get_one_section_check_content(api_client, default_hearing, get_sections_url):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    assert data[0]['content'] == sections[0].content


@pytest.mark.django_db
def test_45_get_many_sections_check_amount(api_client, default_hearing, get_sections_url):
    create_sections(default_hearing, 3)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    assert len(data) == 3


@pytest.mark.django_db
def test_45_get_many_sections_check_abstract(api_client, default_hearing, get_sections_url):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    abstracts = [s['abstract'] for s in data]

    # ensure we have 3 abstracts
    assert len(abstracts) == 3

    assert sections[0].abstract in abstracts
    assert sections[1].abstract in abstracts
    assert sections[2].abstract in abstracts


@pytest.mark.django_db
def test_45_get_many_sections_check_content(api_client, default_hearing, get_sections_url):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_sections_url(default_hearing))

    data = get_results_from_response(response)
    contents = [s['content'] for s in data]

    # ensure we have 3 contents
    assert len(contents) == 3

    assert sections[0].content in contents
    assert sections[1].content in contents
    assert sections[2].content in contents


@pytest.mark.django_db
def test_45_get_hearing_with_one_section_check_amount(api_client, default_hearing):
    create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert len(data['sections']) == 1


@pytest.mark.django_db
def test_45_get_hearing_with_one_section_check_fields(api_client, default_hearing):
    create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    section = data['sections'][0]
    assert all(
        key in section
        for key in SectionSerializer.Meta.fields
    )


@pytest.mark.django_db
def test_45_get_hearing_with_one_section_check_abstract(api_client, default_hearing):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert data['sections'][0]['abstract'] == sections[0].abstract


@pytest.mark.django_db
def test_45_get_hearing_with_one_section_check_content(api_client, default_hearing):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert data['sections'][0]['content'] == sections[0].content


@pytest.mark.django_db
def test_45_get_section_type(api_client, default_hearing):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert data['sections'][0]['type'] == InitialSectionType.PART
    assert data['sections'][0]['type_name_singular'] == 'osa-alue'
    assert data['sections'][0]['type_name_plural'] == 'osa-alueet'


@pytest.mark.django_db
def test_45_get_hearing_with_many_sections_check_amount(api_client, default_hearing):
    create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id))

    data = get_data_from_response(response)
    assert len(data['sections']) == 3


@pytest.mark.django_db
def test_45_get_hearing_with_many_sections_check_abstract(api_client, default_hearing):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, ))

    data = get_data_from_response(response)
    abstracts = [s['abstract'] for s in data['sections']]

    # ensure we have 3 abstracts
    assert len(abstracts) == 3

    assert sections[0].abstract in abstracts
    assert sections[1].abstract in abstracts
    assert sections[2].abstract in abstracts


@pytest.mark.django_db
def test_45_get_hearing_with_many_sections_check_content(api_client, default_hearing):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, ))

    data = get_data_from_response(response)
    contents = [s['content'] for s in data['sections']]

    # ensure we have 3 contents
    assert len(contents) == 3

    assert sections[0].content in contents
    assert sections[1].content in contents
    assert sections[2].content in contents


@pytest.mark.django_db
def test_section_stringification(random_hearing):
    section = random_hearing.sections.first()
    stringified = force_text(section)
    assert section.title in stringified
    assert random_hearing.title in stringified


@pytest.mark.django_db
def test_closure_info_ordering(closure_info_section):

    # check new section
    assert closure_info_section.ordering == CLOSURE_INFO_ORDERING

    # check changing type from closure info
    closure_info_section.type = SectionType.objects.get(identifier=InitialSectionType.PART)
    closure_info_section.save()
    assert closure_info_section.ordering != CLOSURE_INFO_ORDERING

    # check changing type to closure info
    closure_info_section.type = SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO)
    closure_info_section.save()
    assert closure_info_section.ordering == CLOSURE_INFO_ORDERING


@pytest.mark.django_db
def test_closure_info_visibility(api_client, closure_info_section, get_sections_url):
    hearing = closure_info_section.hearing

    # hearing closed, closure info section should be in results
    hearing.close_at = now() - datetime.timedelta(days=1)
    hearing.save()

    # check sections field in the hearing
    response = api_client.get(get_hearing_detail_url(hearing.id))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data['sections'])

    # check nested and root level sections endpoint
    response = api_client.get(get_sections_url(hearing))
    data = get_results_from_response(response)
    assert_id_in_results(closure_info_section.id, data)

    # hearing open, closure info section should not be in results
    hearing.close_at = now() + datetime.timedelta(days=1)
    hearing.save()

    # check sections field in the hearing
    response = api_client.get(get_hearing_detail_url(hearing.id))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data['sections'], False)

    # check nested and root level sections endpoint
    response = api_client.get(get_sections_url(hearing))
    data = get_results_from_response(response)
    assert_id_in_results(closure_info_section.id, data, False)


@pytest.mark.django_db
def test_initial_section_types_exist():
    for section_type_id in ('introduction', 'part', 'scenario', 'closure-info'):
        assert SectionType.objects.filter(identifier=section_type_id).exists()


@pytest.mark.django_db
def test_new_section_type(new_section_type):
    assert SectionType.objects.filter(identifier='new-section-type').exists()

    # test duplicate name
    another_new_section_type = SectionType.objects.create(name_singular='new section type', name_plural='foos')
    assert another_new_section_type.identifier != 'new-section-type'
    assert SectionType.objects.filter(id=another_new_section_type.id).exists()
    assert SectionType.objects.filter(identifier='new-section-type').exists()
    assert SectionType.objects.filter(name_singular='new section type').count() == 2


@pytest.mark.django_db
def test_section_type_filtering(new_section_type):
    assert SectionType.objects.count() == 5
    assert SectionType.objects.initial().count() == 4
    assert SectionType.objects.exclude_initial().count() == 1


@pytest.mark.django_db
def test_initial_section_type_cannot_be_edited():
    closure_info = SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO)
    closure_info.name_singular = 'edited name'
    with pytest.raises(Exception) as excinfo:
        closure_info.save()
    assert excinfo.value.__str__() == 'Initial section types cannot be edited.'
    closure_info.refresh_from_db()
    assert closure_info.name_singular != 'edited name'


@pytest.mark.django_db
def test_added_section_type_can_be_edited(new_section_type):
    new_section_type.name_singular = 'edited name'
    new_section_type.save()
    new_section_type.refresh_from_db()
    assert new_section_type.name_singular == 'edited name'


@pytest.mark.django_db
def test_root_endpoint_filters(api_client, default_hearing, random_hearing):
    url = '/v1/section/'

    response = api_client.get('%s?hearing=%s' % (url, default_hearing.id))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 3

    response = api_client.get('%s?hearing=%s&type=%s' % (url, default_hearing.id, 'introduction'))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 1


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
    response_data = get_results_from_response(response)
    assert len(response_data) == 0
