from openquake.engine import __version__ as oqversion


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
