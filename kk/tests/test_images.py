import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, HearingImage
from kk.tests.base import BaseKKDBTest


@pytest.fixture()
def default_hearing():
    hearing = Hearing(abstract='Hearing One')
    hearing.save()
    return hearing


class TestImage(BaseKKDBTest):

    def setup(self):
        super(TestImage, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint

    def get_hearing_detail_url(self, id):
        return '%s%s/?format=json' % (self.hearing_endpoint, id)

    def create_hearing_image(self, hearing, name):
        # TODO: copy images to IMAGES_DIR if required
        path = '%s/%s' % (settings.IMAGES_DIR, name)
        image = HearingImage(hearing=hearing, image=path, title=name)
        image.save()

    def test_8_list_hearing_images_check_number_of_images(self, default_hearing):
        self.create_hearing_image(default_hearing, 'original.jpg')
        self.create_hearing_image(default_hearing, 'small.jpg')
        self.create_hearing_image(default_hearing, 'thumbnail.jpg')

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data
        assert len(data['images']) == 3

    def test_8_list_hearing_images_check_names(self, default_hearing):
        self.create_hearing_image(default_hearing, 'original.jpg')
        self.create_hearing_image(default_hearing, 'small.jpg')
        self.create_hearing_image(default_hearing, 'thumbnail.jpg')

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data

        urls = []
        for im in data['images']:
            urls.append(os.path.basename(im['url']))

        assert 'original.jpg' in urls
        assert 'small.jpg' in urls
        assert 'thumbnail.jpg' in urls

    def test_37_list_hearing_images_check_number_of_images(self, default_hearing):
        self.create_hearing_image(default_hearing, 'original.jpg')
        self.create_hearing_image(default_hearing, 'small.jpg')
        self.create_hearing_image(default_hearing, 'thumbnail.jpg')

        # /v1/hearing/<hearingID>/images/
        url = '%s%s/images/?format=json' % (self.hearing_endpoint, default_hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        assert len(data) == 3

    def test_37_list_hearing_images_check_titles(self, default_hearing):
        self.create_hearing_image(default_hearing, 'original.jpg')
        self.create_hearing_image(default_hearing, 'small.jpg')
        self.create_hearing_image(default_hearing, 'thumbnail.jpg')

        url = '%s%s/images/?format=json' % (self.hearing_endpoint, default_hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        titles = []
        for im in data:
            titles.append(im['title'])

        assert 'original.jpg' in titles
        assert 'small.jpg' in titles
        assert 'thumbnail.jpg' in titles
