# -*- coding: utf-8 -*-
import datetime
import logging

import pytz
from copy import deepcopy

from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware
from kk.enums import SectionType
from kk.models import Hearing
from kk.models.comment import BaseComment
from operator import itemgetter

log = logging.getLogger(__name__)

source_timezone = pytz.timezone("Europe/Helsinki")


def parse_aware_datetime(value):
    dt = parse_datetime(value)
    if dt is None:
        d = parse_date(value)
        if not d:  # pragma: no cover
            raise ValueError("%s is not a datetime or a date" % value)
        dt = datetime.datetime.combine(d, datetime.time())
    return make_aware(dt, timezone=source_timezone)


def import_comments(target, comments_data):
    CommentModel = BaseComment.find_subclass(target)
    assert issubclass(CommentModel, BaseComment)
    for datum in sorted(comments_data, key=itemgetter("id")):
        import_comment(CommentModel, datum, target)


def import_comment(CommentModel, datum, target):
    hidden = (datum.pop("is_hidden") == "true")
    like_count = max(int(datum.pop("like_count", 0)), len(datum.pop("likes", ())))
    updated_at = datum.pop("updated_at", None)
    created_at = datum.pop("created_at", None)
    c_args = {
        CommentModel.parent_field: target,
        "created_at": parse_aware_datetime(created_at),
        "modified_at": parse_aware_datetime(updated_at or created_at),
        "author_name": datum.pop("username"),
        "title": (datum.pop("title") or ""),
        "content": ("%s %s" % (  # TODO: Should we have a separate lead field?
            datum.pop("lead", "") or "",
            datum.pop("body", "") or "",
        )).strip(),
        "published": not hidden,
        "n_legacy_votes": like_count,
        "n_votes": like_count
    }
    return CommentModel.objects.create(**c_args)


def import_section(hearing, section_datum, section_type):
    # Offset ensures that scenario sections are placed below other sections.
    # The 2 offset ensures the introduction section (position 1) remains first.
    offset = (1000 if section_type == SectionType.SCENARIO else 2)
    s_args = {
        "type": section_type,
        "created_at": parse_aware_datetime(section_datum.pop("created_at")),
        "modified_at": parse_aware_datetime(section_datum.pop("updated_at")),
        "ordering": int(section_datum.pop("position", 1)) + offset,
        "title": (section_datum.pop("title") or ""),
        "abstract": (section_datum.pop("lead") or ""),
        "content": (section_datum.pop("body") or ""),
    }
    section = hearing.sections.create(**s_args)
    import_comments(section, section_datum.pop("comments", ()))
    main_image = section_datum.pop("main_image", None)
    if main_image:  # pragma: no branch  # TODO: Implement image import
        log.warn("Did not know how to import main image for section %s", section.pk)


def import_hearing(hearing_datum, force=False):
    hearing_datum = deepcopy(hearing_datum)  # We'll be mutating the data as we go, so it's courteous to take a copy.
    hearing_datum.pop("id")
    slug = hearing_datum.pop("slug")
    old_hearing = Hearing.objects.filter(id=slug).first()
    if old_hearing:  # pragma: no cover
        if settings.DEBUG or force:
            log.info("Hearing %s already exists, importing new entry with mutated slug", slug)
            slug += "_%s" % get_random_string(5)
        else:
            log.info("Hearing %s already exists, skipping", slug)
            return
    hearing = Hearing(
        id=slug,
        created_at=parse_aware_datetime(hearing_datum.pop("created_at")),
        modified_at=parse_aware_datetime(hearing_datum.pop("updated_at")),
        open_at=parse_aware_datetime(hearing_datum.pop("opens_at")),
        close_at=parse_aware_datetime(hearing_datum.pop("closes_at")),
        title=hearing_datum.pop("title"),
        published=(hearing_datum.pop("published") == "true")
    )
    hearing.save(no_modified_at_update=True)
    hearing.sections.create(
        type=SectionType.INTRODUCTION,
        title="",
        abstract=(hearing_datum.pop("lead") or ""),
        content=(hearing_datum.pop("body") or ""),
    )

    import_comments(hearing, hearing_datum.pop("comments", ()))

    for section_datum in sorted(hearing_datum.pop("sections", ()), key=itemgetter("position")):
        import_section(hearing, section_datum, SectionType.PLAIN)
    for alt_datum in sorted(hearing_datum.pop("alternatives", ()), key=itemgetter("position")):
        import_section(hearing, alt_datum, SectionType.SCENARIO)

    # Compact section ordering...
    for index, section in enumerate(hearing.sections.order_by("ordering"), 1):
        section.ordering = index
        section.save(update_fields=("ordering",))

    if hearing_datum.keys():  # pragma: no branch
        log.warn("These keys were not handled while importing %s: %s", hearing, hearing_datum.keys())
    return hearing


def import_from_data(data):
    """
    Import data from a data blob parsed from JSON

    :param data: A parsed data blob
    :type data: dict
    :return: The created hearings in a dict, keyed by original hearing key
    :rtype: dict[object, Hearing]
    """
    hearings = {}
    for hearing_id, hearing_data in sorted(data.get("hearings", {}).items()):
        log.info("Beginning import of hearing %s", hearing_id)
        hearings[hearing_id] = import_hearing(hearing_data)
    return hearings
