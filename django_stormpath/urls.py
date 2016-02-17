from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns('django_stormpath.views',
    url(r'^login/$', 'stormpath_id_site_login', name='stormpath_id_site_login'),
    url(r'^logout/$', 'stormpath_id_site_logout', name='stormpath_id_site_logout'),
    url(r'^register/$', 'stormpath_id_site_register', name='stormpath_id_site_register'),
    url(r'^forgot-password/$', 'stormpath_id_site_forgot_password', name='stormpath_id_site_forgot_password'),
    url(r'^handle-callback/(?P<provider>stormpath)', 'stormpath_callback', name='stormpath_id_site_callback'),
)

if getattr(settings, 'STORMPATH_ENABLE_GOOGLE', False):
    urlpatterns += patterns('django_stormpath.views',
        url(r'handle-callback/(?P<provider>google)', 'stormpath_callback',
            name='stormpath_google_login_callback'),
        url(r'^social-login/(?P<provider>google)/', 'stormpath_social_login',
            name='stormpath_google_social_login'),
    )
if getattr(settings, 'STORMPATH_ENABLE_FACEBOOK', False):
    urlpatterns += patterns('django_stormpath.views',
        url(r'handle-callback/(?P<provider>facebook)', 'stormpath_callback',
            name='stormpath_facebook_login_callback'),
        url(r'^social-login/(?P<provider>facebook)/', 'stormpath_social_login',
            name='stormpath_facebook_social_login'),
    )
if getattr(settings, 'STORMPATH_ENABLE_GITHUB', False):
    urlpatterns += patterns('django_stormpath.views',
        url(r'handle-callback/(?P<provider>github)', 'stormpath_callback',
            name='stormpath_github_login_callback'),
        url(r'^social-login/(?P<provider>github)/', 'stormpath_social_login',
            name='stormpath_github_social_login'),
    )
if getattr(settings, 'STORMPATH_ENABLE_LINKEDIN', False):
    urlpatterns += patterns('django_stormpath.views',
        url(r'handle-callback/(?P<provider>linkedin)', 'stormpath_callback',
            name='stormpath_linkedin_login_callback'),
        url(r'^social-login/(?P<provider>linkedin)/', 'stormpath_social_login',
            name='stormpath_linkedin_social_login'),
    )
