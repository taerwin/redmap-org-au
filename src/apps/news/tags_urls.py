from django.conf.urls.defaults import *
from news.views import TagsView

urlpatterns = patterns('tags',
                       url(r'^$', TagsView, name='news_tags_list'),
                       )
