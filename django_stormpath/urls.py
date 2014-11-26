from django.conf.urls import patterns, url

urlpatterns = patterns('django_stormpath.views',
    url(r'^login/$', 'stormpath_id_site_login', name='stormpath_id_site_login'),
    url(r'^logout/$', 'stormpath_id_site_logout', name='stormpath_id_site_logout'),
    url(r'^register/$', 'stormpath_id_site_register', name='stormpath_id_site_register'),
    url(r'^forgot-password/$', 'stormpath_id_site_forgot_password', name='stormpath_id_site_forgot_password'),
    url(r'^stormpath-id-site-callback/$', 'stormpath_id_site_callback', name='stormpath_id_site_callback'),
)
