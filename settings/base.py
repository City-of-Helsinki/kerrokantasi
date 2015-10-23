# Django settings

import os

PROJECT_ROOT = os.path.sep.join(
    os.path.realpath(__file__).split(os.path.sep)[:-2])

# available languages
gettext = lambda s: s
LANGUAGES = (
    ('fi', gettext('Finish')),
    ('se', gettext('Swedish')),
    ('en', gettext('English')),
    )

# list of installed apps
INSTALLED_APPS = (
    'django-contrib-auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'modeltranslation',
    'django-contrib-admin',
    )

# default language for modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fi'


