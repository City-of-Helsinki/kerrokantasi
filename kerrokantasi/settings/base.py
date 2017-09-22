import os
gettext = lambda s: s

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '52k^*)c*bz9t0lzsf_$a+jl3zcy6re!gnw77__)y(#v91-p%tp'
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'kerrokantasi',  # User model is project-wide
    'democracy',  # Reusable participatory democracy app
    'parler',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
AUTH_USER_MODEL = 'kerrokantasi.User'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "var", "static")
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "var", "media")
LANGUAGES = (
    ('fi', gettext('Finnish')),
    ('sv', gettext('Swedish')),
    ('en', gettext('English')),
)
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/[a-z-]*/?v1/.*$'

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


JWT_AUTH = {
    'JWT_PAYLOAD_GET_USER_ID_HANDLER': 'helusers.jwt.get_user_id_from_payload_handler',
    'JWT_SECRET_KEY': 'kerrokantasi',
    'JWT_AUDIENCE': 'kerrokantasi'
}


DEMOCRACY_UI_BASE_URL = 'http://localhost:8086'
DEMOCRACY_PLUGINS = {
    "mapdon-hkr": "democracy.plugins.Plugin",  # TODO: Create an actual class for this once we know the data format
    "mapdon-ksv": "democracy.plugins.Plugin",
    "mapdon-ksv-visualize": "democracy.plugins.Plugin",
    "map-questionnaire": "democracy.plugins.Plugin",
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
