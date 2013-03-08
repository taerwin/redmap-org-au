from django.conf.urls.defaults import *
from accounts.views import Profile, EditProfile, ViewProfile, MyGroups

urlpatterns = patterns(
    'accounts',
    url(r'^$', Profile, name='acct_profile'),
    url(r'^edit/$', EditProfile, name='acct_edit_profile'),
    url(r'^view/(?P<username>.+)/$', ViewProfile, name='view_profile'),
    url(r'^groups/$', MyGroups.as_view(), name='my_groups'),
)
