
import pytest

from democracy.factories.poll import SectionPollFactory, SectionPollOptionFactory
from democracy.models import SectionPoll, SectionPollAnswer
from democracy.tests.test_comment import get_comment_data
from democracy.tests.test_hearing import valid_hearing_json
from democracy.tests.test_section import create_sections
from democracy.tests.utils import get_data_from_response, assert_common_keys_equal


@pytest.fixture
def valid_hearing_json_with_poll(valid_hearing_json):
    valid_hearing_json['sections'][0]['questions'] = [
        {
            "type": "single-choice",
            "text": {
                "en": "Which is better?",
                "fi": "Kumpi on parempi?",
            },
            "independent_poll": True,
            "options": [
                {
                    "n_answers": 0,
                    "text": {
                        "en": "First option",
                        "fi": "Ensimmäinen vaihtoehto",
                    },
                },
                {
                    "n_answers": 0,
                    "text": {
                        "en": "Second option",
                        "fi": "Toinen vaihtoehto",
                    },
                },
            ],
            "n_answers": 0,
        },
        {
            "type": "multiple-choice",
            "text": {
                "en": "Both?",
                "fi": "Molemmat?",
            },
            "independent_poll": True,
            "options": [
                {
                    "n_answers": 0,
                    "text": {
                        "en": "Yes",
                        "fi": "kyllä",
                    },
                },
                {
                    "n_answers": 0,
                    "text": {
                        "en": "No",
                        "fi": "Ei",
                    },
                },
            ],
            "n_answers": 0,
        },
    ]
    return valid_hearing_json


@pytest.mark.django_db
def test_get_section_with_poll(api_client, default_hearing):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3)
    response = api_client.get('/v1/hearing/%s/sections/' % default_hearing.id)
    data = get_data_from_response(response)
    assert len(data[0]['questions']) == 1
    assert len(data[0]['questions'][0]['options']) == 3


@pytest.mark.django_db
def test_post_section_with_poll(valid_hearing_json_with_poll, john_smith_api_client):
    response = john_smith_api_client.post('/v1/hearing/', data=valid_hearing_json_with_poll, format='json')
    data = get_data_from_response(response, status_code=201)
    questions1 = valid_hearing_json_with_poll['sections'][0]['questions']
    questions2 = data['sections'][0]['questions']
    assert len(questions1) == len(questions2)
    assert len(questions1[0]['options']) == len(questions2[0]['options'])
    assert questions1[0]['text']['fi'] == questions2[0]['text']['fi']
    assert questions1[0]['options'][0]['text']['fi'] == questions2[0]['options'][0]['text']['fi']
    assert questions1[1]['options'][1]['text']['fi'] == questions2[1]['options'][1]['text']['fi']


@pytest.mark.django_db
def test_put_section_with_poll(valid_hearing_json_with_poll, john_smith_api_client):
    response = john_smith_api_client.post('/v1/hearing/', data=valid_hearing_json_with_poll, format='json')
    data = get_data_from_response(response, status_code=201)
    data['sections'][0]['questions'] = list(reversed(data['sections'][0]['questions']))
    data['sections'][0]['questions'][0]['options'] = list(reversed(data['sections'][0]['questions'][0]['options']))
    data['sections'][0]['questions'][0]['text']['en'] = 'Edited question'
    data['sections'][0]['questions'][0]['options'][0]['text']['en'] = 'Edited option'
    response = john_smith_api_client.put('/v1/hearing/%s/' % data['id'], data=data, format='json')
    updated_data = get_data_from_response(response, status_code=200)
    questions1 = valid_hearing_json_with_poll['sections'][0]['questions']
    questions2 = updated_data['sections'][0]['questions']
    assert data['sections'][0]['questions'][0]['text']['en'] == 'Edited question'
    assert data['sections'][0]['questions'][1]['text']['en'] == 'Which is better?'
    assert data['sections'][0]['questions'][0]['options'][0]['text']['en'] == 'Edited option'
    assert data['sections'][0]['questions'][0]['options'][1]['text']['en'] == 'Yes'


@pytest.mark.django_db
def test_post_section_poll_answer_unauthenticated(api_client, default_hearing, geojson_feature):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3)
    url = '/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, section.id)
    data = get_comment_data()
    data['answers'] = [{}]
    response = api_client.post(url, data=data)
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_section_poll_answer_single_choice(john_doe_api_client, default_hearing, geojson_feature):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3, type=SectionPoll.TYPE_SINGLE_CHOICE)
    option = poll.options.all().first()

    url = '/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, section.id)
    data = get_comment_data()
    data['answers'] = [{
        'question': poll.id,
        'type': SectionPoll.TYPE_SINGLE_CHOICE,
        'answers': [option.id],
    }]
    response = john_doe_api_client.post(url, data=data)
    assert response.status_code == 201
    poll.refresh_from_db(fields=['n_answers'])
    option.refresh_from_db(fields=['n_answers'])
    assert poll.n_answers == 1
    assert option.n_answers == 1


@pytest.mark.django_db
def test_post_section_poll_answer_multiple_choice(john_doe_api_client, default_hearing, geojson_feature):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3, type=SectionPoll.TYPE_MULTIPLE_CHOICE)
    option1, option2, option3 = poll.options.all()

    url = '/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, section.id)
    data = get_comment_data()
    data['answers'] = [{
        'question': poll.id,
        'type': SectionPoll.TYPE_MULTIPLE_CHOICE,
        'answers': [option1.id, option3.id],
    }]
    response = john_doe_api_client.post(url, data=data)
    assert response.status_code == 201
    poll.refresh_from_db(fields=['n_answers'])
    option1.refresh_from_db(fields=['n_answers'])
    option2.refresh_from_db(fields=['n_answers'])
    option3.refresh_from_db(fields=['n_answers'])
    assert poll.n_answers == 1
    assert option1.n_answers == 1
    assert option2.n_answers == 0
    assert option3.n_answers == 1


@pytest.mark.django_db
def test_patch_section_poll_answer(john_doe_api_client, default_hearing, geojson_feature):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3, type=SectionPoll.TYPE_MULTIPLE_CHOICE)
    option1, option2, option3 = poll.options.all()

    url = '/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, section.id)
    data = get_comment_data()
    data['answers'] = [{
        'question': poll.id,
        'type': SectionPoll.TYPE_MULTIPLE_CHOICE,
        'answers': [option1.id, option3.id],
    }]
    response = john_doe_api_client.post(url, data=data)
    assert response.status_code == 201

    url = '/v1/hearing/%s/sections/%s/comments/%s/' % (default_hearing.id, section.id, response.data['id'])
    data = response.data
    data['answers'][0]['answers'] = [option2.id, option3.id]
    response = john_doe_api_client.patch(url, data=data)
    assert response.status_code == 200

    option1.refresh_from_db(fields=['n_answers'])
    option2.refresh_from_db(fields=['n_answers'])
    option3.refresh_from_db(fields=['n_answers'])
    assert option1.n_answers == 0
    assert option2.n_answers == 1
    assert option3.n_answers == 1


@pytest.mark.django_db
def test_answers_appear_in_user_data(john_doe_api_client, default_hearing):
    section = default_hearing.sections.first()
    poll = SectionPollFactory(section=section, option_count=3, type=SectionPoll.TYPE_SINGLE_CHOICE)
    option = poll.options.all().first()
    data = get_comment_data()
    data['answers'] = [{'question': poll.id, 'type': SectionPoll.TYPE_SINGLE_CHOICE, 'answers': [option.id]}]
    john_doe_api_client.post('/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, section.id), data=data)
    response = john_doe_api_client.get('/v1/users/')
    assert poll.pk in response.data[0]['answered_questions']
