import pytest
import datetime
import urllib
import os

from django.conf import settings

from kk.models import Hearing, Image, Introduction, Scenario
from kk.tests.base import BaseKKDBTest, default_hearing


ORIGINAL = 'original.jpg'
SMALL = 'small.jpg'
THUMBNAIL = 'thumbnail.jpg'


class TestImage(BaseKKDBTest):

    def setup(self):
        super(TestImage, self).setup()

        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.hearing_list_endpoint = '%s?format=json' % self.hearing_endpoint

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

        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)

        assert 'images' in data
        assert len(data['images']) == 3

    def test_8_list_hearing_images_check_names(self, default_hearing):
        self.create_default_images(default_hearing)

        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert 'images' in data

        urls = [os.path.basename(im['url']) for im in data['images']]

        assert ORIGINAL in urls
        assert SMALL in urls
        assert THUMBNAIL in urls

    def test_get_hering_check_image_fields(self, default_hearing):
        self.create_default_images(default_hearing)

        response = self.client.get(self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert 'images' in data

        for im in data['images']:
            assert 'caption' in im
            assert 'title' in im
            assert 'width' in im
            assert 'height' in im
            assert 'url' in im

    def test_37_list_hearing_images_check_number_of_images(self, default_hearing):
        self.create_default_images(default_hearing)

        # /v1/hearing/<hearingID>/images/
        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id, 'images'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        assert len(data) == 3

    def test_37_list_hearing_images_check_titles(self, default_hearing):
        self.create_default_images(default_hearing)

        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id, 'images'))
        assert response.status_code is 200

        data = self.get_data_from_response(response)
        titles = [im['title'] for im in data]

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles

    def test_38_get_introduction_with_images(self, default_hearing):
        # instead of images only, we get introduction(s) and images included in
        # a payload for a hearing
        introduction = Introduction.objects.create(
            abstract='Introduction abstract', hearing=default_hearing)
        self.create_default_images(introduction)

        # /v1/hearing/<hearingID>/introductions/
        response = self.client.get(self.get_hearing_detail_url(
            default_hearing.id, 'introductions'))
        assert response.status_code is 200

        # check images added to the first introduction
        data = self.get_data_from_response(response)
        assert 'images' in data[0]

        titles = [im['title'] for im in data[0]['images']]

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles

    def test_38_get_hearing_check_introduction_with_images(self, default_hearing):
        # get hearing and check if there's introduction and introduction's
        # images included in a payload of this hearing
        introduction = Introduction.objects.create(
            abstract='Introduction abstract', hearing=default_hearing)
        self.create_default_images(introduction)

        # /v1/hearing/<hearingID>/
        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        # check introduction added to hearing
        data = self.get_data_from_response(response)
        assert 'introductions' in data
        assert 'images' in data['introductions'][0]

        titles = [im['title'] for im in data['introductions'][0]['images']]

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles

    def test_38_get_scenario_with_images(self, default_hearing):
        # instead of images only, we get scenario(s) and images included in
        # a payload for a hearing
        scenario = Scenario.objects.create(
            abstract='Scenario abstract', hearing=default_hearing)
        self.create_default_images(scenario)

        # /v1/hearing/<hearingID>/scenarios/
        response = self.client.get(self.get_hearing_detail_url(
            default_hearing.id, 'scenarios'))
        assert response.status_code is 200

        # check images added to the first introduction
        data = self.get_data_from_response(response)
        assert 'images' in data[0]

        titles = [im['title'] for im in data[0]['images']]

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles

    def test_38_get_hearing_check_scenario_with_images(self, default_hearing):
        # get hearing and check if there's scenario and scenario's
        # images included in a payload of this hearing
        scenario = Scenario.objects.create(
            abstract='Scenario abstract', hearing=default_hearing)
        self.create_default_images(scenario)

        # /v1/hearing/<hearingID>/
        response = self.client.get(
            self.get_hearing_detail_url(default_hearing.id))
        assert response.status_code is 200

        # check scenario added to hearing
        data = self.get_data_from_response(response)
        assert 'scenarios' in data
        assert 'images' in data['scenarios'][0]

        titles = [im['title'] for im in data['scenarios'][0]['images']]

        assert ORIGINAL in titles
        assert SMALL in titles
        assert THUMBNAIL in titles
