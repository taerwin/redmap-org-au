from django.conf.urls.defaults import patterns, url
from news.views import FrontendNews, NewsDetail

urlpatterns = patterns('zinnia',
                       url(r'^$', FrontendNews.as_view(
                       ), name="zinnia_entry_archive_index"),
                       url(
                           r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
                       NewsDetail.as_view(), name='zinnia_entry_detail'),
                       )
