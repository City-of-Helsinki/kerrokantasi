import datetime
import os
import urllib
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.timezone import now
import pytest
import reversion
from kk.models import Hearing, Scenario
from kk.models.hearing import HearingComment
from kk.tests.base import BaseKKDBTest, default_hearing
from kk.tests.utils import assert_datetime_fuzzy_equal, get_data_from_response


class TestComment(BaseKKDBTest):
    def setup(self):
        super(TestComment, self).setup()

        self.default_content = 'I agree with you sir Lancelot. My favourite colour is blue'
        self.red_content = 'Mine is red'
        self.green_content = 'I like green'
        self.comment_data = {
            'content': self.default_content,
            'scenario': None
        }

    def create_default_comments(self, hearing):
        # add three comments
        response = self.client.post(self.get_hearing_detail_url(hearing.id, 'comments'), data=self.comment_data)
        data = {}
        data['content'] = self.red_content
        response = self.client.post(self.get_hearing_detail_url(hearing.id, 'comments'), data=data)
        data['content'] = self.green_content
        response = self.client.post(self.get_hearing_detail_url(hearing.id, 'comments'), data=data)

    def test_55_add_comment_without_authentication(self, default_hearing):
        # post data to hearing ednpoint /v1/hearings/<hearingID>/comments/
        response = self.client.post(self.get_hearing_detail_url(default_hearing.id, 'comments'), data=self.comment_data)
        assert response.status_code == 403

    def test_55_add_comment_to_hearing_empty_data(self, default_hearing):
        pytest.xfail("Not sure what this is testing")
        # authenticate first
        self.user_login()

        # post data to hearing ednpoint /v1/hearings/<hearingID>/comments/
        response = self.client.post(self.get_hearing_detail_url(default_hearing.id, 'comments'), data=None)
        assert response.status_code == 400

        data = self.get_data_from_response(response)
        assert data is not None

    def test_55_add_comment_to_hearing_invalid_data(self, default_hearing):
        pytest.xfail("Not sure what this is testing")
        # authenticate first
        self.user_login()

        # post data to hearing ednpoint /v1/hearings/<hearingID>/comments/
        invalid_data = {
            'invalidKey': 'Korben Dallas multipass'
        }
        response = self.client.post(self.get_hearing_detail_url(default_hearing.id, 'comments'), data=invalid_data)
        assert response.status_code == 400

        data = self.get_data_from_response(response)
        assert data is not None

    def test_55_add_comment_to_hearing(self, default_hearing):
        # authenticate first
        self.user_login()

        # post data to hearing ednpoint /v1/hearings/<hearingID>/comments/
        response = self.client.post(self.get_hearing_detail_url(default_hearing.id, 'comments'), data=self.comment_data)
        assert response.status_code in [200, 201]

        data = self.get_data_from_response(response)
        assert data['created_by'] == self.username
        assert data['content'] == self.default_content
        assert data['votes'] == 0

    def test_54_list_all_comments_added_to_hearing_check_amount(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        assert len(data) == 3

    def test_54_list_all_comments_added_to_hearing_check_all_properties(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        # get first returned comment
        comment = data[0]

        assert 'content' in comment
        assert 'created_at' in comment
        assert 'votes' in comment
        assert 'created_by' in comment

    def test_54_list_all_comments_added_to_hearing_check_content(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        contents = [c['content'] for c in data]

        assert self.default_content in contents
        assert self.red_content in contents
        assert self.green_content in contents

    def test_54_list_all_comments_added_to_hearing_check_votes(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        for comment in data:
            assert comment['votes'] == 0

    def test_54_list_all_comments_added_to_hearing_check_created_by(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        for comment in data:
            assert comment['created_by'] == self.username

    def test_54_list_all_comments_added_to_hearing_check_created_at(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id, 'comments'))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        for comment in data:
            assert_datetime_fuzzy_equal(now(), comment['created_at'])

    def test_54_get_hearing_with_comments_check_amount_of_comments(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        assert 'comments' in data

        assert len(data['comments']) == 3

    def test_54_get_hearing_with_comments_check_n_comments_property(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        assert data['n_comments'] == 3

    def test_54_get_hearing_with_comments_check_comment_properties(self, default_hearing):
        self.user_login()
        self.create_default_comments(default_hearing)

        # list all comments
        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        assert 'comments' in data

        # get first comment to check
        comment = data['comments'][0]

        assert 'content' in comment
        assert 'created_at' in comment
        assert 'votes' in comment
        assert 'created_by' in comment

    def test_56_add_comment_to_scenario_without_authentication(self, default_hearing):
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)

        # post data to scenario endpoint /v1/hearing/<hearingID>/scenarios/<scenarioID>/comments/
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        response = self.client.post(url, data=self.comment_data)
        # expect forbidden
        assert response.status_code == 403

    def test_56_add_comment_to_scenario_scenario_pk_none(self, default_hearing):
        pytest.xfail("not required anymore")
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)
        self.user_login()
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        response = self.client.post(url, data=self.comment_data)
        # expect bad request, we didn't specify scenario id
        assert response.status_code == 400

    def test_56_add_comment_to_scenario_content_none(self, default_hearing):
        pytest.xfail("not sure what this is testing")
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)
        self.user_login()
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        # nullify content
        self.comment_data['content'] = None
        response = self.client.post(url, data=self.comment_data)
        # expect bad request, we didn't set any content
        assert response.status_code == 400

    def test_56_add_comment_to_scenario_without_data(self, default_hearing):
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)
        self.user_login()
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        response = self.client.post(url, data=None)
        # expect bad request, we didn't set any data
        assert response.status_code == 400

    def test_56_add_comment_to_scenario_invalid_key(self, default_hearing):
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)
        self.user_login()
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        response = self.client.post(url, data={'invalidKey': 'Yes it is'})
        # expect bad request, we have invalid key in payload
        assert response.status_code == 400

    def test_56_add_comment_to_scenario(self, default_hearing):
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=default_hearing)
        self.user_login()
        url = self.get_hearing_detail_url(default_hearing.id, 'scenarios/%s/comments' % scenario.id)

        # set scenario explicitly
        self.comment_data['scenario'] = scenario.pk
        response = self.client.post(url, data=self.comment_data)
        assert response.status_code == 201

        data = self.get_data_from_response(response)
        assert 'scenario' in data
        assert data['scenario'] == scenario.pk

        assert 'content' in data
        assert data['content'] == self.default_content

    def test_56_get_hearing_with_scenario_check_n_comments_property(self):
        hearing = Hearing.objects.create(abstract='Hearing to test scenario comments')
        scenario = Scenario.objects.create(title='Scenario to comment', hearing=hearing)
        self.user_login()
        url = self.get_hearing_detail_url(hearing.id, 'scenarios/%s/comments' % scenario.id)

        self.comment_data['scenario'] = scenario.pk
        response = self.client.post(url, data=self.comment_data)
        assert response.status_code == 201

        # get hearing and check scenarios's n_comments property
        url = self.get_hearing_detail_url(hearing.id)
        response = self.client.get(url)
        assert response.status_code == 200

        data = self.get_data_from_response(response)
        assert 'n_comments' in data['scenarios'][0]
        assert data['scenarios'][0]['n_comments'] == 1


@pytest.mark.django_db
def test_n_comments_updates(admin_user, default_hearing):
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 0
    comment = default_hearing.comments.create(created_by=admin_user, content="Hello")
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 1
    comment.soft_delete()
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 0


@pytest.mark.django_db
def test_comment_edit_versioning(john_doe_api_client, random_hearing):
    response = john_doe_api_client.post('/v1/hearing/%s/comments/' % random_hearing.pk, data={
        "content": "THIS SERVICE SUCKS"
    })
    data = get_data_from_response(response, 201)
    comment_id = data["id"]
    comment = HearingComment.objects.get(pk=comment_id)
    assert comment.content.isupper()  # Oh my, all that screaming :(
    assert not reversion.get_for_object(comment)  # No revisions
    response = john_doe_api_client.patch('/v1/hearing/%s/comments/%s/' % (random_hearing.pk, comment_id), data={
        "content": "Never mind, it's nice :)"
    })
    data = get_data_from_response(response, 200)
    comment = HearingComment.objects.get(pk=comment_id)
    assert not comment.content.isupper()  # Screaming is gone
    assert len(reversion.get_for_object(comment)) == 1  # One old revision


@pytest.mark.django_db
def test_correct_m2m_fks(admin_user, default_hearing):
    hearing_comment = default_hearing.comments.create(created_by=admin_user, content="hello")
    first_scenario = default_hearing.scenarios.first()
    scenario_comment = first_scenario.comments.create(created_by=admin_user, content="hello")
    hc_voters_query = force_text(hearing_comment.voters.all().query)
    sc_voters_query = force_text(scenario_comment.voters.all().query)
    assert "scenariocomment" in sc_voters_query and "hearingcomment" not in sc_voters_query
    assert "hearingcomment" in hc_voters_query and "scenariocomment" not in hc_voters_query
