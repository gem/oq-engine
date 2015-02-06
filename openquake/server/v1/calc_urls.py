from django.conf.urls import patterns, url

# each url is prefixed with /v1/calc/
urlpatterns = patterns(
    'openquake.server.views',
    url(r'^(hazard|risk)$', 'calc'),
    url(r'^(\d+)$', 'calc_info'),
    url(r'^(\d+)/results$', 'calc_results'),
    url(r'^result/(\d+)$', 'get_result'),
    url(r'^run$', 'run_calc'),
)
