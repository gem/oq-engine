from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^engine_version$', 'openquake.server.views.get_engine_version'),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
    url(r'^engine$', 'openquake.server.views.web_engine', name="index"),
    url(r'^engine/(\d+)/outputs$',
        'openquake.server.views.web_engine_get_outputs', name="outputs"),
    url(r'^engine/license$', 'openquake.server.views.license',
        name="license"),
)
