import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing,  Scenario
from kk.tests.base import BaseKKDBTest, default_hearing


class TestScenario(BaseKKDBTest):

    def setup(self):
        super(TestScenario, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint

    def create_scenarios(self, hearing, n):
        Scenario.objects.all().delete()
        scenarios = []
        for i in range(n):
            scenario = Scenario(abstract='Test scenario abstract %s' % str(i + 1),
                                content='Test scenario content %s' % str(i + 1), hearing=hearing)
            scenario.save()
            scenarios.append(scenario)
        return scenarios

    def test_45_get_one_scenario_check_amount(self, default_hearing):
        self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 1

    def test_45_get_one_scenario_check_abstract(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['abstract'] == scenarios[0].abstract

    def test_45_get_one_scenario_check_content(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data[0]['content'] == scenarios[0].content

    def test_45_get_many_scenarios_check_amount(self, default_hearing):
        self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 3

    def test_45_get_many_scenarios_check_abstract(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3

        assert scenarios[0].abstract in abstracts
        assert scenarios[1].abstract in abstracts
        assert scenarios[2].abstract in abstracts

    def test_45_get_many_scenarios_check_content(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        contents = [s['content'] for s in data]

        # ensure we have 3 contents
        assert len(contents) == 3

        assert scenarios[0].content in contents
        assert scenarios[1].content in contents
        assert scenarios[2].content in contents

    def test_45_get_hearing_with_one_scenario_check_amount(self, default_hearing):
        self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['scenarios']) == 1

    def test_45_get_hearing_with_one_scenario_check_abstract(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['scenarios'][0]['abstract'] == scenarios[0].abstract

    def test_45_get_hearing_with_one_scenario_check_content(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 1)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert data['scenarios'][0]['content'] == scenarios[0].content

    def test_45_get_hearing_with_many_scenarios_check_amount(self, default_hearing):
        self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data['scenarios']) == 3

    def test_45_get_hearing_with_many_scenarios_check_abstract(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        abstracts = [s['abstract'] for s in data['scenarios']]

        # ensure we have 3 abstracts
        assert len(abstracts) == 3

        assert scenarios[0].abstract in abstracts
        assert scenarios[1].abstract in abstracts
        assert scenarios[2].abstract in abstracts

    def test_45_get_hearing_with_many_scenarios_check_content(self, default_hearing):
        scenarios = self.create_scenarios(default_hearing, 3)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id,))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        contents = [s['content'] for s in data['scenarios']]

        # ensure we have 3 contents
        assert len(contents) == 3

        assert scenarios[0].content in contents
        assert scenarios[1].content in contents
        assert scenarios[2].content in contents
