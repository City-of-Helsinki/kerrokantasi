import pytest

from kk.models import Hearing
from kk.tests.base import BaseKKDBTest

class TestHearing(BaseKKDBTest):
    def setup(self):
        super(TestHearing, self).setup()

        self.hearing_one = Hearing(abstract='Hearing One')
        self.hearing_two = Hearing(abstract='Hearing Two')
        self.hearing_three = Hearing(abstract='Hearing Three')

        # save hearings
        self.hearing_one.save()
        self.hearing_two.save()
        self.hearing_three.save()
       
        self.endpoint = '%s/hearing/' % self.base_endpoint
        self.list_endpoint = '%s?format=json' % self.endpoint
    
    def create_hearings(self, n):
        for i in range(1, n+1):
            Hearing(abstract='Test purpose created hearing %s' % str(i)).save()

    def test_list_all_hearings_no_objects(self):
        self.hearing_one.delete()
        self.hearing_two.delete()
        self.hearing_three.delete()

        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 0

    def test_list_all_hearings_check_number_of_objects(self):
        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 3
       
    def test_list_all_hearings_check_abstract(self):
        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['abstract'] == self.hearing_three.abstract
        assert data[1]['abstract'] == self.hearing_two.abstract
        assert data[2]['abstract'] == self.hearing_one.abstract

    def test_list_top_5_hearings_check_number_of_objects(self):
        self.create_hearings(10)
        response = self.client.get('%s&limit=5' % self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['results']) == 5

    def test_list_top_5_hearings_check_abstract(self):
        self.create_hearings(10)
        response = self.client.get('%s&limit=5' % self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        objects = data['results']
        assert '10' in objects[0]['abstract']
        assert '9' in objects[1]['abstract']
        assert '8' in objects[2]['abstract']
        assert '7' in objects[3]['abstract']
        assert '6' in objects[4]['abstract']


