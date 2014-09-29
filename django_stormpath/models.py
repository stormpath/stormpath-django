"""Custom Django User models for Stormpath.

Any application that uses django_stormpath must provide a user model with a
href field. The href is used in the authentication backend to keep track which
remote Stormpath user the local user represents. It is meant to be used in an
application that modifies user data on Stormpath. If needing to add more
fields please extend the StormpathUser class from this module.
"""

from django.conf import settings
from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import (BaseUserManager,
        AbstractBaseUser, PermissionsMixin)
from django.forms import model_to_dict
from django.core.exceptions import ObjectDoesNotExist

from stormpath.client import Client
from stormpath.error import Error as StormpathError

CLIENT = Client(
        id=settings.STORMPATH_ID,
        secret=settings.STORMPATH_SECRET)
APPLICATION = CLIENT.applications.get(
        href=settings.STORMPATH_APPLICATION)


class StormpathUserManager(BaseUserManager):

    def create(self, *args, **kwargs):
        self.create_user(*args, **kwargs)

    def create_user(self, email, given_name, surname, password, **kwargs):

        if not email:
            raise ValueError("Users must have an email address")

        if not given_name or not surname:
            raise ValueError("Users must provide a given name and a surname")

        user = self.model(email=StormpathUserManager.normalize_email(email),
            given_name=given_name, surname=surname)

        user.set_password(password)
        user.save(using=self._db)
        user._remove_raw_password()
        return user

    def create_superuser(self, **kwargs):
        user = self.create_user(**kwargs)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        user._remove_raw_password()
        return user


class StormpathBaseUser(AbstractBaseUser, PermissionsMixin):

    class Meta:
        abstract = True

    href = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)
    given_name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True)

    STORMPATH_BASE_FIELDS = ['href', 'username', 'given_name', 'surname', 'middle_name', 'email', 'password']
    EXCLUDE_FIELDS = ['href', 'last_login']

    PASSWORD_FIELD = 'password'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['given_name', 'surname']

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = StormpathUserManager()

    def _mirror_data_from_db_user(self, account, data):
        for field in self.EXCLUDE_FIELDS:
            try:
                del data[field]
            except KeyError:
                pass
        try:
            if data['password'] is None:
                del data['password']
        except KeyError:
            pass
        for key in data:
            if key in self.STORMPATH_BASE_FIELDS:
                account[key] = data[key]
            else:
                account.custom_data[key] = data[key]

        account.status = account.STATUS_DISABLED if data['is_active'] is False else account.STATUS_ENABLED

        return account

    def _mirror_data_from_stormpath_account(self, account):
        for field in self.STORMPATH_BASE_FIELDS:
            if field != 'password':
                self.__setattr__(field, account[field])

    def _create_stormpath_user(self, data, raw_password):
        data['password'] = raw_password
        account = APPLICATION.accounts.create(data)
        return account

    def _update_stormpath_user(self, data, raw_password):
        # if password has changed
        if raw_password:
            data['password'] = raw_password
        else:
            # don't set the password if it hasn't changed
            del data['password']
        accounts = APPLICATION.accounts.search({'email': data.get('email')})
        if accounts:
            acc = accounts[0]
            acc = self._mirror_data_from_db_user(acc, data)
            acc.save()
            return acc
        raise self.DoesNotExist('Could not find Stormpath User.')

    def get_full_name(self):
        return "{0} {1}".format(self.given_name, self.surname)

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()

    def _update_for_db_and_stormpath(self, *args, **kwargs):
        try:
            with transaction.atomic():
                super(StormpathBaseUser, self).save(*args, **kwargs)
                self._update_stormpath_user(model_to_dict(self), self._get_raw_password())
        except StormpathError:
            raise
        except ObjectDoesNotExist:
            self.delete()
            raise
        except Exception:
            raise

    def _create_for_db_and_stormpath(self, *args, **kwargs):
        try:
            with transaction.atomic():
                super(StormpathBaseUser, self).save(*args, **kwargs)
                account = self._create_stormpath_user(model_to_dict(self), self._get_raw_password())
                self.href = account.href
                self.username = account.username
                self.save(*args, **kwargs)
        except StormpathError:
            raise
        except Exception:
            accounts = APPLICATION.accounts.search({'email': self.email})
            if accounts:
                accounts[0].delete()
            raise

    def _save_db_only(self, *args, **kwargs):
        super(StormpathBaseUser, self).save(*args, **kwargs)

    def _remove_raw_password(self):
        """We need to send a raw password to Stormpath. After an Account is saved on Stormpath
        we need to remove the raw password field from the local object"""

        try:
            del self.raw_password
        except AttributeError:
            pass

    def _get_raw_password(self):
        try:
            return self.raw_password
        except AttributeError:
            return None

    def set_password(self, raw_password):
        """We don't want to keep passwords locally"""
        self.set_unusable_password()
        self.raw_password = raw_password

    def save(self, *args, **kwargs):
        # Are we updating an existing User?
        if self.id:
            self._update_for_db_and_stormpath(*args, **kwargs)
        # Or are we creating a new user?
        else:
            self._create_for_db_and_stormpath(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            email = self.email
            super(StormpathBaseUser, self).delete(*args, **kwargs)
            try:
                accounts = APPLICATION.accounts.search({'email': email})
                if accounts:
                    accounts[0].delete()
            except:
                raise


class StormpathUser(StormpathBaseUser):
    pass

