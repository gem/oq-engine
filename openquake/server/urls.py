from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^engine_version$', 'openquake.server.views.get_engine_version'),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
)
