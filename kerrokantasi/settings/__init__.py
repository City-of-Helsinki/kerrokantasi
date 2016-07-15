from .util import get_settings, load_local_settings, load_secret_key
from . import base

settings = get_settings(base)
load_local_settings(settings, "local_settings")
load_secret_key(settings)

if not settings["DEBUG"] and settings["JWT_AUTH"]["JWT_SECRET_KEY"] == "kerrokantasi":
    raise ValueError("Refusing to run out of DEBUG mode with insecure JWT secret key.")

settings['CKEDITOR_CONFIGS'] = {
    'default': {
        'stylesSet': [
            {
                "name": 'Lead',
                "element": 'p',
                "attributes": {'class': 'lead'},
            },
        ],
        'contentsCss': ['%sckeditor/ckeditor/contents.css' % settings['STATIC_URL'], '.lead { font-weight: bold;}'],
        'extraAllowedContent': 'video [*]{*}(*);source [*]{*}(*);',
        'extraPlugins': 'video,dialog,fakeobjects,iframe',
        'toolbar': [
            ['Styles', 'Format'],
            ['Bold', 'Italic', 'Underline', 'StrikeThrough', 'Undo', 'Redo'],
            ['Link', 'Unlink', 'Anchor'],
            ['BulletedList', 'NumberedList'],
            ['Image', 'Video', 'Iframe', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Smiley', 'SpecialChar'],
            ['Source']
        ]
    },
}

globals().update(settings)  # Export the settings for Django to use.
