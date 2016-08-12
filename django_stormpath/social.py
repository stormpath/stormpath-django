from django.contrib.auth import login as django_login
from django.shortcuts import resolve_url
from django.core.urlresolvers import reverse
from django.conf import settings


from stormpath.error import Error as StormpathError
from stormpath.resources.provider import Provider
from requests_oauthlib import OAuth2Session

from .models import CLIENT, APPLICATION
from .backends import StormpathSocialBackend

SOCIAL_AUTH_BACKEND = 'django_stormpath.backends.StormpathSocialBackend'

GITHUB_AUTHORIZATION_BASE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'

GOOGLE_AUTHORIZATION_BASE_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'

FACEBOOK_AUTHORIZATION_BASE_URL = 'https://www.facebook.com/dialog/oauth'
FACEBOOK_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'

LINKEDIN_AUTHORIZATION_BASE_URL = 'https://www.linkedin.com/uas/oauth2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/uas/oauth2/accessToken'


def _get_django_user(account):
    backend = StormpathSocialBackend()
    return backend.authenticate(account=account)


def get_access_token(provider, authorization_response, redirect_uri):
    if provider == Provider.GOOGLE:
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['GOOGLE']['client_id'],
            redirect_uri=redirect_uri
        )
        ret = p.fetch_token(
            GOOGLE_TOKEN_URL,
            client_secret=settings.STORMPATH_SOCIAL['GOOGLE']['client_secret'],
            authorization_response=authorization_response
        )

        return ret['access_token']
    elif provider == Provider.FACEBOOK:
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['FACEBOOK']['client_id'],
            redirect_uri=redirect_uri
        )

        from requests_oauthlib.compliance_fixes import facebook_compliance_fix

        p = facebook_compliance_fix(p)
        ret = p.fetch_token(
            FACEBOOK_TOKEN_URL,
            client_secret=settings.STORMPATH_SOCIAL['FACEBOOK']['client_secret'],
            authorization_response=authorization_response
        )

        return ret['access_token']
    elif provider == Provider.GITHUB or provider.upper() == Provider.GITHUB:
        p = OAuth2Session(client_id=settings.STORMPATH_SOCIAL['GITHUB']['client_id'])
        ret = p.fetch_token(
            GITHUB_TOKEN_URL,
            client_secret=settings.STORMPATH_SOCIAL['GITHUB']['client_secret'],
            authorization_response=authorization_response
        )

        return ret['access_token']
    elif provider == Provider.LINKEDIN:
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['LINKEDIN']['client_id'],
            redirect_uri=redirect_uri
        )

        from requests_oauthlib.compliance_fixes import linkedin_compliance_fix

        p = linkedin_compliance_fix(p)
        ret = p.fetch_token(
            LINKEDIN_TOKEN_URL,
            client_secret=settings.STORMPATH_SOCIAL['LINKEDIN']['client_secret'],
            authorization_response=authorization_response
        )

        return ret['access_token']
    else:
        return None


def handle_social_callback(request, provider):
    provider_redirect_url = 'stormpath_' + provider.lower() + '_login_callback'
    abs_redirect_uri = request.build_absolute_uri(reverse(provider_redirect_url, kwargs={'provider': provider}))
    access_token = get_access_token(provider, request.build_absolute_uri(), abs_redirect_uri)

    if not access_token:
        raise RuntimeError('Error communicating with Autentication Provider: {}'.format(provider))

    params = {'provider': provider, 'access_token': access_token}

    try:
        account = APPLICATION.get_provider_account(**params)
    except StormpathError as e:
        # We might be missing a social directory
        # First we look for one and see if it's already there
        # and just error out
        for asm in APPLICATION.account_store_mappings:
            if (getattr(asm.account_store, 'provider') and asm.account_store.provider.provider_id == provider):
                raise e

        # Or if we couldn't find one we create it for the user
        # map it to the current application
        # and try authenticate again
        create_provider_directory(provider, abs_redirect_uri)
        account = APPLICATION.get_provider_account(**params)

    user = _get_django_user(account)
    user.backend = SOCIAL_AUTH_BACKEND
    django_login(request, user)
    redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

    return redirect_to


def create_provider_directory(provider, redirect_uri):
    """Helper function for creating a provider directory"""
    dir = CLIENT.directories.create({
        'name': APPLICATION.name + '-' + provider,
        'provider': {
            'client_id': settings.STORMPATH_SOCIAL[provider.upper()]['client_id'],
            'client_secret': settings.STORMPATH_SOCIAL[provider.upper()]['client_secret'],
            'redirect_uri': redirect_uri,
            'provider_id': provider,
        },
    })

    APPLICATION.account_store_mappings.create({
        'application': APPLICATION,
        'account_store': dir,
        'list_index': 99,
        'is_default_account_store': False,
        'is_default_group_store': False,
    })


def get_authorization_url(provider, redirect_uri):
    if provider == Provider.GOOGLE:
        scope = ['email', "profile"]
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['GOOGLE']['client_id'],
            scope=scope,
            redirect_uri=redirect_uri
        )
        authorization_url, state = p.authorization_url(GOOGLE_AUTHORIZATION_BASE_URL)

        return authorization_url, state

    elif provider == Provider.FACEBOOK:
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['FACEBOOK']['client_id'],
            redirect_uri=redirect_uri
        )

        from requests_oauthlib.compliance_fixes import facebook_compliance_fix

        p = facebook_compliance_fix(p)
        authorization_url, state = p.authorization_url(FACEBOOK_AUTHORIZATION_BASE_URL)

        return authorization_url, state

    elif provider == Provider.GITHUB or provider.upper() == Provider.GITHUB:
        p = OAuth2Session(client_id=settings.STORMPATH_SOCIAL['GITHUB']['client_id'])
        authorization_url, state = p.authorization_url(GITHUB_AUTHORIZATION_BASE_URL)

        return authorization_url, state

    elif provider == Provider.LINKEDIN:
        p = OAuth2Session(
            client_id=settings.STORMPATH_SOCIAL['LINKEDIN']['client_id'],
            redirect_uri=redirect_uri
        )

        from requests_oauthlib.compliance_fixes import linkedin_compliance_fix

        p = linkedin_compliance_fix(p)
        authorization_url, state = p.authorization_url(LINKEDIN_AUTHORIZATION_BASE_URL)

        return authorization_url, state
    else:
        raise RuntimeError('Invalid Provider {}'.format(provider))
