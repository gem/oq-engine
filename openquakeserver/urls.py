from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import include
from django.conf.urls.defaults import url

urlpatterns = patterns(
    '',
    url(r'^v1/calc/', include('openquakeserver.engine.v1.calc_urls')),
)
