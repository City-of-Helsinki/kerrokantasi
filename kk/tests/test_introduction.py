import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, Introduction
from kk.tests.base import BaseKKDBTest, default_hearing

class TestIntroduction(BaseKKDBTest):
    def setup(self):
        super(TestIntroduction, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint
   
    def create_introductions(self, hearing, n):
        Introduction.objects.all().delete()
        intros = []
        for i in range (n):
            introduction = Introduction(abstract='Test introduction abstract %s' % str(i + 1), 
                    content='Test introduction content %s' % str(i + 1), hearing=hearing)
            introduction.save()
            intros.append(introduction)
        return intros

    def test_45_get_one_introduction_check_amount(self, default_hearing):
        self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 1

    def test_45_get_one_introduction_check_abstract(self, default_hearing):
        intros = self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['abstract'] == intros[0].abstract

    def test_45_get_one_introduction_check_content(self, default_hearing):
        intros = self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['content'] == intros[0].content

    def test_45_get_many_introductions_check_amount(self, default_hearing):
        self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 3

    def test_45_get_many_introductions_check_abstract(self, default_hearing):
        intros = self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3
        
        assert intros[0].abstract in abstracts
        assert intros[1].abstract in abstracts
        assert intros[2].abstract in abstracts

    def test_45_get_many_introductions_check_content(self, default_hearing):
        intros = self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'introductions'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        contents = [s['content'] for s in data]

        # ensure we have 3 contents
        assert len(contents) == 3
        
        assert intros[0].content in contents
        assert intros[1].content in contents
        assert intros[2].content in contents

    def test_45_get_hearing_with_one_introduction_check_amount(self, default_hearing):
        self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['introductions']) == 1

    def test_45_get_hearing_with_one_introduction_check_abstract(self, default_hearing):
        intros = self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['introductions'][0]['abstract'] == intros[0].abstract

    def test_45_get_hearing_with_one_introduction_check_content(self, default_hearing):
        intros = self.create_introductions(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['introductions'][0]['content'] == intros[0].content

    def test_45_get_hearing_with_many_introductions_check_amount(self, default_hearing):
        self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['introductions']) == 3

    def test_45_get_hearing_with_many_introductions_check_abstract(self, default_hearing):
        intros = self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data['introductions']]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3
        
        assert intros[0].abstract in abstracts
        assert intros[1].abstract in abstracts
        assert intros[2].abstract in abstracts

    def test_45_get_hearing_with_many_introductions_check_content(self, default_hearing):
        intros = self.create_introductions(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        contents = [s['content'] for s in data['introductions']]

        # ensure we have 3 contents
        assert len(contents) == 3
        
        assert intros[0].content in contents
        assert intros[1].content in contents
        assert intros[2].content in contents

