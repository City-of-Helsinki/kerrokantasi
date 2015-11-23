import reversion
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields.fields import EnumField
from kk.enums import SectionType
from kk.models.comment import BaseComment, recache_on_save
from kk.models.images import BaseImage
from .base import StringIdBaseModel, Commentable
from .hearing import Hearing


class Section(Commentable, StringIdBaseModel):
    hearing = models.ForeignKey(Hearing, related_name='sections', on_delete=models.PROTECT)
    ordering = models.IntegerField(default=0, db_index=True)
    type = EnumField(SectionType, default=SectionType.PLAIN)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return "%s: %s" % (self.hearing, self.title)

    def save(self, *args, **kwargs):
        if not self.pk and not self.ordering and self.hearing_id:
            # Automatically derive next ordering on initial save, if possible
            self.ordering = max(self.hearing.sections.values_list("ordering", flat=True) or [0]) + 1
        return super(Section, self).save(*args, **kwargs)


class SectionImage(BaseImage):
    section = models.ForeignKey(Section, related_name="images")


@reversion.register
@recache_on_save
class SectionComment(BaseComment):
    parent_field = "section"
    parent_model = Section
    section = models.ForeignKey(Section, related_name="comments")
