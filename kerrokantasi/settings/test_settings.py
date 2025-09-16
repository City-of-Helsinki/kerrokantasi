from . import *  # noqa

# Using globals() to avoid issues with type checking which most likely
# can not follow the use of globals().update in the settings.__init__

OIDC_API_TOKEN_AUTH = globals()["OIDC_API_TOKEN_AUTH"]
OIDC_API_TOKEN_AUTH["API_AUTHORIZATION_FIELD"] = ["authorization.permissions.scopes"]
OIDC_API_TOKEN_AUTH["ISSUER"] = ["http://test.local:8000/openid"]
OIDC_API_TOKEN_AUTH["REQUIRE_API_SCOPE_FOR_AUTHENTICATION"] = False

TIME_ZONE = "UTC"
