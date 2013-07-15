from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

# each url is prefixed with /calc/
urlpatterns = patterns(
    'openquakeserver.engine.views',
    url(r'^hazard/$', 'calc_hazard'),
    url(r'^hazard/(\d+)/$', 'calc_hazard_info'),

    url(r'^risk/$', 'calc_risk'),
    url(r'^risk/(\d+)/$', 'calc_risk_info'),
)
