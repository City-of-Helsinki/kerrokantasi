from unittest.mock import Mock, patch

from helusers._oidc_auth_impl import ApiTokenAuthentication
from helusers.authz import UserAuthorization

from kerrokantasi.oidc import StrongApiTokenAuthentication


def test_api_token_authentication_none():
    auth = StrongApiTokenAuthentication()
    request = Mock()
    with patch.object(ApiTokenAuthentication, "authenticate") as super_authenticate:
        super_authenticate.return_value = None
        assert auth.authenticate(request) is None


def test_api_token_authentication_regular():
    authentication = StrongApiTokenAuthentication()
    user = Mock()
    authorization = UserAuthorization(user, {"amr": "FOO"})
    request = Mock()
    with patch.object(ApiTokenAuthentication, "authenticate") as super_authenticate:
        super_authenticate.return_value = (user, authorization)
        result = authentication.authenticate(request)
        assert result == (user, authorization)
        assert user.has_strong_auth is False


def test_api_token_authentication_strong(settings):
    settings.STRONG_AUTH_PROVIDERS = ("FOO",)
    authentication = StrongApiTokenAuthentication()
    user = Mock()
    authorization = UserAuthorization(user, {"amr": "FOO"})
    request = Mock()
    with patch.object(ApiTokenAuthentication, "authenticate") as super_authenticate:
        super_authenticate.return_value = (user, authorization)
        result = authentication.authenticate(request)
        assert result == (user, authorization)
        assert user.has_strong_auth is True
