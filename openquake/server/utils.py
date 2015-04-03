from django.conf import settings

def oq_server_context_processor(request):
    """
    A custom context processor which allows injection of additional
    context variables.
    """

    context = {}

    context['oq_engine_server_url'] = '//' + request.META.get('HTTP_HOST', 'localhost:8000')

    return context

