import json

from django.contrib.auth.models import User
from django.test.client import Client as DjangoTestClient

import pytest

from .conftest import default_hearing  # TODO: Remove me

__all__ = ["BaseKKTest", "default_hearing", "BaseKKDBTest"]

pytestmark = pytest.mark.django_db


class BaseKKTest:

    def setup(self):
        self.client = DjangoTestClient()
        self.base_endpoint = '/v1'
        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint
        self.username = 'testresident'
        self.email = 'testresident@helo.fi'
        self.password = 'password'
        self.user = None

    def get_hearing_detail_url(self, id, element=None):
        element = '' if element is None else '/%s' % element
        return '%s%s%s/?format=json' % (self.hearing_endpoint, id, element)

    def get_data_from_response(self, response):
        return json.loads(response.content.decode('utf-8'))

    def user_login(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        assert user is not None
        result = self.client.login(username=self.username, password=self.password)
        assert result is True
        self.user = user


@pytest.mark.django_db
class BaseKKDBTest(BaseKKTest):
    pytestmark = pytest.mark.django_db
