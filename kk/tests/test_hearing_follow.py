import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, HearingComment, Scenario, ScenarioComment
from kk.tests.base import BaseKKDBTest, default_hearing


class TestHearingFollow(BaseKKDBTest):

    def setup(self):
        super(TestHearingFollow, self).setup()

    def get_hearing_follow_url(self, hearing_id):
        # /v1/hearings/<hearingID>/follow/
        return self.get_hearing_detail_url(hearing_id, 'follow')

    def test_10_hearing_follow_without_authentication(self, default_hearing):
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 403

    def test_10_hearing_follow(self, default_hearing):
        self.user_login()
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        print(response.content)
        assert response.status_code == 201

    def test_10_hearing_follow_again(self, default_hearing):
        self.user_login()
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 201
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 304
