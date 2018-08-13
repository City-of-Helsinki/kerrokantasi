import os

import environ
import raven

gettext = lambda s: s

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
root = environ.Path(BASE_DIR)

env = environ.Env()

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    ADMINS=(list, []),
    DATABASE_URL=(str, 'postgis:///kerrokantasi'),
    JWT_SECRET_KEY=(str, ''),
    JWT_AUDIENCE=(str, ''),
    MEDIA_ROOT=(environ.Path(), root('media')),
    STATIC_ROOT=(environ.Path(), root('static')),
    MEDIA_URL=(str, '/media/'),
    STATIC_URL=(str, '/static/'),
    SENTRY_DSN=(str, ''),
    SENTRY_ENVIRONMENT=(str,''),
    COOKIE_PREFIX=(str, 'kerrokantasi'),
    DEMOCRACY_UI_BASE_URL=(str, 'http://localhost:8086'),
    TRUST_X_FORWARDED_HOST=(bool, False),
)

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
ADMINS = env('ADMINS')

DATABASES = {
    'default': env.db('DATABASE_URL')
}

JWT_AUTH = {
    'JWT_SECRET_KEY': env('JWT_SECRET_KEY'),
    'JWT_AUDIENCE': env('JWT_AUDIENCE')
}

MEDIA_ROOT = env('MEDIA_ROOT')
MEDIA_URL = env('MEDIA_URL')

STATIC_ROOT = env('STATIC_ROOT')
STATIC_URL = env('STATIC_URL')

SENTRY_DSN = env('SENTRY_DSN')

RAVEN_CONFIG = {
    'dsn': env('SENTRY_DSN'),
    'environment': env('SENTRY_ENVIRONMENT'),
    'release': raven.fetch_git_sha(BASE_DIR),
}

CSRF_COOKIE_NAME = '{}-csrftoken'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_NAME = '{}-sessionid'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_PATH = '/{}'.format(env('COOKIE_PREFIX'))

DEMOCRACY_UI_BASE_URL = env('DEMOCRACY_UI_BASE_URL')

USE_X_FORWARDED_HOST = env('TRUST_X_FORWARDED_HOST')

### Settings below do not usually need changing

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'helusers',
    'munigeo',
    'kerrokantasi',  # User model is project-wide
    'democracy',  # Reusable participatory democracy app
    'parler',
    'django_filters',
]

if RAVEN_CONFIG['dsn']:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'kerrokantasi.wsgi.application'

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
AUTH_USER_MODEL = 'kerrokantasi.User'
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
        'helusers.jwt.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'],
    'DEFAULT_VERSION': '1',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

JWT_AUTH['JWT_PAYLOAD_GET_USER_ID_HANDLER'] = 'helusers.jwt.get_user_id_from_payload_handler'

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

# CKEDITOR_CONFIGS is in __init__.py
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'

# Image files should not exceed 1MB (SI)
MAX_IMAGE_SIZE = 10**6

SENDFILE_BACKEND = 'sendfile.backends.development'
SENDFILE_ROOT = os.path.join(BASE_DIR, "var", "protected")
SENDFILE_URL = '/protected'
