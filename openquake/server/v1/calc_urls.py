from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

# each url is prefixed with /v1/calc/
urlpatterns = patterns(
    'openquake.server.views',
    url(r'^(hazard|risk)$', 'calc'),
    url(r'^(hazard|risk)/(\d+)$', 'calc_info'),
    url(r'^(hazard|risk)/(\d+)/results$', 'calc_results'),
    url(r'^(hazard|risk)/result/(\d+)$', 'get_result'),
    url(r'^(hazard|risk)/run$', 'run_calc'),
)
