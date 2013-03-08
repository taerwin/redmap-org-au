from django.conf.urls.defaults import *
from django.views.generic import ListView
from frontend.views import *
from redmapdb.models import SpeciesCategory
from cms.views import page_view
from django.views.defaults import page_not_found
from news.views import FrontendNews
from redmap.common.views import upload_progress


urlpatterns = patterns('frontend',
    url(r'^$', Homepage.as_view(), name="home"),

    url(r'^region/(?P<region_slug>[\w-]+)/$', region_landing_page, name='region_landing_page'),

    url(r'^region/(?P<region_slug>[\w-]+)/sightings/$', SightingsPhoto.as_view(), name="sighting_photo_by_region", kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/sightings/latest/$', SightingsList.as_view(), name="sighting_all_by_region", kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/sightings/map/$', SightingsMap.as_view(), name="sighting_map_by_region", kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/sightings/(?P<pk>\d+)/$', SightingDetailView.as_view(), name='sighting_detail_by_region', kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/sightings/$', page_not_found, name='region_sighting_base'),  # This route is used for menu highlighting of the sighting detail page

    url(r'^region/(?P<region_slug>[\w-]+)/species/$', SpeciesCategoryView.as_view(), name="species_category_list_by_region", kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/species/(?P<category>\d+)/$', SpeciesInCategoryList.as_view(), name="species_list_by_region", kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/species/(?P<category>\d+)/(?P<pk>\d+)/$', SpeciesDetailView.as_view(), name='species_detail_by_region', kwargs={'is_region_page': True}),

    url(r'^region/(?P<region_slug>[\w-]+)/resources/(?P<slug>.*)/$', page_view, name='region_cms_page', kwargs={'is_region_page': True}),
    url(r'^region/(?P<region_slug>[\w-]+)/resources/$', page_not_found, name='region_cms_page_base', kwargs={'is_region_page': True}),  # This route is used for menu highlighting of the resource menu under regions
    url(r'^region/(?P<region_slug>[\w-]+)/scientists/$', Scientists.as_view(), name="scientists_by_region", kwargs={'is_region_page': True}),

    url(r'^region/(?P<region_slug>[\w-]+)/news/$', FrontendNews.as_view(), name="region_zinnia_entry_archive_index"),

    url(r'^sightings/$', SightingsPhoto.as_view(), name="sighting_photo"),
    url(r'^sightings/latest/$', SightingsList.as_view(), name="sighting_latest"),
    url(r'^sightings/map/$', SightingsMap.as_view(), name="sighting_map"),
    url(r'^species/$', SpeciesCategoryView.as_view(), name="species_category_list"),


    url(r'^sightings/(?P<pk>\d+)/$', SightingDetailView.as_view(), name='sighting_detail'),
    url(r'^sightings/add/$', add_wizard, name="sighting_add"),

    url(r'^species/(?P<category>\d+)/$', SpeciesInCategoryList.as_view(), name="species_list"),
    url(r'^species/(?P<category>\d+)/(?P<pk>\d+)/$', SpeciesDetailView.as_view(), name='species_detail'),

    url(r'^resources/(?P<slug>.*)/$', page_view, name='cms_page'),
    url(r'^faq/$', Faqs.as_view(), name="faqs"),
    url(r'^scientists/$', Scientists.as_view(), name="scientists"),
    url(r'^articles/$', Articles.as_view(), name="articles"),
    url(r"^articles/", include("zinnia.urls")),
    url(r'^newsletter/ajax/$', NewsletterSignup, name="newsletter_signup"),
    url(r'^newsletter/$', NewsletterSignupPage, name="newsletter_signup_page"),

    url(r'^render/cluster/(?P<count>\d+)/$', render_cluster, name="render_cluster"),

    url(r'^upload_progress/$', upload_progress, name='upload_progress'),
)
