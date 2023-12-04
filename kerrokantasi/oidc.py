from django.conf import settings
from helusers.oidc import ApiTokenAuthentication


class StrongApiTokenAuthentication(ApiTokenAuthentication):
    def authenticate(self, request):
        authentication_result = super().authenticate(request)
        if authentication_result is None:
            return None

        user, auth = authentication_result

        # amr (Authentication Methods References) should contain the used auth
        # provider name e.g. suomifi
        old_has_strong_auth = user.has_strong_auth
        user.has_strong_auth = auth.data.get("amr") in settings.STRONG_AUTH_PROVIDERS
        if user.has_strong_auth != old_has_strong_auth:
            # Strong auth status has changed, update it
            user.save(update_fields=["has_strong_auth"])

        return user, auth
