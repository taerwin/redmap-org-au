import positions
from itertools import groupby

from django.db import models
from django.db.models import Q
from redmapdb.models import Region

from chainablemanager import ChainableManager


class SponsorCategory(models.Model):

    name = models.CharField(max_length=255)
    order = positions.PositionField()

    objects = positions.PositionManager()

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return self.name


class SponsorManager(ChainableManager):
    class QuerySetMixin(object):
        __dict__ = {}

        def _dict_by(self, field, keys):
            """
            Return a dict of sponsors, keyed by `true_name` and `false_name`.
            The lookup is done in a single query, but the dict items are no
            longer lazy - they are fully evaluated lists of model instances.
            """
            qs = self.order_by(field)
            grouped_qs = groupby(qs, lambda s: getattr(s, field))
            grouped_dict = dict((k, list(v)) for k, v in grouped_qs)

            return dict((real_key, grouped_dict.get(db_key, []))
                        for db_key, real_key in keys.items())

        def get_major_minor(self):
            "Return a dict of sponsors, keyed by 'major' or 'minor'."
            return self._dict_by('is_major', {True: 'major', False: 'minor'})

        def get_lead_supporter(self):
            "Return a dict of sponsors, keyed by 'lead' or 'supporter'."
            return self._dict_by('is_lead', {True: 'lead', False: 'supporter'})

        def get_major(self):
            return self.filter(is_major=True)

        def get_minor(self):
            return self.filter(is_major=False)

        def get_minor_supporter(self):
            return self.filter(is_major=False, is_lead=False)

        def get_lead(self):
            return self.filter(is_lead=True)

        def national(self):
            return self.filter(region__isnull=True)

        def get_for_region(self, region, get_major=True):
            return self.filter(region=region, is_major=get_major)

        def get_funding_partners(self):
            return self.filter(category__name='Funding partners')

        def get_national_funding_partners(self):
            return self.national().filter(category__name='Funding partners')

        def get_national_lead_sponsors(self):
            return self.national().filter(is_lead=True)

        def get_supporters(self):
            return self.filter(category__name='Supporters')

        def get_major_lead(self):
            return self.filter(is_major=True, is_lead=True)


class Sponsor(models.Model):

    name = models.CharField(max_length=255)
    category = models.ForeignKey(SponsorCategory, null=True)
    image_url = models.ImageField(upload_to=u'sponsors')
    website_url = models.CharField(max_length=255, null=True, blank=True)
    region = models.ForeignKey(Region, blank=True, null=True)
    is_major = models.BooleanField()
    is_lead = models.BooleanField()

    objects = SponsorManager()

    def __unicode__(self):
        return self.name


class Faq(models.Model):

    title = models.CharField(max_length=255)
    content = models.TextField()
    order = positions.PositionField()

    objects = positions.PositionManager()

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return self.title
