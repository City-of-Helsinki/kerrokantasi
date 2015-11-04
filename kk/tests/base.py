import pytest
import json

from django.test.client import Client as DjangoTestClient

from kk.models import Hearing

pytestmark = pytest.mark.django_db


class BaseKKTest:

    def setup(self):
        self.client = DjangoTestClient()
        self.base_endpoint = '/v1'
        self.hearing_endpoint = '%s/hearing/' % self.base_endpoint

    def get_hearing_detail_url(self, id, element=None):
        element = '' if element is None else '/%s' % element
        return '%s%s%s/?format=json' % (self.hearing_endpoint, id, element)

    def get_data_from_response(self, response):
        return json.loads(response.content.decode('utf-8'))


@pytest.mark.django_db
class BaseKKDBTest(BaseKKTest):
    pytestmark = pytest.mark.django_db

# fixture for default hearing
@pytest.fixture()
def default_hearing():
    hearing = Hearing(abstract='Default test hearing One')
    hearing.save()
    return hearing
