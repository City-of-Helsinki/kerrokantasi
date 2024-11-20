import freezegun
import pytest
import reversion
from django.utils import timezone
from reversion.models import Version

from democracy.factories.hearing import (
    CommentImageFactory,
    HearingFactory,
    LabelFactory,
    MinimalHearingFactory,
    SectionCommentFactory,
    SectionFactory,
    SectionFileFactory,
    SectionImageFactory,
)
from democracy.factories.organization import OrganizationFactory
from democracy.factories.poll import SectionPollFactory, SectionPollOptionFactory
from democracy.models import (
    ContactPerson,
    Project,
    ProjectPhase,
    SectionPollAnswer,
    SectionType,
)
from democracy.utils import user_data_remover
from kerrokantasi.models import User
from kerrokantasi.tests.factories import UserFactory


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def threshold_time():
    return timezone.now() - timezone.timedelta(days=30)


@pytest.mark.django_db
class TestRemoveUserFromComments:
    def test_user_data_nulled_after_threshold_time(self, user, threshold_time):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            comment = SectionCommentFactory(
                created_by=user, section=SectionFactory(), flagged_by=user
            )
        dont_remove_user_from_comment = SectionCommentFactory(
            created_by=user, section=SectionFactory()
        )

        user_data_remover.remove_user_from_old_comments(threshold_time)
        comment.refresh_from_db()
        dont_remove_user_from_comment.refresh_from_db()
        assert comment.created_by is None
        assert comment.modified_by is None
        assert comment.deleted_by is None
        assert comment.author_name is None
        assert comment.flagged_by is None
        assert dont_remove_user_from_comment.created_by == user

    def test_delete_versions_from_old_comments(self, user, threshold_time):
        with (
            freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)),
            reversion.create_revision(),
        ):
            comment = SectionCommentFactory(created_by=user, section=SectionFactory())
        with reversion.create_revision():
            comment_too = SectionCommentFactory(
                created_by=user, section=SectionFactory()
            )
            comment.title = "new version"
            comment_too.title = "new version too"
            comment.save()
            comment_too.save()

        assert Version.objects.get_for_object(comment).count() > 0
        user_data_remover.delete_old_comments_versions(threshold_time)
        assert Version.objects.get_for_object(comment).count() == 0
        assert Version.objects.get_for_object(comment_too).count() > 0

    def test_voter_removal_moves_voters_vote_to_unregistered_votes(
        self, user, threshold_time
    ):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            comment = SectionCommentFactory(created_by=user, section=SectionFactory())
        user = User.objects.create(username="voter")
        UserFactory(username="not_voter")
        comment.voters.add(user)
        comment.recache_n_votes()
        vote_count = comment.n_votes

        assert vote_count == comment.voters.count()
        assert comment.n_unregistered_votes == 0

        user_data_remover.remove_user_votes_from_old_comments(threshold_time)
        comment.refresh_from_db()
        assert comment.voters.count() == 0
        assert vote_count == comment.n_unregistered_votes
        assert vote_count == comment.n_votes

    def test_user_removed_from_poll_answers_after_threshold_time(
        self, user, threshold_time
    ):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            poll_answer = SectionPollAnswer.objects.create(
                option=SectionPollOptionFactory(),
                comment=SectionCommentFactory(section=SectionFactory()),
                created_by=user,
            )
        dont_remove_user_poll_answer = SectionPollAnswer.objects.create(
            option=SectionPollOptionFactory(),
            comment=SectionCommentFactory(section=SectionFactory()),
            created_by=user,
            modified_by=user,
            deleted_by=user,
        )
        user_data_remover.remove_user_from_old_poll_answers(threshold_time)

        poll_answer.refresh_from_db()
        dont_remove_user_poll_answer.refresh_from_db()

        assert user == dont_remove_user_poll_answer.created_by
        assert poll_answer.created_by is None
        assert poll_answer.modified_by is None
        assert poll_answer.deleted_by is None


@pytest.mark.django_db
class TestRemoveUserFromHearing:
    def test_hearing_user_fields_are_nulled_after_threshold(self, user, threshold_time):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            hearing = HearingFactory(
                close_at=timezone.now(),
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )

        dont_remove_user_from_hearing = HearingFactory(
            close_at=timezone.now(),
            created_by=user,
            modified_by=user,
            deleted_by=user,
        )

        user_data_remover.remove_user_from_old_hearings(threshold_time)
        hearing.refresh_from_db()
        dont_remove_user_from_hearing.refresh_from_db()

        assert hearing.created_by is None
        assert hearing.modified_by is None
        assert hearing.deleted_by is None
        assert dont_remove_user_from_hearing.created_by is not None
        assert dont_remove_user_from_hearing.modified_by is not None
        assert dont_remove_user_from_hearing.deleted_by is not None

    def test_hearing_contact_persons_are_cleared_after_threshold_time(
        self, user, threshold_time
    ):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            hearing = HearingFactory(
                close_at=timezone.now(),
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            hearing.contact_persons.add(
                ContactPerson.objects.create(
                    name="contact",
                )
            )
        assert hearing.contact_persons.count() == 1

        dont_remove_user_hearing = HearingFactory(
            close_at=timezone.now(),
            created_by=user,
            modified_by=user,
            deleted_by=user,
        )
        dont_remove_user_hearing.contact_persons.add(
            ContactPerson.objects.create(
                name="contact",
            )
        )

        user_data_remover.remove_contact_persons_from_old_hearings(threshold_time)
        hearing.refresh_from_db()
        dont_remove_user_hearing.refresh_from_db()

        assert hearing.contact_persons.count() == 0
        assert dont_remove_user_hearing.contact_persons.count() == 1

    def test_contact_person_deleted_if_not_used_threshold_time(
        self, user, threshold_time
    ):
        contact_person = ContactPerson.objects.create(
            name="contact",
        )
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            hearing = HearingFactory(
                close_at=timezone.now(),
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            hearing.contact_persons.add(contact_person)

        dont_delete_hearing = HearingFactory(
            close_at=timezone.now(),
            created_by=user,
            modified_by=user,
            deleted_by=user,
        )
        contact_too = ContactPerson.objects.create(name="contact_too")
        dont_delete_hearing.contact_persons.add(contact_too)

        assert ContactPerson.objects.count() == 2

        user_data_remover.remove_contact_persons_from_old_hearings(threshold_time)
        contact_too.refresh_from_db()

        assert ContactPerson.objects.count() == 1
        assert contact_too.id is not None


@pytest.mark.django_db
class TestUserDelete:
    def test_user_is_deleted_when_no_activity(self, user, threshold_time):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            UserFactory(username="inactive")

        assert User.objects.filter(username="inactive").first() is not None
        user_data_remover.delete_old_users_without_activity(threshold_time)
        assert User.objects.filter(username="inactive").first() is None

    def test_old_user_is_not_deleted_if_active_after_threshold(
        self, user, threshold_time
    ):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            active_old_user = UserFactory(username="active")

        SectionCommentFactory(created_by=active_old_user, section=SectionFactory())

        user_data_remover.delete_old_users_without_activity(threshold_time)

        assert User.objects.filter(username="active").first() is not None

    def test_old_user_is_deleted_after_its_activity_removed(self, user, threshold_time):
        with freezegun.freeze_time(threshold_time - timezone.timedelta(days=1)):
            active_old_user = UserFactory(username="inactive")
            SectionCommentFactory(
                created_by=active_old_user,
                section=SectionFactory(created_by=active_old_user),
            )
            MinimalHearingFactory(created_by=active_old_user, close_at=timezone.now())

        user_data_remover.remove_user_from_old_comments(threshold_time)
        user_data_remover.remove_old_objects_user_data(threshold_time)
        user_data_remover.remove_user_from_old_hearings(threshold_time)
        user_data_remover.remove_user_votes_from_old_comments(threshold_time)
        user_data_remover.delete_old_users_without_activity(threshold_time)

        assert User.objects.filter(username="inactive").first() is None

    def test_user_is_not_deleted_if_joined_after_threshold(self, user, threshold_time):
        user_data_remover.delete_old_users_without_activity(threshold_time)
        assert User.objects.filter(id=user.id).first() is not None


@pytest.mark.django_db
class TestRemoveUserDataFromModels:
    @pytest.fixture(autouse=True)
    def create_data_in_time(self, threshold_time, user):
        create_time = threshold_time - timezone.timedelta(days=1)
        with freezegun.freeze_time(create_time):
            ContactPerson.objects.create(
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            hearing = MinimalHearingFactory()
            section = SectionFactory(
                hearing=hearing,
                create_random_comments=False,
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            poll = SectionPollFactory(
                created_by=user,
                modified_by=user,
                deleted_by=user,
                section=section,
            )
            SectionPollAnswer.objects.create(
                option=SectionPollOptionFactory(poll=poll),
                comment=SectionCommentFactory(
                    created_by=user,
                    modified_by=user,
                    deleted_by=user,
                    section=SectionFactory(),
                ),
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            project = Project.objects.create(
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            ProjectPhase.objects.create(
                created_by=user,
                modified_by=user,
                deleted_by=user,
                project=project,
            )
            OrganizationFactory(
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            LabelFactory(
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            SectionType.objects.create(
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )
            SectionImageFactory(
                created_by=user,
                modified_by=user,
                deleted_by=user,
                section=section,
            )
            SectionFileFactory(created_by=user, modified_by=user, deleted_by=user)
            SectionPollOptionFactory(
                created_by=user,
                modified_by=user,
                deleted_by=user,
                poll=poll,
            )
            CommentImageFactory(
                comment=SectionCommentFactory(section=section),
                created_by=user,
                modified_by=user,
                deleted_by=user,
            )

    def test_user_details_are_removed_from_listed_models_after_threshold(
        self, user, threshold_time
    ):
        listed_models = user_data_remover.LOOKUP_OBJECTS

        for o in listed_models:
            assert o.objects.filter(created_by=user).count() == 1
            assert o.objects.filter(modified_by=user).count() == 1
            assert o.objects.filter(deleted_by=user).count() == 1

        user_data_remover.remove_old_objects_user_data(threshold_time)

        for o in listed_models:
            assert o.objects.filter(created_by=user).count() == 0
            assert o.objects.filter(modified_by=user).count() == 0
            assert o.objects.filter(deleted_by=user).count() == 0
