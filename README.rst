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

.. note::
    This library will NOT work on Google App Engine due to incompatibilities
    with the
    `requests <http://stackoverflow.com/questions/9604799/can-python-requests-library-be-used-on-google-app-engine>`_
    package :(


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

You can read more about how Django's custom user model works `here <https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#specifying-a-custom-user-model> _`.

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

Once this is done, you're ready to get started!  The next thing you need to do
is to sync your database and apply any migrations:

.. code-block:: console

    $ python manage.py syncdb
    $ python manage.py migrate

And that's it!  You're now ready to get started =)


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

    UserModel.objects.create_user('john.doe@example.com', 'John', 'Doe', 'Password123!')

To create a super user, you can use ``manage.py``:

.. code-block:: console

    $ python manage.py createsuperuser --username=joe --email=joe@example.com

This will set ``is_admin``, ``is_staff`` and ``is_superuser`` to ``True`` on
the newly created user.  All extra parameters like the aforementioned flags are
saved on Stormpath in the Accounts customData Resource and can be inspected
outside of Django. This just calls the ``UserModel.objects.create_superuser`` method
behind the scenes.

Once you're all set up you can use the ``StormpathUser`` model just as you would the normal
django user model to form relationships within your models:

    class Book(models.Model):
        author = models.ForeignKey(settings.AUTH_USER_MODEL)


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
    # Site dashboard.  NOTE: This URL must be *exactly* the same as the one in
    # your Stormpath ID Site dashboard.
    STORMPATH_ID_SITE_CALLBACK_URI = 'http://localhost:8000/stormpath-id-site-callback/'

    # The URL you'd like to redirect users to after they've successfully logged
    # into their account.
    LOGIN_REDIRECT_URL = '/redirect/here'

Lastly, you've got to include some URLs in your main ``urls.py`` as well:

.. code-block:: python

    url(r'', include('django_stormpath.urls')),

An example of how to use the available URL mappings can be found `here
<https://github.com/stormpath/stormpath-django/blob/develop/testproject/testapp/templates/testapp/index.html>`_.


Social Login
------------

Django Stormpath supports social login as well. Currently supported Providers are: Google, Github, Linkedin and Facebook.
First thing that you need to do is add `StormpathSocialBackend` to the list of allowed authentication backends
in your settings file:

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # ...
        'django_stormpath.backends.StormpathSocialBackend',
    )

After that you can enable each provider with the following settings:

.. code-block:: python

    STORMPATH_ENABLE_GOOGLE = True
    STORMPATH_ENABLE_FACEBOOK = True
    STORMPATH_ENABLE_GITHUB = True
    STORMPATH_ENABLE_LINKEDIN = True

    STORMPATH_SOCIAL = {
            'GOOGLE': {
                'client_id': os.environ['GOOGLE_CLIENT_ID'],
                'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
            },
            'FACEBOOK': {
                'client_id': os.environ['FACEBOOK_CLIENT_ID'],
                'client_secret': os.environ['FACEBOOK_CLIENT_SECRET']
            },
            'GITHUB': {
                'client_id': os.environ['GITHUB_CLIENT_ID'],
                'client_secret': os.environ['GITHUB_CLIENT_SECRET']
            },
            'LINKEDIN': {
                'client_id': os.environ['LINKEDIN_CLIENT_ID'],
                'client_secret': os.environ['LINKEDIN_CLIENT_SECRET']
            },
    }


And that's it! Now if you navigate to "https://yourdjangoapp.com/social-login/google/" for each provider respectively,
you will be redirected to that provider for authentication. If you are authenticated succesffully you will be redirected back
to your django app and logged in automatically. Stormpath django also creates a directory for each social provider automatically
so you don't need to worry about it.

.. note::
    Please note that the callback URL's for each provider are listed in django stormpath's urls.py file.
    You will need to use these callback urls and set them as redirect URI's when configuring each provider
    in their respecive dashboards. For intance the callback URL for Google is: "https://yourdjangoapp.com/social-login/google/callback".

.. note::
    Note that for OAuth2 to work we need to be using HTTPS.
    For django to work correctly with HTTPS please set the following settings:

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


Caching
-------

The best kind of websites are fast websites.  ``Django-Stormpath`` includes
built-in support for caching.  You can currently use either:

- A local memory cache (*default*).
- A `memcached <http://memcached.org>`_ cache.
- A `redis <http://redis.io/>`_ cache.

All can be easily configured using configuration variables.

There are several configuration settings you can specify to control caching
behavior.  You need to add the ``STORMPATH_CACHE_OPTIONS`` to your Django
project's settings file.

Here's an example which shows how to enable caching with redis::

     from stormpath.cache.redis_store import RedisStore

     STORMPATH_CACHE_OPTIONS = {
        'store': RedisStore,
        'store_opts': {
            'host': 'localhost',
            'port': 6379
        }
    }

Here's an example which shows how to enable caching with memcached::

     from stormpath.cache.memcached_store import MemcachedStore

     STORMPATH_CACHE_OPTIONS = {
        'store': MemcachedStore,
        'store_opts': {
            'host': 'localhost',
            'port': 11211
        }
     }

If no cache is specified, the default, ``MemoryStore``, is used.  This will
cache all resources in local memory.

For a full list of options available for each cache backend, please see the
official `Caching Docs <https://docs.stormpath.com/python/product-guide/#caching>`_
in our Python library.


Copyright and License
---------------------

Copyright &copy; 2014 Stormpath, inc.  You may use and/or modify this library
under the terms of Apache License version 2.0.  Please see the
`LICENSE <https://github.com/stormpath/stormpath-django/blob/develop/LICENSE>`_
file for details.


Change Log
----------

All library changes, in descending order.


Version 1.0.3
*************

**Released on June 18, 2015.**

- Updating ID site docs slightly.
- Fixing Travis CI builds.
- Upgrading to the latest Stormpath release.


Version 1.0.2
*************

**Released on May 12, 2015.**

- Improving Travis CI builds so that tests are run against Django 1.6.x, 1.7.x,
  and 1.8.x.  This will help flush out Django version issues (*hopefully!*).
- Fixing old migration issue.  This should make all new ``syncdb`` commands run
  successfully regardless of database used.
- Supporting ``User.first_name`` and ``User.last_name`` per Django's
  conventions.  This makes our user model play nice with third party Django apps
  =)


Version 1.0.1
*************

**Released on April 30, 2015.**

- Adding missing migrations.  This fixes issues when running ``syncdb`` on a
  new Postgres database.
- Making the built-in ``delete()`` method remove both copies of the account.


Version 1.0.0
*************

**Released on April 18, 2015.**

- Fixing issue with ``StormpathPermissionsMixin`` by replacing it with the
  built-in ``PermissionsMixin`` that Django provides.  Thanks again,
  `@davidmarquis <https://github.com/davidmarquis>`_!
- The above change is a **breaking** change -- so users of earlier versions of
  django-stormpath are encouraged to stay on their current release unless they
  want to manually handle the database migrations.  This breakage is *very rare*
  for our libraries, but was necessary in this case to fix the underlying
  library issues.
- Updating broken test case for the new release.


Version 0.0.7
*************

**Released on April 15, 2015.**

- Fixing documentation issue in the README -- we had an incorrect code sample
  setting up urlpatterns.  Thanks `@espenak <https://github.com/espenak>`_ for
  the find!
- Adding a `StormpathUserManager.delete()` method.  This makes it possible to
  'cleanly' delete users from both Django and Stormpath.
- Fixing Group permission editing.  Thanks `@davidmarquis <https://github.com/davidmarquis>`_!
- Fixing bug with maintaining the username field when editing user objects.
  Thanks again, `@davidmarquis <https://github.com/davidmarquis>`_!
- Adding in missing dependency: ``requests_oauthlib``.  This is required for our
  ID site functionality to work, but was missing.


Version 0.0.6
*************

**Released on February 11, 2015.**

- PEP-8 fixing imports, and making things python 3 compatible (thanks
  @rtrajano)!


Version 0.0.5
*************

**Released on February 5, 2015.**

- Adding support for social login.
- Various test fixes.
- PEP-8.


Version 0.0.4
*************

**Released on January 19, 2015.**

- Fixing incompatible arguments being passed from django-rest-framework-jwt to
  ``StormpathBackend.authenticate()``.
- Changing unexpected behaviors (*no return value*) of
  ``StormpathuserManager.create()``.

All fixes thanks to `@skolsuper <https://github.com/skolsuper>`_!


Version 0.0.3
*************

**Released on December 9, 2014.**

- Adding cache support.
- Fixing docs.
- Adding docs on caching.
- Adding support for ID site.


Version 0.0.2
*************

**Released on November 26, 2014.**

- Fixing README stuff :(


Version 0.0.1
*************

**Released on November 26, 2014.**

- First release!
