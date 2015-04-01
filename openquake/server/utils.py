from django.conf import settings

def oq_server_context_processor(request):
    """
    A custom context processor which allows injection of additional
    context variables.
    """

    context = {}

    context['oq_engine_server_url'] = '//' + request.META.get('SERVER_NAME', 'localhost') + ':' + request.META.get('SERVER_PORT', '8000')

    return context

