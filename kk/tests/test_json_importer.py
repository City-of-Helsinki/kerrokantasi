# -*- coding: utf-8 -*-
# Please ignore the mess.
from copy import deepcopy

import pytest
from django.utils.crypto import get_random_string

from kk.enums import SectionType
from kk.importing.json_importer import import_from_data, parse_aware_datetime
from kk.models import Hearing
from kk.tests.utils import assert_datetime_fuzzy_equal, get_geojson

LIKE = {
    "comment_id": "154",
    "created_at": "2014-11-27T18:02:53.874498",
    "id": "37",
    "user_id": "16"
}

SECTION = {
    'body': 'qnn iqrzxdmft wrmtfnh kqmetge uk',
    'comments': [{'body': 'ddcofnrdfepk roiyndappdo hzh tsk',
                  'created_at': '2015-10-21T13:59:06.565066',
                  'id': '2010',
                  'is_hidden': 'false',
                  'lead': 'rchcvjenxt szclinijw jbabqhzsdna',
                  'like_count': '0',
                  'likes': [],
                  'main_image': None,
                  'section_id': '3',
                  'title': 'rhyahbehu edxqzdyud ewwxccrlsnod',
                  'username': 'Scabiosa'},
                 {'body': 'biimp tx twvfe pvmy ifhkruwwpwdg',
                  'created_at': '2015-10-30T09:49:44.254095',
                  'id': '2351',
                  'is_hidden': 'false',
                  'lead': 'rchcvjenxt szclinijw jbabqhzsdna',
                  'like_count': '1',
                  'likes': [{'comment_id': '2351',
                             'created_at': '2015-10-30T10:44:48.803608',
                             'id': '5380',
                             'user_id': '454'}],
                  'main_image': None,
                  'section_id': '3',
                  'title': 'wsvrnugozbwnwamap fzoaicajhdqwgj',
                  'updated_at': '2015-10-30T10:44:48.806759',
                  'username': 'Anders'}],
    'created_at': '2015-09-30T13:24:20.986358',
    'hearing_id': '31',
    'id': '3',
    'lead': 'abxindykmrg clatg sox qgadjdkyik',
    'main_image': {'caption': 'Haruspuiston alue.',
                   'created_at': '2015-09-30T13:24:21.002837',
                   'filename': 'images/meri-rastila/section_3/main_image.jpg',
                   'id': '68'},
    'main_image_id': '68',
    'position': '2',
    'title': 'w   et gfs  jybt abysehkjd hcjut',
    'updated_at': '2015-09-30T13:24:21.012934'
}

ALT1 = {'body': 'ghmss idtflgqchqxx qudexo xhjcdq', 'comments': [
    {'alternative_id': '35', 'body': 'cpkpvgrrmttnwsprmfo qouyeyqlvutl', 'created_at': '2014-11-30T08:27:17.305858',
     'id': '181', 'is_hidden': 'false', 'lead': 'rchcvjenxt szclinijw jbabqhzsdna', 'like_count': '0', 'likes': [],
     'main_image': None, 'title': 'mdzxrue xnh   vltlqeg rvu kfsphi', 'username': 'Pertti'}],
    'created_at': '2014-11-25T19:01:23.885067', 'hearing_id': '12', 'id': '35',
    'lead': 'qcpxtft cfvm sx uz  xadxctnvvqbt',
    'main_image': None, 'main_image_id': None,
    'position': '1', 'title': 'nox v qj qsndntryubrnhvsbwmgdzmx', 'updated_at': '2014-11-25T19:01:23.900769'}

ALT2 = {'body': 'qixzbjypctfgffvro kjqlangqf ltvp', 'comments': [
    {'alternative_id': '34', 'body': 'jsks njxemfiaqxtsawch vzzmvhwnu ', 'created_at': '2014-12-03T19:22:44.262491',
     'id': '209', 'is_hidden': 'false', 'lead': 'rchcvjenxt szclinijw jbabqhzsdna', 'like_count': '0', 'likes': [],
     'main_image': None, 'title': ' ijiwfhkstq aphhodwirh ncpbuipmb', 'username': 'Asunto Kalliossa'},
    {'alternative_id': '34', 'body': 'zpt  fnrdfyhm   irzlmdtghrdzpygt', 'created_at': '2014-11-27T08:25:28.055787',
     'id': '98', 'is_hidden': 'false', 'lead': 'rchcvjenxt szclinijw jbabqhzsdna', 'like_count': '1', 'likes': [LIKE],
     'main_image': None, 'title': 'hzyew gspcp ptpeltsznjgnxr uvcpm', 'username': 'Johannes'}],
    'created_at': '2014-11-25T19:01:23.881728', 'hearing_id': '12', 'id': '34',
    'lead': 'kovgskyhbthkdqmzguoyvnwvsenq lqu',
    'main_image': {'caption': 'Vaihtoehdon 1 esimerkkikuva.', 'created_at': '2014-11-25T19:01:23.890566',
                   'filename': 'images/hameentie/alternative_1/main_image.jpg', 'id': '45'}, 'main_image_id': '45',
    'position': '0', 'title': 'aksebfq rufmmwszkdkdocanzliys cv', 'updated_at': '2014-11-25T19:01:23.900758'}

HEARING = {'_area': 'x', '_geometry': get_geojson(), 'alternatives': [ALT1, ALT2],
           'body': ' gcthqzqrndsutwhoiqiabothsomtjwp',
           'closes_at': '2014-12-31', 'comments': [
    {'body': 'x hisydetgyr tooetpydxmmdg  ylnc', 'created_at': '2014-12-23T09:30:51.991187', 'hearing_id': '12',
     'id': '245', 'is_hidden': 'false', 'lead': 'rchcvjenxt szclinijw jbabqhzsdna', 'like_count': '0', 'likes': [],
     'main_image': None, 'title': 'figlxwalwwze pyffyhjywksjlslijkj', 'username': 'ratikka4'},
    {'body': 'kdrzglteivqdtgfuxiigyjbsezsz urx', 'created_at': '2014-11-27T09:34:56.023891', 'hearing_id': '12',
     'id': '112', 'is_hidden': 'false', 'lead': 'rchcvjenxt szclinijw jbabqhzsdna', 'like_count': '0', 'likes': [],
     'main_image': None, 'title': ' clpcjxkhxw lgaejuywfpwsrikszcqy', 'username': 'Pasi'}],
    'created_at': '2014-11-25T19:01:23.859401', 'id': '12', 'lead': 'lipibmupbapezxiloyqjzd jnao knvd',
    'main_image': {
               'caption': 'Liikenne nykyisin Hõmeentiellõ. (Helsingin kaupungin aineistopankki / Seppo Laakso)',
               'created_at': '2014-11-25T19:01:23.898028', 'filename': 'images/hameentie/main_image.jpg',
               'id': '48'}, 'main_image_id': '48', 'opens_at': '2014-11-25', 'published': 'true',
    'sections': [SECTION], 'slug': '', 'title': 'ikwnydbg hjl riffyjsbrq shxv nkl',
    'updated_at': '2015-01-26T10:20:12.869162'}

EXAMPLE_DATA = {
    'hearings': {
        '1': HEARING
    }
}


@pytest.mark.django_db
def test_json_importer():
    data = deepcopy(EXAMPLE_DATA)
    hearing_id = get_random_string()
    hearing_data = data["hearings"]["1"]
    hearing_data["slug"] = hearing_id
    import_from_data(data)
    hearing = Hearing.objects.get(id=hearing_id)
    assert_datetime_fuzzy_equal(hearing.modified_at, parse_aware_datetime(hearing_data["updated_at"]))
    assert_datetime_fuzzy_equal(hearing.created_at, parse_aware_datetime(hearing_data["created_at"]))
    assert hearing.title == 'ikwnydbg hjl riffyjsbrq shxv nkl'
    assert hearing.sections.filter(type=SectionType.SCENARIO).count() == 2
    assert hearing.sections.filter(type=SectionType.PLAIN).count() == 1
    assert hearing.comments.count() == 2
    # TODO: This test could probably be better
