from django.conf import settings
from django.shortcuts import redirect

from .models import APPLICATION
from .id_site import handle_id_site_callback


def stormpath_id_site_callback(request):
    ret = APPLICATION.handle_id_site_callback(
            request.build_absolute_uri())
    return handle_id_site_callback(request, ret)


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

