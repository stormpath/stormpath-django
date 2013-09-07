from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django_stormpath.backends import StormpathBackend
from django_stormpath.forms import UserCreateForm
try:
    from unittest import mock
except ImportError:
    import mock


class BackendTest(TestCase):
    def allow_account(self, key_id, key_secret, href, username, password):
        account = mock.MagicMock()

        account.username = "gangelos"
        account.given_name = "Gabriel"
        account.surname = "Angelos"
        account.email = "gabriel@bloodravens.com"
        account.password = "A3palto0la"
        account.href = "https://api.stormpath.com/va/accounts/123"
        account.is_enabled = mock.MagicMock(return_value=True)

        return account

    def deny_account(self, key_id, key_secret, href, username, password):
        return None

    def setUp(self):
        self.username = "gangelos"
        self.given_name = "Gabriel"
        self.surname = "Angelos"
        self.email = "gabriel@bloodravens.com"
        self.password = "A3palto0la"
        self.href = settings.STORMPATH_APPLICATION
        self.key_id = settings.STORMPATH_ID
        self.key_secret = settings.STORMPATH_SECRET
        self.user_model = get_user_model()

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account',
        allow_account)
    def test_user_creation(self):

        user = StormpathBackend().authenticate(self.username, self.password)
        self.assertTrue(self.user_model.objects.filter(id=user.id).exists())

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account',
        allow_account)
    def test_user_update(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name="FAKE",
            email=self.email,
            password=self.password,
            url=self.href)
        user.save()

        user = StormpathBackend().authenticate(self.username, self.password)
        dbuser = self.user_model.objects.get(id=user.id)
        self.assertEqual(dbuser.last_name, self.surname)

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account',
        allow_account)
    def test_db_wasnt_updated(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password="STORMPATH")
        user.save()

        # The query should only execute when fetching the Django user
        # If Stormpath users haven't changed, the database shouldn't be queried
        with self.assertNumQueries(1):
            dbuser = StormpathBackend().authenticate(
                self.username,
                self.password)
            self.assertEqual(user.id, dbuser.id)

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account',
        deny_account)
    def test_invalid_credentials(self):

        StormpathBackend().authenticate(self.username, self.password)

        with self.assertRaises(ObjectDoesNotExist):
            self.user_model.objects.get(username=self.username)

    @mock.patch('django_stormpath.backends.StormpathBackend.check_account',
        deny_account)
    def test_nonexisting_account(self):
        user = self.user_model(
            username=self.username,
            first_name=self.given_name,
            last_name=self.surname,
            email=self.email,
            password=self.password)
        user.save()

        dbuser = StormpathBackend().authenticate(self.username, self.password)
        self.assertIsNone(dbuser)
        self.assertTrue(self.user_model.objects.filter(id=user.id).exists())


class UserCreateTest(TestCase):

    def setUp(self):
        self.username = "gangelos"
        self.given_name = "Gabriel"
        self.surname = "Angelos"
        self.email = "gabriel@bloodravens.com"
        self.password = "A3palto0la"
        self.user_model = get_user_model()

    @mock.patch('django_stormpath.forms.get_application')
    def test_user_create(self, get_application):
        form = UserCreateForm({
            'last_name': self.surname, 'username': self.username,
            'password2': 'password', 'password': 'password',
            'email': self.email, 'first_name': self.given_name})

        self.assertTrue(form.is_valid())
        search = get_application.return_value.accounts.search
        search.assert_any_call({'username': self.username})
        search.assert_any_call({'email': self.email})

        form.save()
        stormpath_data = {
            'given_name': self.given_name, 'email': self.email,
            'password': 'password',
            'username': self.username, 'surname': self.surname}
        accounts = get_application.return_value.accounts
        accounts.create.assert_called_once_with(stormpath_data)

        try:
            user = self.user_model.objects.get(**{'last_name': self.surname,
                'username': self.username, 'email': self.email,
                'first_name': self.given_name})
        except ObjectDoesNotExist as err:
            self.fail(str(err))

        self.assertEqual(user.password, "STORMPATH")

    @mock.patch('django_stormpath.forms.Client')
    def test_matching_passwords(self, client):
        form = UserCreateForm({
            'last_name': self.surname, 'username': self.username,
            'password2': 'password', 'password': 'password2',
            'email': self.email, 'first_name': self.given_name})

        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()

    @mock.patch('django_stormpath.forms.get_application')
    def test_user_exists(self, get_application):
        form = UserCreateForm({
            'last_name': self.surname, 'username': self.username,
            'password2': 'password', 'password': 'password',
            'email': self.email, 'first_name': self.given_name})

        accounts = get_application.return_value.accounts.search.return_value
        accounts.__len__.return_value = 1
        self.assertFalse(form.is_valid())

    def tearDown(self):
        self.user_model.objects.all().delete()
