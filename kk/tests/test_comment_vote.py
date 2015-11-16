import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, HearingComment, Scenario, ScenarioComment
from kk.tests.base import BaseKKDBTest, default_hearing


class TestCommentVote(BaseKKDBTest):

    def setup(self):
        super(TestCommentVote, self).setup()

        self.default_content = 'Awesome comment to vote.'
        self.comment_data = {
            'content': self.default_content,
            'scenario': None
        }

    def add_default_scenario_and_comment(self, hearing):
        scenario = Scenario.objects.create(title='Scenario title', hearing=hearing)
        comment = ScenarioComment.objects.create(content='Comment text', scenario=scenario)
        return [scenario, comment]

    def get_scenario_comment_vote_url(self, hearing_id, scenario_id, comment_id):
        # /v1/hearings/<hearingID>/scenarios/<scenarioID>/comments/<commentID>/votes/
        return self.get_hearing_detail_url(hearing_id, 'scenarios/%s/comments/%s/vote' % (scenario_id, comment_id))

    def add_default_hearing_comment(self, hearing):
        return HearingComment.objects.create(content='Comment text', hearing=hearing)

    def get_hearing_comment_vote_url(self, hearing_id, comment_id):
        # /v1/hearings/<hearingID>/comments/<commentID>/votes/
        return self.get_hearing_detail_url(hearing_id, 'comments/%s/vote' % comment_id)

    def get_hearing_comment_unvote_url(self, hearing_id, comment_id):
        # /v1/hearings/<hearingID>/comments/<commentID>/unvotes/
        return self.get_hearing_detail_url(hearing_id, 'comments/%s/unvote' % comment_id)

    def test_31_scenario_comment_vote_without_authentication(self, default_hearing):
        scenario, comment = self.add_default_scenario_and_comment(default_hearing)
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 403

    def test_31_hearing_comment_vote_without_authentication(self, default_hearing):
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 403

    def test_31_scenario_comment_vote_add_vote(self, default_hearing):
        self.user_login()
        scenario, comment = self.add_default_scenario_and_comment(default_hearing)
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 201

    def test_31_hearing_comment_vote_add_vote(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201

    def test_31_scenario_comment_vote_add_vote_check_voter(self, default_hearing):
        self.user_login()
        scenario, comment = self.add_default_scenario_and_comment(default_hearing)
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 201

        comments = ScenarioComment.objects.filter(id=comment.id, voters=self.user)
        assert len(comments) == 1

    def test_31_hearing_comment_vote_add_vote_check_voter(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201

        comments = HearingComment.objects.filter(id=comment.id, voters=self.user)
        assert len(comments) == 1

    def test_31_scenario_comment_vote_add_vote_check_amount_of_votes(self, default_hearing):
        self.user_login()
        scenario, comment = self.add_default_scenario_and_comment(default_hearing)
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 201

        comment = ScenarioComment.objects.get(id=comment.id, voters=self.user)
        assert comment.voters.all().count() == 1
        assert comment.n_votes == 1

    def test_31_hearing_comment_vote_add_vote_check_amount_of_votes(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201

        comment = HearingComment.objects.get(id=comment.id, voters=self.user)
        assert comment.voters.all().count() == 1
        assert comment.n_votes == 1

    def test_31_scenario_comment_vote_add_second_vote(self, default_hearing):
        self.user_login()
        scenario, comment = self.add_default_scenario_and_comment(default_hearing)
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 201
        # Add vote again. Expect error, because vote has been given already.
        response = self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, comment.id))
        assert response.status_code == 304

    def test_31_hearing_comment_vote_add_second_vote(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201
        # Add vote again. Expect error, because vote has been given already.
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 304

    def test_hearing_comment_unvote(self, default_hearing):
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_unvote_url(default_hearing.id, comment.id))
        assert response.status_code == 403
        self.user_login()
        self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        response = self.client.post(self.get_hearing_comment_unvote_url(default_hearing.id, comment.id))
        assert response.status_code == 204
        assert comment.n_votes == 0
        response = self.client.post(self.get_hearing_comment_unvote_url(default_hearing.id, comment.id))
        assert response.status_code == 304