"""Library helpers."""


from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist


def validate_settings(settings):
    """Ensure all user-supplied settings exist, or throw a useful error message.

    :param obj settings: The Django settings object.
    """
    if not (settings.STORMPATH_ID and settings.STORMPATH_SECRET):
        raise ImproperlyConfigured('Both STORMPATH_ID and STORMPATH_SECRET must be specified in settings.py.')

    if not settings.STORMPATH_APPLICATION:
        raise ImproperlyConfigured('STORMPATH_APPLICATION must be specified in settings.py.')


def organization_if_any(settings, CLIENT):
    """Obtain instance of organization if STORMPATH_ORGANIZATION_NAME_KEY set, otherwise None.

    :param obj settings: The Django settings object.
    :param obj CLIENT: The Python SDK client object."""
    if hasattr(settings, 'STORMPATH_ORGANIZATION_NAME_KEY'):
        found = CLIENT.organizations.query(name_key=settings.STORMPATH_ORGANIZATION_NAME_KEY)
        if len(found) != 1:
            raise ObjectDoesNotExist('No organization found matching STORMPATH_ORGANIZATION_NAME_KEY')
        return found[0]
