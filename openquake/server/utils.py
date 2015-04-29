from openquake.engine import __version__ as oqversion


def getusername(request):
    """
    Return the real user is authentication support is enabled and user is
    authenticated, otherwise it returns "platform" as user for backward
    compatibility.
    """

    user_name = (request.user.username if hasattr(request, 'user') and
                 request.user.is_authenticated() else 'platform')

    return user_name


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
