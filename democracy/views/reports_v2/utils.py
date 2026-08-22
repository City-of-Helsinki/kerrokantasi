from django.conf import settings
from django.utils.dateparse import parse_datetime
from pptx.util import Pt


def get_default_translation(field: dict, lang_code: str):
    """
    Returns given field's translated value based on settings LANGUAGE_CODE.
    When settings language is not found in given field, any other available
    translation is returned or an empty string when no translation is present.
    """
    lang = lang_code if lang_code else settings.LANGUAGE_CODE
    if field.get(lang):
        return field.get(lang)
    for _, value in field.items():
        if value:
            return value
    return ""


def get_selected_language(lang: str | None) -> str:
    """Returns a supported language code based on given lang param or fi by default"""
    if lang == "en":
        return "en"
    return "fi"


def get_formatted_hearing_timerange(open_at: str, close_at: str) -> str:
    """
    Returns a formatted time range string based on given open and close times
    in format "from-to" e.g. "24.3.-4.5.2022".
    """
    open_at = parse_datetime(open_at)
    close_at = parse_datetime(close_at)
    open_at_timeunits = ["%d.", "%m.", "%Y"]
    if open_at.year == close_at.year:
        # remove redundant year
        open_at_timeunits = ["%d.", "%m."]
        if open_at.month == close_at.month:
            # remove redundant month
            open_at_timeunits = ["%d."]
    open_at_formatted = open_at.strftime("".join(open_at_timeunits))
    close_at_formatted = close_at.strftime("%d.%m.%Y")
    return f"{open_at_formatted}-{close_at_formatted}"


def get_powerpoint_title_font_size(text: str, is_main_title: bool = True) -> int:
    """Returns correct font size for a powerpoint title"""
    text_length = len(text)
    if is_main_title:
        font_sizes = ((40, 56), (60, 40), (90, 36), (160, 28))
        default_font_size = 24
    else:
        font_sizes = ((100, 50), (120, 44), (200, 36))
        default_font_size = 28
    font_size = next(
        (size for max_length, size in font_sizes if text_length <= max_length),
        default_font_size,
    )
    return Pt(font_size)
