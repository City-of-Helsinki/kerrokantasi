import os

import environ
import sentry_sdk
import subprocess
from sentry_sdk.integrations.django import DjangoIntegration

gettext = lambda s: s # noqa makes possible to translate strings here

CONFIG_FILE_NAME = "config_dev.toml"


def get_git_revision_hash():
    """
    We need a way to retrieve git revision hash for sentry reports
    I assume that if we have a git repository available we will
    have git-the-command as well
    """
    try:
        # We are not interested in gits complaints
        git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL, encoding='utf8')
    # ie. "git" was not found
    # should we return a more generic meta hash here?
    # like "undefined"?
    except FileNotFoundError:
        git_hash = "git_not_available"
    # Ditto
    except subprocess.CalledProcessError:
        git_hash = "no_repository"
    return git_hash.rstrip()


root = environ.Path(__file__) - 3  # three levels back in hierarchy
env = environ.Env(
    # Common Django settings
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    ADMINS=(list, []),
    DATABASE_URL=(str, 'postgis:///kerrokantasi'),
    MEDIA_ROOT=(environ.Path(), root('media')),
    STATIC_ROOT=(environ.Path(), root('static')),
    MEDIA_URL=(str, '/media/'),
    STATIC_URL=(str, '/static/'),
    TRUST_X_FORWARDED_HOST=(bool, False),
    INTERNAL_IPS=(list, []),
    # Helsinki Django app settings
    SENTRY_DSN=(str, ''),
    SENTRY_ENVIRONMENT=(str, ''),
    COOKIE_PREFIX=(str, 'kerrokantasi'),
    URL_PREFIX=(str, ''),
    # Kerrokantasi specific settings
    DEMOCRACY_UI_BASE_URL=(str, 'http://localhost:8086'),
    SENDFILE_BACKEND=(str, 'sendfile.backends.development'),
    PROTECTED_ROOT=(environ.Path(), root('protected_media')),
    PROTECTED_URL=(str, '/protected_media/'),
    DEFAULT_MAP_COORDINATES=(tuple, (60.192059, 24.945831)),  # Coordinates of Helsinki
    DEFAULT_MAP_ZOOM=(int, 11),
    # Authentication settings
    OIDC_API_AUDIENCE=(str, ''),
    OIDC_API_SCOPE_PREFIX=(str, ''),
    OIDC_API_REQUIRE_SCOPE_FOR_AUTHENTICATION=(bool, True),
    OIDC_API_ISSUER=(str, ''),
    OIDC_API_AUTHORIZATION_FIELD=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_KEY=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_SECRET=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT=(str, ''),
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = root()

# Django environ has a nasty habit of complaining at level
# WARN abount env file not being present. Here we pre-empt it.
env_file_path = os.path.join(BASE_DIR, CONFIG_FILE_NAME)
if os.path.exists(env_file_path):
    print(f'Reading config from {env_file_path}')
    environ.Env.read_env(env_file_path)

#### Django standard settings handling ####

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
ADMINS = env('ADMINS')

DATABASES = {
    'default': env.db('DATABASE_URL')
}

MEDIA_ROOT = env('MEDIA_ROOT')
MEDIA_URL = env('MEDIA_URL')

STATIC_ROOT = env('STATIC_ROOT')
STATIC_URL = env('STATIC_URL')

USE_X_FORWARDED_HOST = env('TRUST_X_FORWARDED_HOST')

INTERNAL_IPS = env('INTERNAL_IPS')

#### Helsinki specific settings handling ####

# SENTRY_DSN is actually standard for sentry
if env('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        environment=env('SENTRY_ENVIRONMENT'),
        release=get_git_revision_hash(),
        integrations=[DjangoIntegration()]
    )

CSRF_COOKIE_NAME = '{}-csrftoken'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_NAME = '{}-sessionid'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_SECURE = False if DEBUG else True
# Useful when kerrokantasi API is served from a sub-path of a shared
# hostname (like api.yourorg.org)
SESSION_COOKIE_PATH = '/{}'.format(env('URL_PREFIX'))

#### Kerrokantasi specific settings handling ####

DEMOCRACY_UI_BASE_URL = env('DEMOCRACY_UI_BASE_URL')

SENDFILE_BACKEND = env('SENDFILE_BACKEND')
SENDFILE_ROOT = env('PROTECTED_ROOT')
SENDFILE_URL = env('PROTECTED_URL')

#### Settings below do not usually need changing ####

# CKEDITOR_CONFIGS is in __init__.py
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'

# Image files should not exceed 1MB (SI)
MAX_IMAGE_SIZE = 10**6

INSTALLED_APPS = [
    "helusers",
    "helusers.providers.helsinki_oidc",
    'social_django',    
    'helusers.apps.HelusersAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'modeltranslation',
    'mptt',
    'nested_admin',
    'rest_framework',
    'reversion',
    'corsheaders',
    'easy_thumbnails',
    'rest_framework_nested',
    'djgeojson',
    'leaflet',
    'ckeditor',
    'ckeditor_uploader',
    'munigeo',
    'kerrokantasi',  # User model is project-wide
    'democracy',  # Reusable participatory democracy app
    'parler',
    'django_filters',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'kerrokantasi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'helusers.context_processors.settings',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

LOGOUT_REDIRECT_URL = '/'

WSGI_APPLICATION = 'kerrokantasi.wsgi.application'

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = (
    ('fi', gettext('Finnish')),
    ('sv', gettext('Swedish')),
    ('en', gettext('English')),
)
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/[a-z0-9-]*/?v1/.*$'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'helusers.oidc.ApiTokenAuthentication',
        'django.contrib.auth.backends.ModelBackend',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'],
    'DEFAULT_VERSION': '1',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

DEMOCRACY_PLUGINS = {
    "mapdon-hkr": "democracy.plugins.Plugin",  # TODO: Create an actual class for this once we know the data format
    "mapdon-ksv": "democracy.plugins.Plugin",
    "mapdon-ksv-visualize": "democracy.plugins.Plugin",
    "map-bikeracks": "democracy.plugins.Plugin",
    "map-winterbiking": "democracy.plugins.Plugin"
}

PARLER_DEFAULT_LANGUAGE_CODE = 'en'
PARLER_LANGUAGES = {
    None: (
        {'code': 'en', },
        {'code': 'fi', },
        {'code': 'sv', },
    ),
    'default': {
        'hide_untranslated': False,
        'fallbacks': ['fi', 'en', 'sv'],
    }
}
PARLER_ENABLE_CACHING = False

DETECT_LANGS_MIN_PROBA = 0.3

FILTERS_NULL_CHOICE_LABEL = 'null'

OIDC_API_TOKEN_AUTH = {
    'AUDIENCE': env('OIDC_API_AUDIENCE'),
    'API_SCOPE_PREFIX': env('OIDC_API_SCOPE_PREFIX'),
    'API_AUTHORIZATION_FIELD': env('OIDC_API_AUTHORIZATION_FIELD'),
    'REQUIRE_API_SCOPE_FOR_AUTHENTICATION': env('OIDC_API_REQUIRE_SCOPE_FOR_AUTHENTICATION'),
    'ISSUER': env('OIDC_API_ISSUER'),
}

OIDC_AUTH = {"OIDC_LEEWAY": 60 * 60}

AUTHENTICATION_BACKENDS = (
    'helusers.tunnistamo_oidc.TunnistamoOIDCAuth',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'kerrokantasi.User'
LOGIN_REDIRECT_URL = '/'

SOCIAL_AUTH_TUNNISTAMO_KEY = env('SOCIAL_AUTH_TUNNISTAMO_KEY')
SOCIAL_AUTH_TUNNISTAMO_SECRET = env('SOCIAL_AUTH_TUNNISTAMO_SECRET')
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = env('SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT')

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Map defaults
DEFAULT_MAP_COORDINATES = env('DEFAULT_MAP_COORDINATES')
DEFAULT_MAP_ZOOM = env('DEFAULT_MAP_ZOOM')


LOGIN_URL = '/'
LOGOUT_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SITE_ID=1