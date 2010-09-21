# views.py
# From geographic_admin/world/views.py

from django.conf import settings
from django.shortcuts import render_to_response

def welcome(request):
    """
    Create a Welcome Page for GeoDjango with Template as a string
    """
    if 'django.contrib.gis' in settings.INSTALLED_APPS:
        return render_to_response('welcome.html', {})
    else:
        return render_to_response('welcome_error.html', {})

