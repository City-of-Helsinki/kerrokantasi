# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class Commenting(Enum):
    NONE = 0
    REGISTERED = 1
    OPEN = 2

    class Labels:
        NONE = _("No commenting")
        REGISTERED = _("Registered users only")
        OPEN = _("Open commenting")


class SectionType(Enum):
    INTRODUCTION = "introduction"
    PLAIN = "plain"
    SCENARIO = "scenario"
    AREA = "area"
