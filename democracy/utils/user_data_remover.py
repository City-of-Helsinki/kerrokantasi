from datetime import datetime
from typing import TypeVar

from django.db.models import QuerySet
from reversion.models import Version

from democracy.models import (
    ContactPerson,
    Hearing,
    Label,
    Organization,
    Project,
    ProjectPhase,
    Section,
    SectionComment,
    SectionFile,
    SectionImage,
    SectionPoll,
    SectionPollAnswer,
    SectionPollOption,
    SectionType,
)
from democracy.models.base import BaseModel
from democracy.models.section import CommentImage
from kerrokantasi.models import User

B = TypeVar("B", bound=BaseModel)


LOOKUP_OBJECTS = [
    ContactPerson,
    SectionPollAnswer,
    Project,
    ProjectPhase,
    Organization,
    Section,
    Label,
    SectionType,
    SectionImage,
    SectionFile,
    SectionPoll,
    SectionPollOption,
    CommentImage,
]

# Getting the objects


def get_hearings_closed_before(before: datetime) -> QuerySet[Hearing]:
    """Returns hearings that were closed on or before the given datetime."""
    return Hearing.objects.filter(close_at__lt=before)


def get_objects_before(model: type(B), before: datetime) -> QuerySet[B]:
    """Returns objects that were created before the given datetime."""
    return model.objects.filter(created_at__lt=before)


def get_inactive_users(
    joined_before: datetime,
) -> QuerySet[User]:
    """Returns all users that have joined before given datetime and are not creators
    or modifiers of hearings, comments, polls, organizations, files, images, polls
    or are not listed in any voters.
    """
    return User.objects.filter(
        date_joined__lt=joined_before,
        sectioncomment_created__isnull=True,
        sectioncomment_modified__isnull=True,
        hearing_created__isnull=True,
        hearing_modified__isnull=True,
        sectionpollanswer_created__isnull=True,
        sectionpollanswer_modified__isnull=True,
        section_created__isnull=True,
        section_modified__isnull=True,
        organization_created__isnull=True,
        organization_modified__isnull=True,
        project_created__isnull=True,
        project_modified__isnull=True,
        projectphase_created__isnull=True,
        projectphase_modified__isnull=True,
        contactperson_created__isnull=True,
        contactperson_modified__isnull=True,
        label_created__isnull=True,
        label_modified__isnull=True,
        sectiontype_created__isnull=True,
        sectiontype_modified__isnull=True,
        sectionimage_created__isnull=True,
        sectionimage_modified__isnull=True,
        sectionfile_created__isnull=True,
        sectionfile_modified__isnull=True,
        sectionpoll_created__isnull=True,
        sectionpoll_modified__isnull=True,
        sectionpolloption_created__isnull=True,
        sectionpolloption_modified__isnull=True,
        commentimage_created__isnull=True,
        commentimage_modified__isnull=True,
        voted_democracy_sectioncomment__isnull=True,
    )


# Manipulating the objects


def _delete_versions_from_comments(comments: QuerySet[SectionComment]):
    """Deletes version history from given set of comments."""
    for comment in comments:
        versions = Version.objects.get_for_object(comment)
        versions.delete()


def _remove_users_from_voters(section_comment: SectionComment):
    """Removes given user from section_comment's voters and add one vote to
    n_unregistered_votes field.
    """
    count = section_comment.voters.count()
    section_comment.n_unregistered_votes += count
    section_comment.voters.clear()
    section_comment.save()


def _remove_user_from_poll_answers(comments: QuerySet[SectionComment]):
    """Remove user from the poll_answers by setting the user referenced
    fields to None.
    """
    polls = SectionPollAnswer.objects.filter(comment__in=comments)
    _set_base_model_user_fields_to_null(polls)


def _set_base_model_user_fields_to_null(model_qs: QuerySet[BaseModel]):
    """Set the created_by, modified_by and delete_by fields of the given
    base model queryset to None.
    """
    model_qs.update(created_by=None, modified_by=None, deleted_by=None)


def delete_old_users_without_activity(joined_before: datetime):
    """Delete users which have not created or modified hearings, comments, polls,
    or voted and area joined before the given datetime.
    """
    users = get_inactive_users(joined_before)
    users.delete()


def delete_old_comments_versions(before: datetime):
    """Delete version history from comments that have been created before the
    given datetime.
    """
    comments = get_objects_before(SectionComment, before)
    _delete_versions_from_comments(comments)


def remove_contact_persons_from_old_hearings(before: datetime):
    """Unlink contact persons from hearings that have been closed before the
    given datetime. Delete the contact person objects if they are not associated with
    any hearings or organizations.
    """
    hearings = get_hearings_closed_before(before)

    for hearing in hearings:
        hearing.contact_persons.clear()

    ContactPerson.objects.filter(hearings=None, organization=None).delete()


def remove_old_objects_user_data(before: datetime, exclude=()):
    """Remove user data from old objects that have been created before the
    given datetime.
    """
    for object_class in [o for o in LOOKUP_OBJECTS if o not in exclude]:
        objects = get_objects_before(object_class, before)
        _set_base_model_user_fields_to_null(objects)


def remove_user_from_old_comments(before: datetime):
    """Remove user from comment by setting the user referenced fields and author_name
    to None.
    """
    comments = get_objects_before(SectionComment, before)
    _set_base_model_user_fields_to_null(comments)
    comments.update(author_name=None, flagged_by=None)


def remove_user_from_old_hearings(before: datetime):
    """Unlink contact persons from hearings that have been close_at since the
    given datetime.
    """
    hearings = get_hearings_closed_before(before)

    _set_base_model_user_fields_to_null(hearings)


def remove_user_from_old_poll_answers(before: datetime):
    """Remove user from old poll answers that have been created before the
    given datetime.
    """
    comments = get_objects_before(SectionComment, before)
    _remove_user_from_poll_answers(comments)


def remove_user_votes_from_old_comments(before: datetime):
    """Moves user votes to unregistered votes for comments. Removed votes are put
    to n_unregistered_votes field.
    """
    comments = get_objects_before(SectionComment, before)
    for comment in comments:
        _remove_users_from_voters(comment)
