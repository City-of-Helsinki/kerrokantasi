import freezegun
import pytest
import reversion
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from reversion.models import Version

from democracy.factories.hearing import (
    MinimalHearingFactory,
    SectionCommentFactory,
    SectionFactory,
)
from democracy.factories.poll import SectionPollFactory, SectionPollOptionFactory
from democracy.models import ContactPerson, SectionComment, SectionPollAnswer
from kerrokantasi.models import User
from kerrokantasi.tests.factories import UserFactory


def run_remove_user_data_command(*args):
    call_command("remove_user_data", *args)


@pytest.mark.django_db
class TestRemoveUserDataCommand:
    @pytest.fixture(autouse=True)
    def init_test_data(self):
        with freezegun.freeze_time(
            timezone.now()
            - timezone.timedelta(
                days=settings.DEFAULT_USER_DATA_REMOVAL_THRESHOLD_DAYS + 1
            )
        ):
            sec = SectionFactory(create_random_comments=False)
            self.old_user = UserFactory(username="old_user", date_joined=timezone.now())
            self.old_user_without_activity = UserFactory(
                username="tobe_deleted_user", date_joined=timezone.now()
            )
            with reversion.create_revision():
                self.old_section_comment = SectionCommentFactory(
                    created_by=self.old_user, section=sec, create_random_voters=False
                )
                self.old_section_comment.title = "Old Title"
                self.old_section_comment.save()
            self.old_section_comment.voters.add(self.old_user)
            self.old_section_comment.recache_n_votes()
            self.old_hearing = MinimalHearingFactory(created_by=self.old_user)
            SectionComment.objects.filter(section__hearing=self.old_hearing).delete()
            self.old_contact_person = ContactPerson.objects.create(
                name="Old Contact Person", created_by=self.old_user
            )
            self.old_hearing.contact_persons.add(self.old_contact_person)
            poll = SectionPollFactory(section=sec)
            option = SectionPollOptionFactory(poll=poll)
            self.old_poll_answer = SectionPollAnswer.objects.create(
                created_by=self.old_user,
                option=option,
                comment=self.old_section_comment,
            )

        self.new_user = UserFactory(username="newer_user", date_joined=timezone.now())
        self.new_section_comment = SectionCommentFactory(
            created_by=self.new_user, section=sec, create_random_voters=False
        )
        self.new_hearing = MinimalHearingFactory(
            created_by=self.new_user, close_at=timezone.now()
        )
        self.new_contact_person = ContactPerson.objects.create(
            name="New Contact Person", created_by=self.new_user
        )
        self.new_hearing.contact_persons.add(self.new_contact_person)
        self.new_poll_answer = SectionPollAnswer.objects.create(
            created_by=self.new_user, option=option, comment=self.new_section_comment
        )

    old_objects = [
        "old_section_comment",
        "old_poll_answer",
        "old_hearing",
    ]
    new_objects = [
        "new_section_comment",
        "new_hearing",
        "new_contact_person",
        "new_poll_answer",
    ]

    def test_delete_user(self):
        self.old_user.delete()
        self.old_section_comment.refresh_from_db()
        self.old_hearing.refresh_from_db()
        self.old_poll_answer.refresh_from_db()
        self.old_contact_person.refresh_from_db()
        assert self.old_section_comment.created_by is None
        assert self.old_hearing.created_by is None
        assert self.old_poll_answer.created_by is None
        assert self.old_contact_person.created_by is None
        assert self.old_section_comment.content is not None
        assert self.old_section_comment.content != ""
        assert self.old_section_comment.id > 0

    def assert_old_objects_created_by_matches(self, exclude=()):
        for model in [model for model in self.old_objects if model not in exclude]:
            obj = getattr(self, model)
            obj.refresh_from_db()
            assert obj.created_by == self.old_user

    def assert_old_objects_created_by_none(self, exclude=()):
        for model in [model for model in self.old_objects if model not in exclude]:
            obj = getattr(self, model)
            obj.refresh_from_db()
            assert obj.created_by is None

    def assert_new_objects_created_by_matches(self):
        for model in self.new_objects:
            obj = getattr(self, model)
            obj.refresh_from_db()
            assert obj.created_by == self.new_user

    def test_all_options(self):
        """Test remove_user_data command with all options."""
        args = [
            "--remove-user-data-from-old-objects",
            "--delete-comment-version-history",
            "--delete-users",
            "--older-than-days",
            str(settings.DEFAULT_USER_DATA_REMOVAL_THRESHOLD_DAYS),
        ]
        run_remove_user_data_command(*args)

        self.old_section_comment.refresh_from_db()
        self.old_poll_answer.refresh_from_db()
        self.old_hearing.refresh_from_db()
        old_user = User.objects.filter(id=self.old_user.id).first()
        user_without_activity = User.objects.filter(
            username=self.old_user_without_activity.username
        ).first()
        self.new_user.refresh_from_db()

        self.assert_old_objects_created_by_none()
        assert self.old_hearing.contact_persons.count() == 0
        assert self.old_section_comment.n_unregistered_votes == 1
        assert self.old_section_comment.voters.count() == 0
        assert self.old_section_comment.n_votes == 1
        self.assert_new_objects_created_by_matches()
        assert Version.objects.get_for_object(self.old_section_comment).count() == 0

        assert user_without_activity is None
        assert old_user is None
        assert self.new_user is not None

    def test_remove_only_user_data_from_old_objects(self):
        """Test remove_user_data command with remove_user_data_from_old_objects option."""
        args = ["--remove-user-data-from-old-objects"]
        run_remove_user_data_command(*args)

        self.old_section_comment.refresh_from_db()
        self.old_poll_answer.refresh_from_db()
        self.old_hearing.refresh_from_db()

        self.assert_old_objects_created_by_none()
        assert self.old_section_comment.n_unregistered_votes == 1
        assert self.old_section_comment.voters.count() == 0
        assert self.old_section_comment.n_votes == 1
        assert self.old_hearing.contact_persons.count() == 0

        self.assert_new_objects_created_by_matches()

    def test_remove_user_data_from_old_objects_with_delete_version_option(self):
        """Test remove_user_data command with remove_user_data_from_old_objects option."""
        args = [
            "--remove-user-data-from-old-objects",
            "--delete-comment-version-history",
        ]

        assert Version.objects.get_for_object(self.old_section_comment).count() > 0
        run_remove_user_data_command(*args)

        self.old_section_comment.refresh_from_db()
        self.old_poll_answer.refresh_from_db()
        self.old_hearing.refresh_from_db()

        self.assert_old_objects_created_by_none()
        assert self.old_section_comment.n_unregistered_votes == 1
        assert self.old_section_comment.voters.count() == 0
        assert self.old_section_comment.n_votes == 1
        assert self.old_hearing.contact_persons.count() == 0

        self.assert_new_objects_created_by_matches()

        assert Version.objects.get_for_object(self.old_section_comment).count() == 0

    def test_only_delete_inactive_users(self):
        """Test remove_user_data command with delete_users option."""
        args = ["--delete-users"]
        run_remove_user_data_command(*args)

        self.old_section_comment.refresh_from_db()
        self.old_poll_answer.refresh_from_db()
        self.old_hearing.refresh_from_db()

        self.assert_old_objects_created_by_matches()
        assert self.old_section_comment.n_unregistered_votes == 0
        assert self.old_section_comment.voters.count() == 1
        assert self.old_section_comment.n_votes == 1
        assert self.old_hearing.contact_persons.count() == 1

        self.assert_new_objects_created_by_matches()
        old_user = User.objects.filter(id=self.old_user.id).first()
        user_without_activity = User.objects.filter(
            username=self.old_user_without_activity.username
        ).first()
        self.new_user.refresh_from_db()
        assert user_without_activity is None
        assert old_user is not None
        assert self.new_user is not None
