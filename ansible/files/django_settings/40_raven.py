import raven

RAVEN_CONFIG = {
    'dsn': 'https://6d2e42fdea884ca09b926b61d0b457a9:50db3d011030410b9b7c37139058f51a@sentry.hel.ninja/17',
    # Needs to change if settings.py is not in an immediate child of the project
    'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
    'environment': 'production',
}
INSTALLED_APPS = INSTALLED_APPS + ['raven.contrib.django.raven_compat',]
