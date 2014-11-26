from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import django_stormpath.urls
admin.autodiscover()


urlpatterns = patterns('',

    url(r'^$', 'testapp.views.home'),
    url(r'', include(django_stormpath.urls)),
    url(r'^admin/', include(admin.site.urls)),

)
