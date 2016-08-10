import sys

import datetime

from django.core.management.base import BaseCommand

try:
    input = raw_input
except NameError:
    pass

from django_stormpath.models import StormpathUserManager, APPLICATION


class Command(NoArgsCommand):
    help = 'Syncs remote accounts to the local database.'

    def handle(self, **options):
        try:
            user_manager = StormpathUserManager()
            start_time = datetime.datetime.now()
            user_manager.sync_accounts()
            duration = datetime.datetime.now() - start_time
            print("Successfully synced accounts from %s directory in %s" % (APPLICATION.name, duration))
        except Exception as e:
            print("Error! %s" % e)
            sys.exit(-1)

