import getpass

from django.conf import settings
from openquake.engine import __version__ as oqversion


def get_user(request):
    """
    Returns the real username if authentication support is enabled and user is
    authenticated, otherwise it returns "platform" as user for backward
    compatibility.
    Returns also if the user is 'superuser' or not.
    """

    is_super = False
    if hasattr(request, 'user'):
        if request.user.is_authenticated():
            name = request.user.username
        if request.user.is_superuser:
            is_super = True
    else:
        name = (settings.DEFAULT_USER if
                hasattr(settings, 'DEFAULT_USER') else getpass.getuser())

    return {'name': name, 'is_super': is_super}


def oq_server_context_processor(request):
    """
    A custom context processor which allows injection of additional
    context variables.
    """

    context = {}

    context['oq_engine_server_url'] = ('//' +
                                       request.META.get('HTTP_HOST',
                                                        'localhost:8000'))
    context['oq_engine_version'] = oqversion

    return context
