
from tagging.models import Tag
from django.conf import settings

# Access the redmap_tag.  May need to create it.
# Seems like a work around but since many apps require this it's
# not practical to initialise using a fixture.
def get_redmap_tag():
    tag, created = Tag.objects.get_or_create(name=settings.REDMAP_TAG)
    return tag