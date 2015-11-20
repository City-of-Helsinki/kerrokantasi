import datetime
import os
import urllib

from django.conf import settings
from django.utils.encoding import force_text

import pytest
from kk.enums import SectionType
from kk.models import Hearing, Section
from kk.tests.base import BaseKKDBTest, default_hearing


class TestSection(BaseKKDBTest):

    def setup(self):
        super(TestSection, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint

    def create_sections(self, hearing, n):
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

    def test_45_get_one_section_check_amount(self, default_hearing):
        self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 1

    def test_45_get_one_section_check_abstract(self, default_hearing):
        sections = self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['abstract'] == sections[0].abstract

    def test_45_get_one_section_check_content(self, default_hearing):
        sections = self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['content'] == sections[0].content

    def test_45_get_many_sections_check_amount(self, default_hearing):
        self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 3

    def test_45_get_many_sections_check_abstract(self, default_hearing):
        sections = self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3

        assert sections[0].abstract in abstracts
        assert sections[1].abstract in abstracts
        assert sections[2].abstract in abstracts

    def test_45_get_many_sections_check_content(self, default_hearing):
        sections = self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'sections'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        contents = [s['content'] for s in data]

        # ensure we have 3 contents
        assert len(contents) == 3

        assert sections[0].content in contents
        assert sections[1].content in contents
        assert sections[2].content in contents

    def test_45_get_hearing_with_one_section_check_amount(self, default_hearing):
        self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['sections']) == 1

    def test_45_get_hearing_with_one_section_check_fields(self, default_hearing):
        self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert 'id' in data['sections'][0]
        assert 'title' in data['sections'][0]
        assert 'abstract' in data['sections'][0]
        assert 'content' in data['sections'][0]
        assert 'type' in data['sections'][0]

    def test_45_get_hearing_with_one_section_check_abstract(self, default_hearing):
        sections = self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['sections'][0]['abstract'] == sections[0].abstract

    def test_45_get_hearing_with_one_section_check_content(self, default_hearing):
        sections = self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['sections'][0]['content'] == sections[0].content

    def test_45_get_section_type(self, default_hearing):
        sections = self.create_sections(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert SectionType(data['sections'][0]['type']) == SectionType.PLAIN

    def test_45_get_hearing_with_many_sections_check_amount(self, default_hearing):
        self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['sections']) == 3

    def test_45_get_hearing_with_many_sections_check_abstract(self, default_hearing):
        sections = self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data['sections']]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3

        assert sections[0].abstract in abstracts
        assert sections[1].abstract in abstracts
        assert sections[2].abstract in abstracts

    def test_45_get_hearing_with_many_sections_check_content(self, default_hearing):
        sections = self.create_sections(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
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
