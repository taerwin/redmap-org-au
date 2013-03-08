from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from zinnia.models import Entry
from zinnia.admin import EntryAdmin
from models import NewsImage
from common.admin import make_published


class NewsImageInline(admin.TabularInline):
    model = NewsImage


class EntryAdminImage(EntryAdmin):
    inlines = (NewsImageInline,)
    actions = [make_published]

    fieldsets = ((_('Content'), {'fields': (
        'title', 'content', 'image', 'image_caption', 'status')}), ) + \
        EntryAdmin.fieldsets[1:]

admin.site.unregister(Entry)
admin.site.register(Entry, EntryAdminImage)
