import pytest
import datetime
import urllib

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

    def test_get_next_closing_hearing_one_available(self):
        first_close_at = datetime.datetime.now()+datetime.timedelta(days=1)
        third_close_at = datetime.datetime.now()+datetime.timedelta(days=3)
        hearing_one = Hearing(abstract='Closing hearing one')
        hearing_two = Hearing(abstract='Closing hearing two')
        self.hearing_one.close_at = third_close_at

        # hearing_one will close today
        # hearing_two will close today
        # First hearing created during setup will close in three days

        # We expect first hearing created in a setup which is next for our hearing_one

        hearing_one.save()
        hearing_two.save()
        self.hearing_one.save()

        url = '%s&next_closing=%s' % (self.list_endpoint, urllib.parse.quote_plus(first_close_at.strftime('%Y-%m-%dT%H:%M:%S.%uZ')))
        response = self.client.get(url)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
 
        assert len(data) is 1
        assert data[0]['abstract'] == self.hearing_one.abstract

    def test_get_next_closing_hearing_two_available(self):
        first_close_at = datetime.datetime.now()+datetime.timedelta(days=1)
        second_close_at = datetime.datetime.now()+datetime.timedelta(days=2)
        third_close_at = datetime.datetime.now()+datetime.timedelta(days=3)
        hearing_one = Hearing(abstract='Closing hearing one', close_at=first_close_at)
        hearing_two = Hearing(abstract='Closing hearing two', close_at=second_close_at)
        self.hearing_one.close_at = third_close_at

        # hearing_one will close in one day
        # hearing_two will close in two days
        # First hearing created during setup will close in three days

        # We expect hearing_two which is next for our hearing_one

        hearing_one.save()
        hearing_two.save()
        self.hearing_one.save()

        # add one second to datetime
        # at least it fixes the same datetime returned issue with SQLite in my case
        # e.g. &next_closing=2015-11-03T08%3A28%3A09.2Z returns object which close_at is 2015-11-03T08:28:09
        # though, query constraint is 'close_at > 2015-11-03T08:28:09'
        next_close_date = first_close_at + datetime.timedelta(0,1)
        url = '%s&next_closing=%s' % (self.list_endpoint, urllib.parse.quote_plus(next_close_date.strftime('%Y-%m-%dT%H:%M:%S.%uZ')))
        response = self.client.get(url)
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert len(data) is 1
        assert data[0]['abstract'] == hearing_two.abstract
