import pytest

from kk.factories.hearing import HearingCommentFactory, HearingFactory
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


@pytest.mark.django_db
def test_cant_delete():
    hearing = HearingFactory()
    with pytest.raises(NotImplementedError):
        hearing.delete()
    assert hearing.pk


@pytest.mark.django_db
def test_unpublished():
    # the story of an unpublished hearing
    hearing = Hearing.objects.create(published=False)
    assert not Hearing.objects.public(pk=hearing.pk).exists()  # not in the regular qs
    assert Hearing.objects.with_unpublished(pk=hearing.pk).exists()  # but in the unpub qs
    assert Hearing.objects.everything(pk=hearing.pk).exists()  # and the everything qs
    assert not Hearing.objects.deleted(pk=hearing.pk).exists()  # not deleted yet
    hearing.soft_delete()
    assert not Hearing.objects.with_unpublished(pk=hearing.pk).exists()  # deleted, not in unpub anymore
    assert Hearing.objects.everything(pk=hearing.pk).exists()  # but still in everything
    assert Hearing.objects.deleted(pk=hearing.pk).exists()  # and now also in deleted
