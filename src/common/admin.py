
from zinnia.managers import DRAFT, HIDDEN, PUBLISHED


def make_published(modeladmin, request, queryset):
    queryset.update(status=PUBLISHED)
make_published.short_description = "Mark selected entries as published"
