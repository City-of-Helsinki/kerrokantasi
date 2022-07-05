import pytest
from pptx.util import Pt

# pylint: disable=import-error
from democracy.views.reports_v2.utils import (
        get_default_translation,
        get_formatted_hearing_timerange,
        get_powerpoint_title_font_size,
        get_selected_language,
    )

@pytest.mark.parametrize('lang_code, expected', [
    ('fi', 'fi_test'),
    ('en', 'en_test'),
    ('sv', 'sv_test'),
    ('aa', 'fi_test'),
])
def test_get_default_translation_returns_correct_str(lang_code, expected):
    '''Tests that correct translation is returned from a field'''
    test_field = {'fi': 'fi_test', 'en': 'en_test', 'sv': 'sv_test'}
    assert get_default_translation(test_field, lang_code) == expected


@pytest.mark.parametrize('lang_code, expected', [
    ('fi', 'fi'),
    ('en', 'en'),
    ('sv', 'fi'),
    (None, 'fi'),
])
def test_get_selected_language_returns_correct_lang_code(lang_code, expected):
    '''Tests that only supported languages are returned'''
    assert get_selected_language(lang_code) == expected


@pytest.mark.parametrize('open_at, close_at, expected', [
    ('2022-03-24T22:00:00Z', '2022-03-28T21:00:00Z', '24.-28.03.2022'),
    ('2022-03-24T22:00:00Z', '2022-04-29T21:00:00Z', '24.03.-29.04.2022'),
    ('2022-03-24T22:00:00Z', '2023-04-29T21:00:00Z', '24.03.2022-29.04.2023'),
])
def test_get_formatted_hearing_timerange_returns_correct_time_string(open_at, close_at, expected):
    '''Tests that time range is formatted and returned correctly'''
    assert get_formatted_hearing_timerange(open_at, close_at) == expected


@pytest.mark.parametrize('text_length, is_main_title, expected', [
    (38, True, 56),
    (60, True, 40),
    (85, True, 36),
    (160, True, 28),
    (200, True, 24),
    (100, False, 50),
    (115, False, 44),
    (200, False, 36),
    (240, False, 28),
])
def test_get_powerpoint_title_font_size_returns_correct_val(text_length, is_main_title, expected):
    '''Tests that correct font sizes are returned for given text and title type'''
    assert get_powerpoint_title_font_size('x'*text_length, is_main_title) == Pt(expected)
