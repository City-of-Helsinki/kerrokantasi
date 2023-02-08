import pytest
from django.db.models import Sum
from django.utils.timezone import now

from democracy.models import Hearing, Label


@pytest.mark.django_db
def test_hearing_factory(random_label, random_hearing):
    assert isinstance(random_label, Label)
    assert isinstance(random_hearing, Hearing)
    assert random_hearing.close_at > now()
    assert random_hearing.n_comments == random_hearing.sections.all().aggregate(Sum('n_comments'))['n_comments__sum']
    assert random_hearing.sections.count()
