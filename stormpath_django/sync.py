from contextlib import contextmanager
from django.db import transaction


@contextmanager
def stormpath_sync(db_user, sp_account):
    pass
