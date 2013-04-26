from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django_stormpath.backends import StormpathBackend
from stormpath.resource.accounts import Account
from stormpath.resource import enabled


try:
    from unittest import mock
except ImportError:
    import mock


def allow_account(self, href, username, password):
    account = Account()

    account.username = "gangelos"
    account.given_name = "Gabriel"
    account.surname = "Angelos"
    account.email = "gabriel@bloodravens.com"
    account.status = enabled

    return account


def deny_account(self, href, username, password):
    return None


class BackendTest(TestCase):

    def setUp(self):
        self.username = "gangelos"
        self.given_name = "Gabriel"
        self.surname = "Angelos"
        self.email = "gabriel@bloodravens.com"
        self.password = "A3palto0la"
        self.href = settings.STORMPATH_URL
        self.user_model = get_user_model()

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account', allow_account)
    def test_user_creation(self):

        StormpathBackend().authenticate(self.username, self.password)

        self.assertTrue(isinstance(self.user_model.objects.get(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password="STORMPATH"), self.user_model))

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account', allow_account)
    def test_user_update(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name="FAKE",
            email=self.email,
            password=self.password)
        user.save()

        StormpathBackend().authenticate(self.username, self.password)

        self.assertTrue(isinstance(self.user_model.objects.get(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password="STORMPATH"), self.user_model))

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account', allow_account)
    def test_db_wasnt_updated(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password="STORMPATH")
        user.save()

        with self.assertNumQueries(1):
            StormpathBackend().authenticate(self.username, self.password)

        self.assertTrue(isinstance(self.user_model.objects.get(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password="STORMPATH"), self.user_model))

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account', deny_account)
    def test_invalid_credentials(self):

        StormpathBackend().authenticate(self.username, self.password)

        with self.assertRaises(ObjectDoesNotExist):
            self.user_model.objects.get(username=self.username)

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account', deny_account)
    def test_nonexisting_account(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password=self.password)
        user.save()

        StormpathBackend().authenticate(self.username, self.password)

        self.assertTrue(isinstance(self.user_model.objects.get(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password=self.password), self.user_model))
