from django import template
from django.conf import settings
from tagging.models import Tag
from redmap.common.tags import get_redmap_tag

register = template.Library()


@register.simple_tag
def get_tag(region=None):

    if region is None:
        tag = [get_redmap_tag(), ]
    else:
        tag = list(Tag.objects.get_for_object(region))

    if tag:
        return tag[0]
    else:
        return None
