django-stormpath
================

Simple, scalable, user authentication for Django (powered by `Stormpath <https://stormpath.com>`_).

.. image:: https://img.shields.io/pypi/v/django-stormpath.svg
    :alt: django-stormpath Release
    :target: https://pypi.python.org/pypi/django-stormpath

.. image:: https://img.shields.io/pypi/dm/django-stormpath.svg
    :alt: django-stormpath Downloads
    :target: https://pypi.python.org/pypi/django-stormpath

.. image:: https://img.shields.io/travis/stormpath/stormpath-django.svg
    :alt: django-stormpath Build
    :target: https://travis-ci.org/stormpath/stormpath-django

.. note::
    This is a beta release, if you run into any issues, please file a report on
    our `Issue Tracker <https://github.com/stormpath/stormpath-django/issues>`_.


Meta
----

This library provides user account storage, authentication, and authorization
with `Stormpath <https://stormpath.com>`_.

This library works with Python 2.7.x and Python 3.x.


Installation
------------

To install the library, you'll need to use `pip <http://pip.readthedocs.org/en/latest/>`_:

.. code-block:: console

    $ pip install django-stormpath


How it Works
------------

django-stormpath provides an ``AUTHENTICATION_BACKEND`` which is used to
communicate with the Stormpath REST API.

When a user tries to log in, and Stormpath is used as the authentication
backend, django-stormpath always asks the Stormpath service if the user's
credentials (*username or email and password*) are correct.  Password hashes are
always stored in Stormpath, and not locally.

If a user's credentials are valid, there are two possible scenarios:

1. User doesn't exist in Django's database (*PostgreSQL, MySQL, Oracle etc.*).
   In this case, a user will be created in the local Django user database with
   their username, password, email, first name, and last name identical to the
   Stormpath user's. Then this user will be authenticated.

2. User exists in Django's database.  In this case, if a user's information has
   changed on Stormpath, the Django user's fields are updated accordingly.
   After this, the user will be authenticated.

.. note::
    An account on Stormpath can be disabled, enabled, locked and unverified.
    When a user is created or updated, the ``is_active`` field is set to
    ``True`` if the Stormpath account is enabled and ``False`` otherwise.

 .. note::
    For a Stormpath user to be able to log into the Django admin interface
    it must specify the ``is_superuser`` and ``is_staff`` properties in the
    Stormpath Account's customData resource.


Usage
-----

First, you need to add ``django_stormpath`` to your ``INSTALLED_APPS`` setting
in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...,
        'django_stormpath',
    )

Next, you need to add the Stormpath backend into ``AUTHENTICATION_BACKENDS``:

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # ...
        'django_stormpath.backends.StormpathBackend',
    )

After that's done, you'll also need to tell Django to use Stormpath's user
model:

.. code-block:: python

    AUTH_USER_MODEL = 'django_stormpath.StormpathUser'

Lastly, you need to specify your Stormpath credentials: your API key and secret,
as well as your Stormpath Application URL.

For more information about these things, please see the official
`guide <http://docs.stormpath.com/python/product-guide/>`_.

To specify your Stormpath credentials, you'll need to add the following settings
to your ``settings.py``:

.. code-block:: python

    STORMPATH_ID = 'yourApiKeyId'
    STORMPATH_SECRET = 'yourApiKeySecret'
    STORMPATH_APPLICATION = 'https://api.stormpath.com/v1/applications/YOUR_APP_UID_HERE'


Example: Creating a User
------------------------

To pragmatically create a user, you can use the following code:

.. code-block:: python

    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    UserModel.objects.create(
        email = 'john.doe@example.com',
        given_name = 'John',
        surname = 'Doe',
        password = 'password123!'
    )

The above example just calls the ``create_user`` method:

.. code-block:: python

    UserModel.create_user('john.doe@example', 'John', 'Doe', 'Password123!')

To create a super user, you can use ``manage.py``:

.. code-block:: console

    $ python manage.py createsuperuser --username=joe --email=joe@example.com

This will set ``is_admin``, ``is_staff`` and ``is_superuser`` to ``True`` on
the newly created user.  All extra parameters like the aforementioned flags are
saved on Stormpath in the Accounts customData Resource and can be inspected
outside of Django.

.. note::
    When doing the initial ``syncdb`` call (or ``manage.py createsuperuser``)
    an Account is also created on Stormpath.  Every time the ``save`` method
    is called on the UserModel instance it is saved/updated on Stormpath as
    well.  This includes working with the Django built-in admin interface.


ID Site
-------

If you'd like to not worry about building your own registration and login
screens at all, you can use Stormpath's new `ID site feature
<http://docs.stormpath.com/guides/using-id-site/>`_.  This is a hosted login
subdomain which handles authentication for you automatically.

To make this work in Django, you need to specify a few settings: 

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # ...
        'django_stormpath.backends.StormpathIdSiteBackend',
    )

    # This should be set to the same URI you've specified in your Stormpath ID
    # Site dashboard.
    STORMPATH_ID_SITE_CALLBACK_URI = 'must_be_the_same_as_in_id_site_dashboard'

    # The URL you'd like to redirect users to after they've successfully logged
    # into their account.
    LOGIN_REDIRECT_URL = '/redirect/here'

Lastly, you've got to include some URLs in your main ``urls.py`` as well:

.. code-block:: python

    url(r'', include(django_stormpath.urls)),

An example of how to use the available URL mappings can be found `here
<https://github.com/stormpath/stormpath-django/blob/develop/testproject/testapp/templates/testapp/index.html>`_.


Copyright and License
---------------------

Copyright &copy; 2014 Stormpath, inc.  You may use and/or modify this library
under the terms of Apache License version 2.0.  Please see the
`LICENSE <https://github.com/stormpath/stormpath-django/blob/develop/LICENSE>`_
file for details.
