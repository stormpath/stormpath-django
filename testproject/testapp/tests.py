from time import sleep
from uuid import uuid4

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group

import django_stormpath
from django_stormpath.models import CLIENT
from django_stormpath.backends import StormpathBackend
from django_stormpath.forms import *

from pydispatch import dispatcher

from stormpath.error import Error as StormpathError
from stormpath.resources.base import SIGNAL_RESOURCE_CREATED


def sleep_receiver_function(signal, sender, data, params):
    """Sleeps for one second.

    This is used to sleep for a second after every Stormpath resource is
    created, to avoid test failures.
    """
    sleep(1)


# Connect the signal.
dispatcher.connect(sleep_receiver_function, signal=SIGNAL_RESOURCE_CREATED)


UserModel = get_user_model()


class LiveTestBase(TestCase):

    def setUp(self):
        super(LiveTestBase, self).setUp()

        self.prefix = 'stormpath-django-test-%s' % uuid4().hex
        self.app = CLIENT.applications.create(
            {'name': self.prefix},
            create_directory = True
        )
        django_stormpath.models.APPLICATION = self.app

    def tearDown(self):
        super(LiveTestBase, self).tearDown()

        for group in self.app.groups:
            group.delete()

        for mapping in self.app.account_store_mappings:
            mapping.account_store.delete()

        for account in self.app.accounts:
            account.delete()

        self.app.delete()

    def create_django_user(self, superuser=False, email=None, password=None,
            custom_data=None, given_name=None, surname=None, first_name=None,
            last_name=None):
        rnd = uuid4().hex
        if email is None:
            email = rnd + '@example.com'
        if given_name is None and first_name is None:
            given_name = 'Given ' + rnd
        if surname is None and last_name is None:
            surname = 'Sur ' + rnd
        if password is None:
            password = 'W00t123!' + rnd

        props = {
            'email': email,
            'given_name': given_name,
            'surname': surname,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
        }

        if superuser:
            user = UserModel.objects.create_superuser(**props)
        else:
            user = UserModel.objects.create_user(**props)
        return user


class TestUserAndGroups(LiveTestBase):
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

    def test_get_with_non_existing(self):
        UserModel.objects.create_user(
            email='me1@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        with self.assertRaises(UserModel.DoesNotExist):
            UserModel.objects.get(email='does.not@exist.com')

    def test_get_with_existing(self):
        UserModel.objects.create_user(
            email='me2@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        user = UserModel.objects.get(
            email='me2@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        self.assertTrue(user)

    def test_get_wrong_password(self):
        UserModel.objects.create_user(
            email='me3@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        with self.assertRaises(UserModel.DoesNotExist):
            UserModel.objects.get(
                email='me3@example.com', given_name='Sample', surname='User',
                password='wrong')

    def test_get_or_create_user_with_non_existing(self):
        user, created = UserModel.objects.get_or_create(
            email='me4@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        self.assertTrue(created)
        self.assertEqual(self.app.accounts.get(user.href).given_name, 'Sample')
        user = UserModel.objects.get(email='me4@example.com')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me4@example.com', 'TestPassword123!'))

    def test_get_or_create_user_with_wrong_password(self):
        UserModel.objects.create_user(
            email='me5@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        with self.assertRaises(IntegrityError):
            user, created = UserModel.objects.get_or_create(
                email='me5@example.com', given_name='Sample', surname='User',
                password='wrong')

    def test_get_or_create_user_with_existing(self):
        UserModel.objects.create_user(
            email='me6@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        user, created = UserModel.objects.get_or_create(
            email='me6@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        self.assertFalse(created)
        self.assertEqual(self.app.accounts.get(user.href).given_name, 'Sample')
        user = UserModel.objects.get(email='me6@example.com')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me6@example.com', 'TestPassword123!'))

    def test_update_or_create_user_with_non_existing(self):
        user, created = UserModel.objects.update_or_create(
            defaults={'given_name': 'Updated'},
            email='me7@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        self.assertTrue(created)
        self.assertEqual(
            self.app.accounts.get(user.href).given_name, 'Updated')
        user = UserModel.objects.get(email='me7@example.com')
        self.assertEqual(user.given_name, 'Updated')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me7@example.com', 'TestPassword123!'))

    def test_update_or_create_user_with_wrong_password(self):
        UserModel.objects.create_user(
            email='me8@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        with self.assertRaises(IntegrityError):
            user, created = UserModel.objects.update_or_create(
                defaults={'given_name': 'Updated'},
                email='me8@example.com', given_name='Sample', surname='User',
                password='123!TestPassword')

    def test_update_or_create_user_with_non_existing_and_password(self):
        user, created = UserModel.objects.update_or_create(
            defaults={'given_name': 'Updated', 'password': '123!TestPassword'},
            email='me9@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        self.assertTrue(created)
        self.assertEqual(
            self.app.accounts.get(user.href).given_name, 'Updated')
        user = UserModel.objects.get(email='me9@example.com')
        self.assertEqual(user.given_name, 'Updated')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me9@example.com', '123!TestPassword'))

    def test_update_or_create_user_with_existing(self):
        UserModel.objects.create_user(
            email='me10@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        user, created = UserModel.objects.update_or_create(
            defaults={'given_name': 'Updated'},
            email='me10@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')

        self.assertFalse(created)
        self.assertEqual(
            self.app.accounts.get(user.href).given_name, 'Updated')
        user = UserModel.objects.get(email='me10@example.com')
        self.assertEqual(user.given_name, 'Updated')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me10@example.com', 'TestPassword123!'))

    def test_update_or_create_user_with_existing_and_password(self):
        UserModel.objects.create_user(
            email='me11@example.com', given_name='Sample', surname='User',
            password='TestPassword123!')
        user, created = UserModel.objects.update_or_create(
            defaults={'given_name': 'Updated', 'password': '123!TestPassword'},
            email='me11@example.com', given_name='Sample', surname='User')

        self.assertFalse(created)
        self.assertEqual(
            self.app.accounts.get(user.href).given_name, 'Updated')
        user = UserModel.objects.get(email='me11@example.com')
        self.assertEqual(user.given_name, 'Updated')
        self.assertEqual(user.surname, 'User')
        self.assertIsNotNone(
            StormpathBackend().authenticate(
                'me11@example.com', '123!TestPassword'))

    def test_updating_a_user_with_invalid_fields_should_not_delete_user(self):
        """
        Issue https://github.com/stormpath/stormpath-django/issues/49
        """
        user = self.create_django_user(
                email='john.doe3@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)

        user.email = ''
        with self.assertRaises(StormpathError):
            user.save()

        a = self.app.accounts.get(user.href)
        self.assertEqual(a.email, 'john.doe3@example.com')

    def test_updating_nonexistent_user_deletes_that_user(self):
        user = self.create_django_user(
                email='john.doe3@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)

        a.delete()

        user = UserModel.objects.get(email='john.doe3@example.com')
        user.given_name = 'Johnny'

        with self.assertRaises(user.DoesNotExist):
            user.save()

        with self.assertRaises(UserModel.DoesNotExist):
            UserModel.objects.get(email='john.doe3@example.com')

    def test_authentication_pulls_user_into_local_db(self):
        self.assertEqual(0, UserModel.objects.count())
        acc = self.app.accounts.create({
            'email': 'jd@example.com',
            'given_name': 'John',
            'surname': 'Doe',
            'password': 'TestPassword123!',
        })

        b = StormpathBackend()

        b.authenticate(acc.email, 'TestPassword123!')
        self.assertEqual(1, UserModel.objects.count())

    def test_authentication_updates_user_info_in_local_db(self):
        self.assertEqual(0, UserModel.objects.count())
        acc = self.app.accounts.create({
            'email': 'jd@example.com',
            'given_name': 'John',
            'surname': 'Doe',
            'password': 'TestPassword123!',
        })

        b = StormpathBackend()

        b.authenticate(acc.email, 'TestPassword123!')
        self.assertEqual(1, UserModel.objects.count())

        acc.surname = 'Test'
        acc.save()

        user = b.authenticate(acc.email, 'TestPassword123!')
        self.assertEqual(1, UserModel.objects.count())
        self.assertEqual('Test', user.surname)

    def test_auth_doesnt_work_for_bogus_user(self):
        b = StormpathBackend()

        u = b.authenticate('nonexistent@example.com', 'TestPassword123!')
        self.assertIsNone(u)
        self.assertEqual(0, UserModel.objects.count())

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
        self.assertEqual(1, Group.objects.count())
        self.assertEqual(2, len(self.app.groups))

    def test_group_creation_error_on_local_db(self):
        self.assertEqual(0, Group.objects.count())
        Group.objects.create(name='testGroup')

        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, len(self.app.groups))

        # we delete the image from stormpath
        self.app.groups.search({'name': 'testGroup'})[0].delete()

        # and try to re-create a duplicate locally
        with transaction.atomic():
            # we need to do manual commits here because django won't let us
            # do more queries until we commit
            self.assertRaises(IntegrityError,
            Group.objects.create, **{'name': 'testGroup'})
        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, len(self.app.groups))

    def test_deleting_a_user(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)
        self.assertEqual(1, UserModel.objects.count())
        href = user.href
        user.delete()
        self.assertEqual(0, UserModel.objects.count())
        a = self.app.accounts.get(href)
        self.assertRaises(StormpathError, a.__getattr__, 'email')

    def test_deleting_users(self):
        self.assertEqual(0, UserModel.objects.count())
        user_1 = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John2',
                surname='Doe',
                password='TestPassword123!')
        user_2 = self.create_django_user(
                email='john.doe2@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        href_1, href_2 = user_1.href, user_2.href
        self.assertEqual(
            set([a.href for a in self.app.accounts]), {href_1, href_2})
        self.assertEqual(2, UserModel.objects.count())
        UserModel.objects.delete()
        self.assertEqual(0, UserModel.objects.count())
        a = self.app.accounts.get(href_1)
        self.assertRaises(StormpathError, a.__getattr__, 'email')
        a = self.app.accounts.get(href_2)
        self.assertRaises(StormpathError, a.__getattr__, 'email')

    def test_deleteing_a_group(self):
        self.assertEqual(0, Group.objects.count())
        Group.objects.create(name='testGroup')

        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, len(self.app.groups))

        Group.objects.all().delete()

        self.assertEqual(0, Group.objects.count())
        self.assertEqual(0, len(self.app.groups))

    def test_saving_group_membership(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')

        g = Group.objects.create(name='testGroup')
        user.groups.add(g)
        user.save()

        a = self.app.accounts.get(href=user.href)

        self.assertEqual(1, UserModel.objects.count())
        self.assertEqual(1, Group.objects.count())
        self.assertEqual(1, user.groups.filter(name=g.name).count())
        self.assertEqual(1, len(a.group_memberships))

        user.groups.all().delete()

        g = self.app.groups.create({'name': 'testGroup'})
        CLIENT.group_memberships.create({'account': a, 'group': g})

        user.save()
        self.assertEqual(1, len(self.app.groups))
        self.assertEqual(0, len(a.group_memberships))

    def test_updating_non_existent_sp_user(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')

        a = self.app.accounts.get(href=user.href)
        a.delete()

        self.assertRaises(ObjectDoesNotExist, user.save)

    def test_updating_a_user_that_doesnt_exists_on_sp(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')

        self.assertEqual(1, UserModel.objects.count())
        user.delete()
        self.assertEqual(0, UserModel.objects.count())
        self.assertEqual(0, len(self.app.accounts))

    def test_creating_a_user_with_invalid_password(self):
        self.assertEqual(0, UserModel.objects.count())
        self.assertRaises(StormpathError, self.create_django_user,
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='invalidpassword')  # stormpath pass policy

        self.assertEqual(0, UserModel.objects.count())
        self.assertEqual(0, len(self.app.accounts))

    def test_valid_check_password(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        self.assertTrue(user.check_password('TestPassword123!'))

    def test_invalid_check_password(self):
        self.assertEqual(0, UserModel.objects.count())
        user = self.create_django_user(
                email='john.doe1@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')
        self.assertFalse(user.check_password('invalidpassword'))


class TestDjangoUser(LiveTestBase):
    def test_creating_a_user(self):
        user = self.create_django_user(
                email='john.doe1@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)
        self.assertEqual(user.first_name, user.given_name)
        self.assertEqual(user.first_name, a.given_name)
        self.assertEqual(user.last_name, user.surname)
        self.assertEqual(user.last_name, a.surname)

    def test_creating_a_superuser(self):
        user = self.create_django_user(
                superuser=True,
                email='john.doe2@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)
        self.assertEqual(user.first_name, user.given_name)
        self.assertEqual(user.first_name, a.given_name)
        self.assertEqual(user.last_name, user.surname)
        self.assertEqual(user.last_name, a.surname)
        self.assertEqual(a.custom_data['spDjango_is_staff'], True)
        self.assertEqual(a.custom_data['spDjango_is_superuser'], True)

    def test_updating_a_user(self):
        user = self.create_django_user(
                email='john.doe3@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)

        user.surname = 'Smith'
        user.save()

        a = self.app.accounts.get(user.href)
        self.assertEqual(user.surname, a.surname)
        self.assertEqual(user.last_name, user.surname)
        self.assertEqual(user.last_name, a.surname)

        user.first_name = 'Jane'
        user.save()

        a = self.app.accounts.get(user.href)
        self.assertEqual(user.given_name, a.given_name)
        self.assertEqual(user.first_name, a.given_name)
        self.assertEqual(user.first_name, a.given_name)

    def test_updating_a_users_password(self):
        user = self.create_django_user(
                email='john.doe3@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')
        a = self.app.accounts.get(user.href)
        self.assertEqual(user.href, a.href)

        user.set_password('123!TestPassword')
        self.assertTrue(hasattr(user, 'raw_password'))

        user.save()

        b = StormpathBackend()

        self.assertFalse(hasattr(user, 'raw_password'))
        self.assertFalse(user.has_usable_password())
        self.assertTrue(b.authenticate(a.email, '123!TestPassword'))
        self.assertFalse(b.authenticate(a.email, 'TestPassword123!'))

    def test_authentication_pulls_user_into_local_db(self):
        self.assertEqual(0, UserModel.objects.count())
        acc = self.app.accounts.create({
            'email': 'jd@example.com',
            'given_name': 'John',
            'surname': 'Doe',
            'password': 'TestPassword123!',
        })

        b = StormpathBackend()

        b.authenticate(acc.email, 'TestPassword123!')
        self.assertEqual(1, UserModel.objects.count())
        user = UserModel.objects.get()
        self.assertEqual(user.first_name, user.given_name)
        self.assertEqual(user.first_name, acc.given_name)
        self.assertEqual(user.last_name, user.surname)
        self.assertEqual(user.last_name, acc.surname)

    def test_user_email_verification_enabled(self):
        directory = self.app.default_account_store_mapping.account_store
        directory.account_creation_policy.verification_email_status = 'ENABLED'
        directory.account_creation_policy.save()
        user = self.create_django_user(
                email='john.doe3@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')

        a = self.app.accounts.get(user.href)

        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertEqual(a.status, a.STATUS_UNVERIFIED)

        a.status = a.STATUS_ENABLED
        a.save()
        sb = StormpathBackend()
        user = sb._create_or_get_user(a)

        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertEqual(a.status, a.STATUS_ENABLED)

        a.status = a.STATUS_DISABLED
        a.save()
        user = sb._create_or_get_user(a)
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertEqual(a.status, a.STATUS_DISABLED)

    def test_user_email_verification_disabled(self):
        user = self.create_django_user(
                email='john.doe3@example.com',
                first_name='John',
                last_name='Doe',
                password='TestPassword123!')

        a = self.app.accounts.get(user.href)

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertEqual(a.status, a.STATUS_ENABLED)

        a.status = a.STATUS_DISABLED
        a.save()
        sb = StormpathBackend()
        user = sb._create_or_get_user(a)

        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertEqual(a.status, a.STATUS_DISABLED)

        a.status = a.STATUS_UNVERIFIED
        a.save()
        user = sb._create_or_get_user(a)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertEqual(a.status, a.STATUS_UNVERIFIED)


class TestForms(LiveTestBase):
    def test_user_creation_form_password_missmatch(self):
        data = {'email': 'john.doe@example.com',
                'username': 'johndoe',
                'given_name': 'John',
                'surname': 'Doe',
                'password1': 'TestPassword123!',
                'password2': 'TestPassword12345!'}
        form = StormpathUserCreationForm(data)
        is_valid = form.is_valid()
        self.assertFalse(is_valid)
        self.assertRaises(ValueError, form.save)

    def test_user_creation_form_password_invalid(self):
        data = {'email': 'john.doe@example.com',
                'username': 'johndoe',
                'given_name': 'John',
                'surname': 'Doe',
                'password1': 'invalid',
                'password2': 'invalid'}
        form = StormpathUserCreationForm(data)
        is_valid = form.is_valid()
        self.assertFalse(is_valid)
        self.assertRaises(ValueError, form.save)

    def test_user_creation_form_existing_email(self):
        self.create_django_user(
                email='john.doe@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')

        data = {'email': 'john.doe@example.com',
                'username': 'johndoe',
                'given_name': 'John',
                'surname': 'Doe',
                'password1': 'TestPassword123!',
                'password2': 'TestPassword123!'}
        form = StormpathUserCreationForm(data)
        is_valid = form.is_valid()
        self.assertFalse(is_valid)
        self.assertRaises(ValueError, form.save)

    def test_user_creation_form_existing_username(self):
        user = self.create_django_user(
                email='john.doe@example.com',
                given_name='John',
                surname='Doe',
                password='TestPassword123!')

        acc = self.app.accounts.get(href=user.href)

        data = {'email': 'john.doe@example.com',
                'given_name': 'John',
                'username': acc.username,
                'surname': 'Doe',
                'password1': 'TestPassword123!',
                'password2': 'TestPassword123!'}

        form = StormpathUserCreationForm(data)
        is_valid = form.is_valid()
        self.assertFalse(is_valid)
        self.assertRaises(ValueError, form.save)

    def test_saving_user_form(self):
        data = {'email': 'john.doe123@example.com',
                'username': 'johndoe',
                'given_name': 'John',
                'surname': 'Doe',
                'password1': 'TestPassword123!',
                'password2': 'TestPassword123!'}
        form = StormpathUserCreationForm(data)
        is_valid = form.is_valid()
        self.assertTrue(is_valid)
        form.save()
        self.assertEqual(1, UserModel.objects.count())
