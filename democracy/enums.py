from django.db.models import IntegerChoices
from django.utils.translation import gettext_lazy as _


class Commenting(IntegerChoices):
    NONE = 0, _("No commenting")
    REGISTERED = 1, _("Registered users only")
    OPEN = 2, _("Open commenting")
    STRONG = 3, _("Strong authentication only")


class InitialSectionType:
    MAIN = "main"
    PART = "part"
    SCENARIO = "scenario"
    CLOSURE_INFO = "closure-info"


class CommentingMapTools(IntegerChoices):
    NONE = 0, _("none")
    MARKER = 1, _("marker")
    ALL = 2, _("all")
