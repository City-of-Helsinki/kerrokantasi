# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class Commenting(Enum):
    NONE = 0
    REGISTERED = 1
    OPEN = 2
    STRONG = 3

    class Labels:
        NONE = _("No commenting")
        REGISTERED = _("Registered users only")
        OPEN = _("Open commenting")
        STRONG = _("Strong authentication only")


class InitialSectionType:
    MAIN = "main"
    PART = "part"
    SCENARIO = "scenario"
    CLOSURE_INFO = "closure-info"

class CommentingMapTools(Enum):
    NONE = 0
    MARKER = 1
    ALL = 2

    class Labels:
        NONE =_("none")
        MARKER = _("marker")
        ALL = _("all")