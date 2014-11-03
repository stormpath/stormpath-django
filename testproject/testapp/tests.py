from uuid import uuid4

from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from stormpath_django.models import CLIENT
import stormpath_django


UserModel = get_user_model()


class LiveTestBase(TestCase):

    def setUp(self):
        super(LiveTestBase, self).setUp()
        self.prefix = 'stormpath-django-test-%s-' % uuid4().hex
        self.app = CLIENT.applications.create(
                {'name': self.prefix + 'testapp'},
                create_directory=True)
        stormpath_django.models.APPLICATION = self.app

    def get_random_name(self):
        return self.prefix + uuid4().hex

    def tearDown(self):
        super(LiveTestBase, self).tearDown()
        for d in CLIENT.directories:
            if d.name.startswith('stormpath-django'):
                d.delete()
        for a in self.app.accounts:
            a.delete()

        for g in self.app.groups:
            g.delete()
        self.app.delete()

    def create_django_user(self, superuser=False, email=None, password=None,
            custom_data=None, given_name=None, surname=None):
        rnd = uuid4().hex
        if email is None:
            email = rnd + '@example.com'
        if given_name is None:
            given_name = 'Given ' + rnd
        if surname is None:
            surname = 'Sur ' + rnd
        if password is None:
            password = 'W00t123!' + rnd

        props = {
            'email': email,
            'given_name': given_name,
            'surname': surname,
            'password': password,
        }

        if superuser:
            user = UserModel.objects.create_superuser(**props)
        else:
            user = UserModel.objects.create_user(**props)
        return user


class TestUserCreation(LiveTestBase):
    def test_creating_a_user(self):
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)

    def test_creating_a_superuser(self):
        user = self.create_django_user(
                superuser=True,
                email='john.doe2@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)
        self.assertEqual(a.custom_data['spDjango_is_staff'], True)
        self.assertEqual(a.custom_data['spDjango_is_superuser'], True)

    def test_updating_a_user(self):
        user = self.create_django_user(
                email='john.doe3@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)

        user.surname = 'Smith'
        user.save()

        a = self.app.accounts.get(user.href)
        self.assertEqual(user.surname, a.surname)

    def test_authentication_pulls_user_into_local_db(self):
        self.assertEqual(0, UserModel.objects.count())
        acc = self.app.accounts.create({
            'email': 'jd@example.com',
            'given_name': 'John',
            'surname': 'Doe',
            'password': 'TestPassword123!',
        })

        from stormpath_django.backends import StormpathBackend
        b = StormpathBackend()

        b.authenticate(acc.email, 'TestPassword123!')
        self.assertEqual(1, UserModel.objects.count())

    def test_groups_get_pulled_in_on_authentication(self):
        self.assertEqual(0, UserModel.objects.count())
        self.assertEqual(0, Group.objects.count())
        acc = self.app.accounts.create({
            'email': 'jd2@example.com',
            'given_name': 'John',
            'surname': 'Doe',
            'password': 'TestPassword123!!!',
        })

        g1 = self.app.groups.create({'name': 'testGroup'})
        g2 = self.app.groups.create({'name': 'testGroup2'})  # noqa

        acc.add_group(g1)
        acc.save()

        from stormpath_django.backends import StormpathBackend
        b = StormpathBackend()

        user = b.authenticate(acc.email, 'TestPassword123!!!')

        self.assertEqual(1, UserModel.objects.count())
        self.assertEqual(2, Group.objects.count())
        self.assertEqual(1, user.groups.filter(name=g1.name).count())

    def test_groups_get_created_on_stormpath(self):
        self.assertEqual(0, Group.objects.count())
        Group.objects.create(name='testGroup')

        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, len(self.app.groups))

    def test_group_creation_errors_are_handled(self):
        self.assertEqual(0, Group.objects.count())
        Group.objects.create(name='testGroup')

        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, len(self.app.groups))

        self.app.groups.create({'name': 'exists'})

        self.assertRaises(IntegrityError, Group.objects.create, **{'name': 'exists'})

