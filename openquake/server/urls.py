from django.conf.urls import patterns, url, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'admin/login.html'}, name="login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        name="logout"),

    url(r'^engine_version$', 'openquake.server.views.get_engine_version'),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
    url(r'^engineweb$', 'openquake.server.views.engineweb', name="index"),
    url(r'^engineweb/(\d+)/outputs$',
        'openquake.server.views.engineweb_get_outputs', name="outputs"),
    url(r'^engineweb/license$', 'openquake.server.views.license',
        name="license"),
)
