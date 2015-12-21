from django.conf import settings
from django.conf.urls import patterns, url, include


urlpatterns = patterns(
    '',

    url(r'^engine_version$', 'openquake.server.views.get_engine_version'),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
    url(r'^v1/valid/', 'openquake.server.views.validate_nrml'),
    url(r'^engine/?$', 'openquake.server.views.web_engine', name="index"),
    url(r'^engine/(\d+)/outputs$',
        'openquake.server.views.web_engine_get_outputs', name="outputs"),
    url(r'^engine/license$', 'openquake.server.views.license',
        name="license"),
)

if settings.LOCKDOWN:
    from django.contrib import admin

    admin.autodiscover()
    urlpatterns += patterns(
        '',

        url(r'^admin/', include(admin.site.urls)),
        url(r'^accounts/login/$', 'django.contrib.auth.views.login',
            {'template_name': 'account/login.html'}, name="login"),
        url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
            {'template_name': 'account/logout.html'}, name="logout"),
    )
