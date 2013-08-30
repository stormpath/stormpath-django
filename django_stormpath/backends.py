from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from stormpath.client import Client
from stormpath.error import Error


class StormpathBackend(object):
    """Authenticate with STORMPATH_setting in settings.py

    The methods are authenticate and get_user. All Django auth backends
    require them. They return a user model object if authentication was
    successful or None. save_user is a helper function to determine if the user
    object should be saved.
    """

    def check_account(self, key_id, key_secret, href, username, password):
        """Check if Stormpath authentication works

        :param id: Stormpath Key ID
        :param secret: Stormpath Key Secret
        :param href: URL of a Stormpath application
        :param username: Can be actual username or email
        :param password: Account password

        Returns an account object if successful or None otherwise.
        """
        client = Client(id=key_id, secret=key_secret)
        application = client.applications.get(href)

        try:
            account = application.authenticate_account(username, password)
            return account
        except Error:
            return None

    def save_user(self, user, account):
        """Save user fields if Stormpath account fields have changed.

        :param user: user model object
        :param account: Stormpath account object as returned by
            application.authenticate_account
        """
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

        if user.is_active != (account.is_enabled()):
            save = True
            user.is_active = (account.is_enabled())

        if save:
            # This is a dummy password. It is never used for authentication.
            user.password = "STORMPATH"
            user.save()

        return user

    def authenticate(self, username=None, password=None):
        """Create a new user model if it doesn't already exist or
        update and existing user to match the Stormpath account.

        The authenticate method takes credentials as keyword arguments.
        Usually, the method is used with a username and password as arguments.

        Returns a user model if the Stormpath authentication was successful or
        None otherwise. It expects three variable to be defined in Django
        settings: \n
            STORMPATH_ID = "apiKeyId" \n
            STORMPATH_SECRET = "apiKeySecret" \n
            STORMPATH_APPLICATION =
            "https://api.stormpath.com/v1/applications/APP_UID"
        """
        key_id = settings.STORMPATH_ID
        key_secret = settings.STORMPATH_SECRET
        app_href = settings.STORMPATH_APPLICATION
        account = self.check_account(
            key_id, key_secret, app_href, username, password)
        if account:
            user_model = get_user_model()
            try:
                user = user_model.objects.get(
                    Q(username=account.username) | Q(email=account.email))
                user.url = account.href
            except user_model.DoesNotExist:
                user = user_model(username="", password="STORMPATH",
                    url=account.href)
            return self.save_user(user, account)
        return None

    def get_user(self, user_id):
        """Return a user model object

        The method takes a user_id - which could be a username, database ID
        etc. and returns a user model object.
        """
        try:
            user_model = get_user_model()
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
