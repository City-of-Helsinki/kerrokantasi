from django.conf import settings
from helusers.oidc import ApiTokenAuthentication as HelApiTokenAuth


class ApiTokenAuthentication(HelApiTokenAuth):
    def __init__(self, *args, **kwargs):
        super(ApiTokenAuthentication, self).__init__(*args, **kwargs)

    def authenticate(self, request):
        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        payload = self.decode_jwt(jwt_value)
        user, auth = super(ApiTokenAuthentication, self).authenticate(request)

        # amr (Authentication Methods References) should contain the used auth
        # provider name e.g. suomifi
        if payload.get('amr') in settings.STRONG_AUTH_PROVIDERS:
            user.has_strong_auth = True
        else:
            user.has_strong_auth = False

        user.save()
        return (user, auth)
