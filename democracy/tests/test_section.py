import datetime

import pytest
from django.utils.encoding import force_text
from django.utils.timezone import now

from democracy.enums import SectionType
from democracy.models import Section
from democracy.models.section import CLOSURE_INFO_ORDERING
from democracy.tests.utils import assert_id_in_results, get_data_from_response, get_hearing_detail_url
from democracy.views.section import SectionSerializer

hearing_endpoint = '/v1/hearing/'
hearing_list_endpoint = hearing_endpoint


@pytest.fixture()
def closure_info_section(default_hearing):
    return Section.objects.create(
        type=SectionType.CLOSURE_INFO,
        hearing=default_hearing
    )


@pytest.mark.django_db
def create_sections(hearing, n):
    Section.objects.all().delete()
    sections = []
    for i in range(n):
        section = Section(
            abstract='Test section abstract %s' % str(i + 1),
            content='Test section content %s' % str(i + 1),
            hearing=hearing,
            type=SectionType.PLAIN
        )
        section.save()
        sections.append(section)
    return sections


@pytest.mark.django_db
def test_45_get_one_section_check_amount(api_client, default_hearing):
    create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
    assert len(data) == 1


@pytest.mark.django_db
def test_45_get_one_section_check_abstract(api_client, default_hearing):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
    assert data[0]['abstract'] == sections[0].abstract


@pytest.mark.django_db
def test_45_get_one_section_check_content(api_client, default_hearing):
    sections = create_sections(default_hearing, 1)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
    assert data[0]['content'] == sections[0].content


@pytest.mark.django_db
def test_45_get_many_sections_check_amount(api_client, default_hearing):
    create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
    assert len(data) == 3


@pytest.mark.django_db
def test_45_get_many_sections_check_abstract(api_client, default_hearing):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
    abstracts = [s['abstract'] for s in data]

    # ensure we have 3 abstracts
    assert len(abstracts) == 3

    assert sections[0].abstract in abstracts
    assert sections[1].abstract in abstracts
    assert sections[2].abstract in abstracts


@pytest.mark.django_db
def test_45_get_many_sections_check_content(api_client, default_hearing):
    sections = create_sections(default_hearing, 3)

    response = api_client.get(get_hearing_detail_url(default_hearing.id, 'sections'))

    data = get_data_from_response(response)
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
    assert SectionType(data['sections'][0]['type']) == SectionType.PLAIN


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
    closure_info_section.type = SectionType.PLAIN
    closure_info_section.save()
    assert closure_info_section.ordering != CLOSURE_INFO_ORDERING

    # check changing type to closure info
    closure_info_section.type = SectionType.CLOSURE_INFO
    closure_info_section.save()
    assert closure_info_section.ordering == CLOSURE_INFO_ORDERING


@pytest.mark.django_db
def test_closure_info_visibility(api_client, closure_info_section):
    hearing = closure_info_section.hearing

    # hearing closed, closure info section should be in results
    hearing.close_at = now() - datetime.timedelta(days=1)
    hearing.save()

    # check sections field in the hearing
    response = api_client.get(get_hearing_detail_url(hearing.id))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data['sections'])

    # check sections endpoint
    response = api_client.get(get_hearing_detail_url(hearing.id, 'sections'))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data)

    # hearing open, closure info section should not be in results
    hearing.close_at = now() + datetime.timedelta(days=1)
    hearing.save()

    # check sections field in the hearing
    response = api_client.get(get_hearing_detail_url(hearing.id))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data['sections'], False)

    # check sections endpoint
    response = api_client.get(get_hearing_detail_url(hearing.id, 'sections'))
    data = get_data_from_response(response)
    assert_id_in_results(closure_info_section.id, data, False)
