from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse

from stormpath.resources.provider import Provider

from .models import APPLICATION
from .id_site import handle_id_site_callback
from .social import get_authorization_url, handle_social_callback


def stormpath_callback(request, provider):
    if provider == 'stormpath':
        ret = APPLICATION.handle_stormpath_callback(
                request.build_absolute_uri())
        return handle_id_site_callback(request, ret)

    rdr = handle_social_callback(request, provider)
    return redirect(rdr)


def stormpath_id_site_login(request):
    rdr = APPLICATION.build_id_site_redirect_url(
            callback_uri=settings.STORMPATH_ID_SITE_CALLBACK_URI,
            state=request.GET.get('state'))
    return redirect(rdr)


def stormpath_id_site_register(request):
    rdr = APPLICATION.build_id_site_redirect_url(
            callback_uri=settings.STORMPATH_ID_SITE_CALLBACK_URI,
            state=request.GET.get('state'),
            path="/#/register")
    return redirect(rdr)


def stormpath_id_site_forgot_password(request):
    rdr = APPLICATION.build_id_site_redirect_url(
            callback_uri=settings.STORMPATH_ID_SITE_CALLBACK_URI,
            state=request.GET.get('state'),
            path="/#/forgot")
    return redirect(rdr)


def stormpath_id_site_logout(request):
    rdr = APPLICATION.build_id_site_redirect_url(
            callback_uri=settings.STORMPATH_ID_SITE_CALLBACK_URI,
            state=request.GET.get('state'),
            logout=True)
    return redirect(rdr)


def stormpath_social_login(request, provider):
    redirect_uri = request.build_absolute_uri(
            reverse('stormpath_' + provider + '_login_callback', kwargs={'provider': provider}))
    authorization_url, sate = get_authorization_url(provider, redirect_uri)
    return redirect(authorization_url)


def stormpath_social_login_callback(request, provider):
    rdr = handle_social_callback(request, provider)
    return redirect(rdr)
