# -*- coding: utf-8 -*-
import datetime
import logging
from copy import deepcopy
from operator import itemgetter

import pytz
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.text import slugify
from django.utils.timezone import make_aware

from democracy.enums import SectionType
from democracy.models import Hearing, Section
from democracy.models.comment import BaseComment
from democracy.models.images import BaseImage

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


def import_images(target, datum):
    main_image = datum.pop("main_image", None)
    main_image_id = datum.pop("main_image_id", None)
    if main_image:
        assert main_image_id == main_image["id"]
    alt_images = datum.pop("images", ())
    images = sorted(
        [i for i in [main_image] + list(alt_images) if i],
        key=lambda i: (i.get("position", "0"), i.get("id"))
    )
    for index, image_datum in enumerate(images):
        import_image(target, image_datum, index)


def import_image(target, datum, position):
    ImageModel = BaseImage.find_subclass(target)
    image_path = datum.pop("filename")
    updated_at = datum.pop("updated_at", None)
    created_at = datum.pop("created_at", None)
    i_args = {
        ImageModel.parent_field: target,
        "created_at": parse_aware_datetime(created_at),
        "modified_at": parse_aware_datetime(updated_at or created_at),
        "caption": datum.pop("caption"),
        "ordering": position
    }
    image = ImageModel(**i_args)
    image.image.name = image_path
    if not image.image.storage.exists(image.image):  # pragma: no cover
        log.warn("Image %s (for %r) not in storage -- continuing anyway", image_path, target)
    image.save()
    return image


def import_section(hearing, section_datum, section_type, force=False):
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
    if s_args.get("title"):  # pragma: no branch  # sane ids if possible
        pk = "%s-%s" % (hearing.pk, slugify(s_args["title"]))
        if len(pk) > 32:
            log.warning("Truncating section pk %s to %s", pk, pk[:32])
            pk = pk[:32]
        old_section = Section.objects.filter(pk=pk).first()
        if old_section:
            if settings.DEBUG or force:
                log.info("Section %s already exists, importing new entry with mutated pk", pk)
                pk = "%s_%s" % (pk[:26], get_random_string(5))
            else:
                log.info("Section %s already exists, skipping", pk)
                return
        s_args["pk"] = pk
    section = hearing.sections.create(**s_args)
    import_comments(section, section_datum.pop("comments", ()))
    import_images(section, section_datum)


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

    if "_geometry" in hearing_datum:  # pragma: no branch
        # `_geometry` is the parsed version of `_area`, so get rid of that
        hearing_datum.pop("_area", None)

    hearing = Hearing(
        id=slug,
        created_at=parse_aware_datetime(hearing_datum.pop("created_at")),
        modified_at=parse_aware_datetime(hearing_datum.pop("updated_at")),
        open_at=parse_aware_datetime(hearing_datum.pop("opens_at")),
        close_at=parse_aware_datetime(hearing_datum.pop("closes_at")),
        title=hearing_datum.pop("title"),
        published=(hearing_datum.pop("published") == "true"),
        geojson=(hearing_datum.pop("_geometry", None) or None)
    )
    assert not hearing.geojson or isinstance(hearing.geojson, dict)
    hearing.save(no_modified_at_update=True)
    hearing.sections.create(
        type=SectionType.INTRODUCTION,
        title="",
        abstract=(hearing_datum.pop("lead") or ""),
        content=(hearing_datum.pop("body") or ""),
    )
    import_comments(hearing, hearing_datum.pop("comments", ()))
    import_images(hearing, hearing_datum)

    for section_datum in sorted(hearing_datum.pop("sections", ()), key=itemgetter("position")):
        import_section(hearing, section_datum, SectionType.PLAIN, force)
    for alt_datum in sorted(hearing_datum.pop("alternatives", ()), key=itemgetter("position")):
        import_section(hearing, alt_datum, SectionType.SCENARIO, force)

    # Compact section ordering...
    for index, section in enumerate(hearing.sections.order_by("ordering"), 1):
        section.ordering = index
        section.save(update_fields=("ordering",))

    if hearing_datum.keys():  # pragma: no cover
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