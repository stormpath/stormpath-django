"""Custom Django User models for Stormpath.

Any application that uses django_stormpath must provide a user model with a
url field. The url is used in the authentication backend to keep track which
remote Stormpath user the local user represents. It is meant to be used in an
application that modifies user data on Stormpath. The user classes provided
here are convenient to inherit from in custom user models in applications but
the only requirement is that the user model has an url which is not provided by
the default Django User model and the user model has to be set as the default.

* Example (settings.py):

    AUTH_MODEL_USER = 'django_stormpath.StormpathUser'

"""

from django.db import models
from django.contrib.auth.models import (AbstractUser,
    BaseUserManager, AbstractBaseUser, PermissionsMixin)


class StormpathUserManager(BaseUserManager):

    def create_user(self, email, username, first_name, last_name, password):

        if not email:
            raise ValueError("Users must have an email address")

        if not first_name or not last_name:
            raise ValueError("Users must provide a given name and a surname")

        user = self.model(email=StormpathUserManager.normalize_email(email),
            first_name=first_name, last_name=last_name)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, *args):

        user = self.create_user(args)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class StormpathBaseUser(AbstractBaseUser, PermissionsMixin):

    url = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = StormpathUserManager()

    def get_full_name(self):
        return "{0} {1}".format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()


class StormpathUser(AbstractUser):
    url = models.CharField(max_length=255, null=True, blank=True)
