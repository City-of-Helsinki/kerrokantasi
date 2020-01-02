
from copy import deepcopy

from django.db import transaction

from democracy.enums import InitialSectionType
from democracy.models import SectionType


def _copy_translations(new_obj, old_obj):
    for old_translation in old_obj.translations.all():
        translation = deepcopy(old_translation)
        translation.pk = None
        translation.master_id = new_obj.pk
        translation.save()


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

    new_hearing = deepcopy(old_hearing)
    new_hearing.pk = None

    # possible field value overrides
    for key, value in kwargs.items():
        setattr(new_hearing, key, value)

    new_hearing.n_comments = 0
    new_hearing.save()
    new_hearing.labels.set(old_hearing.labels.all())
    _copy_translations(new_hearing, old_hearing)

    # create new sections, section images and section polls
    closure_info = SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO)
    for old_section in old_hearing.sections.exclude(type=closure_info):
        old_images = old_section.images.all()
        old_polls = old_section.polls.all()
        section = deepcopy(old_section)
        section.pk = None
        section.hearing = new_hearing
        section.n_comments = 0
        section.save()
        _copy_translations(section, old_section)
        for old_image in old_images:
            image = deepcopy(old_image)
            image.pk = None
            image.section = section
            image.save()
            _copy_translations(image, old_image)
        for old_poll in old_polls:
            old_options = old_poll.options.all()
            poll = deepcopy(old_poll)
            poll.pk = None
            poll.section = section
            poll.save()
            _copy_translations(poll, old_poll)
            for old_option in old_options:
                option = deepcopy(old_option)
                option.pk = None
                option.poll = poll
                option.save()
                _copy_translations(option, old_option)

    return new_hearing
