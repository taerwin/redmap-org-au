from django.conf import settings

from redmapdb.models import Region


def nav_regions(request):
    """
    Displays a list of available regions for the site navigation menu
    """
    return {
        'nav_regions': Region.objects.all().order_by('description')
    }


def sighting_statuses(request):
    """
    Expose sighting tracking statuses to templates.

    Used primarily on sighting validation and sighting detail screens.
    """

    return {
        'SIGHTING_VALID': settings.VALID_SIGHTING,
        'SIGHTING_INVALID': settings.INVALID_SIGHTING,
        'SIGHTING_REQUIRES_VALIDATION': settings.REQUIRES_VALIDATION,
        'SIGHTING_REASSIGNED': settings.REASSIGNED,
        'SIGHTING_SPAM': settings.SPAM_SIGHTING
    }
