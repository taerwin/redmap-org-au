from django.core.urlresolvers import reverse
from django.utils.functional import lazy


def reverse_lazy(urlstring, *args, **kwargs):
    return lazy(reverse, str)(urlstring, *args, **kwargs)


def dms2dd(degrees, minutes, seconds):
    '''
    Converts degress, minutes and seconds to their equivalent
    number of decimal degrees
    '''

    decimal = 0.0
    if (degrees >= 0):
        decimal = degrees + (float(minutes) / 60) + (float(seconds) / 3600)
    else:
        decimal = degrees - (float(minutes) / 60) - (float(seconds) / 3600)

    return decimal
