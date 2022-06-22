from kerrokantasi.settings import base
from kerrokantasi.settings.util import get_settings, load_local_settings

print('reading settings')
settings = get_settings(base)
print('read base settings')
load_local_settings(settings, "local_settings")
print('read local settings')

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
