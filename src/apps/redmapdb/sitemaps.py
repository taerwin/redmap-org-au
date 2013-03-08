from django.contrib.sitemaps import Sitemap
from models import Species, Person


class SpeciesSitemap(Sitemap):

    items = Species.objects.get_redmap


