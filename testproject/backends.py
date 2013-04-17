from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from stormpath.client import ClientApplicationBuilder
from stormpath.resource import ResourceError, enabled
from stormpath.auth import UsernamePasswordRequest


class StormpathBackend(object):
    """
    Authenticate against the settings STORMPATH_URL
    """

    def authenticate(self, username=None, password=None):
        href = settings.STORMPATH_URL
        client_application = ClientApplicationBuilder().set_application_href(href).build()
        application = client_application.application

        try:
            request = UsernamePasswordRequest(username, password)
            result = application.authenticate_account(request)
            account = result.account
        except ResourceError:
            return None

        user_model = get_user_model()
        try:
            user = user_model.objects.get(
                Q(username=account.username) | Q(email=account.email))
            user.first_name = account.given_name
            user.last_name = account.surname

        except user_model.DoesNotExist:
            user = user_model(
                username=account.username, email=account.email,
                first_name=account.given_name, last_name=account.surname,
                password="")

        if user.is_active and not account.status == enabled:
                user.is_active = False
        else:
            if not user.is_active and account.status == enabled:
                user.is_active = True

        user.save()
        return user

    def get_user(self, user_id):
        try:
            user_model = get_user_model()
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
