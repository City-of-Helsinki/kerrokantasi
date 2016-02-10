from copy import copy
from django.db import transaction


@transaction.atomic
def copy_hearing(old_hearing, **kwargs):
    """
    Creates a new Hearing based on an existing Hearing.

    Kwargs can be used to override field values.

    Copy strategy:
      * All Hearing model field values will be copied
      * New identical Sections will be created
      * New identical HearingImages will be created
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

    new_hearing.save()
    new_hearing.labels = old_hearing.labels.all()

    # create new sections and section images
    for section in old_hearing.sections.all():
        old_images = section.images.all()
        section.pk = None
        section.hearing = new_hearing
        section.save()
        for image in old_images:
            image.pk = None
            image.section = section
            image.save()

    # create new hearing images
    for image in old_hearing.images.all():
        image.pk = None
        image.hearing = new_hearing
        image.save()

    return new_hearing
