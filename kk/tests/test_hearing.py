import pytest
import datetime
import urllib
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from kk.models import Hearing, Label
from kk.tests.base import BaseKKDBTest, default_hearing
from kk.tests.utils import assert_datetime_fuzzy_equal


class TestHearing(BaseKKDBTest):
    def setup(self):
        super(TestHearing, self).setup()
        self.endpoint = '%s/hearing/' % self.base_endpoint
        self.list_endpoint = '%s?format=json' % self.endpoint

    def get_detail_url(self, id):
        return '%s%s/?format=json' % (self.endpoint, id)

    def create_hearings(self, n):
        Hearing.objects.all().delete()  # Get rid of all other hearings
        hearings = []

        # Depending on the database backend, created_at dates (which are used for ordering)
        # may be truncated to the closest second, so we purposefully backdate these
        # to ensure ordering on all platforms.
        for i in range(n):
            hearings.append(
                Hearing.objects.create(
                    abstract='Test purpose created hearing %s' % (i + 1),
                    created_at=now() - datetime.timedelta(seconds=1 + (n - i))
                )
            )
        return hearings

    def test_list_all_hearings_no_objects(self):
        self.create_hearings(0)
        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200
        data = self.get_data_from_response(response)
        assert len(data) == 0

    def test_list_all_hearings_check_number_of_objects(self):
        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == Hearing.objects.count()

    def test_list_all_hearings_check_abstract(self):
        hearings = self.create_hearings(3)
        response = self.client.get(self.list_endpoint)
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['abstract'] == hearings[2].abstract
        assert data[1]['abstract'] == hearings[1].abstract
        assert data[2]['abstract'] == hearings[0].abstract

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
        # We expect data to be returned in this, particular order
        assert '10' in objects[0]['abstract']
        assert '9' in objects[1]['abstract']
        assert '8' in objects[2]['abstract']
        assert '7' in objects[3]['abstract']
        assert '6' in objects[4]['abstract']

    def test_get_next_closing_hearings(self):
        self.create_hearings(0)  # Clear out old hearings
        closed_hearing_1 = Hearing.objects.create(abstract='Gone', close_at=now() - datetime.timedelta(days=1))
        closed_hearing_2 = Hearing.objects.create(abstract='Gone too', close_at=now() - datetime.timedelta(days=2))
        future_hearing_1 = Hearing.objects.create(abstract='Next up', close_at=now() + datetime.timedelta(days=1))
        future_hearing_2 = Hearing.objects.create(abstract='Next up', close_at=now() + datetime.timedelta(days=5))
        response = self.client.get(
            '%s&next_closing=%s' % (self.list_endpoint, urllib.parse.quote_plus(now().isoformat())))
        data = self.get_data_from_response(response)
        assert len(data) == 1
        assert data[0]['abstract'] == future_hearing_1.abstract
        response = self.client.get(
            '%s&next_closing=%s' % (self.list_endpoint, urllib.parse.quote_plus(future_hearing_1.close_at.isoformat())))
        data = self.get_data_from_response(response)
        assert len(data) == 1
        assert data[0]['abstract'] == future_hearing_2.abstract

    def test_list_hearings_check_references_not_included(self):
        # DynamicFieldsMixin (https://gist.github.com/dbrgn/4e6fc1fe5922598592d6)
        pytest.xfail("Test fields requested dynamicaly for a list")

    def test_8_get_detail_check_properties(self, default_hearing):
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'abstract' in data
        assert 'heading' in data
        assert 'content' in data
        assert 'images' in data
        assert 'labels' in data
        assert 'scenarios' in data
        assert 'created_at' in data
        assert 'closed' in data
        assert 'close_at' in data
        assert 'id' in data
        assert 'borough' in data
        assert 'servicemap_url' in data
        assert 'latitude' in data
        assert 'longitude' in data
        assert 'n_comments' in data

    def test_8_get_detail_abstract(self):
        hearing = Hearing(abstract='Lorem Ipsum Abstract')
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['abstract'] == hearing.abstract

    def test_8_get_detail_heading(self):
        hearing = Hearing(heading='Lorem Ipsum Heading')
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['heading'] == hearing.heading

    def test_8_get_detail_borough(self):
        hearing = Hearing(borough='Itäinen')
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['borough'] == hearing.borough

    def test_8_get_detail_n_comments(self):
        hearing = Hearing(n_comments=1)
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['n_comments'] == hearing.n_comments

    def test_8_get_detail_closing_time(self):
        hearing = Hearing()
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert_datetime_fuzzy_equal(data['close_at'], hearing.close_at)

    def test_8_get_detail_labels(self):
        hearing = Hearing()
        hearing.save()

        label_one = Label(label='Label One')
        label_one.save()
        label_two = Label(label='Label Two')
        label_two.save()
        label_three = Label(label='Label Three')
        label_three.save()

        hearing.labels.add(label_one, label_two, label_three)

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert len(data['labels']) is 3
        assert label_one.label in data['labels']

    def test_8_get_detail_empty(self):
        pytest.xfail("Add tests for empty values")

    def test_8_get_detail_invalid(self):
        pytest.xfail("Add tests for invalid values")

    def test_7_get_detail_location(self):
        hearing = Hearing(latitude='60.19276', longitude='24.93300')
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['latitude'] == hearing.latitude
        assert data['longitude'] == hearing.longitude

    def test_7_get_detail_servicemap(self):
        hearing = Hearing(
            servicemap_url='http://servicemap.hel.fi/embed/?bbox=60.19276,24.93300,60.19571,24.94513&city=helsinki')
        hearing.save()

        response = self.client.get(self.get_detail_url(hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'results' not in data
        assert data['servicemap_url'] == hearing.servicemap_url
