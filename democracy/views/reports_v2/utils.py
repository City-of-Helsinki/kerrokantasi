from django.conf import settings
from django.utils.dateparse import parse_datetime
from pptx.util import Pt
from typing import Union


def get_default_translation(field: dict, lang_code: str):
    """
    Returns given field's translated value based on settings LANGUAGE_CODE.
    When settings language is not found in given field, any other available
    translation is returned or an empty string when no translation is present.
    """
    lang = lang_code if lang_code else settings.LANGUAGE_CODE
    if field.get(lang):
        return field.get(lang)
    for lang, value in field.items():
        if value:
            return value
    return ""


def get_selected_language(lang: Union[str, None]) -> str:
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
        if text_length <= 40:
            return Pt(56)
        if text_length <= 60:
            return Pt(40)
        if text_length <= 90:
            return Pt(36)
        if text_length <= 160:
            return Pt(28)
        return Pt(24)
    else:
        if text_length <= 100:
            return Pt(50)
        if text_length <= 120:
            return Pt(44)
        if text_length <= 200:
            return Pt(36)
        return Pt(28)
