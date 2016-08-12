from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.conf import settings

from .backends import StormpathIdSiteBackend


ID_SITE_STATUS_AUTHENTICATED = 'AUTHENTICATED'
ID_SITE_STATUS_LOGOUT = 'LOGOUT'
ID_SITE_STATUS_REGISTERED = 'REGISTERED'

ID_SITE_AUTH_BACKEND = 'django_stormpath.backends.StormpathIdSiteBackend'


def _get_django_user(account):
    backend = StormpathIdSiteBackend()
    return backend.authenticate(account=account)


def _handle_authenticated(request, id_site_response):
    user = _get_django_user(id_site_response.account)
    user.backend = ID_SITE_AUTH_BACKEND
    django_login(request, user)
    redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
    return HttpResponseRedirect(redirect_to)


def _handle_logout(request, id_site_response):
    django_logout(request)
    redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

    return HttpResponseRedirect(redirect_to)


_handle_registered = _handle_authenticated


def handle_id_site_callback(request, id_site_response):
    if id_site_response:
        action = CALLBACK_ACTIONS[id_site_response.status]
        return action(request, id_site_response)
    else:
        return None


CALLBACK_ACTIONS = {
    ID_SITE_STATUS_AUTHENTICATED: _handle_authenticated,
    ID_SITE_STATUS_LOGOUT: _handle_logout,
    ID_SITE_STATUS_REGISTERED: _handle_registered,
}
