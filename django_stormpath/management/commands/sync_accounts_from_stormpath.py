import sys

import datetime

from django.core.management.base import BaseCommand
from django_stormpath.models import APPLICATION, StormpathUserManager


class Command(BaseCommand):
    help = 'Syncs remote accounts to the local database.'

    def handle(self, **options):
        try:
            user_manager = StormpathUserManager()
            start_time = datetime.datetime.now()
            user_manager.sync_accounts_from_stormpath()
            duration = datetime.datetime.now() - start_time
            print('Successfully synced accounts from {} directory in {}'.format(APPLICATION.name, duration))
        except Exception as e:
            print('Error! {}'.format(e))
            sys.exit(-1)

