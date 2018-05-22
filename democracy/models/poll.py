from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel
from .base import ORDERING_HELP, BaseModel


class BasePoll(BaseModel, TranslatableModel):
    TYPE_SINGLE_CHOICE = 'single-choice'
    TYPE_MULTIPLE_CHOICE = 'multiple-choice'
    TYPE_CHOICES = (
        (TYPE_SINGLE_CHOICE, _('single choice poll')),
        (TYPE_MULTIPLE_CHOICE, _('multiple choice poll')),
    )

    type = models.CharField(verbose_name=_('poll type'), choices=TYPE_CHOICES, max_length=255)
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)
    is_independent_poll = models.BooleanField(verbose_name=_('poll may be used independently'), default=False)
    n_answers = models.IntegerField(verbose_name=_('answer count'),
                                    help_text=_('number of answers given to this poll'), default=0, editable=False)

    class Meta:
        abstract = True
        ordering = ['ordering']

    def recache_n_answers(self):
        # Answer objects can not be directly counted because of multiple-choice type
        # Need to count linked objects, which are not provided in the base class
        raise NotImplementedError


class BasePollOption(BaseModel, TranslatableModel):
    # `poll` must be defined as a foreign key to the corresponding subclassed Poll-model
    # with related name `options`
    poll = None
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)
    n_answers = models.IntegerField(verbose_name=_('answer count'),
                                    help_text=_('number of answers given with this option'), default=0, editable=False)

    class Meta:
        abstract = True
        ordering = ['ordering']

    def save(self, *args, **kwargs):
        if not self.pk and self.ordering == 1:
            max_ordering = self.poll.options.all().aggregate(Max('ordering')).get('ordering__max') or 0
            self.ordering = max_ordering + 1
        return super().save(*args, **kwargs)

    def recache_n_answers(self):
        n_answers = self.answers.all().count()
        if n_answers != self.n_answers:
            self.n_answers = n_answers
            self.save(update_fields=('n_answers',))
            self.poll.recache_n_answers()


class BasePollAnswer(BaseModel):
    # `option` must be defined as a foreign key to the corresponding subclassed PollOption-model
    # with related name `answers`
    option = None
    source_client = models.CharField(verbose_name=_('name for sender client'), max_length=255)

    def recache_option_n_answers(self):
        self.option.recache_n_answers()

    class Meta:
        abstract = True


def poll_option_recache(sender, instance, **kwargs):
    instance.recache_option_n_answers()


def poll_option_recache_on_save(klass):
    assert issubclass(klass, BasePollAnswer)
    post_save.connect(poll_option_recache, sender=klass)
    pre_delete.connect(poll_option_recache, sender=klass)
    return klass
