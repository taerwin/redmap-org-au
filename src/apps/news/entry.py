from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from zinnia.models import EntryAbstractClass
from zinnia.managers import DRAFT, HIDDEN, PUBLISHED


class Entry(EntryAbstractClass):

    author = models.CharField(max_length=255, null=True, blank=True)
    image_caption = models.CharField(_('Image Caption'), max_length=255,
                                     null=True, blank=True)

    @property
    def is_draft(self):
        return self.status == DRAFT

    @property
    def is_published(self):
        return self.status == PUBLISHED

    @property
    def is_hidden(self):
        return self.status == HIDDEN

    @property
    def is_news(self):
        return self.categories.filter(slug='news').exists()

    @property
    def is_resource(self):
        return self.categories.filter(slug='articles').exists()

    def get_edit_url(self):
        if self.is_resource:
            return reverse("article_edit", args=[self.id])
        else:
            return reverse("news_entry_edit", args=[self.id])

    def get_public_url(self):
        if self.is_resource:
            return reverse("article_view", args=[self.slug])
        else:
            return self.get_absolute_url()

    def __unicode__(self):
        return self.title

    class Meta(EntryAbstractClass.Meta):
        abstract = True
        ordering = ['-start_publication']
