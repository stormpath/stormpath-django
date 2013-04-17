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

    def save_user(self, user, account):

        save = False
        if user.username != account.username:
            save = True
            user.username = account.username

        if user.email != account.email:
            save = True
            user.email = account.email

        if user.first_name != account.given_name:
            save = True
            user.first_name = account.given_name

        if user.last_name != account.surname:
            save = True
            user.last_name = account.surname

        if user.is_active != (account.status == enabled):
            save = True
            user.is_active = (account.status == enabled)

        if save:
            user.save()

        return user

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
        except user_model.DoesNotExist:
            user = user_model(password="STORMPATH")

        return self.save_user(user, account)

    def get_user(self, user_id):
        try:
            user_model = get_user_model()
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
