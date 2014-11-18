from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import include
from django.conf.urls.defaults import url

urlpatterns = patterns(
    '',
    url(r'^engine_version$', 'openquake.server.views.get_engine_version'),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
)
