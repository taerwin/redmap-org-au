from django.core.urlresolvers import resolve, Resolver404
from django.conf import settings
from frontend.models import Faq, Sponsor, SponsorCategory


def content(request):
    return {
        'sponsors': Sponsor.objects.all(),
        'sponsor_categories': SponsorCategory.objects.all(),
        'faqs': Faq.objects.all(),
    }

SIGHTING_URL_NAMES = [
    'sighting_photo',
    'sighting_latest',
    'sighting_map',
    'sighting_photo_by_region',
    'sighting_all_by_region',
    'sighting_map_by_region'
]

SPECIES_URL_NAMES = [
    'species_category_list',
    'species_category_list_by_region'
]


def is_section_page(request):
    """
    Add context variables for active menu flags based on the matching url_name.
    """

    payload = {
        'is_sightings_page': False,
        'is_species_page': False,
    }

    try:
        url_name = resolve(request.path).url_name
        payload.update({
            'is_sightings_page': url_name in SIGHTING_URL_NAMES,
            'is_species_page': url_name in SPECIES_URL_NAMES
        })
    except Resolver404:
        pass
    finally:
        return payload


def resolver_match(request):
    """
    Add a resolver_match object to the context to highlight active menu
    items.

    Note: This feature is included in Django 1.5.
    """
    try:
        return {'resolver_match': resolve(request.path)}
    except Resolver404:
        return {'resolver_match': ''}


def facebook_page_url(request):
    return {
        'facebook_page_url': settings.FACEBOOK_PAGE_URL,
    }


def geoserver_url(request):
    return {
        'geoserver_url': settings.GEOSERVER_URL,
    }
