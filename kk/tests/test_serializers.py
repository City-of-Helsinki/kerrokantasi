# -*- coding: utf-8 -*-
import pytest

from kk.enums import SectionType
from kk.views.section import SectionSerializer


@pytest.mark.django_db
def test_section_serializer(random_hearing):
    section = random_hearing.sections.first()
    section.type = SectionType.PLAIN
    data = SectionSerializer(instance=section).data
    assert data["type"] == "plain"
