import datetime
import os
import urllib

import pytest
from django.conf import settings

from kk.models import Hearing, HearingComment, Section, SectionComment
from kk.tests.base import BaseKKDBTest, default_hearing


class TestHearingFollow(BaseKKDBTest):

    def setup(self):
        super(TestHearingFollow, self).setup()

    def get_hearing_follow_url(self, hearing_id):
        # /v1/hearings/<hearingID>/follow/
        return self.get_hearing_detail_url(hearing_id, 'follow')

    def get_hearing_unfollow_url(self, hearing_id):
        # /v1/hearings/<hearingID>/unfollow/
        return self.get_hearing_detail_url(hearing_id, 'unfollow')

    def test_10_hearing_follow_without_authentication(self, default_hearing):
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 403

    def test_10_hearing_follow(self, default_hearing):
        self.user_login()
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 201

    def test_10_hearing_follow_again(self, default_hearing):
        self.user_login()
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 201
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 304

    def test_hearing_unfollow(self, default_hearing):
        response = self.client.post(self.get_hearing_unfollow_url(default_hearing.id))
        assert response.status_code == 403
        self.user_login()
        response = self.client.post(self.get_hearing_follow_url(default_hearing.id))
        assert response.status_code == 201
        response = self.client.post(self.get_hearing_unfollow_url(default_hearing.id))
        assert response.status_code == 204
        response = self.client.post(self.get_hearing_unfollow_url(default_hearing.id))
        assert response.status_code == 304

    def test_followed_hearing_appear_in_user_data(self, default_hearing):
        self.user_login()
        self.client.post(self.get_hearing_follow_url(default_hearing.id))
        response = self.client.get('/v1/users/')
        assert default_hearing.id in response.data[0]['followed_hearings']
