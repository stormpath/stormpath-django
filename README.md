# Django plugin for Stormpath

[![Build Status](https://travis-ci.org/stormpath/stormpath-django.png?branch=master)](https://travis-ci.org/stormpath/stormpath-django)

A Django application that uses Stormpath SDK API calls to provide
authentication and access controls. It works with Python 3.3 and 2.7.

## Installation and requirements

The only requirement needed to run stormpath-django is Stormpath SDK for
Python. Please note that at least version 1.0.1 of Stormpath is
required.

    # Download from GitHub
    git clone https://github.com/stormpath/stormpath-django.git
    cd stormpath-django

    # Run the tests
    python setup.py test

    # Build
    python setup.py build

    # Install it
    python setup.py install


## How it works

When authenticating a user, Django checks the credentials in order in which
they are added in settings.py until a user is either authenticated or it ran
out of backends to check. This allows us to use Stormpath auth alongside
regular and other Django auth backends.

When a user tries to log in and Stormpath is used as the authentication backend
django_stormpath always asks the Stormpath service if the user's credentials
(username or email and password) are correct. If the credentials are OK, there
are two possible scenarios:

1. User doesn't exist in Django's database (PostgreSQL, MySQL, Oracle etc.)
    - user is created with his username, password, email, first name and last
      name set to match Stormpath's
    - user is authenticated if account is enabled


2. User exists in Django's database
    - if user's info has changed on Stormpath, Django user fields are updated
    - user is logged in if account is enabled


* Note that an account on Stormpath can be disabled, enabled, locked and
  unverified. When a user is created or updated, the is_active field is set
  to True if the Stormpath account is enabled and False if otherwise.

* The user will never be deleted from Django database even if he/she was
  deleted from Stormpath

* The `is_staff`/`is_superuser` fields aren't changed so a user won't be able
  to log into Django Admin unless set manually or by other auth backends


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


## Copyright and License

Copyright &copy; 2013 Stormpath, inc. You may use and/or modify Stormpath Django
plugin under the terms of Apache License version 2.0. Please see the
[LICENSE](LICENSE) file for details.
