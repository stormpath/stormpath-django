# Django plugin for Stormpath

[![Build Status](https://travis-ci.org/stormpath/stormpath-django.png?branch=master)](https://travis-ci.org/stormpath/stormpath-django)

**This integration is UNDER DEVELOPMENT - please use at your own risk**

A Django application that uses Stormpath SDK API calls to provide
authentication and access controls. It works with Python 3.x and 2.7.x.

## Installation and requirements

    # Download from GitHub
    git clone https://github.com/stormpath/stormpath-django.git
    cd stormpath-django

    # Install it
    python setup.py install

    # Install test deps
    python setup.py testdep

    # Run the tests
    # NOTE: requires STORMPATH_API_KEY_ID, STORMPATH_API_KEY_SECRET
    # and STORMPATH_APPLICATION env vars to be set
    # (or placed in a .env file alongside testproject/manage.py)
    python setup.py test

    # Or install via pip
    pip install stormpath-django


## How it works

Stormpath Django integration provides an AUTHENTICATION_BACKEND which is used
to communicate with the Stormpath REST API and authenticate users.

When a user tries to log in and Stormpath is used as the authentication backend
django_stormpath always asks the Stormpath service if the user's credentials
(username or email and password) are correct, in fact passwords aren't even stored
in the local database. If the credentials are OK, there
are two possible scenarios:

1. User doesn't exist in Django's database (PostgreSQL, MySQL, Oracle etc.)
    - user is created with his username, password, email, first name and last
      name set to match Stormpath's
    - user is authenticated if account is enabled


2. User exists in Django's database
    - if user's info has changed on Stormpath, Django user fields are updated
    - user is logged in if account is enabled


* Note: that an account on Stormpath can be disabled, enabled, locked and
  unverified. When a user is created or updated, the is_active field is set
  to True if the Stormpath account is enabled and False if otherwise.

* Note: For a Stormpath user to be able to log into the django admin interface
  it must specify the `is_superuser` and `is_staff` properties in the Accounts
  CustomData.

## Usage

Add `django_stormpath` to your `INSTALLED_APPS` in settings.py.

Add `django_stormpath.backends.StormpathBackend` to `AUTHENTICATION_BACKENDS`
in settings.py.

    AUTHENTICATION_BACKENDS = (
        'django_stormpath.backends.StormpathBackend',
    )

Set `django_stormpath.StormpathUser` as the user model:

    AUTH_USER_MODEL = 'django_stormpath.StormpathUser'

To access the Stormpath service an API key and secret are required. Also, every
Stormpath application has a unique ID so we need to know the application URL to
successfully authenticate with Stormpath. For further information please read
the [Stormpath Product Guide](http://www.stormpath.com/docs/python/product-guide).

The service API key and secret, as well as the appplication URL need to be
set in Django settings:

    STORMPATH_ID = "yourApiKeyId"
    STORMPATH_SECRET = "yourApiKeySecret"
    STORMPATH_APPLICATION = "https://api.stormpath.com/v1/applications/YOUR_APP_UID_HERE"


Example: Creating a user:

    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    UserModel.objects.create(
        email='john.doe@example.com',
        given_name='John',
        surname='Doe',
        password='password123!')

The above method just calls the `create_user` method

    UserModel.create_user('john.doe@example', 'John', 'Doe', 'Password123!')

For creating a superuser use:

    UserModel.create_user('john.doe@example', 'John', 'Doe', 'Password123!')

The above method will set `is_admin`, `is_staff` and `is_superuser` to `True`
on the newly created user. All extra parameters like the aforementioned flags are saved
on Stormpath in the Accounts CustomData Resource and can be inspected outside of
django using, for instance, the `stormpath-cli` tool.

Note: When doing the initial `syncdb` call (or `manage.py createsuperuser`)
an Account is also created on Stormpath. In fact every time the `save` method
is called on the UserModel instance it is saved/updated on Stormpath as well.
This includes working with the django built-in admin interface.

## ID Site

For using Stormpath's [ID Site feature](http://docs.stormpath.com/guides/using-id-site/) we
must add another `AUTHENTICATION_BACKEND`

    AUTHENTICATION_BACKENDS = (
        'django_stormpath.backends.StormpathIdSiteBackend',
    )

The following settings:

    STORMPATH_ID_SITE_CALLBACK_URI = 'must_be_the_same_as_in_id_site_dashboard'
    LOGIN_REDIRECT_URL = '/redirect/here'

And of course include the url mappings in your projects main `urls.py` like so:

    url(r'', include(django_stormpath.urls)),

An example of how to use the available url mappings can be found here: `testproject/testapp/templates/testapp/index.html`.


## Copyright and License

Copyright &copy; 2013 Stormpath, inc. You may use and/or modify Stormpath Django
plugin under the terms of Apache License version 2.0. Please see the
[LICENSE](LICENSE) file for details.
