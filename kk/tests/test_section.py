import pytest
from django.utils.encoding import force_text

from kk.enums import SectionType
from kk.models import Section
from kk.tests.utils import get_data_from_response, get_hearing_detail_url

hearing_endpoint = '/v1/hearing/'
hearing_list_endpoint = hearing_endpoint


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
    assert 'id' in data['sections'][0]
    assert 'title' in data['sections'][0]
    assert 'abstract' in data['sections'][0]
    assert 'content' in data['sections'][0]
    assert 'type' in data['sections'][0]


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
