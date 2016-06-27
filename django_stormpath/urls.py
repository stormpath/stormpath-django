from django.conf.urls import url
from django.conf import settings

from django_stormpath import views


urlpatterns = [
    url(r'^login/$', views.stormpath_id_site_login, name='stormpath_id_site_login'),
    url(r'^logout/$', views.stormpath_id_site_logout, name='stormpath_id_site_logout'),
    url(r'^register/$', views.stormpath_id_site_register, name='stormpath_id_site_register'),
    url(r'^forgot-password/$', views.stormpath_id_site_forgot_password, name='stormpath_id_site_forgot_password'),
    url(r'^handle-callback/(?P<provider>stormpath)', views.stormpath_callback, name='stormpath_id_site_callback'),
]

if getattr(settings, 'STORMPATH_ENABLE_GOOGLE', False):
    urlpatterns += [
        url(r'handle-callback/(?P<provider>google)', views.stormpath_callback,
            name='stormpath_google_login_callback'),
        url(r'^social-login/(?P<provider>google)/', views.stormpath_social_login,
            name='stormpath_google_social_login'),
    ]
if getattr(settings, 'STORMPATH_ENABLE_FACEBOOK', False):
    urlpatterns += [
        url(r'handle-callback/(?P<provider>facebook)', views.stormpath_callback,
            name='stormpath_facebook_login_callback'),
        url(r'^social-login/(?P<provider>facebook)/', views.stormpath_social_login,
            name='stormpath_facebook_social_login'),
    ]
if getattr(settings, 'STORMPATH_ENABLE_GITHUB', False):
    urlpatterns += [
        url(r'handle-callback/(?P<provider>github)', views.stormpath_callback,
            name='stormpath_github_login_callback'),
        url(r'^social-login/(?P<provider>github)/', views.stormpath_social_login,
            name='stormpath_github_social_login'),
    ]
if getattr(settings, 'STORMPATH_ENABLE_LINKEDIN', False):
    urlpatterns += [
        url(r'handle-callback/(?P<provider>linkedin)', views.stormpath_callback,
            name='stormpath_linkedin_login_callback'),
        url(r'^social-login/(?P<provider>linkedin)/', views.stormpath_social_login,
            name='stormpath_linkedin_social_login'),
    ]
    
if django.VERSION[:2] < (1, 8):
    from django.conf.urls import patterns
    urlpatterns = patterns('django_stormpath.views', *urlpatterns)

