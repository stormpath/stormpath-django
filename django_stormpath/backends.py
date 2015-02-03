import logging

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group
from stormpath.error import Error

log = logging.getLogger(__name__)


def get_application():
    """Helper function. Needed for easier testing"""
    from .models import APPLICATION
    return APPLICATION


class StormpathBackend(ModelBackend):
    """Authenticate with STORMPATH_setting in settings.py"""

    def _stormpath_authenticate(self, username, password):
        """Check if Stormpath authentication works

        :param username: Can be actual username or email
        :param password: Account password

        Returns an account object if successful or None otherwise.
        """
        APPLICATION = get_application()
        try:
            result = APPLICATION.authenticate_account(username, password)
            return result.account
        except Error as e:
            log.debug(e)
            return None

    def _get_group_difference(self, sp_groups):
        """Helper method for gettings the groups that
        are present in the local db but not on stormpath
        and the other way around."""
        db_groups = set(Group.objects.all().values_list('name', flat=True))
        missing_from_db = set(sp_groups).difference(db_groups)
        missing_from_sp = db_groups.difference(sp_groups)
        return (missing_from_db, missing_from_sp)

    def _mirror_groups_from_stormpath(self):
        """Helper method for saving to the local db groups
        that are missing but are on Stormpath"""
        APPLICATION = get_application()
        sp_groups = [g.name for g in APPLICATION.groups]
        missing_from_db, missing_from_sp = self._get_group_difference(sp_groups)
        if missing_from_db:
            groups_to_create = []
            for g_name in missing_from_db:
                groups_to_create.append(Group(name=g_name))
            Group.objects.bulk_create(groups_to_create)

    def _create_or_get_user(self, account):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(
                Q(username=account.username) | Q(email=account.email))
            user._mirror_data_from_stormpath_account(account)
            self._mirror_groups_from_stormpath()
            users_sp_groups = [g.name for g in account.groups]
            user.groups = Group.objects.filter(name__in=users_sp_groups)
            user._save_db_only()
            return user
        except UserModel.DoesNotExist:
            user = UserModel()
            user._mirror_data_from_stormpath_account(account)
            self._mirror_groups_from_stormpath()
            user._save_db_only()
            users_sp_groups = [g.name for g in account.groups]
            user.groups = Group.objects.filter(name__in=users_sp_groups)
            user._save_db_only()
            return user

    def authenticate(self, username=None, password=None, **kwargs):
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
        if username is None:
            UserModel = get_user_model()
            username = kwargs.get(UserModel.USERNAME_FIELD)
        account = self._stormpath_authenticate(username, password)
        if account is None:
            return None
        return self._create_or_get_user(account)


class StormpathIdSiteBackend(StormpathBackend):
    """Used for authenticating with ID Site"""

    def authenticate(self, account=None):
        if account is None:
            return None
        return self._create_or_get_user(account)


class StormpathSocialBackend(StormpathIdSiteBackend):
    """Used for authenticating with GOOGLE/FACEBOOK/others"""
    pass
