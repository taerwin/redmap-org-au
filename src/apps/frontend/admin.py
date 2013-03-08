from django.contrib import admin
from frontend.models import SponsorCategory, Sponsor

admin.site.register(SponsorCategory)


class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'category', 'is_major', 'is_lead')
    list_filter = ('region', 'is_major', 'is_lead', 'category')

admin.site.register(Sponsor, SponsorAdmin)
