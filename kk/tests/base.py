import pytest
import json

from django.test.client import Client as DjangoTestClient

pytestmark = pytest.mark.django_db


class BaseKKTest:

    def setup(self):
        self.client = DjangoTestClient()
        self.base_endpoint = '/v1'

    def get_data_from_response(self, response):
        return json.loads(response.content.decode('utf-8'))


@pytest.mark.django_db
class BaseKKDBTest(BaseKKTest):
    pytestmark = pytest.mark.django_db
