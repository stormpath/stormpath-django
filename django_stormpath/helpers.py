"""Library helpers."""


from django.core.exceptions import ImproperlyConfigured


def validate_settings(settings):
    """Ensure all user-supplied settings exist, or throw a useful error message.

    :param obj settings: The Django settings object.
    """
    if not (settings.STORMPATH_ID and settings.STORMPATH_SECRET):
        raise ImproperlyConfigured('Both STORMPATH_ID and STORMPATH_SECRET must be specified in settings.py.')

    if not settings.STORMPATH_APPLICATION:
        raise ImproperlyConfigured('STORMPATH_APPLICATION must be specified in settings.py.')
