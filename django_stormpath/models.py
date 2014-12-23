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
from django.db.models.signals import pre_save, pre_delete
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django import VERSION as django_version

from stormpath.client import Client
from stormpath.error import Error as StormpathError

from django_stormpath import __version__

USER_AGENT = 'stormpath-django/%s django/%s' % (__version__, django_version)

CLIENT = Client(
        id=settings.STORMPATH_ID,
        secret=settings.STORMPATH_SECRET,
        user_agent=USER_AGENT,
        cache_options=getattr(settings, 'STORMPATH_CACHE_OPTIONS', None))

APPLICATION = CLIENT.applications.get(settings.STORMPATH_APPLICATION)


class StormpathPermissionsMixin(PermissionsMixin):
    pass


class StormpathUserManager(BaseUserManager):

    def create(self, *args, **kwargs):
        self.create_user(*args, **kwargs)

    def create_user(self, email, given_name, surname, password):

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


class StormpathBaseUser(AbstractBaseUser, StormpathPermissionsMixin):

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
    EXCLUDE_FIELDS = ['href', 'last_login', 'groups', 'id', 'stormpathpermissionsmixin_ptr', 'user_permissions']

    PASSWORD_FIELD = 'password'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['given_name', 'surname']

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = StormpathUserManager()

    DJANGO_PREFIX = 'spDjango_'

    def _mirror_data_from_db_user(self, account, data):
        for field in self.EXCLUDE_FIELDS:
            if field in data:
                del data[field]

        if 'password' in data:
            del data['password']

        account.status = account.STATUS_DISABLED if data['is_active'] is False else account.STATUS_ENABLED

        if 'is_active' in data:
            del data['is_active']

        for key in data:
            if key in self.STORMPATH_BASE_FIELDS:
                account[key] = data[key]
            else:
                account.custom_data[self.DJANGO_PREFIX + key] = data[key]

        return account

    def _mirror_data_from_stormpath_account(self, account):
        for field in self.STORMPATH_BASE_FIELDS:
            # The password is not sent via the API
            # so we take care here to not try and
            # mirror it because it's not there
            if field != 'password':
                self.__setattr__(field, account[field])
        for key in account.custom_data.keys():
            self.__setattr__(key.split(self.DJANGO_PREFIX)[0], account.custom_data[key])

        self.is_active = True if account.status == account.STATUS_ENABLED else False

    def _save_sp_group_memberships(self, account):
        try:
            db_groups = self.groups.values_list('name', flat=True)
            for g in db_groups:
                if not account.has_group(g):
                    account.add_group(g)

            account.save()

            for gm in account.group_memberships:
                if gm.group.name not in db_groups:
                    gm.delete()
        except Exception:
            raise IntegrityError("Unable to save group memberships.")

    def _create_stormpath_user(self, data, raw_password):
        data['password'] = raw_password
        account = APPLICATION.accounts.create(data)
        self._save_sp_group_memberships(account)
        return account

    def _update_stormpath_user(self, data, raw_password):
        # if password has changed
        if raw_password:
            data['password'] = raw_password
        else:
            # don't set the password if it hasn't changed
            del data['password']
        try:
            acc = APPLICATION.accounts.get(data.get('href'))
            # materialize it
            acc.email

            acc = self._mirror_data_from_db_user(acc, data)
            acc.save()
            self._save_sp_group_memberships(acc)
            return acc
        except StormpathError:
            raise self.DoesNotExist('Could not find Stormpath User.')

    def get_full_name(self):
        return "%s %s" % (self.given_name, self.surname)

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
            # we're not sure if we have a href yet, hence we
            # filter by email
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
            href = self.href
            super(StormpathBaseUser, self).delete(*args, **kwargs)
            try:
                account = APPLICATION.accounts.get(href)
                account.delete()
            except StormpathError:
                raise


class StormpathUser(StormpathBaseUser):
    pass


@receiver(pre_save, sender=Group)
def save_group_to_stormpath(sender, instance, **kwargs):
    try:
        APPLICATION.groups.create({'name': instance.name})
    except StormpathError as e:
        raise IntegrityError(e)


@receiver(pre_delete, sender=Group)
def delete_group_from_stormpath(sender, instance, **kwargs):
    try:
        APPLICATION.groups.search({'name': instance.name})[0].delete()
    except StormpathError as e:
        raise IntegrityError(e)

