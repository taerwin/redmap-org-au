from django.conf.urls.defaults import *
from news.views import ArticleIndex, ArticleEdit, ArticleDelete

urlpatterns = patterns('articles',
                       url(r'^$',
                           ArticleIndex.as_view(), name='article_index'),
                       url(r'^add/$', ArticleEdit, name='article_add'),
                       url(r'^edit/(?P<pk>\d+)/$',
                           ArticleEdit, name='article_edit'),
                       url(r'^delete/(?P<pk>\d+)/$',
                           ArticleDelete, name='article_delete'),
                       )
