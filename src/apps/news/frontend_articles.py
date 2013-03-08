from django.conf.urls.defaults import *
from news.views import ArticleView

urlpatterns = patterns('article',
                       url(r'^(?P<slug>.*)/$',
                           ArticleView, name='article_view'),
                       )
