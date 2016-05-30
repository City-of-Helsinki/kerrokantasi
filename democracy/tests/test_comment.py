import datetime

import pytest
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.timezone import now
from reversion import revisions

from democracy.enums import Commenting, InitialSectionType
from democracy.models import Hearing, Section, SectionType
from democracy.models.section import SectionComment
from democracy.tests.conftest import default_comment_content
from democracy.tests.test_images import get_hearing_detail_url
from democracy.tests.utils import get_data_from_response, assert_common_keys_equal


def get_comment_data(**extra):
    return dict({
        'content': default_comment_content,
        'section': None
    }, **extra)


def get_intro_comments_url(hearing, lookup_field='id'):
    return '/v1/hearing/%s/sections/%s/comments/' % (getattr(hearing, lookup_field), hearing.get_intro_section().id)


@pytest.fixture(params=['nested_by_id', 'nested_by_slug', 'root'])
def get_comments_url_and_data(request):
    """
    A fixture to test three different comment endpoints:
    - /v1/hearing/<hearing id>/sections/<section id>/comments/
    - /v1/hearing/<hearing slug>/sections/<section id>/comments/
    - /v1/comments/?section=<section id>

    Returns the URL and comment data which contains also section ID in case
    the current endpoint is the root endpoint.
    """
    nested_url = '/v1/hearing/%s/sections/%s/comments/'
    return {
        'nested_by_id': lambda hearing, section: (nested_url % (hearing.id, section.id), get_comment_data()),
        'nested_by_slug': lambda hearing, section: (nested_url % (hearing.id, section.id), get_comment_data()),
        'root': lambda hearing, section: ('/v1/comment/?section=%s' % section.id, get_comment_data(section=section.id))
    }[request.param]


@pytest.fixture(params=['id', 'slug'])
def lookup_field(request):
    return request.param


@pytest.mark.django_db
def test_56_add_comment_to_section_without_authentication(api_client, default_hearing, get_comments_url_and_data):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    response = api_client.post(url, data=data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_56_add_comment_to_section_without_data(api_client, default_hearing, get_comments_url_and_data):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    post_data = {'section': data['section']} if 'section' in data else None
    response = api_client.post(url, data=post_data)
    # expect bad request, we didn't set any data except section if this request was for the root level endpoint
    assert response.status_code == 400


@pytest.mark.django_db
def test_56_add_comment_to_section(john_doe_api_client, default_hearing, get_comments_url_and_data):
    section = default_hearing.sections.first()
    url, data = get_comments_url_and_data(default_hearing, section)
    old_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if 'results' in old_comment_list:
        old_comment_list = old_comment_list['results']

    # set section explicitly
    comment_data = get_comment_data(section=section.pk)
    response = john_doe_api_client.post(url, data=comment_data)

    data = get_data_from_response(response, status_code=201)
    assert 'section' in data
    assert data['section'] == section.pk

    assert 'content' in data
    assert data['content'] == default_comment_content

    # Check that the comment is available in the comment endpoint now
    new_comment_list = get_data_from_response(john_doe_api_client.get(url))

    # If pagination is used the actual data is in "results"
    if 'results' in new_comment_list:
        new_comment_list = new_comment_list['results']

    assert len(new_comment_list) == len(old_comment_list) + 1
    new_comment = [c for c in new_comment_list if c["id"] == data["id"]][0]
    assert_common_keys_equal(new_comment, comment_data)
    assert_common_keys_equal(new_comment["created_by"], {
        "first_name": john_doe_api_client.user.first_name,
        "last_name": john_doe_api_client.user.last_name,
        "username": john_doe_api_client.user.username,
    })



@pytest.mark.django_db
def test_56_get_hearing_with_section_check_n_comments_property(api_client, get_comments_url_and_data):
    hearing = Hearing.objects.create(
        title='Test Hearing',
        abstract='Hearing to test section comments',
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
    )
    section = Section.objects.create(
        title='Section to comment',
        hearing=hearing,
        commenting=Commenting.OPEN,
        type=SectionType.objects.get(identifier=InitialSectionType.PART)
    )
    url, data = get_comments_url_and_data(hearing, section)

    response = api_client.post(url, data=data)
    assert response.status_code == 201, ("response was %s" % response.content)

    # get hearing and check sections's n_comments property
    url = get_hearing_detail_url(hearing.id)
    response = api_client.get(url)

    data = get_data_from_response(response)
    assert 'n_comments' in data['sections'][0]
    assert data['sections'][0]['n_comments'] == 1


@pytest.mark.django_db
def test_n_comments_updates(admin_user, default_hearing):
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 9
    comment = default_hearing.get_intro_section().comments.create(created_by=admin_user, content="Hello")
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 10
    comment.soft_delete()
    assert Hearing.objects.get(pk=default_hearing.pk).n_comments == 9


@pytest.mark.django_db
def test_comment_edit_versioning(john_doe_api_client, default_hearing, lookup_field):
    url = get_intro_comments_url(default_hearing, lookup_field)
    response = john_doe_api_client.post(url, data={"content": "THIS SERVICE SUCKS"})
    data = get_data_from_response(response, 201)
    comment_id = data["id"]
    comment = SectionComment.objects.get(pk=comment_id)
    assert comment.content.isupper()  # Oh my, all that screaming :(
    assert not revisions.get_for_object(comment)  # No revisions
    response = john_doe_api_client.patch('%s%s/' % (url, comment_id), data={
        "content": "Never mind, it's nice :)"
    })
    data = get_data_from_response(response, 200)
    comment = SectionComment.objects.get(pk=comment_id)
    assert not comment.content.isupper()  # Screaming is gone
    assert len(revisions.get_for_object(comment)) == 1  # One old revision


@pytest.mark.django_db
def test_correct_m2m_fks(admin_user, default_hearing):
    first_section = default_hearing.sections.first()
    section_comment = first_section.comments.create(created_by=admin_user, content="hello")
    sc_voters_query = force_text(section_comment.voters.all().query)
    assert "sectioncomment" in sc_voters_query and "hearingcomment" not in sc_voters_query


comment_status_spec = {
    Commenting.NONE: (403, 403),
    Commenting.REGISTERED: (403, 201),
    Commenting.OPEN: (201, 201),
}


@pytest.mark.django_db
@pytest.mark.parametrize("commenting", comment_status_spec.keys())
def test_commenting_modes(api_client, john_doe_api_client, default_hearing, commenting):
    intro_section = default_hearing.get_intro_section()
    intro_section.commenting = commenting
    intro_section.save(update_fields=('commenting',))

    anon_status, reg_status = comment_status_spec[commenting]
    url = get_intro_comments_url(default_hearing)
    response = api_client.post(url, data=get_comment_data())
    assert response.status_code == anon_status
    response = john_doe_api_client.post(url, data=get_comment_data())
    assert response.status_code == reg_status


@pytest.mark.django_db
def test_comment_edit_auth(john_doe_api_client, jane_doe_api_client, api_client, default_hearing, lookup_field):
    url = get_intro_comments_url(default_hearing, lookup_field)

    # John posts an innocuous comment:
    johns_message = "Hi! I'm John!"
    response = john_doe_api_client.post(url, data={"content": johns_message})
    data = get_data_from_response(response, 201)
    comment_id = data["id"]

    # Now Jane (in the guise of Mallory) attempts a rogue edit:
    response = jane_doe_api_client.patch('%s%s/' % (url, comment_id), data={"content": "hOI! I'M TEMMIE"})

    # But her attempts are foiled!
    data = get_data_from_response(response, 403)
    assert SectionComment.objects.get(pk=comment_id).content == johns_message

    # Jane, thinking she can bamboozle our authentication by logging out, tries again!
    response = api_client.patch('%s%s/' % (url, comment_id), data={"content": "I'm totally John"})

    # But still, no!
    data = get_data_from_response(response, 403)
    assert SectionComment.objects.get(pk=comment_id).content == johns_message


@pytest.mark.django_db
def test_comment_editing_disallowed_after_closure(john_doe_api_client, default_hearing):
    # Post a comment:
    url = '/v1/hearing/%s/sections/%s/comments/' % (default_hearing.id, default_hearing.get_intro_section().id)
    response = john_doe_api_client.post(url, data=get_comment_data())
    data = get_data_from_response(response, status_code=201)
    comment_id = data["id"]
    # Successfully edit the comment:
    response = john_doe_api_client.patch('%s%s/' % (url, comment_id), data={
        "content": "Hello"
    })
    data = get_data_from_response(response, status_code=200)
    assert data["content"] == "Hello"
    # Close the hearing:
    default_hearing.close_at = default_hearing.open_at
    default_hearing.save()
    # Futilely attempt to edit the comment:
    response = john_doe_api_client.patch('%s%s/' % (url, comment_id), data={
        "content": "No"
    })
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("case", ("plug-valid", "plug-invalid", "noplug"))
def test_add_plugin_data_to_comment(api_client, default_hearing, case):
    with override_settings(
        DEMOCRACY_PLUGINS={
            "test_plugin": "democracy.tests.plug.TestPlugin"
        }
    ):
        section = default_hearing.sections.first()
        if case.startswith("plug"):
            section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(default_hearing.id, 'sections/%s/comments' % section.id)
        comment_data = get_comment_data(
            content="",
            plugin_data=("foo6" if case == "plug-valid" else "invalid555")
        )
        response = api_client.post(url, data=comment_data)
        if case == "plug-valid":
            assert response.status_code == 201
            created_comment = SectionComment.objects.last()
            assert created_comment.plugin_identifier == section.plugin_identifier
            assert created_comment.plugin_data == comment_data["plugin_data"][::-1]  # The TestPlugin reverses data
        elif case == "plug-invalid":
            data = get_data_from_response(response, status_code=400)
            assert data == {"plugin_data": ["The data must contain a 6."]}
        elif case == "noplug":
            data = get_data_from_response(response, status_code=400)
            assert "no plugin data is allowed" in data["plugin_data"][0]
        else:
            raise NotImplementedError("...")


@pytest.mark.django_db
def test_do_not_get_plugin_data_for_comment(api_client, default_hearing):
    with override_settings(
        DEMOCRACY_PLUGINS={
            "test_plugin": "democracy.tests.plug.TestPlugin"
        }
    ):
        section = default_hearing.sections.first()
        section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(default_hearing.id, 'sections/%s/comments' % section.id)
        comment_data = get_comment_data(
            content="",
            plugin_data="foo6"
        )
        response = api_client.post(url, data=comment_data)
        response_data = get_data_from_response(response, status_code=201)
        comment_list = get_data_from_response(api_client.get(url))
        created_comment = [c for c in comment_list if c["id"] == response_data["id"]][0]
        assert "plugin_data" not in created_comment


@pytest.mark.django_db
def test_get_plugin_data_for_comment(api_client, default_hearing):
    with override_settings(
        DEMOCRACY_PLUGINS={
            "test_plugin": "democracy.tests.plug.TestPlugin"
        }
    ):
        section = default_hearing.sections.first()
        section.plugin_identifier = "test_plugin"
        section.save()
        url = get_hearing_detail_url(default_hearing.id, 'sections/%s/comments' % section.id)
        comment_data = get_comment_data(
            content="",
            plugin_data="foo6"
        )
        response = api_client.post(url, data=comment_data)
        response_data = get_data_from_response(response, status_code=201)
        comment_list = get_data_from_response(api_client.get(url, {"include": "plugin_data"}))
        created_comment = [c for c in comment_list if c["id"] == response_data["id"]][0]
        assert created_comment["plugin_data"] == comment_data["plugin_data"][::-1]  # The TestPlugin reverses data


@pytest.mark.parametrize('data', [{'section': 'nonexistingsection'}, None])
@pytest.mark.django_db
def test_post_to_root_endpoint_invalid_section(api_client, default_hearing, data):
    url = '/v1/comment/'

    response = api_client.post(url, data=data)
    assert response.status_code == 400
    assert 'section' in response.data

    comment = default_hearing.sections.first().comments.first()
    url = '%s%s/' % (url, comment.id)

    response = api_client.put(url, data)
    assert response.status_code == 400
    assert 'section' in response.data


@pytest.mark.django_db
def test_root_endpoint_filters(api_client, default_hearing, random_hearing):
    url = '/v1/comment/'
    section = default_hearing.sections.first()
    for i, comment in enumerate(section.comments.all()):
        comment.authorization_code = 'auth_code_%s' % i
        comment.save(update_fields=('authorization_code',))

    response = api_client.get('%s?authorization_code=%s' % (url, section.comments.first().authorization_code))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 1

    response = api_client.get('%s?section=%s' % (url, section.id))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 3

    response = api_client.get('%s?hearing=%s' % (url, default_hearing.id))
    response_data = get_data_from_response(response)
    assert len(response_data['results']) == 9


@pytest.mark.parametrize('hearing_update', [
    ('deleted', True),
    ('published', False),
    ('open_at', now() + datetime.timedelta(days=1))
])
@pytest.mark.django_db
def test_root_endpoint_filtering_by_hearing_visibility(api_client, default_hearing, hearing_update):
    setattr(default_hearing, hearing_update[0], hearing_update[1])
    default_hearing.save()

    response = api_client.get('/v1/comment/')
    response_data = get_data_from_response(response)['results']
    assert len(response_data) == 0
