from django.contrib import admin
from django.template.defaultfilters import pluralize

from models import *


def get_admin_edit_link(instance):
    app_slug = instance._meta.app_label
    model_slug = instance._meta.module_name
    return u"<a href='/admin/{0}/{1}/{2}/'>{3}</a>".format(app_slug, model_slug, instance.pk, instance)
get_admin_edit_link.allow_tags = True


class SpeciesInCategoryInline(admin.TabularInline):
    model = SpeciesInCategory


class SpeciesAdmin(admin.ModelAdmin):

    def sightings(self, species):
        return species.sightings.count()

    search_fields = [
        'species_name', 'common_name',
        'short_description', 'description', 'related',
        'family', 'notes',
    ]
    list_filter = ('speciesincategory__species_category', 'active')
    list_display = ('species_name', 'common_name', 'family', 'sightings')
    inlines = [SpeciesInCategoryInline]
    list_per_page = 200


class SpeciesCategoryAdmin(admin.ModelAdmin):
    inlines = [SpeciesInCategoryInline]


class AdministratorAllocationAdmin(admin.ModelAdmin):
    list_display = ['region', 'person', 'rank']
    ordering = ['region', 'rank']


class SightingTrackingAdmin(admin.ModelAdmin):
    list_display = ['tracking_date', 'sighting_link', 'assignee_link',
                    'sighting_tracking_status']
    list_filter = ['sighting_tracking_status']

    def assignee_link(self, item):
        return get_admin_edit_link(item.person.profile)
    assignee_link.allow_tags = True

    def sighting_link(self, item):
        return get_admin_edit_link(item.sighting)
    sighting_link.allow_tags = True


class SightingTrackingStatusAdmin(admin.ModelAdmin):
    list_display = ['description', 'code']


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['description', 'citation']


class PersonAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'region', 'organisation', 'tag_list']
    list_filter = ['region', 'user__groups', 'organisation']
    search_fields = [
        'user__last_name',
        'user__first_name',
        'user__username',
        'postcode',
        'organisation__description',
        'tag_list',
    ]


class SightingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'l_user', 'l_region', 'sighting_date', 'has_photo', 'is_valid_sighting',
        'is_published', 'species_name', 'l_trackers'
    ]
    list_filter = [
        'is_valid_sighting', 'is_verified_by_scientist', 'is_checked_by_admin',
        'is_published', 'region'
    ]

    def l_user(self, item):
        return get_admin_edit_link(item.user.profile)
    l_user.short_description = 'User'
    l_user.allow_tags = True
    l_user.admin_order_field = 'user__username'

    def l_region(self, item):
        return unicode(item.region)
    l_region.short_description = 'Region'
    l_region.admin_order_field = 'region'

    def l_trackers(self, item):
        count = item.sighting_tracking.count()
        if count == 0:
            return "No trackers"
        else:
            return (u"<a href='../sightingtracking/?sighting__id={0}'>{1} tracker{2}</a>"
                    .format(item.pk, count, pluralize(count)))
    l_trackers.allow_tags = True
    l_trackers.short_description = 'Trackers'


class SpeciesAllocationAdmin(admin.ModelAdmin):

    list_display = ['id', 'species', 'region', 'rank', 'person_link',
                    'contact_in_range']
    list_filter = ['region']
    search_fields = [
        'species__species_name', 'species__common_name',
        'person__username', 'person__email',
        'person__first_name', 'person__last_name']
    save_as = True

    def person_link(self, item):
        return get_admin_edit_link(item.person.profile)
    person_link.allow_tags = True


admin.site.register(Accuracy)
admin.site.register(Activity)
admin.site.register(Count)
admin.site.register(AdministratorAllocation, AdministratorAllocationAdmin)
admin.site.register(FBGroup)
admin.site.register(Habitat)
admin.site.register(Jurisdiction)
admin.site.register(Method)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Region)
admin.site.register(Sex)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(SpeciesCategory, SpeciesCategoryAdmin)
admin.site.register(Sighting, SightingAdmin)
admin.site.register(SightingTracking, SightingTrackingAdmin)
admin.site.register(SightingTrackingStatus, SightingTrackingStatusAdmin)
admin.site.register(SizeMethod)
admin.site.register(SpeciesAllocation, SpeciesAllocationAdmin)
admin.site.register(SpeciesReportGroup)
admin.site.register(SpeciesTaxonomicGroup)
admin.site.register(Time)
admin.site.register(WeightMethod)
