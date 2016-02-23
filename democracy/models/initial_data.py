from democracy.enums import InitialSectionType


INITIAL_SECTION_TYPE_DATA = [
    {
        'identifier': InitialSectionType.INTRODUCTION,
        'name_singular': 'johdanto',
        'name_plural': 'johdannot',
    },
    {
        'identifier': InitialSectionType.CLOSURE_INFO,
        'name_singular': 'sulkeutumistiedote',
        'name_plural': 'sulkeutumistiedotteet',
    },
    {
        'identifier': InitialSectionType.SCENARIO,
        'name_singular': 'vaihtoehto',
        'name_plural': 'vaihtoehdot',
    },
    {
        'identifier': InitialSectionType.PART,
        'name_singular': 'osa-alue',
        'name_plural': 'osa-alueet',
    },
]


def create_initial_section_types(section_type_model):
    for section in INITIAL_SECTION_TYPE_DATA:
        section_type_model.objects.update_or_create(identifier=section['identifier'], defaults=section)
