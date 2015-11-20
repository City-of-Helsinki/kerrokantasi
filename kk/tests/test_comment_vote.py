import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, HearingComment, Section, SectionComment
from kk.tests.base import BaseKKDBTest, default_hearing


class TestCommentVote(BaseKKDBTest):
    def setup(self):
        super(TestCommentVote, self).setup()

        self.default_content = 'Awesome comment to vote.'
        self.comment_data = {
            'content': self.default_content,
            'section': None
        }

    def add_default_section_and_comment(self, hearing):
        section = Section.objects.create(title='Section title', hearing=hearing)
        comment = SectionComment.objects.create(content='Comment text', section=section)
        return [section, comment]

    def get_section_comment_vote_url(self, hearing_id, section_id, comment_id):
        # /v1/hearings/<hearingID>/sections/<sectionID>/comments/<commentID>/votes/
        return self.get_hearing_detail_url(hearing_id, 'sections/%s/comments/%s/vote' % (section_id, comment_id))

    def add_default_hearing_comment(self, hearing):
        return HearingComment.objects.create(content='Comment text', hearing=hearing)

    def get_hearing_comment_vote_url(self, hearing_id, comment_id):
        # /v1/hearings/<hearingID>/comments/<commentID>/votes/
        return self.get_hearing_detail_url(hearing_id, 'comments/%s/vote' % comment_id)

    def get_hearing_comment_unvote_url(self, hearing_id, comment_id):
        # /v1/hearings/<hearingID>/comments/<commentID>/unvotes/
        return self.get_hearing_detail_url(hearing_id, 'comments/%s/unvote' % comment_id)

    def test_31_section_comment_vote_without_authentication(self, default_hearing):
        section, comment = self.add_default_section_and_comment(default_hearing)
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
        assert response.status_code == 403

    def test_31_hearing_comment_vote_without_authentication(self, default_hearing):
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 403

    def test_31_section_comment_vote_add_vote(self, default_hearing):
        self.user_login()
        section, comment = self.add_default_section_and_comment(default_hearing)
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
        assert response.status_code == 201

    def test_31_hearing_comment_vote_add_vote(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201

    def test_31_section_comment_vote_add_vote_check_voter(self, default_hearing):
        self.user_login()
        section, comment = self.add_default_section_and_comment(default_hearing)
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
        assert response.status_code == 201

        comments = SectionComment.objects.filter(id=comment.id, voters=self.user)
        assert len(comments) == 1

    def test_31_hearing_comment_vote_add_vote_check_voter(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        response = self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        assert response.status_code == 201

        comments = HearingComment.objects.filter(id=comment.id, voters=self.user)
        assert len(comments) == 1

    def test_31_section_comment_vote_add_vote_check_amount_of_votes(self, default_hearing):
        self.user_login()
        section, comment = self.add_default_section_and_comment(default_hearing)
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
        assert response.status_code == 201

        comment = SectionComment.objects.get(id=comment.id, voters=self.user)
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

    def test_31_section_comment_vote_add_second_vote(self, default_hearing):
        self.user_login()
        section, comment = self.add_default_section_and_comment(default_hearing)
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
        assert response.status_code == 201
        # Add vote again. Expect error, because vote has been given already.
        response = self.client.post(self.get_section_comment_vote_url(default_hearing.id, section.id, comment.id))
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

    def test_vote_appears_in_user_data(self, default_hearing):
        self.user_login()
        comment = self.add_default_hearing_comment(default_hearing)
        self.client.post(self.get_hearing_comment_vote_url(default_hearing.id, comment.id))
        scenario, sc_comment = self.add_default_scenario_and_comment(default_hearing)
        self.client.post(self.get_scenario_comment_vote_url(default_hearing.id, scenario.id, sc_comment.id))
        response = self.client.get('/v1/users/')
        assert comment.id in response.data[0]['voted_hearing_comments']
        assert sc_comment.id in response.data[0]['voted_scenario_comments']
