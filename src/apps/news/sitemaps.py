from django.contrib.sitemaps import Sitemap
from zinnia.models import Entry


class EntrySitemap(Sitemap):

    items = Entry.published.all

    def location(self, entry):
        return entry.get_public_url()

    def lastmod(self, entry):
        return entry.last_update
