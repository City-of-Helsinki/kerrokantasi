from copy import copy

from django.db import transaction

from democracy.enums import InitialSectionType
from democracy.models import SectionType


@transaction.atomic
def copy_hearing(old_hearing, **kwargs):
    """
    Creates a new Hearing based on an existing Hearing.

    Kwargs can be used to override field values.

    Copy strategy:
      * All Hearing model field values will be copied
      * New identical Sections will be created, except
        for closure info type
      * The same labels will be set for the new Hearing

    :param old_hearing: Hearing to be copied
    :param kwargs: field value overrides
    :return: newly created Hearing
    """
    new_hearing = copy(old_hearing)
    new_hearing.pk = None

    # possible field value overrides
    for key, value in kwargs.items():
        setattr(new_hearing, key, value)

    new_hearing.n_comments = 0
    new_hearing.save()
    new_hearing.labels = old_hearing.labels.all()

    # create new sections and section images
    closure_info = SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO)
    for section in old_hearing.sections.exclude(type=closure_info):
        old_images = section.images.all()
        section.pk = None
        section.hearing = new_hearing
        section.n_comments = 0
        section.save()
        for image in old_images:
            image.pk = None
            image.section = section
            image.save()

    return new_hearing
