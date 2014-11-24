from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import stormpath_django.urls
admin.autodiscover()


urlpatterns = patterns('',

    url(r'^$', 'testapp.views.home'),
    url(r'', include(stormpath_django.urls)),
    url(r'^admin/', include(admin.site.urls)),

)
