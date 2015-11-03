import pytest
import datetime
import urllib

from django.conf import settings

from kk.models import Hearing, HearingImage
from kk.tests.base import BaseKKDBTest

class TestImage(BaseKKDBTest):
    def setup(self):
        super(TestImage, self).setup()

        self.hearing = Hearing(abstract='Hearing One')
        self.hearing.save()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint
   
    def get_hearing_detail_url(self, id):
        return '%s%s/?format=json' % (self.hearing_endpoint, id)

    def create_hearing_image(self, hearing, name):
        # TODO: copy images to IMAGES_DIR if required
        path = '%s/%s' % (settings.IMAGES_DIR, name)
        image = HearingImage(hearing=hearing, image=path, title=name)
        image.save()

    def test_8_list_hearing_images_check_number_of_images(self):
        self.create_hearing_image(self.hearing, 'original.jpg')
        self.create_hearing_image(self.hearing, 'small.jpg')
        self.create_hearing_image(self.hearing, 'thumbnail.jpg')

        response = self.client.get(self.get_hearing_detail_url(self.hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data
        assert len(data['images']) == 3

    def test_8_list_hearing_images_check_urls(self):
        self.create_hearing_image(self.hearing, 'original.jpg')
        self.create_hearing_image(self.hearing, 'small.jpg')
        self.create_hearing_image(self.hearing, 'thumbnail.jpg')

        response = self.client.get(self.get_hearing_detail_url(self.hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data

        urls = []
        for im in data['images']:
            urls.append(im['url'])

        assert '/images/original.jpg' in urls
        assert '/images/small.jpg' in urls
        assert '/images/thumbnail.jpg' in urls

    def test_37_list_hearing_images_check_number_of_images(self):
        self.create_hearing_image(self.hearing, 'original.jpg')
        self.create_hearing_image(self.hearing, 'small.jpg')
        self.create_hearing_image(self.hearing, 'thumbnail.jpg')

        # /v1/hearing/<hearingID>/images/
        url = '%s%s/images/?format=json' % (self.hearing_endpoint, self.hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        assert len(data) == 3

    def test_37_list_hearing_images_check_titles(self):
        self.create_hearing_image(self.hearing, 'original.jpg')
        self.create_hearing_image(self.hearing, 'small.jpg')
        self.create_hearing_image(self.hearing, 'thumbnail.jpg')

        url = '%s%s/images/?format=json' % (self.hearing_endpoint, self.hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        titles = []
        for im in data:
            titles.append(im['title'])
 
        assert 'original.jpg' in titles
        assert 'small.jpg' in titles
        assert 'thumbnail.jpg' in titles
