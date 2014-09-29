from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend
from stormpath.error import Error

from .models import APPLICATION


class StormpathBackend(ModelBackend):
    """Authenticate with STORMPATH_setting in settings.py"""

    def _stormpath_authenticate(self, username, password):
        """Check if Stormpath authentication works

        :param username: Can be actual username or email
        :param password: Account password

        Returns an account object if successful or None otherwise.
        """
        try:
            result = APPLICATION.authenticate_account(username, password)
            return result.account
        except Error:
            return None

    def authenticate(self, username=None, password=None):
        """The authenticate method takes credentials as keyword arguments,
        usually username/email and password.

        Returns a user model if the Stormpath authentication was successful or
        None otherwise. It expects three variable to be defined in Django
        settings: \n
            STORMPATH_ID = "apiKeyId" \n
            STORMPATH_SECRET = "apiKeySecret" \n
            STORMPATH_APPLICATION =
            "https://api.stormpath.com/v1/applications/APP_UID"
        """
        account = self._stormpath_authenticate(username, password)
        if account:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(
                    Q(username=account.username) | Q(email=account.email))
                user._mirror_data_from_stormpath_account(account)
                user._save_db_only()
                return user
            except UserModel.DoesNotExist:
                user = UserModel()
                user._mirror_data_from_stormpath_account(account)
                user._save_db_only()
                return user
        return None

