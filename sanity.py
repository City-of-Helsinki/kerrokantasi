import yaml

from democracy.models.hearing import Hearing, HearingTranslation
from democracy.models.label import Label, LabelTranslation
from democracy.models.organization import (
    ContactPerson,
    ContactPersonTranslation,
    Organization,
)
from democracy.models.project import (
    Project,
    ProjectPhase,
    ProjectPhaseTranslation,
    ProjectTranslation,
)
from democracy.models.section import (
    CommentImage,
    Section,
    SectionComment,
    SectionImage,
    SectionImageTranslation,
    SectionPoll,
    SectionPollAnswer,
    SectionPollOption,
    SectionPollOptionTranslation,
    SectionPollTranslation,
    SectionTranslation,
    SectionType,
)
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from easy_thumbnails.models import Source, Thumbnail, ThumbnailDimensions
from kerrokantasi.models import User
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Building,
    Municipality,
    POI,
    POICategory,
    Plan,
    Street,
)
from reversion.models import Revision, Version


MODELS = [
    Hearing,
    HearingTranslation,
    Label,
    LabelTranslation,
    ContactPerson,
    ContactPersonTranslation,
    Organization,
    Project,
    ProjectPhase,
    ProjectPhaseTranslation,
    ProjectTranslation,
    CommentImage,
    Section,
    SectionComment,
    SectionImage,
    SectionImageTranslation,
    SectionPoll,
    SectionPollAnswer,
    SectionPollOption,
    SectionPollOptionTranslation,
    SectionPollTranslation,
    SectionTranslation,
    SectionType,
    LogEntry,
    Group,
    Permission,
    ContentType,
    Session,
    Source,
    Thumbnail,
    ThumbnailDimensions,
    User,
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Building,
    Municipality,
    POI,
    POICategory,
    Plan,
    Street,
    Revision,
    Version,
]


def get_fields(model):
    return model._meta.fields


def get_name(model):
    return model._meta.model_name


def get_app_label(model):
    return model._meta.app_label


def create_sanitizer_config(models=MODELS, path="sanitizer_config"):

    d = {
        f"{get_app_label(m)}_{get_name(m)}": {f.name: None for f in get_fields(m)}
        for m in models
    }

    open(path, "w").write(yaml.dump(d, default_flow_style=False))
