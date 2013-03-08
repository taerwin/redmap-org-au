
from tagging.models import Tag
from django.conf import settings


def get_redmap_tag():
    tag, created = Tag.objects.get_or_create(name=settings.REDMAP_TAG)
    return tag
