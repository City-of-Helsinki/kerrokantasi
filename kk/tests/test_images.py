import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, Image
from kk.tests.base import BaseKKDBTest, default_hearing


ORIGINAL = 'original.jpg'
SMALL = 'small.jpg'
THUMBNAIL = 'thumbnail.jpg'

class TestImage(BaseKKDBTest):

    def setup(self):
        super(TestImage, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint

    def get_hearing_detail_url(self, id):
        return '%s%s/?format=json' % (self.hearing_endpoint, id)

    def create_image(self, instance, name):
        # TODO: copy images to IMAGES_DIR if required
        path = '%s/%s' % (settings.IMAGES_DIR, name)
        image = Image.objects.create(image=path, title=name)
        instance.images.add(image)

    def create_default_images(self, instance):
        self.create_image(instance, ORIGINAL)
        self.create_image(instance, SMALL)
        self.create_image(instance, THUMBNAIL)

    def test_8_list_hearing_images_check_number_of_images(self, default_hearing):
        self.create_default_images(default_hearing)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data
        assert len(data['images']) == 3

    def test_8_list_hearing_images_check_names(self, default_hearing):
        self.create_default_images(default_hearing)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        data = self.get_data_from_response(response)

        assert 'images' in data

        urls = []
        for im in data['images']:
            urls.append(os.path.basename(im['url']))

        assert ORIGINAL in urls
        assert SMALL in urls
        assert THUMBNAIL in urls

    def test_37_list_hearing_images_check_number_of_images(self, default_hearing):
        self.create_default_images(default_hearing)

        # /v1/hearing/<hearingID>/images/
        url = '%s%s/images/?format=json' % (self.hearing_endpoint, default_hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        assert len(data) == 3

    def test_37_list_hearing_images_check_titles(self, default_hearing):
        self.create_default_images(default_hearing)

        url = '%s%s/images/?format=json' % (self.hearing_endpoint, default_hearing.id)
        response = self.client.get(url)
        data = self.get_data_from_response(response)

        titles = []
        for im in data:
            titles.append(im['title'])

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles
