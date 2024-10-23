import datetime

import pytest
from helusers.settings import api_token_auth_settings
from jose import jwt

from democracy.factories.hearing import HearingFactory, SectionCommentFactory
from democracy.models import SectionComment
from kerrokantasi.tests.factories import UserFactory
from kerrokantasi.tests.gdpr.keys import rsa_key


@pytest.fixture
def single_comment_user():
    user = UserFactory()
    hearing = HearingFactory()
    section = hearing.get_main_section()
    SectionComment.objects.all().delete()
    SectionCommentFactory(section=section, created_by=user, author_name="Jay Jay Query")
    return user


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture(params=["true", "True", "TRUE", "1", 1, True])
def true_value(request):
    return request.param


@pytest.fixture(params=["false", "False", "FALSE", "0", 0, False])
def false_value(request):
    return request.param


def get_api_token_for_user_with_scopes(user, scopes: list, requests_mock):
    """Build a proper auth token with desired scopes."""
    audience = api_token_auth_settings.AUDIENCE
    if isinstance(audience, list):
        audience = audience[0]
    issuer = api_token_auth_settings.ISSUER
    if isinstance(issuer, list):
        issuer = issuer[0]
    config_url = f"{issuer}/.well-known/openid-configuration"
    jwks_url = f"{issuer}/jwks"

    configuration = {
        "issuer": issuer,
        "jwks_uri": jwks_url,
    }

    keys = {"keys": [rsa_key.public_key_jwk]}

    now = datetime.datetime.now()
    expire = now + datetime.timedelta(days=14)

    jwt_data = {
        "iss": issuer,
        "aud": audience,
        "sub": str(user.uuid),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        # Use hardcoded keycloak field, see override_settings_oidc_api_authorization_field
        "authorization": {"permissions": [{"scopes": scopes}]},
    }
    encoded_jwt = jwt.encode(
        jwt_data, key=rsa_key.private_key_pem, algorithm=rsa_key.jose_algorithm
    )

    requests_mock.get(config_url, json=configuration)
    requests_mock.get(jwks_url, json=keys)

    auth_header = f"{api_token_auth_settings.AUTH_SCHEME} {encoded_jwt}"

    return auth_header
