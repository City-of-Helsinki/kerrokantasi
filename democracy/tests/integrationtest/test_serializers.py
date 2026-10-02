import pytest
from django.db import connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext

from democracy.enums import InitialSectionType
from democracy.factories.hearing import SectionImageFactory
from democracy.models import Section, SectionType
from democracy.views.section import SectionSerializer, image_qs_for_request


@pytest.mark.django_db
def test_section_serializer(random_hearing):
    section = random_hearing.sections.first()
    section.type = SectionType.objects.get(identifier=InitialSectionType.PART)
    data = SectionSerializer(instance=section).data
    assert data["type"] == InitialSectionType.PART
    assert "published" not in data


@pytest.mark.django_db
def test_section_serializer_uses_prefetched_section_level_images(random_hearing):
    section = random_hearing.sections.first()
    SectionImageFactory(section=section, published=True)
    section = Section.objects.prefetch_related(
        Prefetch(
            "images",
            image_qs_for_request(None).prefetch_related("translations"),
            to_attr="section_level_images",
        )
    ).get(pk=section.pk)

    with CaptureQueriesContext(connection) as queries:
        data = SectionSerializer(instance=section, context={"request": None}).data

    assert len(data["images"]) == 1
    assert not any(
        "democracy_sectionimage" in query["sql"].lower()
        for query in queries.captured_queries
    )
