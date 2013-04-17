from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.validators import email_re
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

            save = False
            if not user.username == account.username:
                save = True
                user.username = account.username

            if not user.email == account.email:
                save = True
                user.email = account.email

            if not user.first_name == account.given_name:
                save = True
                user.first_name = account.given_name

            if not user.last_name == account.surname:
                save = True
                user.last_name = account.surname

            if not (user.is_active == (account.status == enabled)):
                save = True
                user.is_active = (account.status == enabled)

            if save:
                user.save()

        except user_model.DoesNotExist:
            user = user_model(
                username=account.username, email=account.email,
                first_name=account.given_name, last_name=account.surname,
                password="")
            user.is_active = (account.status == enabled)
            user.save()

        return user

    def get_user(self, user_id):
        try:
            user_model = get_user_model()
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
