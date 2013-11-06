from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import include
from django.conf.urls.defaults import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = patterns(
    '',
    url(r'^v1/calc/', include('openquakeserver.engine.v1.calc_urls')),
)

urlpatterns += staticfiles_urlpatterns()
