import sys

from django.core.management.base import NoArgsCommand

try:
    input = raw_input
except NameError:
    pass

from stormpath.resources.provider import Provider
from stormpath.error import Error as StormpathError

from django_stormpath import social


class Command(NoArgsCommand):
    help = 'Creates a Directory used for logging in with Google, Facebook, Github or Linkedin.'

    def handle_noargs(self, **options):
        providers = [Provider.GOOGLE, Provider.FACEBOOK, Provider.GITHUB, Provider.LINKEDIN]
        print("""
        1. Google
        2. Facebook
        3. Github
        4. Linkedin
        """)

        p = input("Please choose a provider: ")
        try:
            provider_choice = int(p) - 1  # off by one
        except ValueError:
            print("Please choose on of the available provider from the list.")
            sys.exit(-1)

        provider = providers[provider_choice]

        redirect_uri = input("Please specify the FQDN redirect uri for this provider: ")

        if not redirect_uri.startswith('http'):
            print("Invalid redirect URI. Please enter a FQDN URI like http://example.com/social-login/google/callback")
            sys.exit(-1)

        try:
            social.create_provider_directory(provider, redirect_uri)
            print("Successfully created Directory for %s" % provider)
        except StormpathError as e:
            print("Error! %s" % e)
            sys.exit(-1)

