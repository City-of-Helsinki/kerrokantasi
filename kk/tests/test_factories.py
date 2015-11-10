from django.utils.timezone import now

import pytest
from kk.models import Hearing, Label


@pytest.mark.django_db
def test_hearing_factory(random_label, random_hearing):
    assert isinstance(random_label, Label)
    assert isinstance(random_hearing, Hearing)
    assert random_hearing.close_at > now()
    assert random_hearing.n_comments == random_hearing.comments.count()
    assert random_hearing.scenarios.count()
    assert all(comment.content for comment in random_hearing.comments.all())
