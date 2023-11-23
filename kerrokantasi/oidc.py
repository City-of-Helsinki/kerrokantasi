from django.conf import settings
from helusers.oidc import ApiTokenAuthentication


class StrongApiTokenAuthentication(ApiTokenAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)

        if result is None:
            return None

        user, auth = result

        # amr (Authentication Methods References) should contain the used auth
        # provider name e.g. suomifi
        old_has_strong_auth = user.has_strong_auth
        if auth.data.get("amr") in settings.STRONG_AUTH_PROVIDERS:
            user.has_strong_auth = True
        else:
            user.has_strong_auth = False

        if old_has_strong_auth != user.has_strong_auth:
            user.save(update_fields=["has_strong_auth"])

        return user, auth
