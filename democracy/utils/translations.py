from django.conf import settings


def get_translations_dict(obj, field_name):
    """
    Returns a dict of translations for a given field of a model instance.

    :param obj: The model instance
    :param field_name: The name of the field
    :return: A dict with language codes as keys and translations as values
    """

    return {
        lang_code: getattr(obj.translations.filter(language_code=lang_code).first(), field_name, "")
        for lang_code, _ in settings.LANGUAGES
    }
