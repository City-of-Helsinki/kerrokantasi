import pytest

from kk.factories.hearing import HearingFactory, HearingCommentFactory
from kk.models import Hearing, HearingComment


@pytest.mark.django_db
def test_manager_exclude_deleted():
    for _ in range(10):
        HearingFactory()
    for _ in range(3):
        Hearing.objects.first().soft_delete()
    assert Hearing.objects.count() == 7
    assert Hearing.objects.deleted().count() == 3
    obj = Hearing.objects.first()
    orig_nb_comments = obj.comments.count()
    for _ in range(10):
        HearingCommentFactory(hearing=obj)
    for _ in range(3):
        obj.comments.first().soft_delete()
    assert obj.comments.count() == (7 + orig_nb_comments)
    assert obj.comments.deleted().count() == 3
