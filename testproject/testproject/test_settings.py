
from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

STORMPATH_APPLICATION = None  # the test suite generates a random application for it's self

