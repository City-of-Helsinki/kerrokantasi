import pytest

from democracy.enums import InitialSectionType
from democracy.models import SectionType
from democracy.views.section import SectionSerializer


@pytest.mark.django_db
def test_section_serializer(random_hearing):
    section = random_hearing.sections.first()
    section.type = SectionType.objects.get(identifier=InitialSectionType.PART)
    data = SectionSerializer(instance=section).data
    assert data["type"] == InitialSectionType.PART
    assert "published" not in data
